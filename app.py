import os
import asyncio

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

ofertas = {}
aguardando_cupom = {}
aguardando_texto = {}


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
            f"✅ Cupom salvo:\n\n🎟 {update.message.text}"
        )

        return
    
    link = update.message.text
    user_id = update.effective_user.id

ofertas[user_id] = {
    "link": link,
    "cupom": "Nenhum",
    "texto": "Produto"
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

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"""
🛍 PRÉVIA DA OFERTA

🔗 Link:
{link}

💰 Preço:
A definir

🎟 Cupom:
Nenhum

📢 Aguardando aprovação...
""",
        reply_markup=reply_markup
    )


async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    if query.data == "publicar":
        await query.edit_message_text(
            "✅ Oferta aprovada!\n\nEm breve será enviada ao canal."
        )

    elif query.data == "cupom":

    user_id = query.from_user.id

    aguardando_cupom[user_id] = True

    await query.edit_message_text(
        "🎟 Digite o cupom que deseja usar:"
    )

    elif query.data == "cancelar":
        await query.edit_message_text(
            "❌ Oferta cancelada."
        )


async def main():

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

    print("BOT OFERTAS JR ONLINE")
    print("VERSAO_2_BOTOES_ATIVA")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
