from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID, uuid4

class MessageBase(BaseModel):
    content: str
    role: Literal["user", "assistant", "system"]

class Message(MessageBase):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class ConversationBase(BaseModel):
    tenant_id: UUID
    session_id: str
    customer_identifier: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationInDB(ConversationBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class Conversation(ConversationInDB):
    messages: List[Message] = []