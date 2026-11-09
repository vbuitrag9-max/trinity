import os
import json
import re
import uuid
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify, send_file


app = Flask(__name__)


# =========================================================
# CONFIGURACIÓN
# =========================================================

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
    "https://generativelanguage.googleapis.com/"
    + "v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)

CALENDAR_ID = os.environ.get(
    "GOOGLE_CALENDAR_ID",
    "dan.esteban7.0@gmail.com"
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def get_current_datetime():
    """
    Devuelve la fecha y hora actual en formato ISO.
    """
    return datetime.now(timezone.utc).isoformat()


def remove_code_fences(text):
    """
    Elimina bloques de código como:
    ```json
    {...}
    ```
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


def parse_json_text(text):
    """
    Convierte la respuesta de Gemini en un objeto JSON.
    """
    cleaned_text = remove_code_fences(text)

    try:
        return json.loads(cleaned_text)

    except json.JSONDecodeError:
        start = cleaned_text.find("{")
        end = cleaned_text.rfind("}")

        if start >= 0 and end > start:
            possible_json = cleaned_text[start:end + 1]
            return json.loads(possible_json)

        raise ValueError(
            "Gemini no devolvió un JSON válido: "
            + cleaned_text[:1000]
        )


# =========================================================
# GEMINI
# =========================================================

def extract_gemini_text(response_data):
    """
    Extrae el texto de la respuesta de Gemini.
    """
    if not isinstance(response_data, dict):
        return ""

    candidates = response_data.get("candidates", [])

    if not candidates:
        return ""

    first_candidate = candidates[0] or {}
    content = first_candidate.get("content", {})
    parts = content.get("parts", [])

    result = []

    for part in parts:
        if isinstance(part, dict):
            text = part.get("text")

            if text:
                result.append(text)

    return "".join(result).strip()


def call_gemini(user_text, system_instruction):
    """
    Envía una solicitud a Gemini y devuelve el texto generado.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Falta configurar GEMINI_API_KEY en Render."
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
                        "text": user_text
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

    print("GEMINI STATUS:", response.status_code)
    print("GEMINI RESPONSE:", response.text[:2000])

    if not response.ok:
        raise RuntimeError(
            "Gemini respondió HTTP "
            + str(response.status_code)
            + ": "
            + response.text[:1000]
        )

    try:
        response_data = response.json()

    except ValueError:
        raise RuntimeError(
            "Gemini no devolvió una respuesta JSON válida."
        )

    generated_text = extract_gemini_text(response_data)

    if not generated_text:
        raise RuntimeError(
            "Gemini respondió correctamente, pero no devolvió texto."
        )

    return generated_text


# =========================================================
# CREAR COMANDO PARA MAKE
# =========================================================

def create_make_command(user_text):
    """
    Gemini transforma el mensaje del usuario en un comando
    estructurado para Make.
    """

    system_instruction = """
Eres el motor de decisiones de un asistente personal.

Tu tarea es transformar el mensaje del usuario en un comando JSON
para una integración externa.

Devuelve únicamente JSON válido.
No uses markdown.
No uses bloques de código.
No incluyas explicaciones.

Las acciones permitidas son:

- calendar.search
- calendar.create
- none

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

1. Usa calendar.search si el usuario pregunta por eventos,
   reuniones, agenda, compromisos o disponibilidad.

2. Usa calendar.create si el usuario quiere crear o agendar
   un evento.

3. Usa none si el mensaje no necesita Google Calendar.

4. Para calendar.search:
   - query contiene el texto que se quiere buscar.
   - timeMin contiene el inicio del rango.
   - timeMax contiene el final del rango.

5. Para calendar.create:
   - text debe contener una descripción completa del evento.
   - confirm solo puede ser true si el usuario confirmó
     explícitamente la creación.

6. Si el usuario pidió crear un evento pero todavía no confirmó,
   usa calendar.create con confirm false.

7. Convierte fechas como hoy, mañana o el viernes a fechas
   ISO 8601 cuando sea posible.

8. Nunca inventes información.

9. Responde siempre con JSON válido.

Fecha y hora actual:
""" + get_current_datetime()

    raw_response = call_gemini(
        user_text=user_text,
        system_instruction=system_instruction
    )

    command = parse_json_text(raw_response)

    if not isinstance(command, dict):
        raise ValueError(
            "El comando generado por Gemini no es un objeto JSON."
        )

    allowed_actions = {
        "calendar.search",
        "calendar.create",
        "none"
    }

    action = command.get("action")

    if action not in allowed_actions:
        raise ValueError(
            "Gemini devolvió una acción no permitida: "
            + str(action)
        )

    command.setdefault("query", "")
    command.setdefault("timeMin", "")
    command.setdefault("timeMax", "")
    command.setdefault("text", "")
    command.setdefault("confirm", False)

    command["requestId"] = str(uuid.uuid4())
    command["calendar"] = CALENDAR_ID

    return command


# =========================================================
# MAKE
# =========================================================

def call_make(command):
    """
    Envía a Make los campos esperados por el webhook.
    """

    payload = {
        "action": command.get("action"),
        "requestId": command.get("requestId"),
        "calendar": command.get("calendar"),
        "query": command.get("query", ""),
        "timeMin": command.get("timeMin", ""),
        "timeMax": command.get("timeMax", ""),
        "text": command.get("text", ""),
        "confirm": bool(command.get("confirm", False))
    }

    print("MAKE PAYLOAD:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    response = requests.post(
        MAKE_WEBHOOK,
        headers={
   

_This response was too long and has been cut off. Ask me to continue, or to cover a smaller part at a time._
