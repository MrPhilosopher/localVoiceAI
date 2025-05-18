from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    file_path: str
    document_type: str  # pdf, text, etc.

class DocumentCreate(DocumentBase):
    tenant_id: UUID

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class DocumentInDB(DocumentBase):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    is_processed: bool = False
    embedding_status: str = "pending"  # pending, processing, completed, failed

class Document(DocumentInDB):
    pass