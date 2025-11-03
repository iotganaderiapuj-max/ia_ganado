import requests

def enviar_a_thingsboard(url, payload):
    """7️⃣ Envía los datos procesados al dashboard de ThingsBoard"""
    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            print(f"✅ Enviado a ThingsBoard → {payload}")
        else:
            print(f"⚠️ Error al enviar a ThingsBoard ({r.status_code})")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
