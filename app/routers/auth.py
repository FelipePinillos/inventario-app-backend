"""Router para operaciones de autenticación."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import crear_token
from app.crud.usuario import obtener_usuario_db
from app.utils import verify_password
from app.schemas.token import TokenResponse
from app.schemas.usuario import UsuarioResponse
from app.deps import get_current_user


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login de usuario.
    
    - **username**: Nombre del usuario
    - **password**: Contraseña
    """
    usuario = obtener_usuario_db(db, usuario=form_data.username)
    if not usuario or not verify_password(form_data.password, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    access_token = crear_token({"sub": usuario.nombre})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil(current_user = Depends(get_current_user)):
    """Obtener perfil del usuario autenticado."""
    return current_user
