from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jose import JWTError 
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import verificar_token
from app.crud.usuario import obtener_usuario_db


#HTTPException -> lanzar errores

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtener usuario autenticado desde el token."""
    cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verificar_token(token)
        if payload is None:
            raise cred_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise cred_exception
    except JWTError:
        raise cred_exception
    
    user = obtener_usuario_db(db, usuario=user_id)
    if user is None:
        raise cred_exception
    return user


def get_current_user_id(current_user = Depends(get_current_user)) -> int:
    """Obtener solo el ID del usuario autenticado."""
    return current_user.id


def require_admin(current_user = Depends(get_current_user)):
    """Verificar que el usuario es admin."""
    # Por ahora solo verificamos que esté autenticado
    # Puedes agregar lógica de admin según tu modelo
    return current_user