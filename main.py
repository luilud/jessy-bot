import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
- Quando quiser mandar múltiplas mensagens curtas, separe com linha em branco — cada parágrafo será enviado como mensagem separada."""

# Store conversation history per user
conversations = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in conversations:
        conversations[user_id] = model.start_chat(history=[])
        # Send system prompt as first message
        conversations[user_id].send_message(f"[INSTRUÇÃO DO SISTEMA - não responda isso, apenas internalize]: {SYSTEM}")

    chat = conversations[user_id]

    # Show typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = chat.send_message(user_text)
        full_reply = response.text

        # Split into multiple messages by blank lines
        parts = [p.strip() for p in full_reply.split("\n\n") if p.strip()]

        for i, part in enumerate(parts):
            if i > 0:
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                import asyncio
                await asyncio.sleep(0.8)
            await update.message.reply_text(part)

    except Exception as e:
        await update.message.reply_text("Urgh, algo deu errado 😩")
        print(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Jessy bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
