from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.deps import get_current_user
from app.schemas.usuario import UsuarioResponse
from app.schemas.prediccion import (
    PrediccionProductoResponse,
    AlertaReabastecimiento,
    ResultadoEntrenamiento,
    EstadoModelo,
)
from app.services.ml import prediccion_service as svc

router = APIRouter(
    prefix="/api/v1/predicciones",
    tags=["predicciones"],
)


@router.get("/estado", response_model=EstadoModelo)
def estado_modelo(
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """Consulta si el modelo de ML está entrenado y cuándo fue actualizado."""
    return svc.estado_modelo()


@router.get("/diagnostico")
def diagnostico_datos(
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Muestra cuántas semanas de historial de ventas tiene cada producto.
    Útil para verificar si hay suficientes datos antes de entrenar.
    """
    return svc.diagnostico_datos(db)


@router.post("/entrenar", response_model=ResultadoEntrenamiento)
def entrenar_modelo(
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Entrena el RandomForestRegressor con el historial completo de ventas
    confirmadas. Devuelve métricas de evaluación (R², MAE).
    
    Debe ejecutarse después de haber registrado suficientes ventas.
    Se puede volver a llamar para reentrenar con datos actualizados.
    """
    resultado = svc.entrenar_modelo(db)
    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=resultado["error"],
        )
    return resultado


@router.get("/demanda/{producto_id}", response_model=PrediccionProductoResponse)
def predecir_demanda(
    producto_id: int,
    semanas: int = Query(4, ge=1, le=26, description="Número de semanas a predecir (1-26)"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Predice la demanda semanal de un producto para las próximas N semanas
    usando el modelo RandomForestRegressor entrenado.

    Incluye:
    - Predicción semana a semana con fechas exactas.
    - Total demandado en el período.
    - Indicador de si necesita reabastecimiento.
    - Cantidad sugerida a pedir.
    """
    resultado = svc.predecir_demanda_producto(db, producto_id, semanas=semanas)
    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["error"],
        )
    return resultado


@router.get("/alertas", response_model=List[AlertaReabastecimiento])
def alertas_reabastecimiento(
    semanas: int = Query(4, ge=1, le=26, description="Ventana de predicción en semanas"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Devuelve la lista de productos que necesitan reabastecimiento basándose
    en la demanda predicha para las próximas N semanas.

    Los resultados se ordenan por urgencia:
    - **CRITICO**: stock_actual ≤ stock_mínimo.
    - **ALTO**: stock_actual ≤ 1.5 × stock_mínimo.
    - **MEDIO**: demanda predicha supera el stock disponible.
    """
    alertas = svc.obtener_alertas_reabastecimiento(db, semanas=semanas)
    return alertas
