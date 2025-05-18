import os
from dotenv import load_dotenv
from pydantic import BaseSettings, PostgresDsn

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Chat Agent Platform"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")  # Replace in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # LLM Provider
    MCP_API_KEY: str = os.getenv("MCP_API_KEY", "")
    
    # Google Calendar
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # WhatsApp (Optional)
    WHATSAPP_API_KEY: str = os.getenv("WHATSAPP_API_KEY", "")

    class Config:
        case_sensitive = True

settings = Settings()