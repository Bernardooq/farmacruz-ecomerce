import os
from dotenv import load_dotenv

# Carga variables de entorno desde el archivo .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

PROJECT_NAME = "Farmacruz API"
API_V1_STR = "/api/v1"

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")