from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime
from typing import Optional, List

# Farmer Authentication Schemas
class FarmerRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    location: Optional[str] = None


class FarmerRegisterResponse(BaseModel):
    farmer_id: int
    message: str


class FarmerLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class FarmerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    location: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# Plant Management Schemas
class PlantCreate(BaseModel):
    crop_name: str = Field(..., min_length=2, max_length=50)
    plant_name: str = Field(..., min_length=2, max_length=100)


class PlantResponse(BaseModel):
    plant_id: str
    crop_name: str
    plant_name: str
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def format_plant_id(cls, data):
        # We format the integer PK (id) from the DB to user-facing "plant_id" like "P001"
        if hasattr(data, "id"):
            data.plant_id = f"P{data.id:03d}"
        elif isinstance(data, dict) and "id" in data:
            data["plant_id"] = f"P{data['id']:03d}"
        return data


# Report & Recovery History Schemas
import json

class ReportResponse(BaseModel):
    id: int
    plant_id: str
    image_path: str
    disease: str
    severity: str
    confidence: float
    tips: List[str]
    created_at: datetime
    trend: Optional[str] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def format_report_fields(cls, data):
        # Format plant_id to P001 format
        if hasattr(data, "plant_id"):
            data.plant_id = f"P{data.plant_id:03d}"
        elif isinstance(data, dict) and "plant_id" in data:
            data["plant_id"] = f"P{data['plant_id']:03d}"

        # Set trend dynamically from recovery_record relationship if present
        if hasattr(data, "recovery_record") and data.recovery_record:
            data.trend = data.recovery_record.trend
        elif isinstance(data, dict) and "recovery_record" in data and data["recovery_record"]:
            rec = data["recovery_record"]
            data["trend"] = rec.trend if hasattr(rec, "trend") else rec.get("trend")

        # Deserialize tips from JSON string to list
        if hasattr(data, "tips") and isinstance(data.tips, str):
            try:
                data.tips = json.loads(data.tips)
            except Exception:
                data.tips = [data.tips]
        elif isinstance(data, dict) and "tips" in data and isinstance(data["tips"], str):
            try:
                data["tips"] = json.loads(data["tips"])
            except Exception:
                data["tips"] = [data["tips"]]
        return data


class RecoveryHistoryItem(BaseModel):
    date: str  # YYYY-MM-DD
    severity: str
    score: int


class PlantRecoveryResponse(BaseModel):
    plant_id: str
    history: List[RecoveryHistoryItem]
    overall_trend: str
