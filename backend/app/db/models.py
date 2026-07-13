from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Worker(Base):
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)
    
    risk_logs = relationship("RiskLog", back_populates="worker")
    incidents = relationship("Incident", back_populates="worker")

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    rtsp_url = Column(String)
    location = Column(String)
    
    zones = relationship("Zone", back_populates="camera")
    incidents = relationship("Incident", back_populates="camera")

class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    name = Column(String)
    # Store polygon coordinates as JSON e.g. [{"x": 10, "y": 20}, ...]
    polygon = Column(JSON) 
    risk_level = Column(String, default="CAUTION") # e.g. CAUTION, CRITICAL
    
    camera = relationship("Camera", back_populates="zones")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    incident_type = Column(String) # e.g. PPE_VIOLATION, RESTRICTED_ZONE
    severity = Column(String) # e.g. CRITICAL, CAUTION
    details = Column(JSON) # Additional context
    
    camera = relationship("Camera", back_populates="incidents")
    worker = relationship("Worker", back_populates="incidents")

class RiskLog(Base):
    __tablename__ = "risk_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    risk_score = Column(Float)
    
    worker = relationship("Worker", back_populates="risk_logs")
