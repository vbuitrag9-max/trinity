import os
import json
import requests
from flask import Flask, request, jsonify, send_file

# URL del webhook de Make.com (puedes sobreescribirla con la variable de entorno MAKE_WEBHOOK)
MAKE_WEBHOOK = os.environ.get(
    "MAKE_WEBHOOK",
    "https://hook.us2.make.com/mn8gnb5ov1ehe1iwygyx1jphavkfxlb9"
)

app = Flask(__name__)


@app.get("/")
def home():
    return send_file("static/index.html")


def parse_reply(raw):
    """Detecta el formato de la respuesta de Gemini/Make y devuelve texto plano."""
    text = (raw or "").strip()
    try:
        data = json.loads(text)
    except Exception:
        return text  # era texto plano

    if isinstance(data, str):
        return data
    # Formato nativo de respuesta de Gemini API
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass
    # Formato de contenido Gemini (por si Make responde con el mismo shape de entrada)
    if isinstance(data, dict) and isinstance(data.get("parts"), list):
        return "".join(p.get("text", "") for p in data["parts"] if isinstance(p, dict))
    # Claves comunes
    for k in ("reply", "text", "answer", "output", "result", "content", "message"):
        if k in data:
            return str(data[k])
    return text


@app.post("/chat")
def chat():
    user_text = (request.json or {}).get("text", "").strip()
    if not user_text:
        return jsonify({"ok": False, "error": "Mensaje vacío"}), 400

    # Mismo formato que tu escenario de Make ya espera
    payload = {"role": "user", "parts": [{"text": user_text}]}
    try:
        r = requests.post(MAKE_WEBHOOK, json=payload, timeout=90)
        reply = parse_reply(r.text)
        if not reply:
            return jsonify({"ok": False, "error": "Respuesta vacía de Make/Gemini", "raw": r.text[:500]}), 502
        return jsonify({"ok": True, "reply": reply})
    except requests.Timeout:
        return jsonify({"ok": False, "error": "Gemini tardó demasiado, intenta de nuevo"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
