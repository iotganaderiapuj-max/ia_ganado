from flask import Flask, request, jsonify
import requests
import time
from utils.procesamiento_temp import procesar_temperatura
from utils.procesamiento_accel import procesar_acelerometro
from utils.procesamiento_gps import procesar_gps
from utils.envio_thingsboard import enviar_a_thingsboard

app = Flask(__name__)

THINGSBOARD_URL = "http://thingsboard.cloud/api/v1/TOKEN_DE_TU_DISPOSITIVO/telemetry"

@app.route('/ttn-data', methods=['POST'])
def recibir_datos_ttn():
    """3️⃣ Recibe los datos del TTN (The Things Network)"""
    data = request.get_json()
    print("📩 Datos recibidos:", data)

    # Extraer variables
    temp = data.get('temp_dorsal')
    temp_amb = data.get('temp_amb')
    humedad = data.get('humedad', 65)
    gps = data.get('gps', {})
    accel = data.get('acelerometro', {})

    # Procesamiento IA
    resultados_temp = procesar_temperatura(temp, temp_amb, humedad)
    resultados_accel = procesar_acelerometro(accel)
    resultados_gps = procesar_gps(gps)

    # Combinar todos los resultados
    salida = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        **resultados_temp,
        **resultados_accel,
        **resultados_gps
    }

    # Estado general
    salida["estado_general"] = "alerta_celo" if salida["estado"] == "posible_celo" and salida["actividad"] == "alta" else salida["estado"]

    # Enviar a ThingsBoard
    enviar_a_thingsboard(THINGSBOARD_URL, salida)

    return jsonify(salida), 200


if __name__ == '__main__':
    print("🔥 Servidor corriendo en: http://0.0.0.0:5000/ttn-data")
    app.run(host='0.0.0.0', port=5000)
