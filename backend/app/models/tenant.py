from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class TenantBase(BaseModel):
    name: str
    description: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    is_active: bool = True
    has_whatsapp_integration: bool = False
    has_calendar_integration: bool = False
    chat_widget_config: dict = Field(default_factory=dict)

class TenantCreate(TenantBase):
    owner_id: UUID

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    has_whatsapp_integration: Optional[bool] = None
    has_calendar_integration: Optional[bool] = None
    chat_widget_config: Optional[dict] = None

class TenantInDB(TenantBase):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    api_key: str

class Tenant(TenantInDB):
    pass