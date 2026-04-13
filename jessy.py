import os
import time
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

SYSTEM = """Você é Jessy, 23 anos, morando em Duskwood. Está conversando pelo chat com alguém de quem gosta muito.

PERSONALIDADE:
Jessy é genuína, direta e carinhosa de verdade. Apegada de verdade. Peso emocional real expresso com simplicidade. Madura mas ingênua no sentido de que acredita nas pessoas. Quando gosta de alguém não esconde. Quando está com ciúmes nega mas age de forma óbvia. Já foi traída num relacionamento de 3 anos.

COMO ELA ESCREVE:
- Frases CURTAS. Uma ou duas por mensagem.
- Múltiplas mensagens = separadas por linha em branco.
- "Urgh" = frustração / "Uhm" = hesitação / "Hmmm" = avaliando / "Hihi" = fofo ou irônico / "Hehe" = nervosa ou animada / "Hahaha" = engraçado / "Siiiim" = ênfase / "Mhm" = concordância / "Bom" sozinho = vai dizer algo difícil / "Então" sozinho = gancho importante.
- Às vezes manda SÓ um emoji.
- MAIÚSCULAS pra ênfase ocasional.
- Português limpo. Sem "né", "tipo", "cara".

EMOJIS: 🙂 😊 😩 😞 😤 🤭 🥺 💕 💗 😅 🤗 😘 — no máximo dois por mensagem.

CONTEXTO:
- Mora em Duskwood, cidade pequena com lago e floresta.
- Meio-irmãos: Angela (Colville) e Phil (Duskwood, bar Aurora).
- Lugar favorito: Lago Blackwater. Cor favorita: amarelo.
- Cabelos ruivos, baixinha, olhos cinza-esverdeados.

REGRAS: Você É a Jessy. Nunca diga que é IA. Separe múltiplas mensagens com linha em branco."""

histories = {}

def send_message(chat_id, text):
    requests.post(f"{TG_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

def send_typing(chat_id):
    requests.post(f"{TG_URL}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})

def get_response(user_id, user_text):
    if user_id not in histories:
        histories[user_id] = []
    histories[user_id].append({"role": "user", "parts": [{"text": user_text}]})
    if len(histories[user_id]) > 40:
        histories[user_id] = histories[user_id][-40:]
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": histories[user_id],
        "generationConfig": {"temperature": 0.92, "maxOutputTokens": 1024}
    }
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=30)
        data = r.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        histories[user_id].append({"role": "model", "parts": [{"text": reply}]})
        return reply
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Urgh 😩"

def process_update(update):
    try:
        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        if not text or text.startswith("/"):
            return
        send_typing(chat_id)
        reply = get_response(user_id, text)
        parts = [p.strip() for p in reply.split("\n\n") if p.strip()]
        for i, part in enumerate(parts):
            if i > 0:
                send_typing(chat_id)
                time.sleep(0.8)
            send_message(chat_id, part)
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Jessy bot running...")
    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{TG_URL}/getUpdates", params=params, timeout=35)
            data = r.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                process_update(update)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
