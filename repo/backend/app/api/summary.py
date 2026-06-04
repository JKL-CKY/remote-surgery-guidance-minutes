from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..services.summary_generator import SummaryGenerator
from ..models.schemas import SurgerySummaryRequest, SurgerySummaryResponse, TranscriptSegment
from ..core.database import SurgerySession, SurgerySummary, Transcript

router = APIRouter()

summary_generator = SummaryGenerator()


@router.post("/generate/{session_id}", response_model=SurgerySummaryResponse)
async def generate_summary(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    transcripts = db.query(Transcript).filter(
        Transcript.session_id == session.id
    ).order_by(Transcript.start_time).all()
    
    transcript_segments = [
        TranscriptSegment(
            speaker=t.speaker,
            speaker_role=t.speaker_role,
            start_time=t.start_time,
            end_time=t.end_time,
            text=t.text,
            confidence=t.confidence,
            is_anatomical_term=t.is_anatomical_term,
            anatomical_terms=t.anatomical_terms,
            is_surgery_step=t.is_surgery_step,
            surgery_step=t.surgery_step
        )
        for t in transcripts
    ]
    
    summary = summary_generator.generate_summary(
        session_id=session_id,
        transcripts=transcript_segments,
        session_info={
            "patient_name": session.patient_name,
            "surgery_type": session.surgery_type,
            "primary_surgeon": session.primary_surgeon,
            "remote_expert": session.remote_expert,
            "operating_room": session.operating_room,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None
        }
    )
    
    existing_summary = db.query(SurgerySummary).filter(SurgerySummary.session_id == session.id).first()
    if existing_summary:
        existing_summary.key_points = summary.key_points
        existing_summary.surgical_steps = summary.surgical_steps
        existing_summary.anatomical_landmarks = summary.anatomical_landmarks
        existing_summary.technical_improvements = summary.technical_improvements
        existing_summary.complications = summary.complications
        existing_summary.overall_assessment = summary.overall_assessment
    else:
        db_summary = SurgerySummary(
            session_id=session.id,
            key_points=summary.key_points,
            surgical_steps=summary.surgical_steps,
            anatomical_landmarks=summary.anatomical_landmarks,
            technical_improvements=summary.technical_improvements,
            complications=summary.complications,
            overall_assessment=summary.overall_assessment
        )
        db.add(db_summary)
    
    db.commit()
    
    return summary


@router.get("/{session_id}", response_model=SurgerySummaryResponse)
def get_summary(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    summary = db.query(SurgerySummary).filter(SurgerySummary.session_id == session.id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="手术摘要未找到")
    
    return SurgerySummaryResponse(
        key_points=summary.key_points,
        surgical_steps=summary.surgical_steps,
        anatomical_landmarks=summary.anatomical_landmarks,
        technical_improvements=summary.technical_improvements,
        complications=summary.complications,
        overall_assessment=summary.overall_assessment
    )


@router.post("/regenerate/{session_id}", response_model=SurgerySummaryResponse)
async def regenerate_summary(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    return await generate_summary(session_id, db)
