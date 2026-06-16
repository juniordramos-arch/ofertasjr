import os
import asyncio
from threading import Thread

from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

ofertas = {}
aguardando_cupom = {}

==========================

FLASK

==========================

web_app = Flask(name)

@web_app.route("/")
def home():
return "Bot Ofertas JR Online ATIVO"

def run_web():
port = int(os.environ.get("PORT", 10000))
web_app.run(
host="0.0.0.0",
port=port
)

==========================

TELEGRAM

==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"🚀 Bot Ofertas JR Online!\n\nEnvie um link."
)

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

if user_id in aguardando_cupom:

    ofertas[user_id]["cupom"] = update.message.text

    del aguardando_cupom[user_id]

    await update.message.reply_text(
        f"✅ Cupom salvo!\n\n🎟 {update.message.text}"
    )

    return

link = update.message.text

ofertas[user_id] = {
    "link": link,
    "cupom": "Nenhum"
}

keyboard = [
    [
        InlineKeyboardButton(
            "✅ Publicar",
            callback_data="publicar"
        )
    ],
    [
        InlineKeyboardButton(
            "🎟 Editar Cupom",
            callback_data="cupom"
        )
    ],
    [
        InlineKeyboardButton(
            "❌ Cancelar",
            callback_data="cancelar"
        )
    ]
]

await update.message.reply_text(
    f"""

🛍 PRÉVIA DA OFERTA

🔗 {link}

🎟 Cupom: Nenhum
""",
reply_markup=InlineKeyboardMarkup(keyboard)
)

async def button_click(
update: Update,
context: ContextTypes.DEFAULT_TYPE
):

query = update.callback_query

await query.answer()

user_id = query.from_user.id

if query.data == "publicar":

    oferta = ofertas.get(user_id)

    if not oferta:

        await query.edit_message_text(
            "❌ Oferta não encontrada."
        )

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

    await query.edit_message_text(
        "✅ Oferta publicada!"
    )

elif query.data == "cupom":

    aguardando_cupom[user_id] = True

    await query.edit_message_text(
        "🎟 Digite o cupom:"
    )

elif query.data == "cancelar":

    await query.edit_message_text(
        "❌ Oferta cancelada."
    )

def start_bot():

print("BOT OFERTAS JR ONLINE")
print("VERSAO_5_RENDER")

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_link
    )
)

app.add_handler(
    CallbackQueryHandler(
        button_click
    )
)

app.run_polling()

if name == "main":

Thread(
    target=run_web,
    daemon=True
).start()

start_bot()
