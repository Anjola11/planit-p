"""Pydantic schemas for authentication API.

This module defines the request and response models used in authentication
endpoints. These schemas provide automatic validation, serialization, and
API documentation via FastAPI's integration with Pydantic.
"""

from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    """Enumeration of available user roles in the system.
    
    Restricts role values to predefined options for type safety
    and validation. Used in signup and login operations.
    """
    VENDOR = "vendor"
    PLANNER = "planner"

class Address(BaseModel):
    """Address information schema.
    
    Represents a physical address with optional fields for flexibility.
    Used primarily for vendor business location information.
    """
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipCode: Optional[str] = None

class SocialMedia(BaseModel):
    """Social media links schema.
    
    Stores social media profile URLs for user or business accounts.
    All fields are optional to accommodate varying social media presence.
    """
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None

class PriceRange(BaseModel):
    """Price range schema for vendor services.
    
    Represents the pricing boundaries for vendor offerings with
    currency specification. Defaults to Nigerian Naira (NGN).
    """
    min: float = 0
    max: float = 0
    currency: str = "NGN"

class UserInput(BaseModel):
    """User registration request schema.
    
    Validates and structures data for new user signup. Requires
    all fields to create a complete user account.
    """
    fullName: str
    email: str
    password: str
    role: UserRole

class User(BaseModel):
    """Base user response schema.
    
    Represents the core user data returned after registration
    and verification. Excludes sensitive fields like password hash.
    """
    user_id: uuid.UUID 
    email: str 
    email_verified: bool 
    role: str
    created_at: datetime 

class UserCreateResponse(BaseModel):
    """Standard response for user creation operations.
    
    Wraps user data in a consistent response structure with
    success indicator and descriptive message.
    """
    success: bool
    message: str
    data: User

class VerifyOtpInput(BaseModel):
    """OTP verification request schema.
    
    Contains the data needed to validate an email verification code.
    Requires user_id to identify the account and role for model selection.
    """
    user_id: uuid.UUID
    otp: str
    role: str 

class LoginInput(BaseModel):
    """User login request schema.
    
    Validates authentication credentials. Role is required to
    determine which user table (planners/vendors) to query.
    """
    email: str
    password: str
    role: UserRole

class LoginData(BaseModel):
    """Authenticated user response with tokens.
    
    Extended user data returned after successful login, including
    JWT tokens for API authentication. Contains both access and
    refresh tokens for session management.
    """
    user_id: uuid.UUID
    fullName: str
    email: str
    email_verified: bool
    role: str
    created_at: datetime
    access_token: str
    refresh_token: str

class LoginResponse(BaseModel):
    """Standard response for login operations.
    
    Wraps login data (including tokens) in a consistent response
    structure with success indicator and descriptive message.
    """
    success: bool
    message: str
    data: LoginData