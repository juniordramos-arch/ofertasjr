import os
import logging
import asyncio
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
# IMPORTAÇÕES
# =========================

try:
    from handlers import start, receive_link, button_click
    from config import BOT_TOKEN, PORT
    logger.info("✅ Configurações carregadas com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao importar: {e}")
    raise

# =========================
# FLASK APP (HEALTH CHECK)
# =========================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "OfertasJR Pro",
        "version": "3.1.0",
        "mode": "polling"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    """Roda o Flask em uma thread separada"""
    try:
        flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"❌ Erro no Flask: {e}")

# =========================
# FUNÇÃO PRINCIPAL DO BOT
# =========================

async def run_bot():
    """Inicia o bot em modo polling usando asyncio"""
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
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
            response = requests.post(url, json={"drop_pending_updates": True})
            logger.info(f"✅ Webhook removido: {response.json()}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover webhook: {e}")
        
        # Inicia o bot
        logger.info("🚀 Bot iniciado em modo Polling. Aguardando mensagens...")
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
    logger.info("🚀 Iniciando OfertasJR Pro v3.1.0...")
    
    # Inicia Flask em thread separada
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"✅ Flask iniciado na porta {PORT}")
    
    # Aguarda o Flask iniciar
    import time
    time.sleep(2)
    
    # Inicia o bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao rodar bot: {e}")
        raise
