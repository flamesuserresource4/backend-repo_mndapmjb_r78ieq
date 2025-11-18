"""
Database Schemas for Mella (Ambulance on-demand)

Each Pydantic model corresponds to a MongoDB collection. The collection name is
lowercase of the class name (e.g., Ambulance -> "ambulance").
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class User(BaseModel):
    name: str
    phone: str = Field(..., description="Ethiopian phone number")
    role: Literal["patient", "driver", "dispatcher"] = "patient"
    email: Optional[EmailStr] = None

class Ambulance(BaseModel):
    plate: str = Field(..., description="License plate")
    type: Literal["basic", "advanced", "icu"] = "basic"
    driver_name: str
    driver_phone: str
    provider: Optional[str] = Field(None, description="Hospital or EMS provider")
    location: Location
    available: bool = True

class Ride(BaseModel):
    patient_name: str
    patient_phone: str
    pickup: Location
    destination: Optional[str] = None
    priority: Literal["normal", "urgent", "critical"] = "normal"
    status: Literal[
        "requested", "assigned", "enroute", "picked_up", "arrived_hospital", "completed", "canceled"
    ] = "requested"
    ambulance_id: Optional[str] = None
