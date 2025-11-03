import numpy as np

def procesar_gps(gps):
    """6️⃣ Calcula distancia total, velocidad media y rectitud"""
    lat = np.array(gps.get('lat', []))
    lon = np.array(gps.get('lon', []))
    tiempos = np.array(gps.get('timestamp', []))

    if len(lat) < 2:
        return {"distancia": 0, "velocidad": 0, "rectitud": 1}

    R = 6371000
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    dlat = np.diff(lat_r)
    dlon = np.diff(lon_r)
    a = np.sin(dlat/2)**2 + np.cos(lat_r[:-1]) * np.cos(lat_r[1:]) * np.sin(dlon/2)**2
    distancias = 2 * R * np.arcsin(np.sqrt(a))
    distancia_total = np.sum(distancias)

    duracion = tiempos[-1] - tiempos[0]
    velocidad = distancia_total / duracion if duracion > 0 else 0

    desplazamiento_neto = np.sqrt((R * (lat_r[-1]-lat_r[0]))**2 + (R * (lon_r[-1]-lon_r[0]))**2)
    rectitud = desplazamiento_neto / distancia_total if distancia_total > 0 else 1

    return {
        "distancia": round(float(distancia_total), 2),
        "velocidad": round(float(velocidad), 2),
        "rectitud": round(float(rectitud), 2)
    }
