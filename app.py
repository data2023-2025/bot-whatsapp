import os
import requests
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

class MetaWhatsAppClient:
    """Cliente de producción robusto para la API Cloud de WhatsApp."""
    
    def __init__(self):
        self.token = os.getenv(
            "META_WA_TOKEN", 
            "EAAS3zBPxZAhkBRsAReBI5uxADF8ltRdLuUxjRPTv5GYTZCf3qZCQLdEufjRHfhw0IrtWlWb1qaeYZAl92dhJaN2efsl9c03ZBdtvNltHpwYJkze4XE7O5FBdxjMSAZAqcT1z0gOfbIQXsUfiLJDxaoxGryZBr2p4QZCuSB1dS2LSb1agtZAJMcSFxgZC3wWoahhTIZCVHoKMiXAnJPysIMJgw2Jl9Uzf6L01PiY3qIu6nIaifAibPc5XKq8d7FfWQ4V1owEtiyzBCe4iJAUCSr0VDZCCze4hgAZDZD"
        )
        self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "1188705457655193")
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def enviar_mensaje_texto(self, numero_destino: str, mensaje: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_destino,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": mensaje
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ALERTA DE COMUNICACIÓN] Error de red con la API de Meta: {str(e)}")
            return {"status": "error", "message": "No se pudo procesar la solicitud externa"}


client = MetaWhatsAppClient()
TOKEN_VERIFICACION = "LLAVE_MAESTRA_ORAPC_2026"


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """
    Handshake del Webhook optimizado para entornos locales de desarrollo.
    Inyecta el header 'ngrok-skip-browser-warning' para eludir el bloqueo de tráfico.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == TOKEN_VERIFICACION:
        print("[SEGURIDAD] Handshake detectado. Enviando desafío exitoso a Meta.")
        
        # BLINDAJE NGROK: Forzamos la respuesta con los headers de evasión requeridos
        response = make_response(str(challenge), 200)
        response.headers["ngrok-skip-browser-warning"] = "true"
        response.headers["Content-Type"] = "text/plain"
        return response
        
    print("[ADVERTENCIA] Intento indebido de verificación de Webhook detectado.")
    return "Fallo de autenticación: Llave Maestra incorrecta", 403


@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    data = request.get_json()
    
    try:
        if "object" in data and data["object"] == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    if "messages" in value:
                        for message in value["messages"]:
                            numero_remitente = message["from"]
                            
                            if message["type"] == "text":
                                texto_recibido = message["text"]["body"]
                                print(f"[PROCESAMIENTO] Mensaje entrante de {numero_remitente}")
                                
                                respuesta_automatica = (
                                    "Saludos. Tu consulta ha sido recibida de forma segura en la "
                                    "plataforma institucional. Un analista procesará tu requerimiento."
                                )
                                
                                client.enviar_mensaje_texto(numero_remitente, respuesta_automatica)
                                
        # Aseguramos responder siempre a Meta con los headers de bypass
        response = make_response(jsonify({"status": "success", "processed": True}), 200)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response
        
    except Exception as e:
        print(f"[CRÍTICO] Error en el procesamiento del Webhook: {str(e)}")
        return jsonify({"status": "error", "message": "Internal processing error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)