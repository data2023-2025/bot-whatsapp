import os
import logging
from flask import Flask, request, jsonify
import requests

# Configuración de logs para producción en Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# CONFIGURACIÓN DE SEGURIDAD Y CREDENCIALES (Vulnerabilidad Cero)
TOKEN_VERIFICACION = "LLAVE_MAESTRA_ORAPC_2026"
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "TU_ACCESS_TOKEN_DE_META")
META_PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID", "TU_PHONE_NUMBER_ID")

# ESTRUCTURA DE DIRECCIONAMIENTO INSTITUCIONAL (ORAPC 2026)
DIRECTORIO_ATENCION = {
    "1": {
        "nombre": "ADMINISTRADOR",
        "telefono": "584265748432",
        "correo": "demonapc.online@gmail.com",
        "finalidad": "Gestión global, reclamos de alto nivel y administración del sistema.",
        "horario": "Lunes a Viernes - 8:00 AM a 4:00 PM"
    },
    "2": {
        "nombre": "ANALISTA 07",
        "telefono": "584265716007",
        "correo": "dem.onapc07@gmail.com",
        "finalidad": "Recepción de proyectos socio-críticos y atención general.",
        "horario": "Lunes a Viernes - 8:00 AM a 2:00 PM"
    },
    "3": {
        "nombre": "ANALISTA 06",
        "telefono": "584265715868",
        "correo": "dem.onapc06@gmail.com",
        "finalidad": "Asesoría legal y tramitación de solicitudes de participación ciudadana.",
        "horario": "Lunes a Viernes - 8:00 AM a 2:00 PM"
    },
    "4": {
        "nombre": "ANALISTA 05",
        "telefono": "584265715918",
        "correo": "dem.onapc05@gmail.com",
        "finalidad": "Procesamiento de datos estadísticos y control de gestión regional.",
        "horario": "Lunes a Viernes - 8:00 AM a 2:00 PM"
    },
    "5": {
        "nombre": "ANALISTA 02",
        "telefono": "584265716098",
        "correo": "dem.onapc02@gmail.com",
        "finalidad": "Soporte técnico del Aula Virtual y atención institucional.",
        "horario": "Lunes a Viernes - 8:00 AM a 4:00 PM"
    },
    "6": {
        "nombre": "ANALISTA 08",
        "telefono": "584265716106",
        "correo": "dem.onapc08@gmail.com",
        "finalidad": "Atención especializada de casos de justicia de paz comunal.",
        "horario": "Lunes a Viernes - 8:00 AM a 2:00 PM"
    },
    "7": {
        "nombre": "ANALISTA 03",
        "telefono": "584265716049",
        "correo": "dem.onapc03@gmail.com",
        "finalidad": "Revisión de informes técnicos y enlaces municipales.",
        "horario": "Lunes a Viernes - 8:00 AM a 2:00 PM"
    }
}

def enviar_mensaje_whatsapp(destinatario, texto):
    """
    Se conecta con la API de Meta para enviar respuestas en formato de texto plano.
    """
    url = f"https://graph.facebook.com/v25.0/{META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": destinatario,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": texto
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logging.info(f"Respuesta de Meta enviada a {destinatario}: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error crítico al enviar mensaje vía Meta API: {e}")
        return None

def generar_menu_principal():
    """
    Construye de forma dinámica el menú institucional de opciones.
    """
    menu = "🏛️ *OFICINA DE REGISTRO Y ATENCIÓN DE PARTICIPACIÓN CIUDADANA (ORAPC)* 🏛️\n\n"
    menu += "Bienvenido al Sistema Automatizado de Enrutamiento de Casos Judiciales e Institucionales.\n\n"
    menu += "Por favor, seleccione el número del analista o departamento que requiere consultar:\n\n"
    
    for clave, datos in DIRECTORIO_ATENCION.items():
        menu += f"*{clave}* - {datos['nombre']} ({datos['correo']})\n"
        
    menu += "\n✍️ Responda únicamente con el *NÚMERO* de la opción deseada para ver el horario y los detalles de contacto."
    return menu

def procesar_respuesta_usuario(texto_usuario):
    """
    Evalúa la entrada del ciudadano, sanitiza el texto y extrae la información.
    """
    opcion = str(texto_usuario).strip()
    if opcion in DIRECTORIO_ATENCION:
        datos = DIRECTORIO_ATENCION[opcion]
        respuesta = f"📞 *DETALLES DE CONTACTO - {datos['nombre']}*\n\n"
        respuesta += f"📌 *Finalidad de la línea:* {datos['finalidad']}\n"
        respuesta += f"⏰ *Horario de Atención:* {datos['horario']}\n"
        respuesta += f"📲 *Enlace Directo WhatsApp:* wa.me/{datos['telefono']}\n"
        respuesta += f"✉️ *Correo Electrónico:* {datos['correo']}\n\n"
        respuesta += "--- \nSi desea consultar otro departamento, envíe la palabra *MENU*."
        return respuesta
    return None

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    """
    Punto de enlace requerido por Meta para validar la autenticidad del servidor (Handshake).
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == TOKEN_VERIFICACION:
            logging.info("Webhook verificado exitosamente con Llave Maestra.")
            return challenge, 200
        else:
            logging.warning("Intento de conexión no autorizado con token inválido.")
            return "Token de verificación inválido", 403
    return "Faltan parámetros de configuración", 400

@app.route('/webhook', methods=['POST'])
def recibir_eventos():
    """
    Procesa las notificaciones en tiempo real enviadas por Meta al recibir mensajes.
    """
    datos_entrantes = request.get_json()
    logging.info(f"Payload recibido de Meta: {datos_entrantes}")

    try:
        if datos_entrantes and "object" in datos_entrantes:
            for entry in datos_entrantes.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value and value["messages"]:
                        objeto_mensaje = value["messages"][0]
                        telefono_remitente = objeto_mensaje["from"]
                        
                        if objeto_mensaje.get("type") == "text":
                            # SANITIZACIÓN ROBUSTA: Eliminamos comillas accidentales
                            texto_usuario = str(objeto_mensaje["text"]["body"]).strip().replace("'", "").replace('"', '')
                            logging.info(f"Mensaje limpio de {telefono_remitente}: {texto_usuario}")

                            # Control estricto de comandos globales de regreso
                            if texto_usuario.upper() in ["MENU", "MÉNU", "HOLA", "INICIO"]:
                                menu_completo = generar_menu_principal()
                                enviar_mensaje_whatsapp(telefono_remitente, menu_completo)
                            else:
                                respuesta_personalizada = procesar_respuesta_usuario(texto_usuario)
                                if respuesta_personalizada:
                                    enviar_mensaje_whatsapp(telefono_remitente, respuesta_personalizada)
                                else:
                                    menu_completo = generar_menu_principal()
                                    enviar_mensaje_whatsapp(telefono_remitente, menu_completo)
                                    
            return jsonify({"status": "success"}), 200
    except Exception as error_interno:
        logging.error(f"Error en el procesamiento del flujo de eventos: {error_interno}")
        return jsonify({"status": "error", "message": str(error_interno)}), 500

    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
