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
        # Busca el index.html en la raíz del proyecto
        return send_file("index.html")
    except Exception as e:
        return f"Error crítico cargando la interfaz de Trinity: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    user_data = request.get_json() or {}
    user_message = user_data.get("message", "") or user_data.get("text", "")
    
    payload = {"text": user_message}
    
    try:
        response = requests.post(MAKE_WEBHOOK, json=payload, timeout=25)
        print(f"Respuesta de Make (Status {response.status_code}): {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                # Extrae de forma segura el texto de la respuesta sin importar cómo lo devuelva Make
                reply_text = data.get("reply") or data.get("text") or data.get("result") or str(data)
            except Exception:
                reply_text = response.text.strip()
            
            return jsonify({"reply": reply_text if reply_text else "Núcleo activo, pero sin retorno de datos."})
        else:
            return jsonify({"reply": "Error en el enlace neuronal. Make respondió con código de falla."}), 500
    except Exception as e:
        return jsonify({"reply": f"Error de conexión con el núcleo: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
