import os
import logging
import json
import asyncio
from flask import Flask, jsonify, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, WEBHOOK_URL
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
# CRIAÇÃO DO BOT (GLOBAL)
# =========================

bot_app = Application.builder().token(BOT_TOKEN).build()
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
bot_app.add_handler(CallbackQueryHandler(button_click))

# =========================
# FLASK APP
# =========================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "OfertasJR Pro",
        "version": "3.0.5",
        "mode": "webhook"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Processa as atualizações do Telegram via webhook"""
    try:
        # Obtém os dados JSON da requisição
        json_data = request.get_json(force=True)
        
        # Cria o objeto Update
        update = Update.de_json(json_data, bot_app.bot)
        
        # Processa a atualização de forma síncrona usando asyncio
        # Cria um novo loop de eventos para esta requisição
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Executa a função assíncrona de forma síncrona
            loop.run_until_complete(bot_app.process_update(update))
        finally:
            loop.close()
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@flask_app.route('/webhook', methods=['GET'])
def webhook_get():
    """Responde a requisições GET (para teste)"""
    return jsonify({"message": "Webhook endpoint. Use POST para enviar atualizações."})

# =========================
# CONFIGURAÇÃO DO WEBHOOK
# =========================

def setup_webhook():
    """Configura o webhook usando a API do Telegram"""
    import requests
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    try:
        # Verifica se o webhook já está configurado
        check_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        check_response = requests.get(check_url)
        
        if check_response.status_code == 200:
            current = check_response.json()
            if current.get('result', {}).get('url') == webhook_url:
                logger.info(f"✅ Webhook já está configurado: {webhook_url}")
                return True
        
        # Configura o webhook
        response = requests.post(api_url, json={
            "url": webhook_url,
            "drop_pending_updates": True,
            "max_connections": 10
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Webhook configurado com sucesso em: {webhook_url}")
                return True
            else:
                logger.error(f"❌ Erro ao configurar webhook: {result}")
                return False
        else:
            logger.error(f"❌ Erro ao configurar webhook: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro na configuração do webhook: {e}")
        return False

# Configura o webhook ao iniciar
setup_webhook()
