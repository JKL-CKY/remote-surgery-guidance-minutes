from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
from ..core.database import get_db
from ..models.schemas import SurgerySessionCreate, SurgerySessionResponse
from ..core.database import SurgerySession

router = APIRouter()


@router.post("", response_model=SurgerySessionResponse)
def create_surgery_session(
    session: SurgerySessionCreate,
    db: Session = Depends(get_db)
):
    session_id = f"SURG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    db_session = SurgerySession(
        session_id=session_id,
        patient_id=session.patient_id,
        patient_name=session.patient_name,
        surgery_type=session.surgery_type,
        primary_surgeon=session.primary_surgeon,
        remote_expert=session.remote_expert,
        operating_room=session.operating_room,
        video_source=session.video_source,
        audio_source=session.audio_source,
        status="active"
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("", response_model=List[SurgerySessionResponse])
def list_surgery_sessions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(SurgerySession)
    if status:
        query = query.filter(SurgerySession.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{session_id}", response_model=SurgerySessionResponse)
def get_surgery_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    return session


@router.put("/{session_id}/end", response_model=SurgerySessionResponse)
def end_surgery_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    session.status = "completed"
    session.end_time = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/{session_id}")
def delete_surgery_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    db.delete(session)
    db.commit()
    
    return {"message": "手术会话已删除"}
