from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import get_settings

# JWT sirve para crear y verificar tokens de acceso usando una clave secreta
# en este archivo se manejan las funciones relacionadas con la autenticación
# jwt se usa para crear y verificar tokens de acceso

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def crear_token(data: dict):
    """Crear token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verificar_token(token: str):
    """Verificar token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None