"""Router para operaciones de clientes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.crud.cliente import (
    obtener_clientes_db,
    obtener_cliente_db,
    obtener_cliente_por_dni_db,
    crear_cliente_db,
    actualizar_cliente_db,
    eliminar_cliente_db
)
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse

router = APIRouter(prefix="/api/v1/clientes", tags=["clientes"])


@router.get("", response_model=list[ClienteResponse])
def listar_clientes(
    incluir_inactivos: bool = Query(False, description="Incluir clientes inactivos"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene la lista de clientes activos (por defecto)."""
    return obtener_clientes_db(db, incluir_inactivos=incluir_inactivos)


@router.get("/dni/{dni}", response_model=ClienteResponse)
def obtener_cliente_por_dni(
    dni: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un cliente por DNI."""
    cliente = obtener_cliente_por_dni_db(db, dni)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene un cliente por ID."""
    cliente = obtener_cliente_db(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("", response_model=ClienteResponse, status_code=201)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Crea un nuevo cliente."""
    try:
        return crear_cliente_db(db, cliente, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    cliente_update: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualiza un cliente."""
    try:
        return actualizar_cliente_db(db, cliente_id, cliente_update, current_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))


@router.delete("/{cliente_id}")
def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Elimina un cliente - eliminación lógica (solo admin)."""
    try:
        eliminar_cliente_db(db, cliente_id)
        return {"mensaje": "Cliente eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404 if "no encontrado" in str(e) else 400, detail=str(e))
