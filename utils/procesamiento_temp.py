import numpy as np
from datetime import datetime
from math import isfinite

# RANGOS "plausibles" (ajústalos si quieres)
RANGO_T_AMB = (-20.0, 60.0)   # °C ambiente
RANGO_T_DOR = (20.0, 45.0)    # °C dorsal/vaca (típico 28–41)
RANGO_HUM   = (0.0, 100.0)    # %

def _to_float_or_none(x):
    try:
        if x is None: return None
        xf = float(x)
        # NaN o infinitos => inválidos
        if not isfinite(xf): return None
        return xf
    except (TypeError, ValueError):
        return None

def _en_rango(x, lo, hi):
    return (x is not None) and (lo <= x <= hi)

def procesar_temperatura(temp_actual, temp_amb, humedad):
    """
    Calcula temperatura base, variaciones y estado térmico de forma robusta.
    - Tolera None, strings, NaN, 0 'fantasma', y valores fuera de rango.
    - Si no hay dato válido de dorsal, retorna estado 'sin_lectura' pero igual entrega índice térmico.
    - Usa el modelo si está disponible; si no, hace fallback lineal.
    """

    # ---- Normalización segura ----
    t_dor = _to_float_or_none(temp_actual)
    t_amb = _to_float_or_none(temp_amb)
    hum   = _to_float_or_none(humedad)

    # Zeros fantasma (muchas veces significan “sin lectura”); los tratamos como None
    if t_dor == 0.0: t_dor = None
    if t_amb == 0.0: t_amb = None

    # Clamps/validación por rango
    if not _en_rango(t_amb, *RANGO_T_AMB):
        t_amb = None
    if not _en_rango(t_dor, *RANGO_T_DOR):
        # si es None o fuera de rango, la tratamos como sin lectura
        t_dor = None
    if hum is None:
        hum = 65.0
    hum = max(RANGO_HUM[0], min(RANGO_HUM[1], hum))

    # Hora (para el modelo); si no te llega del payload, usa hora local
    try:
        hora = datetime.now().hour
    except Exception:
        hora = 12

    # ---- Temperatura base (modelo o fallback) ----
    temp_base = None
    try:
        # usa tu modelo si existe en el scope
        temp_base = float(modelo.predict([[t_amb if t_amb is not None else 25.0,
                                           hum,
                                           hora]])[0])
    except Exception:
        # Fallback simple cuando no hay modelo o falla
        # Base = ambiente + efecto humedad (muy simple)
        base_amb = t_amb if t_amb is not None else 25.0
        temp_base = base_amb + 0.02 * hum  # ajústalo si quieres

    # ---- Índice térmico ambiental (simple) ----
    indice_termico = (t_amb if t_amb is not None else 25.0) + 0.1 * hum

    # ---- Cuando NO hay lectura dorsal válida ----
    if t_dor is None:
        return {
            "temp_dorsal": None,
            "temp_amb": round(t_amb, 2) if t_amb is not None else None,
            "humedad": round(hum, 2),
            "temp_base": round(temp_base, 2) if temp_base is not None else None,
            "delta_temp": None,
            "delta_pct": None,
            "indice_termico": round(float(indice_termico), 2),
            "estado": "sin_lectura"
        }

    # ---- Con lectura dorsal válida ----
    # Si no hay ambiente válido, usamos base como referencia
    ref = temp_base if temp_base is not None else (t_amb if t_amb is not None else 30.0)

    delta = t_dor - ref
    try:
        delta_pct = (delta / ref) * 100.0 if ref not in (None, 0) else None
    except Exception:
        delta_pct = None

    # Reglas de estado (ajústalas a tu criterio/validación clínica)
    if delta is None:
        estado = "normal"
    else:
        if delta >= 1.5:
            estado = "posible_celo"
        elif delta <= -1.5:
            estado = "enfriamiento"
        else:
            estado = "normal"

    return {
        "temp_dorsal": round(float(t_dor), 2),
        "temp_amb": round(t_amb, 2) if t_amb is not None else None,
        "humedad": round(hum, 2),
        "temp_base": round(temp_base, 2) if temp_base is not None else None,
        "delta_temp": round(delta, 2) if delta is not None else None,
        "delta_pct": round(delta_pct, 2) if (delta_pct is not None and np.isfinite(delta_pct)) else None,
        "indice_termico": round(float(indice_termico), 2),
        "estado": estado
    }
