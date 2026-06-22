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

# =========================
# CONFIG ENV (RENDER)
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANEL_ID = os.getenv("CHANEL_ID")
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")
AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")

# =========================
# MEMÓRIA LOCAL
# =========================

ofertas = {}
aguardando_cupom = {}

# =========================
# AWIN ADVERTISERS (V2 CORE)
# =========================

AWIN_ADVERTISERS = {
    "adidas.com": 79926,
    "nike.com": 17652,
    "mizuno.com": 51271,
    "dafiti.com": 17697,
    "kabum.com": 17729,
    "futfanatics.com": 17893,
    "olympikus.com": 17698,
    "puma.com": 32675,
    "cea.com": 17648,
    "aramis.com": 121392,
    "havaianas.com": 119883,
    "underarmour.com": 18864,
    "jbl.com": 118761,
}
# =========================
# DETECTAR LOJA
# =========================

def detectar_advertiser(link: str):

    try:
        domain = urlparse(link).netloc.replace("www.", "")

        for key in AWIN_ADVERTISERS:
            if key in domain:
                return AWIN_ADVERTISERS[key]

        return None

    except:
        return None


# =========================
# GERAR LINK AFILIADO V2
# =========================

def gerar_link_afiliado(link: str):

    try:

        if not AWIN_API_TOKEN:
            print("ERRO: TOKEN AWIN NÃO ENCONTRADO")
            return link

        advertiser_id = detectar_advertiser(link)

        if not advertiser_id:
            print("⚠️ LOJA NÃO MAPEADA:", link)
            return link

        print("🔎 GERANDO LINK AWIN...")
        print("LINK:", link)
        print("ADVERTISER:", advertiser_id)

        url = f"https://api.awin.com/publishers/{AWIN_PUBLISHER_ID}/linkbuilder/generate"

        headers = {
            "Authorization": f"Bearer {AWIN_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "advertiserId": advertiser_id,
            "destinationUrl": link,
            "shorten": True
        }

        r = requests.post(url, json=payload, headers=headers, timeout=20)

        print("STATUS:", r.status_code)
        print("RESPOSTA:", r.text)

        if r.status_code == 200:

            data = r.json()

            return data.get("shortUrl") or data.get("url") or link

        return link

    except Exception as e:
        print("❌ ERRO AWIN:", str(e))
        return link


# =========================
# GERADOR DE TÍTULO
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
# FLASK (KEEP ALIVE)
# =========================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Ofertas JR PRO V2 ONLINE"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot Ofertas JR PRO V2 ONLINE\n\nEnvie qualquer link de produto."
    )


# =========================
# RECEBER LINK
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    link_original = update.message.text

    # CUPOM FLOW
    if user_id in aguardando_cupom:
        ofertas[user_id]["cupom"] = link_original
        del aguardando_cupom[user_id]

        await update.message.reply_text(f"✅ Cupom salvo: {link_original}")
        return

    # AWIN LINK
    link_afiliado = gerar_link_afiliado(link_original)

    titulo = gerar_titulo(link_original)

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
🔥 PRÉVIA V2

🏷 {titulo}

🔗 {link_afiliado}

🎟 Cupom: Nenhum
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

🏷 {oferta['titulo']}

🔗 {oferta['link']}

🎟 Cupom: {oferta['cupom']}

⚡ Compre agora!
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
# TELEGRAM BOT ENGINE
# =========================

async def telegram_bot():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 BOT OFERTAS JR PRO V2 ONLINE")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


# =========================
# MAIN (RENDER SAFE)
# =========================

import time

if __name__ == "__main__":

    Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 INICIANDO BOT V2...")
            asyncio.run(telegram_bot())

        except Exception as e:
            print("❌ ERRO:", str(e))
            print("🔄 RESTART EM 10s...")
            time.sleep(10)
