import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Carga variables de entorno desde el archivo .env
load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    PROJECT_NAME: str = "Farmacruz API"
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", "contacto@farmacruz.com")
    
    class Config:
        case_sensitive = True

settings = Settings()

# Mantener compatibilidad con código existente
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
PROJECT_NAME = settings.PROJECT_NAME
API_V1_STR = settings.API_V1_STR
FRONTEND_URL = settings.FRONTEND_URL