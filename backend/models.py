from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plants = relationship("Plant", back_populates="farmer", cascade="all, delete-orphan")


class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    crop_name = Column(String, nullable=False)
    plant_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    farmer = relationship("Farmer", back_populates="plants")
    reports = relationship("DiseaseReport", back_populates="plant", cascade="all, delete-orphan")
    recovery_records = relationship("RecoveryRecord", back_populates="plant", cascade="all, delete-orphan")


class DiseaseReport(Base):
    __tablename__ = "disease_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    image_path = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    tips = Column(Text, nullable=False)  # Serialized JSON string of care tips list
    created_at = Column(DateTime, default=datetime.utcnow)

    plant = relationship("Plant", back_populates="reports")
    recovery_record = relationship("RecoveryRecord", back_populates="report", uselist=False, cascade="all, delete-orphan")


class RecoveryRecord(Base):
    __tablename__ = "recovery_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("disease_reports.id"), nullable=False)
    severity_score = Column(Integer, nullable=False)  # 1 = Mild, 2 = Moderate, 3 = Severe
    trend = Column(String, nullable=False)  # Improving/Stable/Worsening/Baseline
    created_at = Column(DateTime, default=datetime.utcnow)

    plant = relationship("Plant", back_populates="recovery_records")
    report = relationship("DiseaseReport", back_populates="recovery_record")
