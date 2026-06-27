import os
import logging
import asyncio
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
        "version": "4.1.1",
        "mode": "repost com conversão de links"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# =========================
# FUNÇÃO: RODAR FLASK
# =========================

def run_flask():
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# =========================
# FUNÇÃO: RODAR BOT (ASSÍNCRONA)
# =========================

async def run_bot():
    """Função assíncrona para rodar o bot"""
    try:
        logger.info("🚀 Iniciando configuração do bot...")
        
        # Cria a aplicação
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Adiciona handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("ajuda", ajuda))
        application.add_handler(CommandHandler("cancelar", cancelar))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_click))
        
        # Remove webhook
        import requests
        try:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
            response = requests.post(api_url, json={"drop_pending_updates": True})
            logger.info(f"✅ Webhook removido: {response.json()}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover webhook: {e}")
        
        # Inicia o bot com polling
        logger.info("🚀 Bot iniciado. Aguardando ofertas...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Mantém o bot rodando
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Erro fatal no bot: {e}")
        raise

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    logger.info("🚀 Iniciando OfertasJR Pro v4.1.1 (Repost com conversão)...")
    
    # Inicia Flask em thread separada
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    logger.info(f"✅ Flask iniciado na porta {os.getenv('PORT', 10000)}")
    
    # Inicia o bot (usa asyncio.run para gerenciar o event loop)
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao rodar bot: {e}")
        raise
