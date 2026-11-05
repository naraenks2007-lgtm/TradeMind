import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    HISTORICAL_DATA_DIR: Path = DATA_DIR / "historical"
    SYNTHETIC_DATA_DIR: Path = DATA_DIR / "synthetic"
    UPLOADS_DATA_DIR: Path = DATA_DIR / "uploads"
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    HINDSIGHT_API_KEY: str = os.getenv("HINDSIGHT_API_KEY", "")
    HINDSIGHT_BASE_URL: str = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
    HINDSIGHT_BANK_ID: str = os.getenv("HINDSIGHT_BANK_ID", "trademind-bank")
    
    UPSTOX_CLIENT_ID: str = os.getenv("UPSTOX_CLIENT_ID", "")
    UPSTOX_CLIENT_SECRET: str = os.getenv("UPSTOX_CLIENT_SECRET", "")
    UPSTOX_REDIRECT_URI: str = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:8000/api/upstox/callback")
    UPSTOX_ACCESS_TOKEN: str = os.getenv("UPSTOX_ACCESS_TOKEN", "")
    MARKET_DATA_PROVIDER: str = os.getenv("MARKET_DATA_PROVIDER", "upstox")
    MARKET_DATA_MODE: str = os.getenv("MARKET_DATA_MODE", "live")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()

# Ensure required directories exist
settings.HISTORICAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DATA_DIR.mkdir(parents=True, exist_ok=True)
