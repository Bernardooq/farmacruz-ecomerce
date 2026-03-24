from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_user, get_current_active_user, get_current_admin_user
from db.base import TicketStatus, TicketPriority, CreatorType, SenderType, User, Customer, UserRole
from schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketDetailResponse, TicketMessageCreate, TicketMessageResponse, TicketPaginatedResponse
from crud.crud_ticket import (
    create_ticket, get_ticket, update_ticket, add_ticket_message, attach_names_to_tickets, attach_names_to_ticket_messages,
    get_tickets_for_admin, get_tickets_for_marketing, get_tickets_for_user_or_customer
)

router = APIRouter()

def get_sender_info(current_user):
    # Retorna tupla: (entity_id, creator_type_enum)
    if hasattr(current_user, 'role'):
        return current_user.user_id, CreatorType.user
    else:
        return current_user.customer_id, CreatorType.customer

""" GET / - Lista de tickets filtrada por rol """
@router.get("/", response_model=TicketPaginatedResponse)
def read_tickets(
    skip: int = 0, limit: int = 100,
    status_filter: Optional[TicketStatus] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if hasattr(current_user, 'role'):
        if current_user.role == UserRole.admin:
            tickets, total = get_tickets_for_admin(db, skip=skip, limit=limit, status_filter=status_filter)
        elif current_user.role == UserRole.marketing:
            tickets, total = get_tickets_for_marketing(db, marketing_id=current_user.user_id, skip=skip, limit=limit, status_filter=status_filter)
        else:
            tickets, total = get_tickets_for_user_or_customer(db, current_user.user_id, CreatorType.user, skip, limit)
    else:
        tickets, total = get_tickets_for_user_or_customer(db, current_user.customer_id, CreatorType.customer, skip, limit)
        
    return {"items": tickets, "total": total}


""" POST / - Crear ticket """
@router.post("/", response_model=TicketResponse)
def create_new_ticket(
    ticket_in: TicketCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entity_id, creator_type = get_sender_info(current_user)
    ticket = create_ticket(db, ticket=ticket_in, creator_id=entity_id, creator_type=creator_type)
    return attach_names_to_tickets(db, [ticket])[0]


""" GET /{id} - Ver detalle de ticket y mensajes """
@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def read_ticket_detail(
    ticket_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Validar permisos
    if not hasattr(current_user, 'role') or current_user.role == UserRole.seller:
        entity_id, c_type = get_sender_info(current_user)
        if ticket.creator_id != entity_id or ticket.creator_type != c_type:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este ticket")
    # Nota: para hacerlo 100% seguro habria que verificar si Marketing tiene permiso sobre el customer/seller del ticket.
    # Por ahora permitimos que puedan ver el detalle si tienen el ID (es a traves del dashboard).
    
    return ticket


""" POST /{id}/messages - Agregar mensaje al ticket """
@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse)
def add_message(
    ticket_id: int,
    msg_in: TicketMessageCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
    entity_id, creator_type = get_sender_info(current_user)
    sender_type = SenderType.user if creator_type == CreatorType.user else SenderType.customer
    
    msg = add_ticket_message(db, ticket_id, sender_id=entity_id, sender_type=sender_type, content=msg_in.content)
    # Return formatted message with name
    ticket.messages.append(msg)
    ticket = attach_names_to_ticket_messages(db, ticket)
    return ticket.messages[-1]


class TicketStatusUpdate(BaseModel):
    status: TicketStatus

""" PUT /{id}/status - Cambiar estado """
@router.put("/{ticket_id}/status", response_model=TicketResponse)
def change_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.admin, UserRole.marketing]:
        raise HTTPException(status_code=403, detail="Solo admin y marketing pueden cambiar el estado")
        
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
    ticket = update_ticket(db, ticket_id, TicketUpdate(status=status_update.status))
    return attach_names_to_tickets(db, [ticket])[0]

""" PUT /{id}/escalate - Escalar ticket """
@router.put("/{ticket_id}/escalate", response_model=TicketResponse)
def escalate_ticket(
    ticket_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.admin, UserRole.marketing]:
        raise HTTPException(status_code=403, detail="Solo admin y marketing pueden escalar tickets")
        
    ticket = update_ticket(db, ticket_id, TicketUpdate(status=TicketStatus.escalated))
    return attach_names_to_tickets(db, [ticket])[0]

""" PUT /{id}/de-escalate - Desescalar ticket (Solo Admin) """
@router.put("/{ticket_id}/de-escalate", response_model=TicketResponse)
def de_escalate_ticket(
    ticket_id: int,
    current_user=Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
    if ticket.status != TicketStatus.escalated:
        raise HTTPException(status_code=400, detail="Solo se pueden desescalar tickets en estado escalado")
        
    ticket = update_ticket(db, ticket_id, TicketUpdate(status=TicketStatus.in_progress))
    return attach_names_to_tickets(db, [ticket])[0]


""" PUT /{id}/assign - Tomar/asignarse el ticket """
@router.put("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.admin, UserRole.marketing]:
        raise HTTPException(status_code=403, detail="Solo admin y marketing pueden tomar tickets")
        
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
    status = TicketStatus.in_progress if ticket.status == TicketStatus.open else ticket.status
    
    ticket = update_ticket(db, ticket_id, TicketUpdate(assigned_to=current_user.user_id, status=status))
    return attach_names_to_tickets(db, [ticket])[0]
