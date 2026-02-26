from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key"
    DATABASE_URL: str = "sqlite:///./bhv.db"
    STORAGE_MODE: str = "local"
    MAX_UPLOAD_SIZE_MB: int = 5
    GITHUB_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
