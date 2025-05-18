from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    company_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

class User(UserInDB):
    pass