"""Models for TravelIntel briefing requests and responses."""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EmergencyNumber(BaseModel):
    label: str = ""
    number: str = ""


class ConsulateInfo(BaseModel):
    name: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""


class HospitalInfo(BaseModel):
    name: str = ""
    address: str = ""
    phone: str = ""


class BriefingFacts(BaseModel):
    risk_grade: str = ""
    security_snapshot: str = ""
    emergency_numbers: List[EmergencyNumber] = Field(default_factory=list)
    consulate: ConsulateInfo = Field(default_factory=ConsulateInfo)
    hospitals: List[HospitalInfo] = Field(default_factory=list)
    legal_restrictions: List[str] = Field(default_factory=list)
    cultural_dos: List[str] = Field(default_factory=list)
    cultural_donts: List[str] = Field(default_factory=list)
    operational_guidance: List[str] = Field(default_factory=list)
    key_locations: List[str] = Field(default_factory=list)


class BriefingRequest(BaseModel):
    name: str
    nationality: str
    destination_country: str
    destination_city: str
    travel_date: Optional[date] = None
    trip_type: str


class BriefingFullRequest(BriefingRequest):
    paid: bool = False
    payment_reference: Optional[str] = None


class BriefingPreview(BaseModel):
    briefing_id: str
    risk_grade: str
    security_snapshot: str
    emergency_numbers: List[EmergencyNumber]
    cached: bool
    created_at: datetime


class BriefingFull(BaseModel):
    briefing_id: str
    facts: BriefingFacts
    narrative: str
    cached: bool
    created_at: datetime
    paid: bool


class PaymentStatus(BaseModel):
    paid: bool = False
    payment_reference: Optional[str] = None
