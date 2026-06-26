import os
import logging
from flask import Flask, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, PORT
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
# FLASK APP (para health check)
# =========================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "OfertasJR Pro",
        "version": "3.0.3",
        "mode": "polling"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    """Roda o servidor Flask em uma thread separada"""
    port = int(PORT)
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    import threading
    import time
    
    logger.info("🚀 Iniciando OfertasJR Pro v3.0.3 (Polling)...")
    
    # Inicia o Flask em uma thread separada
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Aguarda o Flask iniciar
    time.sleep(2)
    logger.info("✅ Servidor Flask rodando na porta " + PORT)
    
    # Configura o bot com Polling
    logger.info("📡 Configurando bot em modo Polling...")
    
    # Cria a aplicação do bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
    bot_app.add_handler(CallbackQueryHandler(button_click))
    
    # Remove qualquer webhook existente
    import requests
    try:
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.post(api_url, json={"drop_pending_updates": True})
        logger.info(f"✅ Webhook removido: {response.json()}")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao remover webhook: {e}")
    
    # Inicia o bot em modo Polling
    logger.info("🚀 Bot iniciado em modo Polling. Aguardando mensagens...")
    bot_app.run_polling()
