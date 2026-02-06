"""Router para operaciones de marcas."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.marca import (
    obtener_marcas_db,
    obtener_marca_db,
    crear_marca_db,
    actualizar_marca_db,
    eliminar_marca_db
)
from app.schemas.marca import MarcaCreate, MarcaUpdate, MarcaResponse

router = APIRouter(prefix="/api/v1/marcas", tags=["marcas"])


@router.get("", response_model=list[MarcaResponse])
def listar_marcas(
    incluir_inactivas: bool = Query(False, description="Incluir marcas inactivas"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de marcas activas (por defecto)."""
    return obtener_marcas_db(db, incluir_inactivas=incluir_inactivas)


@router.get("/{marca_id}", response_model=MarcaResponse)
def obtener_marca(
    marca_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene una marca por ID."""
    marca = obtener_marca_db(db, marca_id)
    if not marca:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return marca


@router.post("", response_model=MarcaResponse, status_code=201)
def crear_marca(
    marca: MarcaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Crea una nueva marca (solo admin)."""
    try:
        return crear_marca_db(db, marca, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{marca_id}", response_model=MarcaResponse)
def actualizar_marca(
    marca_id: int,
    marca_update: MarcaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Actualiza una marca (solo admin)."""
    try:
        return actualizar_marca_db(db, marca_id, marca_update, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrada" in str(e) else 400, detail=str(e))


@router.delete("/{marca_id}")
def eliminar_marca(
    marca_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina una marca - eliminación lógica (solo admin)."""
    try:
        eliminar_marca_db(db, marca_id)
        return {"mensaje": "Marca eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrada" in str(e) else 400, detail=str(e))
