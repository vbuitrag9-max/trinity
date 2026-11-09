import os
import json
import re
import requests

from flask import Flask, request, jsonify, send_file


app = Flask(__name__)


# Variables de entorno en Render
MAKE_WEBHOOK = os.environ.get(
    "MAKE_WEBHOOK",
    "https://hook.us2.make.com/jq9blfnv9gjoa4v84810ge3eucpn2az0"
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
)


# ---------------------------------------------------------
# Utilidades
# ---------------------------------------------------------

def extract_gemini_text(data):
    """
    Extrae el texto generado por Gemini.
    """
    try:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        texts = [
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]

        return "".join(texts).strip()

    except Exception:
        return ""


def remove_code_fences(text):
    """
    Elimina bloques ```json ... ``` si Gemini los devuelve.
    """
    text = (text or "").strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def parse_json_response(text):
    """
    Convierte una respuesta de Gemini en un objeto JSON.
    """
    cleaned = remove_code_fences(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Intenta encontrar el primer objeto JSON dentro del texto
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])

        raise ValueError(
            f"Gemini no devolvió JSON válido: {cleaned[:500]}"
        )


# ---------------------------------------------------------
# Gemini
# ---------------------------------------------------------

def call_gemini(user_content, system_instruction):
    """
    Envía una solicitud a Gemini y devuelve texto plano.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Falta la variable de entorno GEMINI_API_KEY en Render."
        )

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": system_instruction
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": user_content
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2
        }
    }

    response = requests.post(
        GEMINI_URL,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        json=payload,
        timeout=60
    )

    if not response.ok:
        raise RuntimeError(
            f"Gemini respondió HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    data = response.json()
    text = extract_gemini_text(data)

    if not text:
        raise RuntimeError(
            f"Gemini respondió sin texto: {json.dumps(data)[:500]}"
        )

    return text


def create_command_from_user_message(user_text):
    """
    Gemini convierte el lenguaje natural en un comando que Make puede ejecutar.
    """
    system_instruction = """
Eres el controlador de integraciones de un asistente personal.

Convierte el mensaje del usuario en JSON válido y devuelve únicamente JSON,
sin markdown, sin explicaciones y sin bloques de código.

Acciones permitidas:

1. calendar.search
   Para consultar eventos existentes.

2. calendar.create
   Para crear un evento nuevo.

3. none
   Cuando no se necesita usar Google Calendar.

El JSON debe tener exactamente esta estructura:

{
  "action": "calendar.search | calendar.create | none",
  "query": "",
  "timeMin": "",
  "timeMax": "",
  "text": "",
  "confirm": false
}

Reglas:

- Usa calendar.search cuando el usuario pregunte por su agenda,
  reuniones, eventos o disponibilidad.
- Usa calendar.create cuando el usuario quiera crear o agendar algo.
- En calendar.create, confirm debe ser true solamente si el usuario
  confirma explícitamente una creación.
- Si el usuario todavía no ha confirmado una acción sensible, usa
  confirm false.
- Las fechas deben estar en formato ISO 8601 cuando sea posible.
- Responde siempre con JSON válido.
"""

    raw = call_gemini(
        user_content=user_text,
        system_instruction=system_instruction
    )

    command = parse_json_response(raw)

    allowed_actions = {
        "calendar.search",
        "calendar.create",
        "none"
    }

    action = command.get("action")

    if action not in allowed_actions:
        raise ValueError(
            f"Acción no permitida generada por Gemini: {action}"
        )

    command.setdefault("query", "")
    command.setdefault("timeMin", "")
    command.setdefault("timeMax", "")
    command.setdefault("text", "")
    command.setdefault("confirm", False)

    return command


def create_final_answer(user_text, command, integration_result=None):
    """
    Gemini recibe el resultado de Make y genera la respuesta final para el chat.
    """
    system_instruction = """
Eres la asistente personal del usuario.

Responde siempre en español, con claridad y brevedad.

Debes usar el resultado de la integración para contestar.
No inventes eventos, fechas ni acciones realizadas.

Si Make devolvió un error, explica que la integración no pudo completarse.
Si no se ejecutó ninguna acción, dilo claramente.
Si se creó un evento, confirma qué se creó.
Si se encontraron eventos, resume los resultados de forma legible.

No muestres JSON crudo al usuario salvo que sea necesario.
"""

    context = {
        "mensaje_usuario": user_text,
        "comando_generado": command,
        "resultado_make": integration_result
    }

    return call_gemini(
        user_content=json.dumps(
            context,
            ensure_ascii=False,
            indent=2
        ),
        system_instruction=system_instruction
    )


# ---------------------------------------------------------
# Make
# ---------------------------------------------------------

def call_make(command):
    """
    Envía a Make el comando estructurado.
    """
    response = requests.post(
        MAKE_WEBHOOK,
        headers={
            "Content-Type": "application/json"
        },
        json={
            "action": command.get("action"),
            "requestId": command.get("requestId", ""),
            "calendar": "dan.esteban7.0@gmail.com",
            "query": command.get("query", ""),
            "timeMin": command.get("timeMin", ""),
            "timeMax": command.get("timeMax", ""),
        

_This response was too long and has been cut off. Ask me to continue, or to cover a smaller part at a time._
