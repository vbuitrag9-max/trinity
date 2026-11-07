import os
import json
import requests
from flask import Flask, request, jsonify, send_file

# URL del webhook de Make.com (puedes sobreescribirla con la variable de entorno MAKE_WEBHOOK)
MAKE_WEBHOOK = os.environ.get(
    "MAKE_WEBHOOK",
    "https://hook.us2.make.com/jq9blfnv9gjoa4v84810ge3eucpn2az0"
)

app = Flask(__name__)

FALLBACK_KEYS = ("reply", "text", "answer", "output", "result", "content", "message", "response")


def extract(data):
    """Extrae texto plano de cualquier formato conocido de respuesta."""
    if isinstance(data, str):
        return data.strip()
    if isinstance(data, list) and data:
        return extract(data[0])
    if not isinstance(data, dict):
        return str(data)
    # Formato nativo de respuesta de Gemini API
    try:
        return extract(data["candidates"][0]["content"]["parts"][0]["text"])
    except Exception:
        pass
    # Formato de contenido Gemini (parts directo)
    if isinstance(data.get("parts"), list):
        joined = "".join(p.get("text", "") for p in data["parts"] if isinstance(p, dict))
        if joined.strip():
            return joined.strip()
    # Claves comunes, incluida "response" (formato del webhook del usuario)
    for k in FALLBACK_KEYS:
        if k in data and data[k] is not None:
            return extract(data[k])
    return json.dumps(data, ensure_ascii=False)


def parse_reply(raw):
    text = (raw or "").strip()
    try:
        data = json.loads(text)
    except Exception:
        return text  # era texto plano
    return extract(data)


@app.get("/")
def home():
    return send_file("static/index.html")


@app.post("/chat")
def chat():
    user_text = (request.json or {}).get("text", "").strip()
    if not user_text:
        return jsonify({"ok": False, "error": "Mensaje vacío"}), 400

    # Enviamos el mensaje en varios formatos para que el trigger de Make
    # encuentre el campo que su escenario espera (message, text o Gemini parts)
    payload = {
        "message": user_text,
        "text": user_text,
        "role": "user",
        "parts": [{"text": user_text}],
    }
    try:
        r = requests.post(MAKE_WEBHOOK, json=payload, timeout=90)
        reply = parse_reply(r.text)
        if not reply:
            return jsonify({
                "ok": False,
                "error": "Make respondió pero sin texto. Revisa el mapeo de la respuesta en el webhook.",
                "raw": r.text[:500],
            }), 502
        return jsonify({"ok": True, "reply": reply})
    except requests.Timeout:
        return jsonify({"ok": False, "error": "Gemini tardó demasiado, intenta de nuevo"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
