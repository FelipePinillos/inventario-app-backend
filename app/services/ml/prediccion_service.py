"""
Servicio de predicción de demanda usando RandomForestRegressor.

Flujo:
  1. Consulta historial de ventas confirmadas desde la BD.
  2. Agrega cantidades por producto y semana ISO.
  3. Genera features de rezago (lag) y ventanas móviles.
  4. Entrena un RandomForestRegressor global (un modelo para todos los productos).
  5. Genera predicciones semanales futuras por producto.
  6. Detecta alertas de reabastecimiento.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Optional

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

FEATURE_COLS = [
    "id_producto",
    "mes",
    "semana",
    "lag_1",
    "lag_2",
    "lag_4",
    "rolling_mean_4",
    "rolling_std_4",
]
TARGET_COL = "cantidad_vendida"

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


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


def _cargar_modelo() -> Optional[RandomForestRegressor]:
    """Carga el modelo guardado en disco. Devuelve None si no existe."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


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
    Predice la demanda semanal para un producto específico durante las
    próximas `semanas` semanas.

    Retorna un dict con la predicción detallada o un mensaje de error.
    """
    modelo = _cargar_modelo()
    if modelo is None:
        return {
            "error": "El modelo no ha sido entrenado. "
            "Llame a POST /api/v1/predicciones/entrenar primero."
        }

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

    # Buffer con el historial de cantidades (rellenado con 0 si hay poco historial)
    historial = df_prod["cantidad_vendida"].tolist()
    if len(historial) < 4:
        historial = [0.0] * (4 - len(historial)) + historial
    buffer = list(historial[-8:])  # Últimas 8 semanas como ventana deslizante

    ultimo_año = int(df_prod["año"].iloc[-1])
    ultima_semana = int(df_prod["semana"].iloc[-1])

    predicciones = []

    for i in range(semanas):
        # Avanzar una semana
        ultima_semana += 1
        if ultima_semana > 52:
            ultima_semana = 1
            ultimo_año += 1

        # Mes aproximado desde número de semana ISO
        mes = min(12, max(1, round((ultima_semana - 1) / 4.33) + 1))

        lag_1 = float(buffer[-1])
        lag_2 = float(buffer[-2]) if len(buffer) >= 2 else 0.0
        lag_4 = float(buffer[-4]) if len(buffer) >= 4 else 0.0
        rolling_mean_4 = float(np.mean(buffer[-4:])) if len(buffer) >= 4 else float(np.mean(buffer))
        rolling_std_4 = float(np.std(buffer[-4:])) if len(buffer) >= 4 else 0.0

        X_pred = pd.DataFrame(
            [
                {
                    "id_producto": producto_id,
                    "mes": mes,
                    "semana": ultima_semana,
                    "lag_1": lag_1,
                    "lag_2": lag_2,
                    "lag_4": lag_4,
                    "rolling_mean_4": rolling_mean_4,
                    "rolling_std_4": rolling_std_4,
                }
            ]
        )

        cantidad_predicha = max(0.0, float(modelo.predict(X_pred)[0]))
        buffer.append(cantidad_predicha)

        # Convertir semana ISO → fechas reales
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
            }
        )

    total_predicho = sum(p["cantidad_predicha"] for p in predicciones)
    stock_disponible = max(0, stock_actual - stock_minimo)
    necesita_reabastecimiento = total_predicho > stock_disponible
    cantidad_a_pedir = max(0.0, total_predicho - stock_disponible)

    return {
        "producto_id": producto_id,
        "nombre_producto": nombre_producto,
        "stock_actual": stock_actual,
        "stock_minimo": stock_minimo,
        "predicciones": predicciones,
        "total_predicho": round(total_predicho, 2),
        "necesita_reabastecimiento": necesita_reabastecimiento,
        "cantidad_a_pedir": round(cantidad_a_pedir, 2),
    }


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
