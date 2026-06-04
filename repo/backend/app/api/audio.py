from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime
from ..core.database import get_db
from ..core.config import settings
from ..services.audio_processor import AudioProcessor
from ..models.schemas import AudioProcessingResult
from ..core.database import SurgerySession, AudioSegment

router = APIRouter()

audio_processor = AudioProcessor()


@router.post("/upload/{session_id}")
async def upload_audio(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    os.makedirs(settings.TEMP_PATH, exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_PATH, session_id), exist_ok=True)
    
    temp_file = os.path.join(settings.TEMP_PATH, f"{uuid.uuid4()}_{file.filename}")
    with open(temp_file, "wb") as f:
        content = await file.read()
        f.write(content)
    
    segment_index = db.query(AudioSegment).filter(AudioSegment.session_id == session.id).count()
    
    return {
        "temp_file": temp_file,
        "segment_index": segment_index,
        "session_id": session_id
    }


@router.post("/process/{session_id}", response_model=AudioProcessingResult)
async def process_audio(
    session_id: str,
    segment_index: int,
    file_path: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    result = audio_processor.process_audio_segment(
        file_path=file_path,
        session_id=session_id,
        segment_index=segment_index
    )
    
    audio_segment = AudioSegment(
        session_id=session.id,
        segment_index=segment_index,
        file_path=result["file_path"],
        start_time=result["start_time"],
        end_time=result["end_time"],
        duration=result["duration"],
        has_electric_scalpel=result["has_electric_scalpel"],
        has_monitor_alarm=result["has_monitor_alarm"],
        noise_reduction_applied=result["noise_reduction_applied"],
        processed=True
    )
    
    db.add(audio_segment)
    db.commit()
    
    return AudioProcessingResult(**result)


@router.post("/process-batch/{session_id}")
async def process_audio_batch(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    background_tasks.add_task(
        audio_processor.process_full_session,
        session_id=session_id,
        db_session_id=session.id
    )
    
    return {"message": "批处理任务已开始", "session_id": session_id}


@router.get("/segments/{session_id}")
def get_audio_segments(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    segments = db.query(AudioSegment).filter(AudioSegment.session_id == session.id).order_by(AudioSegment.segment_index).all()
    return segments


@router.get("/analyze/{session_id}")
def analyze_audio_quality(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    segments = db.query(AudioSegment).filter(AudioSegment.session_id == session.id).all()
    
    total_segments = len(segments)
    scalpel_count = sum(1 for s in segments if s.has_electric_scalpel)
    alarm_count = sum(1 for s in segments if s.has_monitor_alarm)
    processed_count = sum(1 for s in segments if s.processed)
    
    return {
        "total_segments": total_segments,
        "processed_segments": processed_count,
        "electric_scalpel_detected": scalpel_count,
        "monitor_alarm_detected": alarm_count,
        "noise_reduction_applied_rate": processed_count / total_segments if total_segments > 0 else 0
    }
