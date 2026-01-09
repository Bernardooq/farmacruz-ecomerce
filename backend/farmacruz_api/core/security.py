"""
Modulo de seguridad para FARMACRUZ

Aqui se manejan todas las funciones relacionadas con:
- Hash y verificacion de contraseñas usando Argon2
- Creacion y decodificacion de tokens JWT para autenticacion
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Contexto de hashing de contraseñas usando Argon2 
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto"
)

def get_password_hash(password: str) -> str: # Genera un hash seguro para una contraseña
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool: # Verifica si la contraseña proporcionada coincide con el hash almacenado
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str: # Crea un token JWT con los datos proporcionados y tiempo de expiracion opcional
    to_encode = data.copy()
    
    # Determinar tiempo de expiracion
    if expires_delta:
        expire = datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.now(datetime.timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    # Decodifica el token JWT y devuelve el payload si es valido
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Token invalido, expirado o manipulado
        return None