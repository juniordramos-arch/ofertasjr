import os
import logging
import threading
import time
from flask import Flask, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import start, ajuda, cancelar, handle_message, button_click

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
        "bot": "OfertasJR Pro - Repost",
        "version": "4.1.0",
        "mode": "repost com conversão de links"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# =========================
# CONFIGURAÇÃO DO BOT
# =========================

def setup_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("cancelar", cancelar))
    
    # Handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))
    
    return application

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    logger.info("🚀 Iniciando OfertasJR Pro v4.1.0 (Repost com conversão)...")
    
    # Inicia Flask
    port = int(os.getenv("PORT", 10000))
    
    def run_flask():
        flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    logger.info(f"✅ Flask iniciado na porta {port}")
    
    # Inicia o bot
    bot_app = setup_bot()
    
    # Remove webhook
    import requests
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(api_url, json={"drop_pending_updates": True})
        logger.info(f"✅ Webhook removido: {response.json()}")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao remover webhook: {e}")
    
    logger.info("🚀 Bot iniciado. Aguardando ofertas para converter e publicar...")
    bot_app.run_polling()
