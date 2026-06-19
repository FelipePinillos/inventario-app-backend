from pydantic import BaseModel
from typing import List, Optional


# ---------------------------------------------------------------------------
# Predicción semanal (con intervalo de confianza)
# ---------------------------------------------------------------------------

class PrediccionSemanal(BaseModel):
    semana: int
    año: int
    fecha_inicio: str
    fecha_fin: str
    cantidad_predicha: float
    cantidad_min: float   # percentil 10 entre los árboles del RF
    cantidad_max: float   # percentil 90 entre los árboles del RF


# ---------------------------------------------------------------------------
# Predicción mensual agregada (para gráficos en Angular)
# ---------------------------------------------------------------------------

class PrediccionMensual(BaseModel):
    mes: int
    año: int
    nombre_mes: str
    cantidad_predicha: float
    cantidad_min: float
    cantidad_max: float


# ---------------------------------------------------------------------------
# Respuesta completa de predicción por producto
# ---------------------------------------------------------------------------

class PrediccionProductoResponse(BaseModel):
    producto_id: int
    nombre_producto: str
    stock_actual: int
    stock_minimo: int
    predicciones: List[PrediccionSemanal]
    predicciones_mensuales: List[PrediccionMensual]
    total_predicho: float
    necesita_reabastecimiento: bool
    cantidad_a_pedir: float
    tendencia: str            # CRECIENTE | DECRECIENTE | ESTABLE
    confianza_modelo: float   # Coeficiente de variación promedio (menor = más certero)


# ---------------------------------------------------------------------------
# Historial de ventas reales (para gráfico histórico)
# ---------------------------------------------------------------------------

class VentaHistorica(BaseModel):
    semana: int
    año: int
    fecha_inicio: str
    fecha_fin: str
    cantidad_vendida: float


class HistoricoProductoResponse(BaseModel):
    producto_id: int
    nombre_producto: str
    historial: List[VentaHistorica]
    promedio_semanal: float
    maximo_semanal: float
    minimo_semanal: float


# ---------------------------------------------------------------------------
# Alerta de reabastecimiento
# ---------------------------------------------------------------------------

class AlertaReabastecimiento(BaseModel):
    producto_id: int
    nombre_producto: str
    stock_actual: int
    stock_minimo: int
    demanda_predicha_proximas_semanas: float
    cantidad_a_pedir: float
    urgencia: str     # CRITICO | ALTO | MEDIO
    tendencia: str    # CRECIENTE | DECRECIENTE | ESTABLE


# ---------------------------------------------------------------------------
# Resumen por producto (para dashboard y batch)
# ---------------------------------------------------------------------------

class ProductoPrediccionResumen(BaseModel):
    producto_id: int
    nombre_producto: str
    stock_actual: int
    stock_minimo: int
    total_predicho: float
    necesita_reabastecimiento: bool
    urgencia: Optional[str] = None   # CRITICO | ALTO | MEDIO | None
    tendencia: str


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------

class ResumenDashboard(BaseModel):
    total_productos_con_historial: int
    alertas_criticas: int
    alertas_altas: int
    alertas_medias: int
    modelo_entrenado: bool
    ultima_actualizacion: Optional[str] = None
    productos_predichos: List[ProductoPrediccionResumen]


# ---------------------------------------------------------------------------
# Importancia de features del modelo
# ---------------------------------------------------------------------------

class ImportanciaFeature(BaseModel):
    feature: str
    importancia: float
    importancia_porcentaje: float


class ImportanciaFeaturesResponse(BaseModel):
    features: List[ImportanciaFeature]


# ---------------------------------------------------------------------------
# Entrenamiento y estado
# ---------------------------------------------------------------------------

class ResultadoEntrenamiento(BaseModel):
    mensaje: str
    n_muestras: int
    r2_score: Optional[float] = None
    mae: Optional[float] = None
    productos_entrenados: int
    metodo_evaluacion: str
    modelo_guardado: str
    advertencia: Optional[str] = None


class EstadoModelo(BaseModel):
    entrenado: bool
    mensaje: Optional[str] = None
    ultima_actualizacion: Optional[str] = None
    ruta: Optional[str] = None
