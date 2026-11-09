import os
import json
import requests
from flask import Flask, request, jsonify, send_file

MAKE_WEBHOOK = os.environ.get(
    "MAKE_WEBHOOK",
    "https://hook.us2.make.com/mn8gnb5ov1ehe1iwygyx1jphavkfxlb9"
)

app = Flask(__name__)

@app.route("/")
def index():
    try:
        # Ruta absoluta para asegurar que Render encuentre el HTML siempre
        file_path = os.path.join(app.root_path, "index.html")
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return "Error: El archivo index.html no se encuentra en el servidor.", 404
    except Exception as e:
        return f"Error crítico: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_data = request.get_json() or {}
        user_message = user_data.get("message", "") or user_data.get("text", "")
        
        if not user_message:
            return jsonify({"reply": "Comando vacío recibido en el núcleo."})

        payload = {"text": user_message}
        response = requests.post(MAKE_WEBHOOK, json=payload, timeout=30)
        
        if response.status_code == 200:
            text_resp = response.text.strip()
            try:
                data = response.json()
                reply_text = data.get("reply") or data.get("text") or data.get("result") or str(data)
            except Exception:
                reply_text = text_resp
            return jsonify({"reply": reply_text if reply_text else "Núcleo activo, sin retorno de datos."})
        else:
            return jsonify({"reply": f"Error en enlace neuronal (Código Make: {response.status_code})."})
    except Exception as e:
        return jsonify({"reply": f"Falla en el subproceso: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
