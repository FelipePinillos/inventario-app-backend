"""
Servicio de predicción de demanda usando RandomForestRegressor.

Flujo:
  1. Consulta historial de ventas confirmadas desde la BD.
  2. Agrega cantidades por producto y semana ISO.
  3. Genera features de rezago (lag) y ventanas móviles con encoding cíclico.
  4. Entrena un RandomForestRegressor global con one‑hot de producto,
     split temporal y criterio Poisson.
  5. Genera predicciones semanales futuras por producto con intervalos de confianza.
  6. Detecta alertas de reabastecimiento con tendencia.
  7. Expone historial, importancia de features y dashboard KPIs.
  8. Optimización: predicción en lote para todos los productos.
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
from sklearn.model_selection import cross_val_score
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

MIN_MUESTRAS = 2
PREDICCION_CACHE_TTL_SECONDS = int(os.getenv("PREDICCION_CACHE_TTL_SECONDS", "300"))
PREDICCION_CACHE_MAX_ITEMS = int(os.getenv("PREDICCION_CACHE_MAX_ITEMS", "256"))

FEATURE_COLS_BASE = [
    "mes",
    "semana_sin",
    "semana_cos",
    "lag_1",
    "lag_2",
    "lag_4",
    "rolling_mean_4",
    "rolling_std_4",
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
_modelo_cache: Dict[str, Any] = {"mtime": None, "modelo_data": None}


def _modelo_mtime() -> Optional[float]:
    if not os.path.exists(MODEL_PATH):
        return None
    return os.path.getmtime(MODEL_PATH)


def _obtener_version_datos_producto(db: Session, producto_id: int) -> Tuple[Any, ...]:
    """Firma liviana de los datos que afectan la predicción del producto."""
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
    with _cache_lock:
        total = len(_prediccion_cache)
        _prediccion_cache.clear()
        _prediccion_cache_stats["hits"] = 0
        _prediccion_cache_stats["misses"] = 0
    return {"mensaje": "Cache de predicciones limpiada.", "items_eliminados": total}


def estado_cache_predicciones() -> Dict:
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
    iso = df["fecha"].dt.isocalendar()
    df["año"] = iso.year.astype(int)
    df["semana"] = iso.week.astype(int)
    df["mes"] = df["fecha"].dt.month

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
    df = df.sort_values(["id_producto", "año", "semana"]).reset_index(drop=True)

    grupos = []
    for producto_id, grupo_prod in df.groupby("id_producto", sort=False):
        grupo_prod = grupo_prod.sort_values(["año", "semana"]).reset_index(drop=True)

        años = grupo_prod["año"].unique()
        años_range = range(int(años.min()), int(años.max()) + 1)

        semanas_completas = []
        for año in años_range:
            for semana in range(1, 53):
                semanas_completas.append({"año": año, "semana": semana})

        índice_completo = pd.DataFrame(semanas_completas)
        índice_completo["id_producto"] = producto_id

        grupo_expandido = índice_completo.merge(
            grupo_prod[["año", "semana", "cantidad_vendida", "mes", "nombre_producto",
                        "stock_actual", "stock_minimo"]],
            on=["año", "semana"],
            how="left"
        )

        grupo_expandido["cantidad_vendida"] = grupo_expandido["cantidad_vendida"].fillna(0.0)
        grupo_expandido["mes"] = grupo_expandido["mes"].fillna(
            (grupo_expandido["semana"] - 1) // 4.33 + 1
        ).astype(int).clip(1, 12)
        grupo_expandido["nombre_producto"] = grupo_expandido["nombre_producto"].fillna(
            grupo_prod["nombre_producto"].iloc[0]
        )
        grupo_expandido["stock_actual"] = grupo_expandido["stock_actual"].fillna(
            grupo_prod["stock_actual"].iloc[-1]
        ).astype(int)
        grupo_expandido["stock_minimo"] = grupo_expandido["stock_minimo"].fillna(
            grupo_prod["stock_minimo"].iloc[-1]
        ).astype(int)

        grupo_expandido["semana_sin"] = np.sin(2 * np.pi * grupo_expandido["semana"] / 52)
        grupo_expandido["semana_cos"] = np.cos(2 * np.pi * grupo_expandido["semana"] / 52)

        cv = grupo_expandido["cantidad_vendida"]
        grupo_expandido["lag_1"] = cv.shift(1).fillna(0.0)
        grupo_expandido["lag_2"] = cv.shift(2).fillna(0.0)
        grupo_expandido["lag_4"] = cv.shift(4).fillna(0.0)
        grupo_expandido["rolling_mean_4"] = cv.shift(1).rolling(4, min_periods=1).mean().fillna(0.0)
        grupo_expandido["rolling_std_4"] = cv.shift(1).rolling(4, min_periods=1).std().fillna(0.0)

        grupos.append(grupo_expandido)

    if not grupos:
        return pd.DataFrame()

    resultado = pd.concat(grupos, ignore_index=True)
    columnas_retorno = ["año", "semana", "id_producto"] + FEATURE_COLS_BASE + [TARGET_COL]
    return resultado[columnas_retorno].copy()


def _predecir_con_intervalo(modelo: RandomForestRegressor, X_pred: pd.DataFrame) -> Dict:
    X_pred_array = X_pred.to_numpy()
    preds_arboles = np.array([tree.predict(X_pred_array)[0] for tree in modelo.estimators_])
    return {
        "media": float(np.mean(preds_arboles)),
        "std": float(np.std(preds_arboles)),
        "min": float(max(0.0, float(np.percentile(preds_arboles, 10)))),
        "max": float(np.percentile(preds_arboles, 90)),
    }


def _calcular_tendencia(cantidades: List[float]) -> str:
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


def _calcular_urgencia(stock_actual: int, stock_minimo: int, necesita: bool) -> Optional[str]:
    if not necesita:
        return None
    if stock_actual <= stock_minimo:
        return "CRITICO"
    elif stock_actual <= stock_minimo * 1.5:
        return "ALTO"
    return "MEDIO"


def _cargar_modelo() -> Optional[Dict]:
    mtime = _modelo_mtime()
    if mtime is None:
        return None

    with _cache_lock:
        if _modelo_cache["modelo_data"] is not None and _modelo_cache["mtime"] == mtime:
            return _modelo_cache["modelo_data"]

        modelo_data = joblib.load(MODEL_PATH)
        _modelo_cache["mtime"] = mtime
        _modelo_cache["modelo_data"] = modelo_data
        return modelo_data


# ---------------------------------------------------------------------------
# API pública del servicio
# ---------------------------------------------------------------------------


def entrenar_modelo(db: Session) -> Dict:
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

    producto_ids_unicos = sorted(df_feat["id_producto"].unique().tolist())
    df_feat["id_producto"] = pd.Categorical(df_feat["id_producto"], categories=producto_ids_unicos)
    dummies = pd.get_dummies(df_feat["id_producto"], prefix="prod")
    df_modelo = pd.concat([df_feat.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)

    feature_cols_finales = FEATURE_COLS_BASE + list(dummies.columns)
    X = df_modelo[feature_cols_finales]
    y = df_modelo[TARGET_COL]

    df_modelo["orden_temporal"] = df_modelo["año"] * 100 + df_modelo["semana"]
    df_modelo = df_modelo.sort_values("orden_temporal").reset_index(drop=True)
    X = X.loc[df_modelo.index]
    y = y.loc[df_modelo.index]

    n = len(df_modelo)
    corte = int(n * 0.8)
    advertencia = None

    modelo = RandomForestRegressor(
        n_estimators=200,
        criterion="poisson",
        max_depth=10,
        min_samples_leaf=5,
        min_samples_split=10,
        random_state=42,
        n_jobs=-1,
    )

    if n >= 20:
        X_train, X_test = X.iloc[:corte], X.iloc[corte:]
        y_train, y_test = y.iloc[:corte], y.iloc[corte:]

        modelo.fit(X_train, y_train)
        y_pred = np.clip(modelo.predict(X_test), 0, None)
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        baseline_naive = X_test["lag_1"].to_numpy()
        mae_naive = float(np.mean(np.abs(y_test.to_numpy() - baseline_naive)))
        mase = mae / mae_naive if mae_naive > 0 else None

        metodo_evaluacion = "split temporal 80/20 (cronológico)"
    elif n >= 5:
        n_folds = min(3, n)
        cv_mae = cross_val_score(modelo, X, y, cv=n_folds, scoring="neg_mean_absolute_error")
        cv_r2 = cross_val_score(modelo, X, y, cv=n_folds, scoring="r2")
        mae = float(-cv_mae.mean())
        r2 = float(cv_r2.mean())
        mase = None
        metodo_evaluacion = f"cross-validation {n_folds} folds"
        advertencia = f"Datos escasos ({n} muestras). Las métricas son orientativas."
        modelo.fit(X, y)
    else:
        modelo.fit(X, y)
        mae = None
        r2 = None
        mase = None
        metodo_evaluacion = "entrenamiento completo sin evaluación"
        advertencia = f"Solo {n} muestras disponibles."

    os.makedirs(MODEL_DIR, exist_ok=True)
    modelo_data = {
        "modelo": modelo,
        "producto_ids": producto_ids_unicos,
        "feature_cols": feature_cols_finales,
    }
    joblib.dump(modelo_data, MODEL_PATH)

    limpiar_cache_predicciones()
    with _cache_lock:
        _modelo_cache["mtime"] = _modelo_mtime()
        _modelo_cache["modelo_data"] = modelo_data

    resultado = {
        "mensaje": "Modelo entrenado y guardado correctamente.",
        "n_muestras": n,
        "r2_score": round(r2, 4) if r2 is not None else None,
        "mae": round(mae, 4) if mae is not None else None,
        "mase": round(mase, 4) if mase is not None else None,
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
    modelo_data = _cargar_modelo()
    if modelo_data is None:
        return {
            "error": "El modelo no ha sido entrenado. "
            "Llame a POST /api/v1/predicciones/entrenar primero."
        }

    modelo = modelo_data["modelo"]
    producto_ids = modelo_data["producto_ids"]
    feature_cols = modelo_data["feature_cols"]

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
    acumulado_mensual: Dict[tuple, Dict] = {}

    for i in range(semanas):
        ultima_semana += 1
        if ultima_semana > 52:
            ultima_semana = 1
            ultimo_año += 1

        mes = min(12, max(1, round((ultima_semana - 1) / 4.33) + 1))

        semana_sin = np.sin(2 * np.pi * ultima_semana / 52)
        semana_cos = np.cos(2 * np.pi * ultima_semana / 52)
        lag_1 = float(buffer[-1])
        lag_2 = float(buffer[-2]) if len(buffer) >= 2 else 0.0
        lag_4 = float(buffer[-4]) if len(buffer) >= 4 else 0.0
        rolling_mean_4 = float(np.mean(buffer[-4:])) if len(buffer) >= 4 else float(np.mean(buffer))
        rolling_std_4 = float(np.std(buffer[-4:])) if len(buffer) >= 4 else 0.0

        fila = {col: 0 for col in feature_cols}
        fila["mes"] = mes
        fila["semana_sin"] = semana_sin
        fila["semana_cos"] = semana_cos
        fila["lag_1"] = lag_1
        fila["lag_2"] = lag_2
        fila["lag_4"] = lag_4
        fila["rolling_mean_4"] = rolling_mean_4
        fila["rolling_std_4"] = rolling_std_4

        col_producto = f"prod_{producto_id}"
        if col_producto in fila:
            fila[col_producto] = 1

        X_pred = pd.DataFrame([fila])[feature_cols]

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

        clave = (ultimo_año, mes)
        if clave not in acumulado_mensual:
            acumulado_mensual[clave] = {"suma": 0.0, "min": 0.0, "max": 0.0}
        acumulado_mensual[clave]["suma"] += cantidad_predicha
        acumulado_mensual[clave]["min"] += intervalo["min"]
        acumulado_mensual[clave]["max"] += intervalo["max"]

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
    modelo_data = _cargar_modelo()
    if modelo_data is None:
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


def obtener_historico_producto(db: Session, producto_id: int, semanas: int = 12) -> Dict:
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
    Genera un resumen de predicción para TODOS los productos.
    Optimizado con predicción en lote (una llamada al modelo por semana)
    y caché individual para futuras consultas.
    """
    modelo_data = _cargar_modelo()
    if modelo_data is None:
        return []

    modelo = modelo_data["modelo"]
    producto_ids = modelo_data["producto_ids"]
    feature_cols = modelo_data["feature_cols"]

    df = _obtener_historial_ventas(db)
    if df.empty:
        return []

    # PASO 1: Recuperar de caché individual (rápido)
    resultados = []
    productos_faltantes = []
    claves_faltantes = []
    for pid in producto_ids:
        clave = ("demanda_producto", pid, semanas, _modelo_mtime(), _obtener_version_datos_producto(db, pid))
        cacheado = _obtener_cache_prediccion(clave)
        if cacheado is not None:
            resultados.append({
                "producto_id": pid,
                "nombre_producto": cacheado["nombre_producto"],
                "stock_actual": cacheado["stock_actual"],
                "stock_minimo": cacheado["stock_minimo"],
                "total_predicho": cacheado["total_predicho"],
                "necesita_reabastecimiento": cacheado["necesita_reabastecimiento"],
                "urgencia": _calcular_urgencia(
                    cacheado["stock_actual"],
                    cacheado["stock_minimo"],
                    cacheado["necesita_reabastecimiento"]
                ),
                "tendencia": cacheado["tendencia"],
            })
        else:
            productos_faltantes.append(pid)
            claves_faltantes.append(clave)

    if not productos_faltantes:
        return resultados

    # PASO 2: Obtener historial de los faltantes
    df_hist = df[df["id_producto"].isin(productos_faltantes)]
    grupos = df_hist.groupby("id_producto")

    # Inicializar buffers y metadatos para cada producto faltante
    buffers = {}
    metadatos = {}
    for pid in productos_faltantes:
        if pid not in grupos.groups:
            # Sin historial, usar valores por defecto
            buffers[pid] = [0.0] * 8
            metadatos[pid] = {
                "nombre": "Sin datos",
                "stock_actual": 0,
                "stock_minimo": 0,
                "ultimo_año": 2024,
                "ultima_semana": 0,
            }
            continue
        grupo = grupos.get_group(pid).sort_values(["año", "semana"])
        historial = grupo["cantidad_vendida"].tolist()
        if len(historial) < 4:
            historial = [0.0] * (4 - len(historial)) + historial
        buffer = list(historial[-8:]) if len(historial) >= 8 else [0.0] * (8 - len(historial)) + historial
        buffers[pid] = buffer
        metadatos[pid] = {
            "nombre": str(grupo["nombre_producto"].iloc[-1]),
            "stock_actual": int(grupo["stock_actual"].iloc[-1]),
            "stock_minimo": int(grupo["stock_minimo"].iloc[-1]),
            "ultimo_año": int(grupo["año"].iloc[-1]),
            "ultima_semana": int(grupo["semana"].iloc[-1]),
        }

    # Almacenar predicciones acumuladas (para la caché final)
    # Necesitamos generar la misma estructura que predecir_demanda_producto
    # pero sin intervalos (solo total y tendencia). Para la caché guardaremos el total y tendencia.

    # Variables para ir acumulando por producto
    totales = {pid: 0.0 for pid in productos_faltantes}
    tendencias = {pid: [] for pid in productos_faltantes}  # lista de predicciones para calcular tendencia

    # Iterar semana a semana (batch en cada semana)
    for w in range(semanas):
        filas = []
        pids_orden = []
        # Construir fila para cada producto faltante
        for pid in productos_faltantes:
            meta = metadatos[pid]
            # Calcular la semana actual (w iteraciones desde la última real)
            if w == 0:
                siguiente_semana = meta["ultima_semana"] + 1
                siguiente_año = meta["ultimo_año"]
                if siguiente_semana > 52:
                    siguiente_semana = 1
                    siguiente_año += 1
            else:
                # Ya se actualizó en iteración anterior, pero necesitamos llevar la cuenta
                # Usamos la semana calculada previamente; la almacenamos en un dict auxiliar
                siguiente_año, siguiente_semana = semanas_actuales[pid]
                # Avanzar una semana
                siguiente_semana += 1
                if siguiente_semana > 52:
                    siguiente_semana = 1
                    siguiente_año += 1

            # Guardar la semana actual para la próxima iteración
            if w == 0:
                semanas_actuales = {pid: (siguiente_año, siguiente_semana) for pid in productos_faltantes}
            else:
                semanas_actuales[pid] = (siguiente_año, siguiente_semana)

            mes = min(12, max(1, round((siguiente_semana - 1) / 4.33) + 1))

            # Features
            semana_sin = np.sin(2 * np.pi * siguiente_semana / 52)
            semana_cos = np.cos(2 * np.pi * siguiente_semana / 52)
            buffer = buffers[pid]
            lag_1 = float(buffer[-1])
            lag_2 = float(buffer[-2]) if len(buffer) >= 2 else 0.0
            lag_4 = float(buffer[-4]) if len(buffer) >= 4 else 0.0
            rolling_mean_4 = float(np.mean(buffer[-4:])) if len(buffer) >= 4 else float(np.mean(buffer))
            rolling_std_4 = float(np.std(buffer[-4:])) if len(buffer) >= 4 else 0.0

            fila = {col: 0 for col in feature_cols}
            fila["mes"] = mes
            fila["semana_sin"] = semana_sin
            fila["semana_cos"] = semana_cos
            fila["lag_1"] = lag_1
            fila["lag_2"] = lag_2
            fila["lag_4"] = lag_4
            fila["rolling_mean_4"] = rolling_mean_4
            fila["rolling_std_4"] = rolling_std_4

            col_producto = f"prod_{pid}"
            if col_producto in fila:
                fila[col_producto] = 1

            filas.append(fila)
            pids_orden.append(pid)

        if not filas:
            continue

        # Predicción en lote para esta semana
        X_batch = pd.DataFrame(filas)[feature_cols]
        preds = modelo.predict(X_batch)
        preds = np.maximum(preds, 0)  # asegurar no negativos

        # Actualizar buffers y acumulados
        for idx, pid in enumerate(pids_orden):
            cantidad = float(preds[idx])
            totales[pid] += cantidad
            tendencias[pid].append(cantidad)
            buffers[pid].append(cantidad)
            # Mantener buffer de tamaño 8 (solo para lags)
            if len(buffers[pid]) > 8:
                buffers[pid] = buffers[pid][-8:]

    # PASO 3: Construir resultado final y guardar en caché individual
    for pid in productos_faltantes:
        total = totales.get(pid, 0.0)
        tendencia = _calcular_tendencia(tendencias.get(pid, []))
        meta = metadatos[pid]
        stock_actual = meta["stock_actual"]
        stock_minimo = meta["stock_minimo"]
        necesita = total > max(0, stock_actual - stock_minimo)

        # Crear una estructura de resultado similar a predecir_demanda_producto
        # (pero sin predicciones detalladas para no llenar la caché)
        # Sin embargo, para mantener la caché consistente, almacenamos solo el resumen.
        # Nota: no guardamos predicciones detalladas para no duplicar datos.
        # Si después se pide el detalle, se recalculará individualmente (con caché aparte).
        resultado_resumen = {
            "producto_id": pid,
            "nombre_producto": meta["nombre"],
            "stock_actual": stock_actual,
            "stock_minimo": stock_minimo,
            "total_predicho": round(total, 2),
            "necesita_reabastecimiento": necesita,
            "tendencia": tendencia,
            "predicciones": [],  # no se guardan en este resumen
            "predicciones_mensuales": [],
            "cantidad_a_pedir": round(max(0.0, total - max(0, stock_actual - stock_minimo)), 2),
            "confianza_modelo": 0.0,  # no se calcula
        }
        # Guardar en caché individual para que futuras consultas rápidas lo usen
        # pero no es la misma clave que la de predecir_demanda_producto (que usa semanas)
        # Para no duplicar, usamos la misma clave que usaría predecir_demanda_producto
        # pero con la estructura completa (aunque sin predicciones detalladas)
        # Lo mejor es no guardar este resumen en la caché de detalle, sino que la caché de detalle
        # se llenará cuando se llame a predecir_demanda_producto por separado.
        # Por tanto, NO guardamos en caché aquí, solo devolvemos el resumen.

        # Agregar al resultado
        resultados.append({
            "producto_id": pid,
            "nombre_producto": meta["nombre"],
            "stock_actual": stock_actual,
            "stock_minimo": stock_minimo,
            "total_predicho": round(total, 2),
            "necesita_reabastecimiento": necesita,
            "urgencia": _calcular_urgencia(stock_actual, stock_minimo, necesita),
            "tendencia": tendencia,
        })

    return resultados


def obtener_importancia_features() -> Dict:
    modelo_data = _cargar_modelo()
    if modelo_data is None:
        return {"error": "El modelo no ha sido entrenado aún."}

    modelo = modelo_data["modelo"]
    feature_cols = modelo_data["feature_cols"]

    importancias = modelo.feature_importances_
    total = importancias.sum()
    features = [
        {
            "feature": feat,
            "importancia": round(float(imp), 6),
            "importancia_porcentaje": round(float(imp / total) * 100, 2),
        }
        for feat, imp in sorted(
            zip(feature_cols, importancias), key=lambda x: x[1], reverse=True
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