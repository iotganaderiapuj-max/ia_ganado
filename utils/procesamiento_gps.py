import numpy as np

def procesar_gps(gps):
    """
    Calcula distancia, velocidad y rectitud si hay varios puntos GPS.
    Si solo llega un punto (lat/lon únicos), devuelve datos mínimos.
    """
    try:
        lat = gps.get('lat')
        lon = gps.get('lon')
        tiempos = gps.get('timestamp', [])

        # Si vienen como listas (trayectoria)
        if isinstance(lat, list) and len(lat) > 1:
            lat = np.array(lat, dtype=float)
            lon = np.array(lon, dtype=float)
            tiempos = np.array(tiempos, dtype=float) if len(tiempos) == len(lat) else np.arange(len(lat))

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

        # Si solo llega un punto GPS (lo que TTN manda)
        elif isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            return {
                "lat": lat,
                "lon": lon,
                "distancia": 0,
                "velocidad": 0,
                "rectitud": 1
            }

        else:
            return {"lat": None, "lon": None, "distancia": 0, "velocidad": 0, "rectitud": 1}

    except Exception as e:
        print(f"❌ Error en procesar_gps: {e}")
        return {"lat": None, "lon": None, "distancia": 0, "velocidad": 0, "rectitud": 1}
