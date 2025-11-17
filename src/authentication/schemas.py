from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional, Dict, List


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

# User Input Schemas
class UserInput(BaseModel):
    fullName: str
    email: str
    password: str

# Planner Schemas
class PlannerCreate(BaseModel):
    id: uuid.UUID 
    email: str 
    email_verified: bool 
    created_at: datetime 

class PlannerCreateResponse(BaseModel):
    success: bool
    message: str
    data: PlannerCreate

class VendorCreate(BaseModel):
    id: uuid.UUID 
    email: str 
    email_verified: bool 
    created_at: datetime 

class VendorCreateResponse(BaseModel):
    success: bool
    message: str
    data: VendorCreate