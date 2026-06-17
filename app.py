import os
import asyncio
import requests
from threading import Thread
from urllib.parse import urlparse

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANEL_ID = os.getenv("CHANEL_ID")
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")

ofertas = {}
aguardando_cupom = {}


# =========================
# AWIN LINK CONVERTER
# =========================

def gerar_link_afiliado(link: str):

    try:

        if not AWIN_API_TOKEN:
            print("ERRO: TOKEN AWIN NÃO ENCONTRADO")
            return link

        print("TESTANDO AWIN...")
        print("LINK:", link)

        url = f"https://api.awin.com/publishers/1492066/linkbuilder/generate"

        headers = {
            "Authorization": f"Bearer {AWIN_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "advertiserId": 79926,
            "destinationUrl": link,
            "shorten": True
        }

        r = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=20
        )

        print("STATUS:", r.status_code)
        print("RESPOSTA:", r.text)

        if r.status_code == 200:

            data = r.json()

            if "shortUrl" in data:
                return data["shortUrl"]

            if "url" in data:
                return data["url"]

        return link

    except Exception as e:

        print("ERRO AWIN:", str(e))
        return link
        
# =========================
# GERADOR DE TÍTULO (PRO)
# =========================

def gerar_titulo(link: str):

    try:
        path = urlparse(link).path
        slug = path.split("/")[-1]

        titulo = slug.replace("-", " ").replace("_", " ")

        return titulo.title() if titulo else "Produto em Oferta"

    except:
        return "Produto em Oferta"


# =========================
# FLASK
# =========================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Ofertas JR PRO ONLINE"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot Ofertas JR PRO!\n\nEnvie um link."
    )


# =========================
# RECEBER LINK
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    link_original = update.message.text

    # 🔥 AWIN
    link_afiliado = gerar_link_afiliado(link_original)

    titulo = gerar_titulo(link_original)

    if user_id in aguardando_cupom:

        ofertas[user_id]["cupom"] = update.message.text
        del aguardando_cupom[user_id]

        await update.message.reply_text(
            f"✅ Cupom salvo!\n🎟 {update.message.text}"
        )
        return

    ofertas[user_id] = {
        "link": link_afiliado,
        "titulo": titulo,
        "cupom": "Nenhum"
    }

    keyboard = [
        [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
        [InlineKeyboardButton("🎟 Editar Cupom", callback_data="cupom")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

    await update.message.reply_text(
        f"""
🔥 PRÉVIA PRO

🏷 {titulo}

🔗 {link_afiliado}

🎟 Cupom: Nenhum

⚡ Pronto para publicar
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BOTÕES
# =========================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    oferta = ofertas.get(user_id)

    if query.data == "publicar":

        if not oferta:
            await query.edit_message_text("❌ Oferta não encontrada.")
            return

        mensagem = f"""
🔥 OFERTA IMPERDÍVEL

🏷 Produto: {oferta['titulo']}

🔗 {oferta['link']}

🎟 Cupom: {oferta['cupom']}

⚡ Garanta agora!
"""

        await context.bot.send_message(
            chat_id=CHANEL_ID,
            text=mensagem
        )

        await query.edit_message_text("✅ Publicado com sucesso!")

    elif query.data == "cupom":

        aguardando_cupom[user_id] = True
        await query.edit_message_text("🎟 Envie o cupom agora:")

    elif query.data == "cancelar":

        await query.edit_message_text("❌ Cancelado.")


# =========================
# BOT
# =========================

async def telegram_bot():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 BOT OFERTAS JR PRO ONLINE")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


import time

if __name__ == "__main__":

    Thread(target=run_web, daemon=True).start()

    while True:

        try:

            print("🚀 INICIANDO BOT...")

            asyncio.run(telegram_bot())

        except Exception as e:

            print("❌ ERRO:", str(e))
            print("🔄 REINICIANDO EM 10 SEGUNDOS...")

            time.sleep(10)
