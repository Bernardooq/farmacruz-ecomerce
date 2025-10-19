from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import config
from db.session import engine 
from routes.router import api_router

app = FastAPI(title=config.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL], # Solo permite tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(api_router, prefix=config.API_V1_STR)
@app.get("/")
def read_root():
    try:
        with engine.connect() as connection:
            return {"message": "¡Hola Mundo! Conexión a la DB exitosa."}
    except Exception as e:
        return {"message": "¡Hola Mundo! ERROR al conectar a la DB.", "error": str(e)}