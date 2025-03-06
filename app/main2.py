from fastapi import FastAPI, Request
import httpx
import json
import subprocess
import os
from dotenv import load_dotenv  # Cargar .env
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TOKEN_BOT")
GEMINI_TOKEN = os.getenv("GEMINI_API")

# Configurar Gemini API
genai.configure(api_key=GEMINI_TOKEN)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

app = FastAPI()
messages = []

# Obtener la URL pública de ngrok dinámicamente
def get_ngrok_url():
    try:
        result = subprocess.run(["curl", "-s", "http://127.0.0.1:4040/api/tunnels"], capture_output=True, text=True)
        tunnels = json.loads(result.stdout)
        if "tunnels" in tunnels and tunnels["tunnels"]:
            return tunnels["tunnels"][0]["public_url"]
        else:
            print("No se encontraron túneles activos en ngrok.")
            return None
    except Exception as e:
        print("Error obteniendo la URL de ngrok:", e)
        return None

@app.on_event("startup")
async def set_webhook():
    public_url = get_ngrok_url()

    if not public_url:
        print("No se pudo obtener la URL de ngrok. Asegúrate de que ngrok está corriendo.")
        return

    webhook_url = f"{public_url}/webhook/"
    print(f"Configurando webhook en: {webhook_url}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            data={"url": webhook_url}
        )
        print("Webhook Response:", response.json())

async def send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload)
        return response.json()

async def get_gemini_response(user_message: str) -> str:
    """Obtiene una respuesta de Gemini API"""
    try:
        response = model.generate_content(user_message)
        return response.text if response.text else "No entendí tu mensaje."
    except Exception as e:
        print("Error con Gemini:", e)
        return "Ocurrió un error al procesar tu mensaje."

@app.post("/webhook/")
async def receive_telegram_message(request: Request):
    data = await request.json()
    print("Mensaje recibido:", json.dumps(data, indent=2))

    # Extraer el mensaje del usuario
    user_message = data.get("message", {}).get("text", "")
    chat_id = data.get("message", {}).get("chat", {}).get("id", "")

    if user_message and chat_id:
        messages.append({"type": "user", "message": user_message})

        # Obtener respuesta de Gemini
        bot_message = await get_gemini_response(user_message)

        # Enviar la respuesta al usuario
        await send_message(chat_id, bot_message)

        # Almacenar el mensaje del bot
        messages.append({"type": "bot", "message": bot_message})

    return {"status": "ok"}

@app.get("/webhook/")
async def get_messages():
    """Muestra los mensajes almacenados en JSON"""
    return {"messages": messages}

