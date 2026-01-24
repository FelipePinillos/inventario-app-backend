"""Router para operaciones de proveedores."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.proveedor import (
    obtener_proveedores_db,
    obtener_proveedor_db,
    obtener_proveedor_por_ruc_db,
    crear_proveedor_db,
    actualizar_proveedor_db,
    eliminar_proveedor_db
)
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate, ProveedorResponse

router = APIRouter(prefix="/api/v1/proveedores", tags=["proveedores"])


@router.get("", response_model=list[ProveedorResponse])
def listar_proveedores(
    incluir_inactivos: bool = Query(False, description="Incluir proveedores inactivos"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de proveedores activos (por defecto)."""
    return obtener_proveedores_db(db, incluir_inactivos=incluir_inactivos)


@router.get("/ruc/{ruc}", response_model=ProveedorResponse)
def obtener_proveedor_por_ruc(
    ruc: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un proveedor por RUC."""
    proveedor = obtener_proveedor_por_ruc_db(db, ruc)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


@router.get("/{proveedor_id}", response_model=ProveedorResponse)
def obtener_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un proveedor por ID."""
    proveedor = obtener_proveedor_db(db, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor


@router.post("", response_model=ProveedorResponse, status_code=201)
def crear_proveedor(
    proveedor: ProveedorCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Crea un nuevo proveedor (solo admin)."""
    try:
        return crear_proveedor_db(db, proveedor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{proveedor_id}", response_model=ProveedorResponse)
def actualizar_proveedor(
    proveedor_id: int,
    proveedor_update: ProveedorUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Actualiza un proveedor (solo admin)."""
    try:
        return actualizar_proveedor_db(db, proveedor_id, proveedor_update)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))


@router.delete("/{proveedor_id}")
def eliminar_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina un proveedor - eliminación lógica (solo admin)."""
    try:
        eliminar_proveedor_db(db, proveedor_id)
        return {"mensaje": "Proveedor eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))
