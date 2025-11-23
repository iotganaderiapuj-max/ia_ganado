# app.py — Flask final para TTN v3 + ThingsBoard
from flask import Flask, request, jsonify
import os
import traceback
from datetime import datetime
import pytz

from utils.procesamiento_temp import procesar_temperatura
from utils.procesamiento_accel import procesar_acelerometro
from utils.procesamiento_gps import procesar_gps
from utils.envio_thingsboard import enviar_a_thingsboard

app = Flask(__name__)

# ───────── Config ─────────
TZ = pytz.timezone("America/Bogota")
TB_TOKEN = os.getenv("THINGSBOARD_TOKEN", "TOKEN_DE_TU_DISPOSITIVO")
TB_BASE  = os.getenv("THINGSBOARD_BASE", "https://thingsboard.cloud")
THINGSBOARD_URL = f"{TB_BASE}/api/v1/{TB_TOKEN}/telemetry"

@app.get("/")
def health():
    return jsonify({"ok": True, "service": "iot_ganaderia", "tb_url": THINGSBOARD_URL})

# ---------- Helpers ----------
def _parse_ttn_v3(body: dict):
    """Extrae y normaliza desde TTN v3 (uplink_message.decoded_payload)."""
    end_ids = body.get("end_device_ids") or {}
    dev_id = end_ids.get("device_id")
    uplink = body.get("uplink_message") or {}
    dec = uplink.get("decoded_payload") or {}

    # Hora confiable: received_at (UTC) → Bogotá
    received_at = body.get("received_at") or uplink.get("received_at")
    local_iso = None
    if received_at:
        try:
            dt_utc = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
            local_iso = dt_utc.astimezone(TZ).isoformat()
        except Exception as e:
            print("time parse error:", e)

    # GPS del payload
    lat = dec.get("latitude") or dec.get("lat")
    lon = dec.get("longitude") or dec.get("lon")

    # Si no hay GPS en payload, intenta con ubicación del gateway
    if (lat is None or lon is None):
        rxm = uplink.get("rx_metadata") or []
        if isinstance(rxm, list) and rxm:
            loc = (rxm[0].get("location") or {})
            lat = loc.get("latitude", lat)
            lon = loc.get("longitude", lon)

    # Normaliza llaves que esperan tus utils
    norm = {
        "dev_id":      dev_id,
        "cow_id":      dec.get("cow_id"),
        "temp_body_c": dec.get("To_c") or dec.get("temp_body_c") or dec.get("temp_dorsal"),
        "temp_amb_c":  dec.get("Ta_c") or dec.get("temp_amb_c")  or dec.get("temp_amb"),
        "v_max_ms":    dec.get("v_max_ms"),
        "v_mean_ms":   dec.get("v_mean_ms"),
        "ODBA_g":      dec.get("ODBA_g"),
        "VeDBA_g":     dec.get("VeDBA_g"),
        "lat":         lat,
        "lon":         lon,
        "ts_epoch":    dec.get("epoch_s"),  
        "received_local_iso": local_iso
    }
    return norm

def _parse_flat(body: dict):
    """Compatibilidad si algún cliente envía llaves planas."""
    return {
        "dev_id":      body.get("dev_id"),
        "cow_id":      body.get("cow_id"),
        "temp_body_c": body.get("temp_body_c") or body.get("temp_dorsal"),
        "temp_amb_c":  body.get("temp_amb_c")  or body.get("temp_amb"),
        "humedad":     body.get("humedad", 65),
        "v_max_ms":    body.get("v_max_ms"),
        "v_mean_ms":   body.get("v_mean_ms"),
        "ODBA_g":      body.get("ODBA_g"),
        "VeDBA_g":     body.get("VeDBA_g"),
        "lat":         body.get("lat"),
        "lon":         body.get("lon"),
        "received_local_iso": None
        "ts_epoch":    body.get("ts_epoch"),

    }

def _handle_uplink():
    """Core: parsea, procesa, envía a TB y retorna salida. Siempre 200."""
    try:
        body = request.get_json(force=True, silent=True) or {}
        print("📩 RAW BODY:", body)

        # Detecta TTN v3 (estructura anidada) vs. formato plano
        if "uplink_message" in body or "end_device_ids" in body:
            norm = _parse_ttn_v3(body)
        else:
            norm = _parse_flat(body)

        # Timestamp local (fallback si no vino received_at)
        if not norm.get("received_local_iso"):
            norm["received_local_iso"] = datetime.now(TZ).isoformat()

        # Arma entradas para tus utils
        temp_body = norm.get("temp_body_c")
        temp_amb  = norm.get("temp_amb_c")
        humedad   = norm.get("humedad", 65)
        gps = {"lat": norm.get("lat"), "lon": norm.get("lon")}
        accel = {
            "v_max_ms":  norm.get("v_max_ms"),
            "v_mean_ms": norm.get("v_mean_ms"),
            "ODBA_g":    norm.get("ODBA_g"),
            "VeDBA_g":   norm.get("VeDBA_g"),
        }

        # Procesamientos
        resultados_temp  = (procesar_temperatura(temp_body, temp_amb, humedad) or {})
        resultados_accel = (procesar_acelerometro(accel) or {})
        resultados_gps   = (procesar_gps(gps) or {})

        salida = {
            "timestamp_local": norm["received_local_iso"],
            "dev_id": norm.get("dev_id"),
            "cow_id": norm.get("cow_id"),
            "ts_epoch": norm.get("ts_epoch"),
            
            **resultados_temp,
            **resultados_accel,
            **resultados_gps
        }

        if "estado" not in salida or "actividad" not in salida:
            print("⚠️ Advertencia: faltan claves esperadas en salida:", list(salida.keys()))

        salida["estado_general"] = (
            "alerta_celo"
            if salida.get("estado") == "posible_celo" and salida.get("actividad") == "alta"
            else salida.get("estado", "desconocido")
        )

        print("✅ PARSED:", salida)

        # Envío a ThingsBoard (no bloquea 200 si falla)
        try:
            enviar_a_thingsboard(THINGSBOARD_URL, salida)
        except Exception as e:
            print("⚠️ Error enviando a ThingsBoard:", e)

        return jsonify({"ok": True, "data": salida}), 200

    except Exception as e:
        print("❌ Error procesando uplink:", str(e))
        print(traceback.format_exc())
        # Igual devolvemos 200 para que TTN no reintente sin fin, pero marcamos ok=False
        return jsonify({"ok": False, "error": str(e)}), 200

# ---------- Rutas (todas válidas para TTN) ----------
@app.post("/ttn-data")
def ttn_data_root():
    return _handle_uplink()

@app.post("/ttn-data/uplink")
def ttn_data_uplink():
    return _handle_uplink()

@app.post("/uplink")
def uplink_root():
    return _handle_uplink()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🔥 Servidor corriendo en: http://0.0.0.0:{port}/  → TB={THINGSBOARD_URL}")
    app.run(host="0.0.0.0", port=port)

