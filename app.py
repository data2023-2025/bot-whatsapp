from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuración de variables de entorno (Prioridad de seguridad)
TOKEN_VERIFICACION = os.environ.get("TOKEN_VERIFICACION", "TU_TOKEN_DE_VERIFICACION_AQUI")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "TU_META_ACCESS_TOKEN_AQUI")
META_PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID", "TU_PHONE_NUMBER_ID_AQUI")

# =====================================================================
# LLAVE MAESTRA / CONTROL DE ADMINISTRACIÓN LOCAL
# =====================================================================
# Coloca aquí tu número personal (con código de país, ej: "584122012745")
# Esto actúa como filtro de seguridad en el backend antes de llamar a Meta.
NUMEROS_AUTORIZADOS_BACKEND = [
    "584122012745",
    "TU_SEGUNDO_NUMERO_DE_PRUEBA"
]
# =====================================================================

def enviar_mensaje_whatsapp(telefono_destino, texto_respuesta):
    """
    Se conecta de forma segura con la API Graph de Meta para despachar el mensaje.
    """
    url = f"https://graph.facebook.com/v25.0/{META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono_destino,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": texto_respuesta
        }
    }
    
    try:
        print(f"[BOT] Intentando enviar mensaje a {telefono_destino}...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"[BOT] Código de respuesta de Meta: {response.status_code}")
        print(f"[BOT] Cuerpo de respuesta de Meta: {response.text}")
        
        if response.status_code != 200:
            print(f"[ALERTA] Meta rechazó el envío. Verifique si el número {telefono_destino} está autorizado en el panel de Meta for Developers.")
            
        return response.status_code == 200
    except Exception as e:
        print(f"[BOT] ERROR CRÍTICO al conectar con la API de Meta: {str(e)}")
        return False

@app.route('/', methods=['GET'])
def index():
    return "Servidor del Bot de WhatsApp ORAPC operativo con Filtro de Seguridad.", 200

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    """
    Validación obligatoria (Handshake) para Meta for Developers.
    """
    hub_mode = request.args.get('hub.mode')
    hub_token = request.args.get('hub.verify_token')
    hub_challenge = request.args.get('hub.challenge')
    
    if hub_mode == 'subscribe' and hub_token == TOKEN_VERIFICACION:
        print("[WEBHOOK] Validación exitosa con Meta.")
        return hub_challenge, 200
    print("[WEBHOOK] Error de validación: Tokens no coinciden.")
    return "Fallo de autenticación", 403

@app.route('/webhook', methods=['POST'])
def recibir_webhook():
    """
    Procesamiento del JSON entrante con tolerancia a fallos y extracción segura.
    """
    datos = request.get_json()
    print(f"[WEBHOOK] Payload recibido de Meta: {datos}")
    
    if not datos:
        return jsonify({"status": "error", "message": "Payload vacío"}), 400

    try:
        if "object" in datos and datos["object"] == "whatsapp_business_account":
            for entry in datos.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    if "messages" in value and len(value["messages"]) > 0:
                        mensaje_obj = value["messages"][0]
                        telefono_remitente = mensaje_obj.get("from")
                        
                        # FILTRO DE SEGURIDAD INTERNO (LLAVE MAESTRA)
                        if telefono_remitente not in NUMEROS_AUTORIZADOS_BACKEND:
                            print(f"[SEGURIDAD] Mensaje ignorado de {telefono_remitente}: No está en la lista blanca del backend.")
                            return jsonify({"status": "ignored", "reason": "Unauthorized number"}), 200
                        
                        if "text" in mensaje_obj and "body" in mensaje_obj["text"]:
                            texto_usuario = mensaje_obj["text"]["body"].strip().upper()
                            print(f"[BOT] Mensaje procesado de {telefono_remitente}: '{texto_usuario}'")
                            
                            if texto_usuario == "MENU":
                                menú_institucional = (
                                    "🏛️ *Bienvenido al Sistema de Atención Ciudadana de la ORAPC* 🏛️\n\n"
                                    "Por favor, seleccione una opción respondiendo con el número correspondiente:\n\n"
                                    "1️⃣ *Consultar estado de trámite.*\n"
                                    "2️⃣ *Requisitos para solicitudes.*\n"
                                    "3️⃣ *Hablar con un analista de guardia.*\n"
                                    "4️⃣ *Horarios de atención e información institucional.*"
                                )
                                enviar_mensaje_whatsapp(telefono_remitente, menú_institucional)
                            else:
                                respuesta_por_defecto = "Para desplegar las opciones institucionales, por favor escribe la palabra *MENU*."
                                enviar_mensaje_whatsapp(telefono_remitente, respuesta_por_defecto)
                                
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"[BOT] ERROR INTERNO al parsear el JSON: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
