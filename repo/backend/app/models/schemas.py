from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SurgerySessionCreate(BaseModel):
    patient_id: str
    patient_name: str
    surgery_type: str
    primary_surgeon: str
    remote_expert: str
    operating_room: str
    video_source: Optional[str] = None
    audio_source: Optional[str] = None


class SurgerySessionResponse(BaseModel):
    id: int
    session_id: str
    patient_id: str
    patient_name: str
    surgery_type: str
    primary_surgeon: str
    remote_expert: str
    operating_room: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    video_source: Optional[str] = None
    audio_source: Optional[str] = None

    class Config:
        from_attributes = True


class TranscriptSegment(BaseModel):
    speaker: str
    speaker_role: str
    start_time: float
    end_time: float
    text: str
    confidence: float
    is_anatomical_term: bool = False
    anatomical_terms: Optional[List[str]] = None
    is_surgery_step: bool = False
    surgery_step: Optional[str] = None


class AudioProcessingResult(BaseModel):
    segment_index: int
    file_path: str
    start_time: float
    end_time: float
    duration: float
    has_electric_scalpel: bool
    has_monitor_alarm: bool
    noise_reduction_applied: bool


class SpeakerDiarizationSegment(BaseModel):
    speaker: str
    start_time: float
    end_time: float


class SurgerySummaryRequest(BaseModel):
    session_id: str
    transcripts: List[TranscriptSegment]
    audio_analysis: Optional[Dict[str, Any]] = None


class SurgerySummaryResponse(BaseModel):
    key_points: List[str]
    surgical_steps: List[Dict[str, Any]]
    anatomical_landmarks: List[str]
    technical_improvements: List[str]
    complications: List[str]
    overall_assessment: str


class EmailArchiveRequest(BaseModel):
    session_id: str
    summary: SurgerySummaryResponse
    transcripts: List[TranscriptSegment]
    recipient_email: Optional[str] = None


class EmailArchiveResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
