"""Router para operaciones de usuarios."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.usuario import (
    crear_usuario_db,
    obtener_usuarios_db,
    obtener_usuario_db,
    actualizar_usuario_db,
    eliminar_usuario_db,
)
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse

router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de usuarios."""
    return obtener_usuarios_db(db)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un usuario por ID."""
    usuario = obtener_usuario_db(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("", response_model=UsuarioResponse)
def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Crea un nuevo usuario (solo admin)."""
    try:
        return crear_usuario_db(db, usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualiza un usuario."""
    try:
        return actualizar_usuario_db(db, usuario_id, usuario_update)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))


@router.delete("/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina un usuario (solo admin)."""
    try:
        eliminar_usuario_db(db, usuario_id)
        return {"mensaje": "Usuario eliminado"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))
