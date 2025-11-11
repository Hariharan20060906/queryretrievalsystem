# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    groq_api_key: str
    model_name: str = "llama-3.3-70b-versatile"  # default, but override via .env if needed
    team_token: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
