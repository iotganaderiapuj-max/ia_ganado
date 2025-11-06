import numpy as np

def procesar_acelerometro(accel):
    """
    Procesa los datos del acelerómetro para obtener ODBA, VeDBA y nivel de actividad.
    Tolera valores None, NaN, negativos o fuera de rango.
    """

    # Extrae valores con tolerancia
    odba = accel.get('ODBA') or accel.get('ODBA_g') or 0
    vedba = accel.get('VeDBA') or accel.get('VeDBA_g') or 0

    # Convierte a float de forma segura
    try:
        odba = float(odba)
    except (TypeError, ValueError):
        odba = 0.0

    try:
        vedba = float(vedba)
    except (TypeError, ValueError):
        vedba = 0.0

    # Rechaza valores fuera de rango físico (por ejemplo, ruido)
    if np.isnan(odba) or abs(odba) > 10:
        odba = 0.0
    if np.isnan(vedba) or abs(vedba) > 10:
        vedba = 0.0

    # Clasificación de actividad robusta
    if vedba > 1.5:
        actividad = "alta"
    elif vedba > 0.3:
        actividad = "media"
    else:
        actividad = "baja"

    return {
        "ODBA": round(odba, 3),
        "VeDBA": round(vedba, 3),
        "actividad": actividad
    }
