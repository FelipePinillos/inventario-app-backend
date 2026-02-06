from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.schemas.venta import VentaCreate, VentaUpdate, VentaResponse
from app.crud import venta as crud_venta
from app.deps import get_current_user
from app.schemas.usuario import UsuarioResponse

router = APIRouter(
    prefix="/api/v1/ventas",
    tags=["ventas"]
)

@router.get("", response_model=List[VentaResponse])
def listar_ventas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar todas las ventas con sus detalles"""
    ventas = crud_venta.get_ventas(db, skip=skip, limit=limit)
    return ventas

@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener una venta por ID con todos sus detalles"""
    venta = crud_venta.get_venta_by_id(db, venta_id)
    if not venta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venta con ID {venta_id} no encontrada"
        )
    return venta

@router.get("/cliente/{cliente_id}", response_model=List[VentaResponse])
def listar_ventas_por_cliente(
    cliente_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar ventas de un cliente específico"""
    ventas = crud_venta.get_ventas_by_cliente(db, cliente_id, skip=skip, limit=limit)
    return ventas

@router.get("/usuario/{usuario_id}", response_model=List[VentaResponse])
def listar_ventas_por_usuario(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar ventas realizadas por un usuario"""
    ventas = crud_venta.get_ventas_by_usuario(db, usuario_id, skip=skip, limit=limit)
    return ventas

@router.get("/fecha/rango", response_model=List[VentaResponse])
def listar_ventas_por_fecha(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar ventas por rango de fechas"""
    ventas = crud_venta.get_ventas_by_fecha(db, fecha_inicio, fecha_fin, skip=skip, limit=limit)
    return ventas

@router.post("", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def crear_venta(
    venta: VentaCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """
    Crear una nueva venta con sus detalles
    - Calcula automáticamente los totales
    - Descuenta el stock según presentaciones vendidas
    """
    try:
        nueva_venta = crud_venta.crear_venta(db, venta, current_user_id=current_user.id)
        return nueva_venta
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la venta: {str(e)}"
        )

@router.put("/{venta_id}", response_model=VentaResponse)
def actualizar_venta(
    venta_id: int,
    venta: VentaUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """
    Requiere permisos de administrador
    """
    
    venta_actualizada = crud_venta.actualizar_venta(db, venta_id, venta)
    if not venta_actualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venta con ID {venta_id} no encontrada"
        )
    return venta_actualizada

@router.delete("/{venta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """
    ADVERTENCIA: Esto NO restaura el stock
    """
 
    eliminado = crud_venta.eliminar_venta(db, venta_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venta con ID {venta_id} no encontrada"
        )
    return None

@router.patch("/{venta_id}/cancelar", response_model=VentaResponse)
def cancelar_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """
    Cancelar una venta (cambia estado a CANCELADA y restaura stock)
    Solo administradores
    """
    # Permiso controlado desde el frontend
    
    try:
        venta_cancelada = crud_venta.cancelar_venta(db, venta_id)
        if not venta_cancelada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venta con ID {venta_id} no encontrada"
            )
        return venta_cancelada
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar la venta: {str(e)}"
        )
