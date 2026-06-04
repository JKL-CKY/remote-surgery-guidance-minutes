from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "DaVinci Surgical Minutes"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/davinci_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    WHISPER_MODEL: str = "base"
    WHISPER_LANGUAGE: str = "zh"

    PYANNOTE_AUTH_TOKEN: Optional[str] = None
    PYANNOTE_SPEAKER_DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.1"

    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "surgery@hospital.com"

    EMAIL_ARCHIVE_TO: str = "surgery-archive@hospital.com"
    EMAIL_SUBJECT_PREFIX: str = "[手术记录]"

    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    NOISE_REDUCTION_STRENGTH: float = 0.8
    ELECTRIC_SCALPEL_FREQ_MIN: int = 500
    ELECTRIC_SCALPEL_FREQ_MAX: int = 5000
    MONITOR_ALARM_FREQ_MIN: int = 800
    MONITOR_ALARM_FREQ_MAX: int = 3200

    STORAGE_PATH: str = "./storage"
    TEMP_PATH: str = "./temp"
    MAX_UPLOAD_SIZE: int = 524288000


settings = Settings()
