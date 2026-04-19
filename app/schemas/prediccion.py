from pydantic import BaseModel
from typing import List, Optional


class PrediccionSemanal(BaseModel):
    semana: int
    año: int
    fecha_inicio: str
    fecha_fin: str
    cantidad_predicha: float


class PrediccionProductoResponse(BaseModel):
    producto_id: int
    nombre_producto: str
    stock_actual: int
    stock_minimo: int
    predicciones: List[PrediccionSemanal]
    total_predicho: float
    necesita_reabastecimiento: bool
    cantidad_a_pedir: float


class AlertaReabastecimiento(BaseModel):
    producto_id: int
    nombre_producto: str
    stock_actual: int
    stock_minimo: int
    demanda_predicha_proximas_semanas: float
    cantidad_a_pedir: float
    urgencia: str  # CRITICO | ALTO | MEDIO


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
