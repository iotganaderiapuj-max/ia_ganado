import numpy as np

def procesar_acelerometro(accel):
    ODBA = accel.get('ODBA', 0)
    VeDBA = accel.get('VeDBA', 0)
    actividad = "alta" if VeDBA > 1.5 else "baja"
    return {"ODBA": ODBA, "VeDBA": VeDBA, "actividad": actividad}

