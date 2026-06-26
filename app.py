import os
import logging
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, PORT, WEBHOOK_URL, CHANNEL_ID
from handlers import start, receive_link, button_click

# =========================
# CONFIGURAÇÃO DE LOGS
# =========================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# FLASK APP
# =========================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "OfertasJR Pro",
        "version": "3.0.0"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para o webhook do Telegram"""
    try:
        update = Update.de_json(flask_app.request.get_json(force=True), bot_app.bot)
        bot_app.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================
# INICIALIZAÇÃO DO BOT
# =========================

def setup_bot():
    """Configura e retorna a aplicação do bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
    application.add_handler(CallbackQueryHandler(button_click))
    
    return application

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    logger.info("🚀 Iniciando OfertasJR Pro...")
    
    # Configura o bot
    bot_app = setup_bot()
    
    # Verifica se está em modo desenvolvimento ou produção
    if os.getenv("ENV") == "development":
        logger.info("📡 Modo DEVELOPMENT - usando Polling")
        bot_app.run_polling()
    else:
        logger.info(f"🌐 Modo PRODUCTION - usando Webhook em {WEBHOOK_URL}")
        
        # Configura webhook
        bot_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            drop_pending_updates=True
        )
        
        # Inicia Flask
        port = int(PORT)
        flask_app.run(host="0.0.0.0", port=port)
