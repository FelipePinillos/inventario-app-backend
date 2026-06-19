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
    HistoricoProductoResponse,
    ProductoPrediccionResumen,
    ResumenDashboard,
    ImportanciaFeaturesResponse,
)
from app.services.ml import prediccion_service as svc

router = APIRouter(
    prefix="/api/v1/predicciones",
    tags=["predicciones"],
)


# ---------------------------------------------------------------------------
# Estado y diagnóstico
# ---------------------------------------------------------------------------

@router.get("/estado", response_model=EstadoModelo)
def estado_modelo(
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """Consulta si el modelo de ML está entrenado y cuándo fue actualizado."""
    return svc.estado_modelo()


@router.get("/cache/estado")
def estado_cache_predicciones(
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """Consulta el estado y estadisticas de la cache de predicciones."""
    return svc.estado_cache_predicciones()


@router.delete("/cache")
def limpiar_cache_predicciones(
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """Limpia manualmente la cache de predicciones."""
    return svc.limpiar_cache_predicciones()


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


# ---------------------------------------------------------------------------
# Entrenamiento
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Predicciones
# ---------------------------------------------------------------------------

@router.get("/demanda/{producto_id}", response_model=PrediccionProductoResponse)
def predecir_demanda(
    producto_id: int,
    semanas: int = Query(4, ge=1, le=26, description="Número de semanas a predecir (1-26)"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Predice la demanda semanal de un producto para las próximas N semanas.

    Incluye:
    - Predicción semana a semana con fechas exactas e intervalo de confianza (min/max).
    - Predicción mensual agregada (para gráficos de barras en el frontend).
    - Total demandado en el período.
    - Indicador de reabastecimiento y cantidad sugerida.
    - Tendencia (CRECIENTE / DECRECIENTE / ESTABLE).
    - Confianza del modelo (coeficiente de variación entre árboles).
    """
    resultado = svc.predecir_demanda_producto(db, producto_id, semanas=semanas)
    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["error"],
        )
    return resultado


@router.get("/todos", response_model=List[ProductoPrediccionResumen])
def predecir_todos(
    semanas: int = Query(4, ge=1, le=26, description="Ventana de predicción en semanas"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Genera un resumen de predicción para **todos** los productos con historial.
    Útil para poblar la tabla principal del dashboard del frontend.

    Retorna: producto, stock, demanda predicha, necesidad de reabastecimiento,
    nivel de urgencia y tendencia.
    """
    return svc.predecir_todos_productos(db, semanas=semanas)


# ---------------------------------------------------------------------------
# Historial
# ---------------------------------------------------------------------------

@router.get("/historico/{producto_id}", response_model=HistoricoProductoResponse)
def historico_producto(
    producto_id: int,
    semanas: int = Query(12, ge=1, le=104, description="Últimas N semanas de historial"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Devuelve las últimas N semanas de ventas reales de un producto.
    Diseñado para alimentar el gráfico de demanda histórica en el frontend.

    Incluye: historial semanal, promedio, máximo y mínimo.
    """
    resultado = svc.obtener_historico_producto(db, producto_id, semanas=semanas)
    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["error"],
        )
    return resultado


# ---------------------------------------------------------------------------
# Alertas de reabastecimiento
# ---------------------------------------------------------------------------

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

    Cada alerta incluye la tendencia del producto (CRECIENTE / DECRECIENTE / ESTABLE).
    """
    alertas = svc.obtener_alertas_reabastecimiento(db, semanas=semanas)
    return alertas


# ---------------------------------------------------------------------------
# Dashboard y análisis del modelo
# ---------------------------------------------------------------------------

@router.get("/resumen", response_model=ResumenDashboard)
def resumen_dashboard(
    semanas: int = Query(4, ge=1, le=26, description="Ventana de predicción en semanas"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Endpoint central para el dashboard del frontend. Devuelve en una sola llamada:
    - KPIs: conteo de alertas críticas, altas y medias.
    - Estado del modelo (entrenado / fecha de último entrenamiento).
    - Resumen de todos los productos predichos con tendencia y urgencia.
    """
    return svc.obtener_resumen_dashboard(db, semanas=semanas)


@router.get("/importancia-features", response_model=ImportanciaFeaturesResponse)
def importancia_features(
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Devuelve la importancia relativa de cada variable (feature) usada por el
    modelo RandomForest. Útil para mostrar en el frontend qué factores
    influyen más en la predicción de demanda.

    Variables disponibles: lag_1, lag_2, lag_4, rolling_mean_4, rolling_std_4,
    semana, mes, id_producto.
    """
    resultado = svc.obtener_importancia_features()
    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["error"],
        )
    return resultado


# ---------------------------------------------------------------------------
# Debug - Ver datos raw
# ---------------------------------------------------------------------------

@router.get("/debug/datos")
def debug_datos(
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    """
    Endpoint de depuración: devuelve el historial de ventas raw y las features generadas.
    Permite ver exactamente qué datos se usan para el modelo.
    """
    import pandas as pd
    
    # Obtener historial
    df_raw = svc._obtener_historial_ventas(db)
    if df_raw.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos de ventas confirmadas"
        )
    
    # Crear features
    df_features = svc._crear_features(df_raw)
    
    # Resumen por producto - formato limpio
    resumen_por_producto = []
    for producto_id in df_raw['id_producto'].unique():
        df_prod = df_raw[df_raw['id_producto'] == producto_id]
        resumen_por_producto.append({
            "producto_id": int(producto_id),
            "nombre": df_prod['nombre_producto'].iloc[0],
            "cantidad_semanas": int(len(df_prod)),
            "cantidad_vendida_total": float(df_prod['cantidad_vendida'].sum()),
            "cantidad_vendida_promedio": float(df_prod['cantidad_vendida'].mean()),
            "cantidad_vendida_max": float(df_prod['cantidad_vendida'].max()),
            "cantidad_vendida_min": float(df_prod['cantidad_vendida'].min()),
            "stock_actual": int(df_prod['stock_actual'].iloc[0]),
            "stock_minimo": int(df_prod['stock_minimo'].iloc[0]),
        })
    
    return {
        "historial_ventas": {
            "total_filas": len(df_raw),
            "productos_unicos": int(df_raw['id_producto'].nunique()),
            "datos": df_raw.to_dict(orient='records')[:50],  # Primeras 50 filas
            "estadisticas": {
                "cantidad_vendida_total": float(df_raw['cantidad_vendida'].sum()),
                "cantidad_vendida_promedio": float(df_raw['cantidad_vendida'].mean()),
                "cantidad_vendida_max": float(df_raw['cantidad_vendida'].max()),
                "cantidad_vendida_min": float(df_raw['cantidad_vendida'].min()),
            }
        },
        "features_generadas": {
            "total_filas": len(df_features),
            "columnas": df_features.columns.tolist(),
            "datos": df_features.to_dict(orient='records')[:50],  # Primeras 50 filas
        },
        "resumen_por_producto": resumen_por_producto
    }
