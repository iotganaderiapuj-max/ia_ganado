import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Entrenar o cargar modelo IA
try:
    modelo = joblib.load("modelo_temp.pkl")
except:
    print("⚙️ Entrenando modelo IA de temperatura (RandomForest)...")
    np.random.seed(42)
    # Variables: temperatura ambiente, humedad, hora
    X = np.random.rand(300, 3) * [10, 40, 24] + [20, 30, 0]
    y = 34 + 0.1 * X[:,0] + 0.02 * X[:,1] + 0.05 * X[:,2] + np.random.randn(300)
    modelo = RandomForestRegressor(n_estimators=80)
    modelo.fit(X, y)
    joblib.dump(modelo, "modelo_temp.pkl")

def procesar_temperatura(temp_actual, temp_amb, humedad):
    """4️⃣ Calcula temperatura base, variaciones y estado térmico"""
    if temp_actual is None or temp_amb is None:
        return {"error": "faltan datos de temperatura"}

    hora = 12  # valor fijo si no viene en el payload
    temp_base = modelo.predict([[temp_amb, humedad, hora]])[0]

    delta = temp_actual - temp_base
    delta_pct = (delta / temp_base) * 100

    if delta >= 1.5:
        estado = "posible_celo"
    elif delta <= -1.5:
        estado = "enfriamiento"
    else:
        estado = "normal"

    # Índice térmico ambiental (simplificado)
    indice_termico = temp_amb + 0.1 * humedad

    return {
        "temp_dorsal": round(temp_actual, 2),
        "temp_amb": round(temp_amb, 2),
        "humedad": round(humedad, 2),
        "temp_base": round(float(temp_base), 2),
        "delta_temp": round(float(delta), 2),
        "delta_pct": round(float(delta_pct), 2),
        "indice_termico": round(float(indice_termico), 2),
        "estado": estado
    }
