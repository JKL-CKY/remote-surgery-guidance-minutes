from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.email_archiver import EmailArchiver
from ..models.schemas import EmailArchiveRequest, EmailArchiveResponse, SurgerySummaryResponse, TranscriptSegment
from ..core.database import SurgerySession, SurgerySummary, Transcript

router = APIRouter()

email_archiver = EmailArchiver()


@router.post("/send/{session_id}", response_model=EmailArchiveResponse)
async def send_to_archive(
    session_id: str,
    recipient_email: str = None,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    summary = db.query(SurgerySummary).filter(SurgerySummary.session_id == session.id).first()
    if not summary:
        raise HTTPException(status_code=400, detail="请先生成手术摘要")
    
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
    
    summary_response = SurgerySummaryResponse(
        key_points=summary.key_points,
        surgical_steps=summary.surgical_steps,
        anatomical_landmarks=summary.anatomical_landmarks,
        technical_improvements=summary.technical_improvements,
        complications=summary.complications,
        overall_assessment=summary.overall_assessment
    )
    
    result = email_archiver.archive_surgery_record(
        session=session,
        summary=summary_response,
        transcripts=transcript_segments,
        recipient_email=recipient_email
    )
    
    if result["success"]:
        summary.archived = True
        summary.archive_email_sent = True
        summary.archive_email_id = result.get("message_id")
        db.commit()
    
    return EmailArchiveResponse(**result)


@router.post("/send-custom", response_model=EmailArchiveResponse)
async def send_custom_archive(
    request: EmailArchiveRequest,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    result = email_archiver.archive_surgery_record(
        session=session,
        summary=request.summary,
        transcripts=request.transcripts,
        recipient_email=request.recipient_email
    )
    
    return EmailArchiveResponse(**result)


@router.get("/status/{session_id}")
def get_archive_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(SurgerySession).filter(SurgerySession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="手术会话未找到")
    
    summary = db.query(SurgerySummary).filter(SurgerySummary.session_id == session.id).first()
    if not summary:
        return {"archived": False, "email_sent": False}
    
    return {
        "archived": summary.archived,
        "email_sent": summary.archive_email_sent,
        "message_id": summary.archive_email_id,
        "archived_at": summary.generated_at
    }
