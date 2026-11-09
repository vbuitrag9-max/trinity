import os
import json
import re
import uuid
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify, send_file


app = Flask(__name__)


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


def clean_code_fences(text):
    text = str(text or "").strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return text.strip()


def parse_json_text(text):
    cleaned = clean_code_fences(text)

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])

        raise ValueError(
            "La respuesta no contiene JSON válido: "
            + cleaned[:500]
        )


def extract_gemini_text(data):
    candidates = data.get("candidates", [])

    if not candidates:
        return ""

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])

    output = []

    for part in parts:
        if isinstance(part, dict):
            text = part.get("text", "")

            if text:
                output.append(text)

    return "".join(output).strip()


def call_gemini(user_text, instructions):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Falta la variable GEMINI_API_KEY en Render."
        )

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": instructions
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

    data = response.json()
    text = extract_gemini_text(data)

    if not text:
        raise RuntimeError(
            "Gemini respondió sin texto."
        )

    return text


def create_command(user_text):
    instructions = """
Eres el motor de decisiones de un asistente personal.

Convierte el mensaje del usuario en JSON válido.
Devuelve únicamente JSON.
No uses markdown.

Acciones permitidas:

- calendar.search
- calendar.create
- none

Formato exacto:

{
  "action": "calendar.search | calendar.create | none",
  "query": "",
  "timeMin": "",
  "timeMax": "",
  "text": "",
  "confirm": false
}

Reglas:

- Usa calendar.search para consultar agenda o eventos.
- Usa calendar.create para crear un evento.
- Usa none si no se necesita Google Calendar.
- confirm solo puede ser true si el usuario confirmó explícitamente.
- No inventes información.
- Convierte fechas relativas a ISO 8601 cuando sea posible.

Fecha actual:
""" + datetime.now(timezone.utc).isoformat()

    response_text = call_gemini(
        user_text=user_text,
        instructions=instructions
    )

    command = parse_json_text(response_text)

    if not isinstance(command, dict):
        raise ValueError(
            "Gemini no devolvió un objeto JSON."
        )

    allowed_actions = {
        "calendar.search",
        "calendar.create",
        "none"
    }

    action = command.get("action")

    if action not in allowed_actions:
        raise ValueError(
            "Acción no permitida: "
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


def call_make(command):
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
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=90
    )

    print("MAKE STATUS:", response.status_code)
    print("MAKE RESPONSE:", response.text[:3000])

    if not response.ok:
        raise RuntimeError(
            "Make respondió HTTP "
            + str(response.status_code)
            + ": "
            + response.text[:1000]
        )

    if not response.text.strip():
        raise RuntimeError(
            "Make respondió sin contenido."
        )

    try:
        return response.json()

    except ValueError:
        raise RuntimeError(
            "Make no devolvió JSON válido: "
            + response.text[:1000]
        )


def create_final_answer(user_text, command, make_result):
    context = {
        "mensaje_usuario": user_text,
        "comando": command,
        "resultado_make": make_result
    }

    instructions = """
Eres una asistente personal.

Responde siempre en español.
Sé breve, clara y natural.

Usa el resultado de Make para contestar.
No inventes eventos.
No digas que algo se creó si Make devolvió un error.
Si se encontraron eventos, resume los resultados.
Si se creó un evento, confirma sus datos principales.
No muestres JSON crudo salvo que el usuario lo solicite.
"""

    return call_gemini(
        user_text=json.dumps(
            context,
            ensure_ascii=False,
            indent=2
        ),
        instructions=instructions
    )


@app.get("/")
def home():
    return send_file("static/index.html")


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "personal-assistant"
    })


@app.post("/chat")
def chat():
    body = request.get_json(silent=True) or {}
    user_text = str(body.get("text", "")).strip()

    if not user_text:
        return jsonify({
            "ok": False,
            "error": "Mensaje vacío."
        }), 400

    try:
        command = create_command(user_text)

        if command["action"] == "none":
            answer = call_gemini(
                user_text=user_text,
                instructions="""
Responde al usuario en español como una asistente personal.
No necesitas utilizar ninguna integración.
Sé breve y natural.
"""
            )

            return jsonify({
                "ok": True,
                "reply": answer,
                "command": command
            })

    

_This response was too long and has been cut off. Ask me to continue, or to cover a smaller part at a time._
