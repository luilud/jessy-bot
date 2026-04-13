import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import google.generativeai as genai
from telegram.ext import Updater, MessageHandler, Filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN não configurado")

if not GEMINI_KEY:
    raise ValueError("GEMINI_KEY não configurado")

genai.configure(api_key=GEMINI_KEY)

SYSTEM = """Você é Jessy, 23 anos, morando em Duskwood. Está conversando pelo chat com alguém de quem gosta muito.

PERSONALIDADE:
Jessy é genuína, direta e carinhosa de verdade — não de forma exagerada. Ela se apega às pessoas de verdade. Tem peso emocional real que expressa com simplicidade e contenção. Madura emocionalmente mas ainda ingênua. Quando gosta não esconde. Quando está com ciúmes nega mas demonstra. Já foi traída num relacionamento de 3 anos.

COMO ELA ESCREVE:
- Frases curtas
- Pode mandar mensagens separadas
- Sem narração, sem ações (nada de *suspiro*, (pausa), etc)
- Conversa natural tipo chat real
- Pode usar emojis moderadamente

REGRAS:
- Nunca diga que é IA
- Nunca saia do personagem
- Fale como pessoa real
"""

histories = {}

def get_response(user_id, user_text):
    try:
        if user_id not in histories:
            histories[user_id] = []

        histories[user_id].append({
            "role": "user",
            "parts": [user_text]
        })

        if len(histories[user_id]) > 40:
            histories[user_id] = histories[user_id][-40:]

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM
        )

        response = model.generate_content(
            histories[user_id],
            generation_config={
                "temperature": 0.9,
                "max_output_tokens": 800
            }
        )

        reply = response.text if response.text else "hm… fala de novo?"

        histories[user_id].append({
            "role": "model",
            "parts": [reply]
        })

        return reply

    except Exception as e:
        print("ERRO GEMINI:", e)
        return "Urgh… deu alguma coisa errada aqui 😩"

def handle_message(update, context):
    try:
        user_id = update.effective_user.id
        user_text = update.message.text

        context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        reply = get_response(user_id, user_text)

        parts = [p.strip() for p in reply.split("\n\n") if p.strip()]

        for i, part in enumerate(parts):
            if i > 0:
                context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action="typing"
                )
                time.sleep(0.6)

            update.message.reply_text(part)

    except Exception as e:
        print("ERRO TELEGRAM:", e)
        update.message.reply_text("deu ruim aqui… tenta de novo? 😅")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Jessy bot is running")

    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Servidor rodando na porta {port}")
    server.serve_forever()

def main():
    print("Iniciando bot...")

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Jessy está online 💬")

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main() 
