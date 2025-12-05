from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    VENDOR = "vendor"
    PLANNER = "planner"

class Address(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipCode: Optional[str] = None

class SocialMedia(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None

class PriceRange(BaseModel):
    min: float = 0
    max: float = 0
    currency: str = "NGN"


class UserInput(BaseModel):
    fullName: str
    email: str
    password: str
    role: UserRole

class User(BaseModel):
    user_id: uuid.UUID 
    email: str 
    email_verified: bool 
    role: str
    created_at: datetime 

class UserCreateResponse(BaseModel):
    success: bool
    message: str
    data: User

class VerifyOtpInput(BaseModel):
    user_id: uuid.UUID
    otp: str
    role: str 

class LoginInput(BaseModel):
    email: str
    password: str
    role: UserRole

class LoginData(BaseModel):
    user_id: uuid.UUID
    fullName: str
    email: str
    email_verified: bool
    role: str
    created_at: datetime
    access_token: str
    refresh_token: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: LoginData