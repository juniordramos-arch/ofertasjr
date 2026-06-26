import logging
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import gerar_link_afiliado, extrair_imagem, gerar_titulo

logger = logging.getLogger(__name__)

# =========================
# MEMÓRIA DO BOT
# =========================

ofertas = {}
aguardando_cupom = {}

# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "🚀 **OfertasJR Pro Online!**\n\n"
        "Envie um link de produto para criar uma oferta.\n"
        "Suporta: Shopee, Mercado Livre, Amazon, Kabum e mais!\n\n"
        "💡 Dica: Links da AWIN são convertidos automaticamente."
    )

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o link do produto"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Verifica se é cupom
    if user_id in aguardando_cupom:
        ofertas[user_id]["cupom"] = text
        del aguardando_cupom[user_id]
        await update.message.reply_text(f"✅ Cupom salvo: **{text}**")
        return
    
    # Processa o link
    try:
        link_original = text
        link_afiliado = gerar_link_afiliado(text)
        titulo = gerar_titulo(text)
        imagem = extrair_imagem(text)
        
        # Salva no cache
        ofertas[user_id] = {
            "link_original": link_original,
            "link_afiliado": link_afiliado,
            "titulo": titulo,
            "imagem": imagem,
            "cupom": ""
        }
        
        logger.info(f"Novo link de {user_id}: {titulo}")
        
        # Cria teclado
        keyboard = [
            [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
            [InlineKeyboardButton("🎟 Adicionar Cupom", callback_data="cupom")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
        ]
        
        # Prévia
        preview = f"🔥 **PRÉVIA DA OFERTA**\n\n"
        preview += f"🏷 **Título:** {titulo}\n\n"
        
        if imagem:
            preview += f"📸 **Imagem detectada:** Sim\n"
        else:
            preview += f"📸 **Imagem detectada:** Não\n"
        
        preview += f"\n🔗 **Link afiliado:** {link_afiliado[:50]}..."
        
        await update.message.reply_text(
            preview,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Se tiver imagem, mostra
        if imagem:
            await update.message.reply_photo(
                imagem,
                caption="📸 Imagem do produto detectada"
            )
            
    except Exception as e:
        logger.error(f"Erro ao processar link: {e}")
        await update.message.reply_text(
            "❌ Erro ao processar o link. Verifique se é válido."
        )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa cliques nos botões"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    oferta = ofertas.get(user_id)
    
    if query.data == "publicar":
        if not oferta:
            await query.edit_message_text("❌ Nenhuma oferta encontrada.")
            return
        
        try:
            from config import CHANNEL_ID
            from telegram.error import TelegramError
            
            # Monta mensagem
            msg = f"🔥 **OFERTA EXCLUSIVA**\n\n"
            msg += f"🏷 {oferta['titulo']}\n\n"
            
            if oferta.get("cupom"):
                msg += f"🎟 **Cupom:** {oferta['cupom']}\n\n"
            
            msg += f"🔗 {oferta['link_afiliado']}"
            
            # Envia para o canal
            if oferta.get("imagem"):
                await context.bot.send_photo(
                    CHANNEL_ID,
                    oferta["imagem"],
                    caption=msg
                )
            else:
                await context.bot.send_message(
                    CHANNEL_ID,
                    msg
                )
            
            await query.edit_message_text("✅ **Publicado com sucesso!**")
            logger.info(f"Oferta publicada por {user_id}")
            
        except TelegramError as e:
            logger.error(f"Erro ao publicar: {e}")
            await query.edit_message_text(
                f"❌ Erro ao publicar: {str(e)}"
            )
        
        # Limpa cache
        ofertas.pop(user_id, None)
        
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text(
            "🎟 **Envie o código do cupom:**\n\n"
            "Digite apenas o código (ex: OFERTA10)"
        )
        
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        await query.edit_message_text("❌ **Oferta cancelada.**")
