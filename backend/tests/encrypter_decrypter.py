from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY= "manuel_israel_andre"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto"
)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
print(get_password_hash("admin"))
print(verify_password("admin", "$argon2id$v=19$m=65536,t=3,p=4$CwHA2FsrpbQ2hrA2xlhrjQ$0jf//eTwH/jURf/Un3uCT4ss5WF+anSdm8L2u0QNyTE"))
print(verify_password("admin", "$argon2id$v=19$m=65536,t=3,p=4$O0doDQGg1LoXAmDMOcc4Zw$1jsuF9Ka44VDSkS57ab5p4++3Xfk4TtS0crjkDOSL10"))
print(verify_password("admin", "$argon2id$v=19$m=65536,t=3,p=4$r1WKcc45xxjjXGttzbl3bg$LBtUruiVMH+RUwd8HKoRK/D0xMhzYkAdVOH7wSydMaw"))
access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
access_token = create_access_token(
        data={"sub": "administrator", "role": "admin"},
        expires_delta=access_token_expires
    )

print(access_token)
print(decode_access_token(access_token))
