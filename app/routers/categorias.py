"""Router para operaciones de categorías."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.categoria import (
    obtener_categorias_db,
    obtener_categoria_db,
    crear_categoria_db,
    actualizar_categoria_db,
    eliminar_categoria_db
)
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse

router = APIRouter(prefix="/api/v1/categorias", tags=["categorías"])


@router.get("", response_model=list[CategoriaResponse])
def listar_categorias(
    incluir_inactivas: bool = Query(False, description="Incluir categorías inactivas"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de categorías activas (por defecto)."""
    return obtener_categorias_db(db, incluir_inactivas=incluir_inactivas)


@router.get("/{categoria_id}", response_model=CategoriaResponse)
def obtener_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene una categoría por ID."""
    categoria = obtener_categoria_db(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.post("", response_model=CategoriaResponse, status_code=201)
def crear_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Crea una nueva categoría (solo admin)."""
    try:
        return crear_categoria_db(db, categoria)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def actualizar_categoria(
    categoria_id: int,
    categoria_update: CategoriaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Actualiza una categoría (solo admin)."""
    try:
        return actualizar_categoria_db(db, categoria_id, categoria_update)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrada" in str(e) else 400, detail=str(e))


@router.delete("/{categoria_id}")
def eliminar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina una categoría - eliminación lógica (solo admin)."""
    try:
        eliminar_categoria_db(db, categoria_id)
        return {"mensaje": "Categoría eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrada" in str(e) else 400, detail=str(e))
