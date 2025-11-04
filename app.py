from flask import Flask, request, jsonify
import requests
import time
from utils.procesamiento_temp import procesar_temperatura
from utils.procesamiento_accel import procesar_acelerometro
from utils.procesamiento_gps import procesar_gps
from utils.envio_thingsboard import enviar_a_thingsboard
import os

app = Flask(__name__)

THINGSBOARD_URL = "http://thingsboard.cloud/api/v1/TOKEN_DE_TU_DISPOSITIVO/telemetry"

@app.route('/')
def home():
    return "Servidor Flask funcionando correctamente 🚀"

@app.route('/ttn-data', methods=['POST'])
def recibir_datos_ttn():
    """Recibe los datos del TTN (The Things Network)"""
    data = request.get_json()
    print("📩 Datos recibidos:", data)

    temp = data.get('temp_dorsal')
    temp_amb = data.get('temp_amb')
    humedad = data.get('humedad', 65)
    gps = data.get('gps', {})
    accel = data.get('acelerometro', {})

    resultados_temp = procesar_temperatura(temp, temp_amb, humedad)
    resultados_accel = procesar_acelerometro(accel)
    resultados_gps = procesar_gps(gps)

    salida = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        **resultados_temp,
        **resultados_accel,
        **resultados_gps
    }

    salida["estado_general"] = "alerta_celo" if salida["estado"] == "posible_celo" and salida["actividad"] == "alta" else salida["estado"]

    enviar_a_thingsboard(THINGSBOARD_URL, salida)

    return jsonify(salida), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🔥 Servidor corriendo en: http://0.0.0.0:{port}/")
    app.run(host='0.0.0.0', port=port)

