from flask import Flask, request, jsonify
import requests
import time
from utils.procesamiento_temp import procesar_temperatura
from utils.procesamiento_accel import procesar_acelerometro
from utils.procesamiento_gps import procesar_gps
from utils.envio_thingsboard import enviar_a_thingsboard
import os
import traceback

app = Flask(__name__)

THINGSBOARD_URL = "http://thingsboard.cloud/api/v1/TOKEN_DE_TU_DISPOSITIVO/telemetry"

@app.route('/')
def home():
    return "Servidor Flask funcionando correctamente 🚀"

@app.route('/ttn-data', methods=['POST'])
def recibir_datos_ttn():
    try:
        data = request.get_json()
        print("📩 Datos recibidos desde TTN:", data)

        # 🔹 Lectura de sensores
        temp = data.get('temp_body_c') or data.get('temp_dorsal')
        temp_amb = data.get('temp_amb_c') or data.get('temp_amb')
        humedad = data.get('humedad', 65)

        # 🔹 GPS y acelerómetro
        gps = {"lat": data.get('lat'), "lon": data.get('lon')}
        accel = {"v_max_ms": data.get('v_max_ms'), "v_mean_ms": data.get('v_mean_ms')}

        # 🔹 Procesamientos
        resultados_temp = procesar_temperatura(temp, temp_amb, humedad) or {}
        resultados_accel = procesar_acelerometro(accel) or {}
        resultados_gps = procesar_gps(gps) or {}

        # 🔹 Ensamble de salida final
        salida = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            **resultados_temp,
            **resultados_accel,
            **resultados_gps
        }

        # ⚠️ Comprobación de claves faltantes
        if "estado" not in salida or "actividad" not in salida:
            print("⚠️ Advertencia: faltan claves esperadas en salida:", salida)

        # 🔹 Estado general con seguridad
        salida["estado_general"] = (
            "alerta_celo"
            if salida.get("estado") == "posible_celo" and salida.get("actividad") == "alta"
            else salida.get("estado", "desconocido")
        )

        print("✅ Datos procesados:", salida)

        # 🔹 Envío a ThingsBoard
        enviar_a_thingsboard(THINGSBOARD_URL, salida)

        return jsonify(salida), 200

    except Exception as e:
        print("❌ Error procesando datos TTN:", str(e))
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🔥 Servidor corriendo en: http://0.0.0.0:{port}/")
    app.run(host='0.0.0.0', port=port)
