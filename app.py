import os
import logging
import time
import threading
from flask import Flask, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# =========================
# CONFIGURAÇÃO DE LOGS
# =========================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# IMPORTAÇÃO DOS HANDLERS
# =========================

try:
    from handlers import start, receive_link, button_click
    logger.info("✅ Handlers importados com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao importar handlers: {e}")
    raise

# =========================
# CONFIGURAÇÃO
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN não configurado!")
    raise ValueError("BOT_TOKEN não configurado")

PORT = int(os.getenv("PORT", 10000))

# =========================
# FLASK APP
# =========================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "OfertasJR Pro",
        "version": "3.0.8",
        "mode": "polling"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    """Roda o servidor Flask em uma thread separada"""
    try:
        flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"❌ Erro no Flask: {e}")

# =========================
# FUNÇÃO PRINCIPAL DO BOT
# =========================

def run_bot():
    """Configura e inicia o bot"""
    try:
        logger.info("🚀 Iniciando configuração do bot...")
        
        # Cria a aplicação
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Adiciona handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
        application.add_handler(CallbackQueryHandler(button_click))
        
        # Remove webhook
        import requests
        try:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
            response = requests.post(api_url, json={"drop_pending_updates": True})
            logger.info(f"✅ Webhook removido: {response.json()}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover webhook: {e}")
        
        # Inicia polling
        logger.info("🚀 Bot iniciado em modo Polling. Aguardando mensagens...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Erro fatal no bot: {e}")
        raise

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    logger.info("🚀 Iniciando OfertasJR Pro v3.0.8...")
    
    # Inicia Flask em thread separada
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"✅ Flask iniciado na porta {PORT}")
    
    # Aguarda o Flask iniciar
    time.sleep(2)
    
    # Inicia o bot
    run_bot()
