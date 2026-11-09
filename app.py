import os
import json
import requests
from flask import Flask, request, jsonify, send_file

# URL del webhook de Make.com (actualizada con su nuevo enlace)
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
    if "candidates" in data:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            texts = [p.get("text", "") for p in parts if "text" in p]
            if texts:
                return "".join(texts).strip()
        except Exception:
            pass

    for k in FALLBACK_KEYS:
        if k in data and data[k]:
            val = data[k]
            if isinstance(val, (str, int, float)):
                return str(val).strip()
            res = extract(val)
            if res:
                return res

    for k, v in data.items():
        if isinstance(v, (dict, list)):
            res = extract(v)
            if res:
                return res

    return json.dumps(data, ensure_ascii=False)

def parse_reply(resp):
    try:
        data = resp.json()
    except Exception:
        return resp.text.strip()
    return extract(data)

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_data = request.get_json() or {}
    user_message = user_data.get("message", "") or user_data.get("text", "")
    
    payload = {"text": user_message}
    
    try:
        response = requests.post(MAKE_WEBHOOK, json=payload, timeout=25)
        if response.status_code == 200:
            bot_reply = parse_reply(response)
            return jsonify({"reply": bot_reply})
        else:
            return jsonify({"reply": "Error en el enlace cuántico neuronal. Make no respondió correctamente."}), 500
    except Exception as e:
        return jsonify({"reply": f"Error de conexión con el núcleo: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
