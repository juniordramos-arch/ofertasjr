import os
import asyncio
import requests
from threading import Thread

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

# 🔑 AWIN CONFIG (NOVO)
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")

ofertas = {}
aguardando_cupom = {}

# =========================
# FUNÇÃO AWIN (NOVA)
# =========================

def gerar_link_afiliado(link: str):

    """
    Tenta converter link usando API da Awin.
    Se falhar, retorna o link original.
    """

    try:
        if not AWIN_API_TOKEN:
            return link

        url = "https://api.awin.com/deeplink"

        headers = {
            "Authorization": f"Bearer {AWIN_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "destination": link
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("url", link)

        return link

    except:
        return link


# =========================
# SERVIDOR WEB
# =========================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Ofertas JR Online Online"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot Ofertas JR Online!\n\nEnvie um link."
    )


# =========================
# RECEBER LINK
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    link = update.message.text

    # 🔥 NOVO: converter link via Awin
    link_afiliado = gerar_link_afiliado(link)

    if user_id in aguardando_cupom:

        ofertas[user_id]["cupom"] = update.message.text

        del aguardando_cupom[user_id]

        await update.message.reply_text(
            f"✅ Cupom salvo!\n\n🎟 {update.message.text}"
        )

        return

    ofertas[user_id] = {
        "link": link_afiliado,
        "cupom": "Nenhum",
        "texto": "Produto"
    }

    keyboard = [
        [
            InlineKeyboardButton("✅ Publicar", callback_data="publicar")
        ],
        [
            InlineKeyboardButton("🎟 Editar Cupom", callback_data="cupom")
        ],
        [
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"""
🛍 PRÉVIA DA OFERTA

🔗 Link:
{link_afiliado}

💰 Preço:
A definir

🎟 Cupom:
Nenhum

📢 Aguardando aprovação...
""",
        reply_markup=reply_markup
    )


# =========================
# BOTÕES
# =========================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "publicar":

        user_id = query.from_user.id
        oferta = ofertas.get(user_id)

        if not oferta:
            await query.edit_message_text("❌ Oferta não encontrada.")
            return

        mensagem = f"""
🔥 OFERTA APROVADA

🔗 {oferta['link']}

🎟 Cupom: {oferta['cupom']}
"""

        await context.bot.send_message(
            chat_id=CHANEL_ID,
            text=mensagem
        )

        await query.edit_message_text("✅ Oferta publicada no canal!")

    elif query.data == "cupom":

        user_id = query.from_user.id
        aguardando_cupom[user_id] = True

        await query.edit_message_text(
            "🎟 Digite o cupom que deseja usar:"
        )

    elif query.data == "cancelar":

        await query.edit_message_text("❌ Oferta cancelada.")


# =========================
# BOT
# =========================

async def telegram_bot():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
    app.add_handler(CallbackQueryHandler(button_click))

    print("BOT OFERTAS JR ONLINE")
    print("VERSAO_RENDER + AWIN")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":

    Thread(target=run_web, daemon=True).start()
    asyncio.run(telegram_bot())
