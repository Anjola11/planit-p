from sqlmodel import SQLModel, Field, Column
import uuid
from datetime import datetime, timezone
import sqlalchemy.dialects.postgresql as pg
from typing import Optional, List, Dict
from enum import Enum


def utc_now():
    return datetime.now(timezone.utc)


class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class Address(SQLModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipCode: Optional[str] = None


class SocialMedia(SQLModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None


class PriceRange(SQLModel):
    min: float = 0
    max: float = 0
    currency: str = "NGN"


class Planners(SQLModel, table=True):
    __tablename__ = "planners"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fullName: str
    email: str
    password_hash: str
    profile_picture: Optional[str] = None
    email_verified: bool = False
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(pg.TIMESTAMP(timezone=True))
    )


class Vendors(SQLModel, table=True):
    __tablename__ = "vendors"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fullName: str
    email: str = Field(unique=True)
    password_hash: str
    email_verified: bool = False

    business_name: Optional[str] = None
    business_description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None

    # JSONB fields
    address: Dict = Field(default_factory=dict, sa_column=Column(pg.JSONB))
    social_media: Dict = Field(default_factory=dict, sa_column=Column(pg.JSONB))
    price_range: Dict = Field(default_factory=dict, sa_column=Column(pg.JSONB))

    portfolio: List[str] = Field(default_factory=list, sa_column=Column(pg.JSONB))
    services: List[str] = Field(default_factory=list, sa_column=Column(pg.JSONB))

    cac_number: Optional[str] = None
    cac_document: Optional[str] = None
    website: Optional[str] = None

    availability: bool = True
    business_verified: bool = False
    business_verification_Status: VerificationStatus = VerificationStatus.pending

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(pg.TIMESTAMP(timezone=True))
    )
