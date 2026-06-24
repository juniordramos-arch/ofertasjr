import os
import requests
import time
from threading import Thread
from urllib.parse import urlparse

from flask import Flask
from bs4 import BeautifulSoup

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# ENV
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANEL_ID = os.getenv("CHANEL_ID")
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")
AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")

# DEBUG (importante no Render)
print("BOT_TOKEN OK:", bool(BOT_TOKEN))
print("CHANEL_ID OK:", bool(CHANEL_ID))

# =========================
# MEMÓRIA
# =========================

ofertas = {}
aguardando_cupom = {}

# =========================
# AWIN MAP
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
# FLASK
# =========================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot JR PRO ONLINE"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# =========================
# FUNÇÕES
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


def gerar_link_afiliado(link: str):
    try:
        if not AWIN_API_TOKEN:
            return link

        advertiser_id = detectar_advertiser(link)
        if not advertiser_id:
            return link

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

        if r.status_code == 200:
            data = r.json()
            return data.get("shortUrl") or link

        return link

    except Exception as e:
        print("AWIN ERROR:", e)
        return link


def extrair_imagem(link):
    try:
        r = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        return None

    except:
        return None


def gerar_titulo(link):
    try:
        slug = urlparse(link).path.split("/")[-1]
        return slug.replace("-", " ").replace("_", " ").title()
    except:
        return "Produto"


# =========================
# TELEGRAM HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot online! Envie um link de produto.")


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    if user_id in aguardando_cupom:
        ofertas[user_id]["cupom"] = text
        del aguardando_cupom[user_id]
        await update.message.reply_text(f"✅ Cupom salvo: {text}")
        return

    link = gerar_link_afiliado(text)
    titulo = gerar_titulo(text)
    imagem = extrair_imagem(text)

    ofertas[user_id] = {
        "link": link,
        "titulo": titulo,
        "imagem": imagem,
        "cupom": ""
    }

    keyboard = [
        [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
        [InlineKeyboardButton("🎟 Cupom", callback_data="cupom")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

    await update.message.reply_text(
        f"🔥 PRÉVIA\n\n🏷 {titulo}\n\n🔗 {link}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    oferta = ofertas.get(user_id)

    if query.data == "publicar":

        if not oferta:
            await query.edit_message_text("❌ Sem oferta.")
            return

        msg = f"🔥 OFERTA\n\n🏷 {oferta['titulo']}\n"

        if oferta.get("cupom"):
            msg += f"\n🎟 {oferta['cupom']}\n"

        msg += f"\n🔗 {oferta['link']}\n"

        if oferta.get("imagem"):
            await context.bot.send_photo(CHANEL_ID, oferta["imagem"], caption=msg)
        else:
            await context.bot.send_message(CHANEL_ID, msg)

        await query.edit_message_text("✅ Publicado!")

    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text("🎟 Envie o cupom:")

    elif query.data == "cancelar":
        await query.edit_message_text("❌ Cancelado.")


# =========================
# BOT ENGINE (ESTÁVEL)
# =========================

def telegram_bot():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 BOT ONLINE")

    app.run_polling()


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    Thread(
        target=run_web,
        daemon=True
    ).start()

    while True:

        try:

            print("🚀 INICIANDO BOT...")

            telegram_bot()

        except Exception as e:

            print("ERRO:", e)

            time.sleep(10)
