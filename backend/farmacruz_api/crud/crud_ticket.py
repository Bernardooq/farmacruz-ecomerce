from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from db.base import Ticket, TicketMessage, TicketStatus, CreatorType, SenderType, UserRole, CustomerInfo, GroupSeller, User as UserModel, Customer
from schemas.ticket import TicketCreate, TicketUpdate, TicketMessageCreate
from crud.crud_sales_group import get_user_groups

def create_ticket(db: Session, ticket: TicketCreate, creator_id: int, creator_type: CreatorType) -> Ticket:
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        creator_id=creator_id,
        creator_type=creator_type,
        status=TicketStatus.open
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def attach_names_to_tickets(db: Session, tickets: List[Ticket]) -> List[Ticket]:
    if not tickets: return tickets
    
    user_ids = set()
    customer_ids = set()
    for t in tickets:
        if t.creator_type == CreatorType.user: user_ids.add(t.creator_id)
        elif t.creator_type == CreatorType.customer: customer_ids.add(t.creator_id)
        if t.assigned_to: user_ids.add(t.assigned_to)

    user_map = {}
    if user_ids:
        users = db.query(UserModel.user_id, UserModel.full_name, UserModel.username).filter(UserModel.user_id.in_(user_ids)).all()
        user_map = {u.user_id: u.full_name or u.username for u in users}

    customer_map = {}
    if customer_ids:
        customers = db.query(Customer.customer_id, Customer.full_name, Customer.username).filter(Customer.customer_id.in_(customer_ids)).all()
        customer_map = {c.customer_id: c.full_name or c.username for c in customers}

    for t in tickets:
        if t.creator_type == CreatorType.user: t.creator_name = user_map.get(t.creator_id)
        elif t.creator_type == CreatorType.customer: t.creator_name = customer_map.get(t.creator_id)
        if t.assigned_to: t.assigned_to_name = user_map.get(t.assigned_to)

    return tickets

def attach_names_to_ticket_messages(db: Session, ticket: Ticket) -> Ticket:
    if not ticket or not ticket.messages: return ticket
    
    user_ids = set()
    customer_ids = set()
    for m in ticket.messages:
        if m.sender_type == SenderType.user: user_ids.add(m.sender_id)
        elif m.sender_type == SenderType.customer: customer_ids.add(m.sender_id)

    user_map, customer_map = {}, {}
    if user_ids:
        user_map = {u.user_id: u.full_name or u.username for u in db.query(UserModel.user_id, UserModel.full_name, UserModel.username).filter(UserModel.user_id.in_(user_ids)).all()}
    if customer_ids:
        customer_map = {c.customer_id: c.full_name or c.username for c in db.query(Customer.customer_id, Customer.full_name, Customer.username).filter(Customer.customer_id.in_(customer_ids)).all()}

    for m in ticket.messages:
        if m.sender_type == SenderType.user: m.sender_name = user_map.get(m.sender_id)
        elif m.sender_type == SenderType.customer: m.sender_name = customer_map.get(m.sender_id)

    return ticket

def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if ticket:
        ticket = attach_names_to_tickets(db, [ticket])[0]
        ticket = attach_names_to_ticket_messages(db, ticket)
    return ticket

def get_tickets_for_admin(db: Session, skip: int = 0, limit: int = 100, status_filter: Optional[TicketStatus] = None) -> tuple[List[Ticket], int]:
    query = db.query(Ticket)
    if status_filter: query = query.filter(Ticket.status == status_filter)
    total = query.count()
    tickets = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit).all()
    return attach_names_to_tickets(db, tickets), total

def get_tickets_for_marketing(db: Session, marketing_id: int, skip: int = 0, limit: int = 100, status_filter: Optional[TicketStatus] = None) -> tuple[List[Ticket], int]:
    # Marketing can see:
    # 1. Tickets they created
    # 2. Tickets assigned to them
    # 3. Tickets from Customers in their groups
    # 4. Tickets from Sellers in their groups
    
    group_ids = get_user_groups(db, marketing_id)
    if not group_ids:
        # Se solo ve a si mismo o los suyos
        query = db.query(Ticket).filter(
            or_(
                and_(Ticket.creator_id == marketing_id, Ticket.creator_type == CreatorType.user),
                Ticket.assigned_to == marketing_id
            )
        )
    else:
        # Get Customers in those groups
        customer_ids_subquery = db.query(CustomerInfo.customer_id).filter(
            CustomerInfo.sales_group_id.in_(group_ids)
        ).scalar_subquery()
        
        # Get Sellers in those groups
        seller_ids_subquery = db.query(GroupSeller.seller_id).filter(
            GroupSeller.sales_group_id.in_(group_ids)
        ).scalar_subquery()
        
        query = db.query(Ticket).filter(
            or_(
                # Own tickets or assigned
                and_(Ticket.creator_id == marketing_id, Ticket.creator_type == CreatorType.user),
                Ticket.assigned_to == marketing_id,
                # Customers in groups
                and_(Ticket.creator_id.in_(customer_ids_subquery), Ticket.creator_type == CreatorType.customer),
                # Sellers in groups
                and_(Ticket.creator_id.in_(seller_ids_subquery), Ticket.creator_type == CreatorType.user)
            )
        )
        
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
        
    total = query.count()
    tickets = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit).all()
    return attach_names_to_tickets(db, tickets), total

def get_tickets_for_user_or_customer(db: Session, entity_id: int, entity_type: CreatorType, skip: int=0, limit: int=100) -> tuple[List[Ticket], int]:
    query = db.query(Ticket).filter(
        Ticket.creator_id == entity_id,
        Ticket.creator_type == entity_type
    )
    total = query.count()
    tickets = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit).all()
    return attach_names_to_tickets(db, tickets), total

def update_ticket(db: Session, ticket_id: int, update_data: TicketUpdate) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
        
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(db_ticket, field, value)
        
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def add_ticket_message(db: Session, ticket_id: int, sender_id: int, sender_type: SenderType, content: str) -> TicketMessage:
    msg = TicketMessage(
        ticket_id=ticket_id,
        sender_id=sender_id,
        sender_type=sender_type,
        content=content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
