from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, JSON, Float
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    RECEPCAO = "RECEPCAO"
    TERAPEUTA = "TERAPEUTA"
    SUPERVISOR = "SUPERVISOR"
    FAMILIA = "FAMILIA"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    cpf = Column(String, unique=True, nullable=True)
    
    # NOVOS CAMPOS - Fase 6 (Profissionais)
    full_name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    council_registry = Column(String, nullable=True)
    specialty = Column(String, nullable=True)

    appointments = relationship("Appointment", back_populates="therapist", foreign_keys="Appointment.therapist_id")

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    diagnosis = Column(String, nullable=False)
    
    # Perfil Sensorial / Clínico
    hip_auditiva = Column(Boolean, default=False)
    hip_visual = Column(Boolean, default=False)
    nao_verbal = Column(Boolean, default=False)
    
    # Faturamento / Planos
    sessions_authorized = Column(Integer, default=0)
    sessions_used = Column(Integer, default=0)
    
    # NOVOS CAMPOS - Fase 6 (Dados Adicionais)
    health_insurance = Column(String, nullable=True)
    father_name = Column(String, nullable=True)
    mother_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    parent_cpf = Column(String, nullable=True)
    
    # Relações
    appointments = relationship("Appointment", back_populates="patient")
    evolutions = relationship("ClinicalEvolution", back_populates="patient")
    goals = relationship("Goal", back_populates="patient")
    documents = relationship("Document", back_populates="patient")

class Goal(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="Em andamento")
    progress = Column(Float, default=0.0) 
    
    patient = relationship("Patient", back_populates="goals")

class ResourceRoom(Base):
    __tablename__ = 'resource_rooms'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    appointments = relationship("Appointment", back_populates="room")

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    therapist_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('resource_rooms.id'), nullable=False)
    date_str = Column(String, nullable=False)
    time_str = Column(String, nullable=False)

    patient = relationship("Patient", back_populates="appointments")
    therapist = relationship("User", back_populates="appointments", foreign_keys=[therapist_id])
    room = relationship("ResourceRoom", back_populates="appointments")

class ClinicalEvolution(Base):
    __tablename__ = 'clinical_evolutions'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    date_str = Column(String, nullable=False)
    area = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False) 
    
    # NOVOS CAMPOS - Fase 4
    ai_draft_text = Column(String, nullable=True)
    guardian_signature = Column(String, nullable=True) # EVV compliance
    
    # Telemetria EVV e Carimbo Sincronizado - Fase 9
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    signed_at = Column(String, nullable=True)
    
    patient = relationship("Patient", back_populates="evolutions")

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    title = Column(String, nullable=False)
    upload_date = Column(String, nullable=False)
    # Em produção seria a URL do S3/Blob. Simulando com um texto/link local.
    file_content = Column(String, nullable=False) 
    
    patient = relationship("Patient", back_populates="documents")

class Specialty(Base):
    __tablename__ = 'specialties'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
