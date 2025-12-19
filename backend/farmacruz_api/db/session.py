"""
Configuración de la sesión de base de datos para FARMACRUZ

Este módulo configura el motor de SQLAlchemy y el creador de sesiones
que se utilizará en toda la aplicación para interactuar con PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL

# Motor de base de datos con pool_pre_ping para verificar conexiones antes de usarlas
# Esto ayuda a manejar conexiones que pueden haberse cerrado por timeout
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Fábrica de sesiones de base de datos
# - autocommit=False: Las transacciones deben ser confirmadas explícitamente
# - autoflush=False: Los cambios no se envían automáticamente a la DB antes de cada query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
