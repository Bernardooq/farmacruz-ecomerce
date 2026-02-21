from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import config
from db.session import engine 
from routes.router import api_router
import os

app = FastAPI(title=config.PROJECT_NAME)

# Configurar CORS para permitir múltiples orígenes
allowed_origins = []
frontend_url = os.getenv("FRONTEND_URL", "*")

if frontend_url == "*":
    # Si es *, permitir todos los orígenes
    allowed_origins = ["*"]
else:
    # Si hay múltiples URLs separadas por coma, dividirlas
    allowed_origins = [origin.strip() for origin in frontend_url.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=config.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    try:
        with engine.connect() as connection:
            return {"message": "¡Hola Mundo! Conexion a la DB exitosa."}
    except Exception as e:
        return {"message": "¡Hola Mundo! ERROR al conectar a la DB.", "error": str(e)}
