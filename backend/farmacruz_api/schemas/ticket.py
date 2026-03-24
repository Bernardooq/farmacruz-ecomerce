from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from db.base import TicketStatus, TicketPriority, CreatorType, SenderType

# -- Mensajes -- #

class TicketMessageBase(BaseModel):
    content: str

class TicketMessageCreate(TicketMessageBase):
    pass

class TicketMessageResponse(TicketMessageBase):
    message_id: int
    ticket_id: int
    sender_id: int
    sender_type: SenderType
    sender_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# -- Tickets -- #

class TicketBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    priority: TicketPriority = TicketPriority.medium

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[int] = None

class TicketResponse(TicketBase):
    ticket_id: int
    status: TicketStatus
    creator_id: int
    creator_type: CreatorType
    creator_name: Optional[str] = None
    assigned_to: Optional[int]
    assigned_to_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketDetailResponse(TicketResponse):
    messages: List[TicketMessageResponse] = []

class TicketPaginatedResponse(BaseModel):
    items: List[TicketResponse]
    total: int
