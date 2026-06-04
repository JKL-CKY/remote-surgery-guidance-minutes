from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import surgery, audio, transcript, summary, archive, websocket
from .core.config import settings
from .core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="达芬奇手术纪要系统 - 远程手术指导会议全栈解决方案"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(surgery.router, prefix="/api/surgery", tags=["手术会话管理"])
app.include_router(audio.router, prefix="/api/audio", tags=["音频处理"])
app.include_router(transcript.router, prefix="/api/transcript", tags=["语音转写"])
app.include_router(summary.router, prefix="/api/summary", tags=["AI摘要"])
app.include_router(archive.router, prefix="/api/archive", tags=["邮件归档"])
app.include_router(websocket.router, tags=["WebSocket实时通信"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "达芬奇手术纪要系统 - 远程手术指导会议全栈解决方案",
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "surgery_management": "/api/surgery",
            "audio_processing": "/api/audio",
            "transcription": "/api/transcript",
            "ai_summary": "/api/summary",
            "email_archive": "/api/archive"
        }
    }
