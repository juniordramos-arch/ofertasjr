import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot Ofertas JR Online!\n\nEnvie um link para processar."
    )


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text.startswith("http"):
        await update.message.reply_text(
            "🔍 Link recebido!\n\nEm breve vou converter e gerar a prévia."
        )
    else:
        await update.message.reply_text(
            "❌ Envie um link válido."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_link
        )
    )

    print("BOT OFERTAS JR ONLINE")

    app.run_polling()


if __name__ == "__main__":
    main()
