from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_email: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    action: str
    success: bool
    source: str


class UserOut(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True