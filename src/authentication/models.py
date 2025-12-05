"""Database models for authentication and user management.

This module defines SQLModel classes representing database tables for
users (planners and vendors) and OTP records. Uses PostgreSQL-specific
types (JSONB, TIMESTAMP) for rich data storage and timezone support.
"""

from sqlmodel import SQLModel, Field, Column
import uuid
from datetime import datetime, timezone, timedelta
import sqlalchemy.dialects.postgresql as pg
from typing import Optional, List, Dict
from enum import Enum

def utc_now():
    """Generate current UTC timestamp.
    
    Provides timezone-aware datetime for model default values.
    Ensures consistent timestamp handling across the application.
    
    Returns:
        datetime: Current UTC time with timezone information.
    """
    return datetime.now(timezone.utc)

class VerificationStatus(str, Enum):
    """Business verification status enumeration.
    
    Tracks the verification state of vendor business accounts.
    Used for compliance and trust indicators on the platform.
    """
    pending = "pending"
    verified = "verified"
    rejected = "rejected"

class Address(SQLModel):
    """Address structure for JSONB storage.
    
    Embedded model for storing address data in PostgreSQL JSONB columns.
    Provides flexibility for varying address formats across regions.
    """
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipCode: Optional[str] = None

class SocialMedia(SQLModel):
    """Social media links structure for JSONB storage.
    
    Embedded model for storing social media profile URLs in JSONB columns.
    Allows vendors to showcase their online presence.
    """
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None

class PriceRange(SQLModel):
    """Price range structure for JSONB storage.
    
    Embedded model for storing vendor service pricing information.
    Includes currency specification for international support.
    """
    min: float = 0
    max: float = 0
    currency: str = "NGN"

class Planners(SQLModel, table=True):
    """Event planners user table.
    
    Represents users who plan and organize events on the platform.
    Contains core authentication fields and profile information.
    Separate from vendors to allow role-specific features.
    
    Attributes:
        user_id: Primary key, auto-generated UUID.
        fullName: User's complete name for display.
        email: Unique email address for authentication.
        password_hash: Bcrypt hashed password (never store plaintext).
        profile_picture: Optional URL to user's profile image.
        email_verified: Flag indicating email verification status.
        role: Fixed as "planner" for this table.
        created_at: Account creation timestamp (UTC).
    """
    __tablename__ = "planners"
    
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fullName: str
    email: str
    password_hash: str
    profile_picture: Optional[str] = None
    email_verified: bool = False
    role: str = Field(default="planner")
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(pg.TIMESTAMP(timezone=True))
    )

class Vendors(SQLModel, table=True):
    """Service vendors user table.
    
    Represents businesses providing event-related services (catering,
    venues, photography, etc.). Includes extended business information
    and verification fields beyond basic user data.
    
    Attributes:
        user_id: Primary key, auto-generated UUID.
        fullName: Contact person's full name.
        email: Unique business email for authentication.
        password_hash: Bcrypt hashed password (never store plaintext).
        email_verified: Flag indicating email verification status.
        role: Fixed as "vendor" for this table.
        business_name: Official business/company name.
        business_description: Detailed service description.
        category: Service category (e.g., catering, venue, photography).
        location: Primary business location string.
        address: Structured address stored as JSONB.
        social_media: Social media URLs stored as JSONB.
        price_range: Service pricing information stored as JSONB.
        portfolio: Array of portfolio image URLs stored as JSONB.
        services: Array of offered services stored as JSONB.
        cac_number: Corporate Affairs Commission registration number (Nigeria).
        cac_document: URL to uploaded CAC certificate.
        website: Business website URL.
        availability: Current booking availability flag.
        business_verified: Manual verification status flag.
        business_verification_Status: Current stage in verification workflow.
        created_at: Account creation timestamp (UTC).
    """
    __tablename__ = "vendors"
    
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fullName: str
    email: str = Field(unique=True)
    password_hash: str
    email_verified: bool = False
    role: str = Field(default="vendor")
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    
    # JSONB fields for flexible structured data
    address: Dict = Field(default_factory=dict, sa_column=Column(pg.JSONB))
    social_media: Dict = Field(default_factory=dict, sa_column=Column(pg.JSONB))
    price_range: Dict = Field(default_factory=dict, sa_column=Column(pg.JSONB))
    portfolio: List[str] = Field(default_factory=list, sa_column=Column(pg.JSONB))
    services: List[str] = Field(default_factory=list, sa_column=Column(pg.JSONB))
    
    # Business verification documents
    cac_number: Optional[str] = None
    cac_document: Optional[str] = None
    website: Optional[str] = None
    
    # Business status flags
    availability: bool = True
    business_verified: bool = False
    business_verification_Status: VerificationStatus = VerificationStatus.pending
    
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(pg.TIMESTAMP(timezone=True))
    )

def get_expiry_time(minutes):
    """Generate OTP expiration timestamp.
    """
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

class SignupOtp(SQLModel, table=True):
   
    __tablename__ = "signupOtp"
    
    otp_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    otp: str
    user_id: uuid.UUID
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(pg.TIMESTAMP(timezone=True)))
    expires: datetime = Field(
        default_factory=lambda: get_expiry_time(10),
        sa_column=Column(pg.TIMESTAMP(timezone=True)))

class ForgotPasswordOtp(SQLModel, table=True):
    """Password reset OTP records table.
    
    Stores one-time passwords sent to users for password reset
    workflows. Records expire after 10 minutes for security.
    
    Attributes:
        otp_id: Primary key, auto-generated UUID.
        otp: The verification code (6-digit numeric string).
        user_id: Reference to user requesting password reset (not a foreign key).
        created_at: OTP generation timestamp (UTC).
        expires: Expiration timestamp (10 minutes after creation).
    """
    __tablename__ = "forgotPasswordOtp"
    
    otp_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    otp: str
    user_id: uuid.UUID
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(pg.TIMESTAMP(timezone=True)))
    expires: datetime = Field(
        default_factory=lambda: get_expiry_time(10),
        sa_column=Column(pg.TIMESTAMP(timezone=True)))

