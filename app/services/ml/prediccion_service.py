"""
Servicio de predicción de demanda usando RandomForestRegressor.

Flujo:
  1. Consulta historial de ventas confirmadas desde la BD.
  2. Agrega cantidades por producto y semana ISO.
  3. Genera features de rezago (lag) y ventanas móviles.
  4. Entrena un RandomForestRegressor global (un modelo para todos los productos).
  5. Genera predicciones semanales futuras por producto con intervalos de confianza.
  6. Detecta alertas de reabastecimiento con tendencia.
  7. Expone historial, importancia de features y dashboard KPIs.
"""

import logging
import os
import time
import joblib
from copy import deepcopy
import numpy as np
import pandas as pd
from datetime import date, timedelta
from threading import RLock
from typing import List, Dict, Optional, Tuple, Any

from sqlalchemy import func
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score

from app.models.venta import Venta, DetalleVenta
from app.models.presentacion import Presentacion
from app.models.producto import Producto

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(_BASE_DIR, "..", "..", "..", "models_storage")
MODEL_PATH = os.path.join(MODEL_DIR, "rf_demanda.pkl")

MIN_MUESTRAS = 2  # Mínimo de filas para poder entrenar
PREDICCION_CACHE_TTL_SECONDS = int(os.getenv("PREDICCION_CACHE_TTL_SECONDS", "300"))
PREDICCION_CACHE_MAX_ITEMS = int(os.getenv("PREDICCION_CACHE_MAX_ITEMS", "256"))

FEATURE_COLS = [
    "id_producto",
    "mes",
    "semana",
    "lag_1",
    "lag_2",
    "lag_4",
    "rolling_mean_4", # <--- AQUÍ: El promedio móvil de 4 semanas
    "rolling_std_4",   # <--- (Y aquí la desviación estándar móvil)
]
TARGET_COL = "cantidad_vendida"

NOMBRES_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

_cache_lock = RLock()
_prediccion_cache: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
_prediccion_cache_stats = {"hits": 0, "misses": 0}
_modelo_cache: Dict[str, Any] = {"mtime": None, "modelo": None}


def _modelo_mtime() -> Optional[float]:
    if not os.path.exists(MODEL_PATH):
        return None
    return os.path.getmtime(MODEL_PATH)


def _obtener_version_datos_producto(db: Session, producto_id: int) -> Tuple[Any, ...]:
    """
    Firma liviana de los datos que afectan la predicción del producto.
    Si cambian ventas confirmadas o stock, cambia la llave de caché.
    """
    fila = (
        db.query(
            func.count(DetalleVenta.id),
            func.coalesce(func.sum(DetalleVenta.cantidad), 0),
            func.max(Venta.fecha),
            Producto.stock_actual,
            Producto.stock_minimo,
        )
        .join(Venta, DetalleVenta.id_venta == Venta.id)
        .join(Presentacion, DetalleVenta.id_presentacion == Presentacion.id)
        .join(Producto, Presentacion.id_producto == Producto.id)
        .filter(Presentacion.id_producto == producto_id)
        .filter(Venta.estado == "CONFIRMADA")
        .filter(Venta.fecha.isnot(None))
        .group_by(Producto.stock_actual, Producto.stock_minimo)
        .first()
    )
    if not fila:
        return (0, 0.0, None, None, None)

    total_registros, total_cantidad, ultima_fecha, stock_actual, stock_minimo = fila
    ultima_fecha_key = ultima_fecha.isoformat() if ultima_fecha else None
    return (
        int(total_registros or 0),
        float(total_cantidad or 0),
        ultima_fecha_key,
        int(stock_actual or 0),
        int(stock_minimo or 0),
    )


def _obtener_cache_prediccion(clave: Tuple[Any, ...]) -> Optional[Dict]:
    if PREDICCION_CACHE_TTL_SECONDS <= 0:
        return None

    ahora = time.monotonic()
    with _cache_lock:
        entrada = _prediccion_cache.get(clave)
        if not entrada:
            _prediccion_cache_stats["misses"] += 1
            return None

        if entrada["expira_en"] <= ahora:
            _prediccion_cache.pop(clave, None)
            _prediccion_cache_stats["misses"] += 1
            return None

        _prediccion_cache_stats["hits"] += 1
        return deepcopy(entrada["valor"])


def _guardar_cache_prediccion(clave: Tuple[Any, ...], valor: Dict) -> None:
    if PREDICCION_CACHE_TTL_SECONDS <= 0:
        return

    with _cache_lock:
        if len(_prediccion_cache) >= PREDICCION_CACHE_MAX_ITEMS:
            clave_mas_antigua = min(
                _prediccion_cache,
                key=lambda item: _prediccion_cache[item]["creado_en"],
            )
            _prediccion_cache.pop(clave_mas_antigua, None)

        ahora = time.monotonic()
        _prediccion_cache[clave] = {
            "valor": deepcopy(valor),
            "creado_en": ahora,
            "expira_en": ahora + PREDICCION_CACHE_TTL_SECONDS,
        }


def limpiar_cache_predicciones() -> Dict:
    """Limpia resultados cacheados de predicciones."""
    with _cache_lock:
        total = len(_prediccion_cache)
        _prediccion_cache.clear()
        _prediccion_cache_stats["hits"] = 0
        _prediccion_cache_stats["misses"] = 0
    return {"mensaje": "Cache de predicciones limpiada.", "items_eliminados": total}


def estado_cache_predicciones() -> Dict:
    """Devuelve estadísticas básicas de la caché de predicciones."""
    with _cache_lock:
        ahora = time.monotonic()
        expirados = sum(
            1 for item in _prediccion_cache.values() if item["expira_en"] <= ahora
        )
        return {
            "habilitada": PREDICCION_CACHE_TTL_SECONDS > 0,
            "ttl_segundos": PREDICCION_CACHE_TTL_SECONDS,
            "max_items": PREDICCION_CACHE_MAX_ITEMS,
            "items": len(_prediccion_cache),
            "items_expirados": expirados,
            "hits": _prediccion_cache_stats["hits"],
            "misses": _prediccion_cache_stats["misses"],
        }


def _obtener_historial_ventas(db: Session) -> pd.DataFrame:
    """
    Consulta la BD y devuelve un DataFrame con ventas semanales agregadas
    por producto.

    Columnas resultado:
        id_producto, nombre_producto, año, semana, mes,
        stock_actual, stock_minimo, cantidad_vendida
    """
    filas = (
        db.query(
            DetalleVenta.cantidad,
            Venta.fecha,
            Presentacion.id_producto,
            Producto.nombre.label("nombre_producto"),
            Producto.stock_actual,
            Producto.stock_minimo,
        )
        .join(Venta, DetalleVenta.id_venta == Venta.id)
        .join(Presentacion, DetalleVenta.id_presentacion == Presentacion.id)
        .join(Producto, Presentacion.id_producto == Producto.id)
        .filter(Venta.estado == "CONFIRMADA")
        .filter(Venta.fecha.isnot(None))
        .all()
    )

    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(
        filas,
        columns=[
            "cantidad",
            "fecha",
            "id_producto",
            "nombre_producto",
            "stock_actual",
            "stock_minimo",
        ],
    )
    
    df["fecha"] = pd.to_datetime(df["fecha"])

    # Extraer componentes de semana ISO
    iso = df["fecha"].dt.isocalendar()
    df["año"] = iso.year.astype(int)
    df["semana"] = iso.week.astype(int)
    df["mes"] = df["fecha"].dt.month

    # Agregar por producto + semana
    agg = (
        df.groupby(
            [
                "id_producto",
                "nombre_producto",
                "año",
                "semana",
                "mes",
                "stock_actual",
                "stock_minimo",
            ]
        )
        .agg(cantidad_vendida=("cantidad", "sum"))
        .reset_index()
    )
    return agg


def _crear_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features de rezago (lag) y estadísticas móviles por producto.
    Los lags faltantes (por historial corto) se rellenan con 0
    para que el modelo pueda entrenarse incluso con pocos datos.
    """
    df = df.sort_values(["id_producto", "año", "semana"]).reset_index(drop=True)

    grupos = []
    for _, grupo in df.groupby("id_producto", sort=False):
        grupo = grupo.reset_index(drop=True)
        cv = grupo["cantidad_vendida"]
        grupo["lag_1"] = cv.shift(1).fillna(0.0)
        grupo["lag_2"] = cv.shift(2).fillna(0.0)
        grupo["lag_4"] = cv.shift(4).fillna(0.0)
        grupo["rolling_mean_4"] = cv.shift(1).rolling(4, min_periods=1).mean().fillna(0.0)
        grupo["rolling_std_4"] = cv.shift(1).rolling(4, min_periods=1).std().fillna(0.0)
        grupos.append(grupo)

    if not grupos:
        return pd.DataFrame()

    return pd.concat(grupos, ignore_index=True)


def _predecir_con_intervalo(modelo: RandomForestRegressor, X_pred: pd.DataFrame) -> Dict:
    """
    Usa los árboles individuales del RF para estimar un intervalo de confianza.
    Retorna media, std, percentil 10 (min) y percentil 90 (max).
    """
    X_pred_array = X_pred.to_numpy()
    preds_arboles = np.array([tree.predict(X_pred_array)[0] for tree in modelo.estimators_])
    return {
        "media": float(np.mean(preds_arboles)),
        "std": float(np.std(preds_arboles)),
        "min": float(max(0.0, float(np.percentile(preds_arboles, 10)))),
        "max": float(np.percentile(preds_arboles, 90)),
    }


def _calcular_tendencia(cantidades: List[float]) -> str:
    """
    Compara la media de la primera mitad vs la segunda mitad de las predicciones.
    Retorna CRECIENTE, DECRECIENTE o ESTABLE (umbral ±10 %).
    """
    if len(cantidades) < 2:
        return "ESTABLE"
    mitad = len(cantidades) // 2
    primera = float(np.mean(cantidades[:mitad])) if mitad > 0 else 0.0
    segunda = float(np.mean(cantidades[mitad:])) if mitad < len(cantidades) else 0.0
    if primera < 1e-6:
        return "ESTABLE"
    diff_pct = (segunda - primera) / primera
    if diff_pct > 0.10:
        return "CRECIENTE"
    elif diff_pct < -0.10:
        return "DECRECIENTE"
    return "ESTABLE"


def _cargar_modelo() -> Optional[RandomForestRegressor]:
    """Carga el modelo guardado en disco. Devuelve None si no existe."""
    mtime = _modelo_mtime()
    if mtime is None:
        return None

    with _cache_lock:
        if _modelo_cache["modelo"] is not None and _modelo_cache["mtime"] == mtime:
            return _modelo_cache["modelo"]

        modelo = joblib.load(MODEL_PATH)
        _modelo_cache["mtime"] = mtime
        _modelo_cache["modelo"] = modelo
        return modelo


# ---------------------------------------------------------------------------
# API pública del servicio
# ---------------------------------------------------------------------------


def entrenar_modelo(db: Session) -> Dict:
    """
    Entrena el RandomForestRegressor con el historial de ventas de la BD,
    evalúa su desempeño y guarda el modelo en disco.

    - Con >= 20 muestras: usa train_test_split (80/20) para evaluar.
    - Con >= 5 muestras: usa cross-validation de 3 folds.
    - Con < 5 muestras: entrena con todos los datos y reporta advertencia.

    Retorna un dict con métricas o un mensaje de error.
    """
    df = _obtener_historial_ventas(db)
    if df.empty:
        return {"error": "No hay datos de ventas confirmadas para entrenar el modelo."}

    df_feat = _crear_features(df)
    if len(df_feat) < MIN_MUESTRAS:
        return {
            "error": (
                f"Datos insuficientes. Se necesitan al menos {MIN_MUESTRAS} "
                f"muestras semanales por producto para entrenar. "
                f"Actualmente hay {len(df_feat)}."
            )
        }

    X = df_feat[FEATURE_COLS]
    y = df_feat[TARGET_COL]

    modelo = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1,
    )

    n = len(df_feat)
    advertencia = None

    if n >= 20:
        # Suficientes datos: split clásico 80/20
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))
        metodo_evaluacion = "train_test_split 80/20"
    elif n >= 5:
        # Pocos datos: cross-validation 3 folds sobre todo el dataset
        n_folds = min(3, n)
        cv_mae = cross_val_score(modelo, X, y, cv=n_folds, scoring="neg_mean_absolute_error")
        cv_r2 = cross_val_score(modelo, X, y, cv=n_folds, scoring="r2")
        mae = float(-cv_mae.mean())
        r2 = float(cv_r2.mean())
        metodo_evaluacion = f"cross-validation {n_folds} folds"
        advertencia = (
            f"Datos escasos ({n} muestras). Las métricas son orientativas. "
            "El modelo mejorará con más historial de ventas."
        )
        # Reentrenar con todos los datos para el modelo final
        modelo.fit(X, y)
    else:
        # Muy pocos datos: entrenar sin métricas confiables
        modelo.fit(X, y)
        mae = None
        r2 = None
        metodo_evaluacion = "entrenamiento completo sin evaluación"
        advertencia = (
            f"Solo {n} muestras disponibles. Se recomienda registrar más ventas "
            "para obtener predicciones confiables. Las métricas no están disponibles."
        )

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(modelo, MODEL_PATH)
    limpiar_cache_predicciones()
    with _cache_lock:
        _modelo_cache["mtime"] = _modelo_mtime()
        _modelo_cache["modelo"] = modelo

    resultado = {
        "mensaje": "Modelo entrenado y guardado correctamente.",
        "n_muestras": n,
        "r2_score": round(r2, 4) if r2 is not None else None,
        "mae": round(mae, 4) if mae is not None else None,
        "productos_entrenados": int(df_feat["id_producto"].nunique()),
        "metodo_evaluacion": metodo_evaluacion,
        "modelo_guardado": MODEL_PATH,
    }
    if advertencia:
        resultado["advertencia"] = advertencia
    return resultado


def predecir_demanda_producto(
    db: Session, producto_id: int, semanas: int = 4
) -> Dict:
    """
    Predice la demanda semanal de un producto para las próximas N semanas.
    Incluye intervalo de confianza (min/max por árbol RF), tendencia y vista mensual.
    """
    modelo = _cargar_modelo()
    if modelo is None:
        return {
            "error": "El modelo no ha sido entrenado. "
            "Llame a POST /api/v1/predicciones/entrenar primero."
        }

    clave_cache = (
        "demanda_producto",
        producto_id,
        semanas,
        _modelo_mtime(),
        _obtener_version_datos_producto(db, producto_id),
    )
    resultado_cacheado = _obtener_cache_prediccion(clave_cache)
    if resultado_cacheado is not None:
        return resultado_cacheado

    df = _obtener_historial_ventas(db)
    if df.empty:
        return {"error": "No hay datos de ventas disponibles."}

    df_prod = (
        df[df["id_producto"] == producto_id]
        .sort_values(["año", "semana"])
        .reset_index(drop=True)
    )
    if df_prod.empty:
        return {
            "error": f"No se encontraron ventas confirmadas para el producto ID {producto_id}."
        }

    nombre_producto = str(df_prod["nombre_producto"].iloc[-1])
    stock_actual = int(df_prod["stock_actual"].iloc[-1])
    stock_minimo = int(df_prod["stock_minimo"].iloc[-1])

    historial = df_prod["cantidad_vendida"].tolist()
    if len(historial) < 4:
        historial = [0.0] * (4 - len(historial)) + historial
    buffer = list(historial[-8:])

    ultimo_año = int(df_prod["año"].iloc[-1])
    ultima_semana = int(df_prod["semana"].iloc[-1])

    predicciones = []
    cantidades_predichas = []
    acumulado_mensual: Dict[tuple, Dict] = {}  # (año, mes) → acumulador

    for i in range(semanas):
        ultima_semana += 1
        if ultima_semana > 52:
            ultima_semana = 1
            ultimo_año += 1

        mes = min(12, max(1, round((ultima_semana - 1) / 4.33) + 1))

        lag_1 = float(buffer[-1])
        lag_2 = float(buffer[-2]) if len(buffer) >= 2 else 0.0
        lag_4 = float(buffer[-4]) if len(buffer) >= 4 else 0.0
        rolling_mean_4 = float(np.mean(buffer[-4:])) if len(buffer) >= 4 else float(np.mean(buffer))
        rolling_std_4 = float(np.std(buffer[-4:])) if len(buffer) >= 4 else 0.0

        X_pred = pd.DataFrame(
            [{
                "id_producto": producto_id,
                "mes": mes,
                "semana": ultima_semana,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_4": lag_4,
                "rolling_mean_4": rolling_mean_4,
                "rolling_std_4": rolling_std_4,
            }]
        )

        intervalo = _predecir_con_intervalo(modelo, X_pred)
        cantidad_predicha = max(0.0, intervalo["media"])
        buffer.append(cantidad_predicha)
        cantidades_predichas.append(cantidad_predicha)

        try:
            fecha_inicio = date.fromisocalendar(ultimo_año, ultima_semana, 1)
            fecha_fin = date.fromisocalendar(ultimo_año, ultima_semana, 7)
        except ValueError:
            fecha_inicio = date.today() + timedelta(weeks=i + 1)
            fecha_fin = fecha_inicio + timedelta(days=6)

        predicciones.append(
            {
                "semana": ultima_semana,
                "año": ultimo_año,
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat(),
                "cantidad_predicha": round(cantidad_predicha, 2),
                "cantidad_min": round(intervalo["min"], 2),
                "cantidad_max": round(intervalo["max"], 2),
            }
        )

        # Acumular en vista mensual
        clave = (ultimo_año, mes)
        if clave not in acumulado_mensual:
            acumulado_mensual[clave] = {"suma": 0.0, "min": 0.0, "max": 0.0}
        acumulado_mensual[clave]["suma"] += cantidad_predicha
        acumulado_mensual[clave]["min"] += intervalo["min"]
        acumulado_mensual[clave]["max"] += intervalo["max"]

    # Vista mensual agregada
    predicciones_mensuales = []
    for (anio, mes), vals in sorted(acumulado_mensual.items()):
        predicciones_mensuales.append(
            {
                "mes": mes,
                "año": anio,
                "nombre_mes": NOMBRES_MESES.get(mes, str(mes)),
                "cantidad_predicha": round(vals["suma"], 2),
                "cantidad_min": round(vals["min"], 2),
                "cantidad_max": round(vals["max"], 2),
            }
        )

    total_predicho = sum(p["cantidad_predicha"] for p in predicciones)
    stock_disponible = max(0, stock_actual - stock_minimo)
    necesita_reabastecimiento = total_predicho > stock_disponible
    cantidad_a_pedir = max(0.0, total_predicho - stock_disponible)
    tendencia = _calcular_tendencia(cantidades_predichas)

    # Coeficiente de variación promedio como proxy de incertidumbre del modelo
    rangos = [p["cantidad_max"] - p["cantidad_min"] for p in predicciones]
    media_global = float(np.mean(cantidades_predichas)) if cantidades_predichas else 1.0
    confianza_modelo = round(float(np.mean(rangos)) / (media_global + 1e-6), 4)

    resultado = {
        "producto_id": producto_id,
        "nombre_producto": nombre_producto,
        "stock_actual": stock_actual,
        "stock_minimo": stock_minimo,
        "predicciones": predicciones,
        "predicciones_mensuales": predicciones_mensuales,
        "total_predicho": round(total_predicho, 2),
        "necesita_reabastecimiento": necesita_reabastecimiento,
        "cantidad_a_pedir": round(cantidad_a_pedir, 2),
        "tendencia": tendencia,
        "confianza_modelo": confianza_modelo,
    }
    _guardar_cache_prediccion(clave_cache, resultado)
    return resultado


def obtener_alertas_reabastecimiento(db: Session, semanas: int = 4) -> List[Dict]:
    """
    Recorre todos los productos con historial de ventas y genera alertas de
    reabastecimiento clasificadas por urgencia:

        CRITICO  → stock_actual <= stock_minimo
        ALTO     → stock_actual <= 1.5 × stock_minimo
        MEDIO    → demanda predicha supera el stock disponible
    """
    modelo = _cargar_modelo()
    if modelo is None:
        return []

    df = _obtener_historial_ventas(db)
    if df.empty:
        return []

    producto_ids = df["id_producto"].unique().tolist()
    alertas = []

    for pid in producto_ids:
        resultado = predecir_demanda_producto(db, pid, semanas=semanas)
        if "error" in resultado:
            continue
        if not resultado["necesita_reabastecimiento"]:
            continue

        stock_actual = resultado["stock_actual"]
        stock_minimo = resultado["stock_minimo"]

        if stock_actual <= stock_minimo:
            urgencia = "CRITICO"
        elif stock_actual <= stock_minimo * 1.5:
            urgencia = "ALTO"
        else:
            urgencia = "MEDIO"

        alertas.append(
            {
                "producto_id": pid,
                "nombre_producto": resultado["nombre_producto"],
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "demanda_predicha_proximas_semanas": resultado["total_predicho"],
                "cantidad_a_pedir": resultado["cantidad_a_pedir"],
                "urgencia": urgencia,
                "tendencia": resultado.get("tendencia", "ESTABLE"),
            }
        )

    orden = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2}
    alertas.sort(key=lambda x: orden.get(x["urgencia"], 3))
    return alertas


def estado_modelo() -> Dict:
    """Informa si el modelo está entrenado y cuándo fue guardado."""
    if not os.path.exists(MODEL_PATH):
        return {"entrenado": False, "mensaje": "El modelo aún no ha sido entrenado."}

    mtime = os.path.getmtime(MODEL_PATH)
    from datetime import datetime

    ultima_actualizacion = datetime.fromtimestamp(mtime).isoformat()
    return {
        "entrenado": True,
        "ultima_actualizacion": ultima_actualizacion,
        "ruta": MODEL_PATH,
    }


def diagnostico_datos(db: Session) -> Dict:
    """
    Devuelve un resumen de cuántas semanas de historial tiene cada producto
    y cuántas filas totales estarían disponibles para entrenar.
    """
    df = _obtener_historial_ventas(db)
    if df.empty:
        return {
            "total_registros": 0,
            "total_productos": 0,
            "productos": [],
            "advertencia": "No hay ventas confirmadas con fecha registradas en la BD.",
        }

    df_feat = _crear_features(df)

    resumen = (
        df.groupby(["id_producto", "nombre_producto"])
        .agg(semanas_con_ventas=("cantidad_vendida", "count"),
             total_unidades=("cantidad_vendida", "sum"))
        .reset_index()
        .sort_values("semanas_con_ventas", ascending=False)
    )

    return {
        "total_registros_para_entrenar": len(df_feat),
        "total_productos": int(resumen["id_producto"].nunique()),
        "minimo_requerido": MIN_MUESTRAS,
        "puede_entrenar": len(df_feat) >= MIN_MUESTRAS,
        "productos": resumen.to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
# Nuevas funciones de análisis y dashboard
# ---------------------------------------------------------------------------


def obtener_historico_producto(db: Session, producto_id: int, semanas: int = 12) -> Dict:
    """
    Devuelve las últimas N semanas de ventas reales de un producto.
    Útil para renderizar el gráfico histórico en el frontend.
    """
    df = _obtener_historial_ventas(db)
    if df.empty:
        return {"error": "No hay datos de ventas disponibles."}

    df_prod = (
        df[df["id_producto"] == producto_id]
        .sort_values(["año", "semana"])
        .tail(semanas)
        .reset_index(drop=True)
    )
    if df_prod.empty:
        return {
            "error": f"No se encontraron ventas confirmadas para el producto ID {producto_id}."
        }

    nombre_producto = str(df_prod["nombre_producto"].iloc[-1])
    historial = []
    for _, row in df_prod.iterrows():
        try:
            fecha_inicio = date.fromisocalendar(int(row["año"]), int(row["semana"]), 1)
            fecha_fin = date.fromisocalendar(int(row["año"]), int(row["semana"]), 7)
        except ValueError:
            continue
        historial.append(
            {
                "semana": int(row["semana"]),
                "año": int(row["año"]),
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat(),
                "cantidad_vendida": float(row["cantidad_vendida"]),
            }
        )

    cantidades = df_prod["cantidad_vendida"].tolist()
    return {
        "producto_id": producto_id,
        "nombre_producto": nombre_producto,
        "historial": historial,
        "promedio_semanal": round(float(np.mean(cantidades)), 2) if cantidades else 0.0,
        "maximo_semanal": round(float(np.max(cantidades)), 2) if cantidades else 0.0,
        "minimo_semanal": round(float(np.min(cantidades)), 2) if cantidades else 0.0,
    }


def predecir_todos_productos(db: Session, semanas: int = 4) -> List[Dict]:
    """
    Genera un resumen de predicción para todos los productos con historial.
    Útil para el dashboard general del frontend (tabla/tarjetas de productos).
    """
    modelo = _cargar_modelo()
    if modelo is None:
        return []

    df = _obtener_historial_ventas(db)
    if df.empty:
        return []
    logger.info("Productos con historial de ventas: %s", df["id_producto"].nunique())

    producto_ids = df["id_producto"].unique().tolist()
    resultados = []

    for pid in producto_ids:
        res = predecir_demanda_producto(db, pid, semanas=semanas)
        if "error" in res:
            continue

        stock_actual = res["stock_actual"]
        stock_minimo = res["stock_minimo"]
        urgencia = None
        if res["necesita_reabastecimiento"]:
            if stock_actual <= stock_minimo:
                urgencia = "CRITICO"
            elif stock_actual <= stock_minimo * 1.5:
                urgencia = "ALTO"
            else:
                urgencia = "MEDIO"

        resultados.append(
            {
                "producto_id": pid,
                "nombre_producto": res["nombre_producto"],
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "total_predicho": res["total_predicho"],
                "necesita_reabastecimiento": res["necesita_reabastecimiento"],
                "urgencia": urgencia,
                "tendencia": res["tendencia"],
            }
        )

    return resultados


def obtener_importancia_features() -> Dict:
    """
    Devuelve la importancia relativa de cada feature del modelo RandomForest.
    Permite al frontend mostrar qué variables influyen más en la predicción.
    """
    modelo = _cargar_modelo()
    if modelo is None:
        return {"error": "El modelo no ha sido entrenado aún."}

    importancias = modelo.feature_importances_
    total = importancias.sum()
    features = [
        {
            "feature": feat,
            "importancia": round(float(imp), 6),
            "importancia_porcentaje": round(float(imp / total) * 100, 2),
        }
        for feat, imp in sorted(
            zip(FEATURE_COLS, importancias), key=lambda x: x[1], reverse=True
        )
    ]
    return {"features": features}


def obtener_resumen_dashboard(db: Session, semanas: int = 4) -> Dict:
    """
    Resumen ejecutivo para el dashboard del frontend:
      - Estado del modelo y fecha de último entrenamiento.
      - Conteo de alertas por nivel de urgencia (CRITICO / ALTO / MEDIO).
      - Lista compacta de todos los productos predichos con tendencia.
    """
    estado = estado_modelo()
    alertas = obtener_alertas_reabastecimiento(db, semanas=semanas)
    todos = predecir_todos_productos(db, semanas=semanas)

    conteo: Dict[str, int] = {"CRITICO": 0, "ALTO": 0, "MEDIO": 0}
    for a in alertas:
        nivel = a.get("urgencia", "MEDIO")
        conteo[nivel] = conteo.get(nivel, 0) + 1

    return {
        "total_productos_con_historial": len(todos),
        "alertas_criticas": conteo["CRITICO"],
        "alertas_altas": conteo["ALTO"],
        "alertas_medias": conteo["MEDIO"],
        "modelo_entrenado": estado.get("entrenado", False),
        "ultima_actualizacion": estado.get("ultima_actualizacion"),
        "productos_predichos": todos,
    }
