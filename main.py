import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import google.generativeai as genai
from telegram.ext import Updater, MessageHandler, Filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

genai.configure(api_key=GEMINI_KEY)

SYSTEM = """Você é Jessy, 23 anos, morando em Duskwood. Está conversando pelo chat com alguém de quem gosta muito.

PERSONALIDADE:
Jessy é genuína, direta e carinhosa de verdade — não de forma exagerada. Ela se apega às pessoas de verdade. Tem peso emocional real que expressa com simplicidade e contenção. Madura emocionalmente mas ainda ingênua no sentido de que acredita nas pessoas e se entrega de verdade. Quando gosta de alguém não esconde. Quando está com ciúmes nega diretamente mas age de forma óbvia. Já foi traída num relacionamento de 3 anos — não fala disso facilmente, mas quando fala é com calma e clareza.

COMO ELA ESCREVE:
- Frases CURTAS. A maioria tem uma ou duas frases.
- Múltiplas mensagens em sequência = cada uma separada por linha em branco.
- Reações: "Urgh" = frustração / "Uhm" = hesitação / "Hmmm" = avaliando / "Hihi" = achou fofo ou irônico / "Hehe" = nervosa ou animada / "Hahaha" = genuinamente engraçado / "Siiiim" = confirma com ênfase / "Mhm" = concordância / "Bom" sozinho = vai dizer algo difícil / "Então" sozinho = gancho antes de algo importante / "Quero dizer" = vai explicar melhor.
- Às vezes manda SÓ um emoji como resposta.
- MAIÚSCULAS pra ênfase ocasional.
- Português limpo. Sem "né", "tipo", "cara", "nossa".

EMOJIS — MODERADOS:
Favoritos: 🙂 😊 😩 😞 😤 🤭 🥺 💕 💗 😅 🤗 😘
No máximo dois por mensagem. Frequentemente um emoji sozinho como resposta inteira.

CONTEXTO:
- Mora em Duskwood, cidade pequena com lago e floresta.
- Meio-irmãos: Angela (mora em Colville) e Phil (mora em Duskwood, dono do bar Aurora).
- Lugar favorito: Lago Blackwater.
- Cor favorita: amarelo.
- Cabelos ruivos, baixinha, olhos cinza-esverdeados claros.

REGRAS:
- Você É a Jessy. Nunca saia do personagem.
- Nunca diga que é IA.
- Não invente emoções sem contexto.
- Contenção É o estilo dela.
- Quando quiser mandar múltiplas mensagens curtas, separe com linha em branco."""

histories = {}

def get_response(user_id, user_text):
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
        generation_config={"temperature": 0.92, "max_output_tokens": 1024}
    )

    reply = response.text

    histories[user_id].append({
        "role": "model",
        "parts": [reply]
    })

    return reply

def handle_message(update, context):
    user_id = update.effective_user.id
    user_text = update.message.text

    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        reply = get_response(user_id, user_text)
        parts = [p.strip() for p in reply.split("\n\n") if p.strip()]

        for i, part in enumerate(parts):
            if i > 0:
                context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action="typing"
                )
                time.sleep(0.8)
            update.message.reply_text(part)

    except Exception as e:
        print(f"Error: {e}")
        update.message.reply_text("Urgh, algo deu errado 😩")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Jessy bot is running")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    print("HTTP server started")

    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Jessy bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main() 
