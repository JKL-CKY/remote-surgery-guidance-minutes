from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..services.transcription_service import TranscriptionService
from ..models.schemas import TranscriptSegment
from ..core.database import SurgerySession, Transcript

router = APIRouter()

transcription_service = TranscriptionService()


@router.post("/transcribe/{session_id}")
async def transcribe_audio(
    session_id: str,
    audio_file_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    background_tasks.add_task(
        transcription_service.transcribe_and_save,
        session_id=session.id,
        audio_path=audio_file_path,
        db=db
    )
    
    return {"message": "转写任务已开始", "session_id": session_id}


@router.post("/transcribe-segment/{session_id}", response_model=List[TranscriptSegment])
async def transcribe_segment(
    session_id: str,
    audio_file_path: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    segments = transcription_service.transcribe_segment(audio_file_path)
    
    for seg in segments:
        transcript = Transcript(
            session_id=session.id,
            speaker=seg.speaker,
            speaker_role=seg.speaker_role,
            start_time=seg.start_time,
            end_time=seg.end_time,
            text=seg.text,
            confidence=seg.confidence,
            is_anatomical_term=seg.is_anatomical_term,
            anatomical_terms=seg.anatomical_terms,
            is_surgery_step=seg.is_surgery_step,
            surgery_step=seg.surgery_step
        )
        db.add(transcript)
    
    db.commit()
    
    return segments


@router.get("/{session_id}", response_model=List[TranscriptSegment])
def get_transcripts(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    transcripts = db.query(Transcript).filter(
        Transcript.session_id == session.id
    ).order_by(Transcript.start_time).all()
    
    return [
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


@router.get("/surgery-steps/{session_id}")
def get_surgery_steps(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    transcripts = db.query(Transcript).filter(
        Transcript.session_id == session.id,
        Transcript.is_surgery_step == True
    ).order_by(Transcript.start_time).all()
    
    steps = []
    for t in transcripts:
        steps.append({
            "time": t.start_time,
            "step": t.surgery_step,
            "description": t.text,
            "speaker": t.speaker
        })
    
    return steps


@router.get("/anatomical-terms/{session_id}")
def get_anatomical_terms(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    transcripts = db.query(Transcript).filter(
        Transcript.session_id == session.id,
        Transcript.is_anatomical_term == True
    ).all()
    
    all_terms = set()
    for t in transcripts:
        if t.anatomical_terms:
            all_terms.update(t.anatomical_terms)
    
    return {
        "anatomical_terms": list(all_terms),
        "mention_count": len(all_terms)
    }
