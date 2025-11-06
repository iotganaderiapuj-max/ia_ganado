import numpy as np
from datetime import datetime
from math import radians, sin, cos, asin, sqrt, isfinite

R_EARTH = 6371000.0  # m

def _to_float_or_none(x):
    try:
        if x is None: return None
        xf = float(x)
        if not isfinite(xf): return None
        return xf
    except (ValueError, TypeError):
        return None

def _parse_time_to_seconds(t):
    """
    Devuelve segundos (float) desde epoch.
    Acepta epoch (int/float/str) o ISO8601 (str).
    """
    if t is None: return None
    # epoch
    try:
        val = float(t)
        if isfinite(val): return val
    except Exception:
        pass
    # ISO8601
    try:
        # maneja '...Z'
        iso = str(t).replace("Z", "+00:00")
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return None

def _haversine(lat1, lon1, lat2, lon2):
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R_EARTH * asin(sqrt(max(0.0, min(1.0, a))))

def procesar_gps(gps):
    """
    Calcula distancia, velocidad y rectitud de manera robusta.
    - Acepta un punto (lat/lon) o listas de puntos.
    - Normaliza tiempos (epoch o ISO) a segundos.
    - Filtra valores inválidos (None, NaN, fuera de rango).
    - Trata (0,0) como inválido (opcional y común en GPS sin fix).
    - Limita velocidades absurdas.
    """
    try:
        lat = gps.get("lat")
        lon = gps.get("lon")
        tiempos = gps.get("timestamp", [])

        # --- Caso trayectoria (listas) ---
        if isinstance(lat, (list, tuple)) and isinstance(lon, (list, tuple)):
            # Coerce a float y filtra pares válidos
            lats = [_to_float_or_none(v) for v in lat]
            lons = [_to_float_or_none(v) for v in lon]

            # (0,0) se considera inválido (sin fix)
            valid_idx = [
                i for i, (la, lo) in enumerate(zip(lats, lons))
                if la is not None and lo is not None
                and -90.0 <= la <= 90.0 and -180.0 <= lo <= 180.0
                and not (abs(la) < 1e-9 and abs(lo) < 1e-9)
            ]
            if len(valid_idx) < 1:
                return {"lat": None, "lon": None, "distancia": 0, "velocidad": 0, "rectitud": 1}

            lats = [lats[i] for i in valid_idx]
            lons = [lons[i] for i in valid_idx]

            # Tiempos
            if isinstance(tiempos, (list, tuple)) and len(tiempos) >= len(valid_idx):
                t_sel = [tiempos[i] for i in valid_idx]
                t_secs = [_parse_time_to_seconds(t) for t in t_sel]
            else:
                # si no hay tiempos válidos, usa índice como pseudotiempo
                t_secs = list(map(float, range(len(lats))))

            # reemplaza None en tiempos por interpolación simple
            t_secs = np.array([
                (t if t is not None and isfinite(t) else np.nan) for t in t_secs
            ], dtype=float)

            # si todos NaN → usa índice
            if np.isnan(t_secs).all():
                t_secs = np.arange(len(lats), dtype=float)

            # forward/backward fill básico
            for i in range(len(t_secs)):
                if np.isnan(t_secs[i]):
                    t_secs[i] = t_secs[i-1] if i > 0 else 0.0
            for i in range(len(t_secs)-2, -1, -1):
                if t_secs[i] > t_secs[i+1]:
                    t_secs[i] = t_secs[i+1]  # evita regresión temporal

            # Distancias segmento a segmento
            dists = [
                _haversine(lats[i], lons[i], lats[i+1], lons[i+1])
                for i in range(len(lats)-1)
            ]
            distancia_total = float(np.nansum(dists))

            # Duración
            duracion = float(max(0.0, t_secs[-1] - t_secs[0]))
            velocidad = (distancia_total / duracion) if duracion > 0 else 0.0

            # Filtra velocidades absurdas (> 20 m/s ~ 72 km/h para ganado/porteador)
            if velocidad > 20.0:
                velocidad = 0.0  # o clamp a 20.0

            # Rectitud = desplazamiento neto / distancia recorrida
            desplazamiento_neto = _haversine(lats[0], lons[0], lats[-1], lons[-1])
            rectitud = (desplazamiento_neto / distancia_total) if distancia_total > 0 else 1.0
            rectitud = float(min(1.0, max(0.0, rectitud)))

            return {
                "lat": lats[-1],
                "lon": lons[-1],
                "distancia": round(distancia_total, 2),
                "velocidad": round(velocidad, 2),
                "rectitud": round(rectitud, 2),
            }

        # --- Caso punto único ---
        la = _to_float_or_none(lat)
        lo = _to_float_or_none(lon)
        if la is None or lo is None or not (-90 <= la <= 90) or not (-180 <= lo <= 180) or (abs(la) < 1e-9 and abs(lo) < 1e-9):
            return {"lat": None, "lon": None, "distancia": 0, "velocidad": 0, "rectitud": 1}

        return {"lat": la, "lon": lo, "distancia": 0, "velocidad": 0, "rectitud": 1}

    except Exception as e:
        print(f"❌ Error en procesar_gps: {e}")
        return {"lat": None, "lon": None, "distancia": 0, "velocidad": 0, "rectitud": 1}

