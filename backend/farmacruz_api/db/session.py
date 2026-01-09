"""
Configuracion de la sesion de base de datos para FARMACRUZ

Este modulo configura el motor de SQLAlchemy y el creador de sesiones
que se utilizara en toda la aplicacion para interactuar con PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL

# Motor de base de datos con pool_pre_ping para verificar conexiones antes de usarlas
# Esto ayuda a manejar conexiones que pueden haberse cerrado por timeout
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Fabrica de sesiones de base de datos
# - autocommit=False: Las transacciones deben ser confirmadas explicitamente
# - autoflush=False: Los cambios no se envian automaticamente a la DB antes de cada query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
