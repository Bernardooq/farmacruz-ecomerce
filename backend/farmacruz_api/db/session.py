"""
Configuracion de la sesion de base de datos para FARMACRUZ

Este modulo configura el motor de SQLAlchemy y el creador de sesiones
que se utilizara en toda la aplicacion para interactuar con PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL

# Motor de base de datos con pool optimizado para 200 usuarios concurrentes
# Configuracion calculada para:
# - 200 usuarios con queries rapidas (~20-50ms)
# - ~10-20 queries simultaneas en promedio
# - 2 workers Uvicorn
# - Soporte para background tasks de sincronizacion
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # Verificar conexiones antes de usar (previene stale connections)
    pool_size=10,                # Conexiones persistentes por worker (20 total con 2 workers)
    max_overflow=20,             # Conexiones adicionales bajo carga (60 total maximo)
    pool_timeout=30,             # Timeout si pool saturado (previene hangs)
    pool_recycle=3600,           # Reciclar conexiones cada hora (previene timeouts de DB)
    echo_pool=False,             # Cambiar a True para debugging de pool
)

# Fabrica de sesiones de base de datos
# - autocommit=False: Las transacciones deben ser confirmadas explicitamente
# - autoflush=False: Los cambios no se envian automaticamente a la DB antes de cada query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
