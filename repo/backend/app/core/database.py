from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from ..core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SurgerySession(Base):
    __tablename__ = "surgery_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    patient_id = Column(String(50), index=True)
    patient_name = Column(String(100))
    surgery_type = Column(String(200))
    primary_surgeon = Column(String(100))
    remote_expert = Column(String(100))
    operating_room = Column(String(50))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    video_source = Column(String(500))
    audio_source = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transcripts = relationship("Transcript", back_populates="surgery_session")
    audio_segments = relationship("AudioSegment", back_populates="surgery_session")
    surgery_summary = relationship("SurgerySummary", back_populates="surgery_session", uselist=False)


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("surgery_sessions.id"))
    speaker = Column(String(50))
    speaker_role = Column(String(20))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(Text)
    is_anatomical_term = Column(Boolean, default=False)
    anatomical_terms = Column(JSON, nullable=True)
    is_surgery_step = Column(Boolean, default=False)
    surgery_step = Column(String(200), nullable=True)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    surgery_session = relationship("SurgerySession", back_populates="transcripts")


class AudioSegment(Base):
    __tablename__ = "audio_segments"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("surgery_sessions.id"))
    segment_index = Column(Integer)
    file_path = Column(String(500))
    start_time = Column(Float)
    end_time = Column(Float)
    duration = Column(Float)
    has_electric_scalpel = Column(Boolean, default=False)
    has_monitor_alarm = Column(Boolean, default=False)
    noise_reduction_applied = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    surgery_session = relationship("SurgerySession", back_populates="audio_segments")


class SurgerySummary(Base):
    __tablename__ = "surgery_summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("surgery_sessions.id"))
    key_points = Column(JSON)
    surgical_steps = Column(JSON)
    anatomical_landmarks = Column(JSON)
    technical_improvements = Column(JSON)
    complications = Column(JSON)
    overall_assessment = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    archived = Column(Boolean, default=False)
    archive_email_sent = Column(Boolean, default=False)
    archive_email_id = Column(String(200), nullable=True)

    surgery_session = relationship("SurgerySession", back_populates="surgery_summary")
