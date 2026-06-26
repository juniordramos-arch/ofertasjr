import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import gerar_link_afiliado, extrair_imagem, gerar_titulo, baixar_imagem_para_telegram

logger = logging.getLogger(__name__)

# =========================
# MEMÓRIA
# =========================

ofertas = {}
aguardando_cupom = {}

# =========================
# IMAGEM PADRÃO
# =========================

IMAGEM_PADRAO = "https://via.placeholder.com/800x600/1a1a2e/FFFFFF?text=Oferta+JR+Pro"

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
    
    try:
        link_afiliado = gerar_link_afiliado(text)
        titulo = gerar_titulo(text)
        imagem = extrair_imagem(text)
        
        # Se não encontrou imagem, usa a padrão
        if not imagem:
            imagem = IMAGEM_PADRAO
            logger.info("🖼️ Usando imagem padrão")
        
        # Remove extensões e caracteres especiais do título
        titulo_limpo = titulo.replace(".Html", "").replace(".html", "").strip()
        
        ofertas[user_id] = {
            "link": link_afiliado,
            "titulo": titulo_limpo,
            "imagem": imagem,
            "cupom": ""
        }
        
        logger.info(f"📥 Novo link de {user_id}: {titulo_limpo}")
        
        keyboard = [
            [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
            [InlineKeyboardButton("🎟 Adicionar Cupom", callback_data="cupom")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
        ]
        
        # =========================
        # PRÉVIA
        # =========================
        preview = f"🔥 **PRÉVIA DA OFERTA**\n\n"
        preview += f"**{titulo_limpo}**\n\n"
        
        if imagem == IMAGEM_PADRAO:
            preview += f"📸 Imagem padrão (fallback)\n\n"
        else:
            preview += f"📸 Imagem capturada ✅\n\n"
        
        preview += f"🔗 {link_afiliado[:50]}..."
        
        # Envia a prévia com os botões
        await update.message.reply_text(preview, reply_markup=InlineKeyboardMarkup(keyboard))
        
        # =========================
        # ENVIA A IMAGEM
        # =========================
        try:
            # Se for arquivo local, abre e envia
            if isinstance(imagem, str) and imagem.startswith("/tmp/"):
                with open(imagem, 'rb') as photo:
                    await update.message.reply_photo(
                        photo,
                        caption=f"📸 Captura de tela: {titulo_limpo}"
                    )
                # Remove arquivo temporário
                try:
                    os.remove(imagem)
                except:
                    pass
            else:
                # Envia por URL
                await update.message.reply_photo(
                    imagem,
                    caption=f"📸 {titulo_limpo}"
                )
            logger.info(f"✅ Imagem enviada para {user_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar imagem: {e}")
            await update.message.reply_text("⚠️ Não foi possível carregar a imagem.")
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar link: {e}")
        await update.message.reply_text("❌ Erro ao processar o link. Verifique se é válido.")

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
            
            msg = f"🔥 **OFERTA EXCLUSIVA**\n\n"
            msg += f"**{oferta['titulo']}**\n\n"
            
            if oferta.get("cupom"):
                msg += f"🎟 **Cupom:** {oferta['cupom']}\n\n"
            
            msg += f"🔗 {oferta['link']}"
            
            # =========================
            # ENVIA PARA O CANAL
            # =========================
            if oferta.get("imagem"):
                # Se for arquivo local
                if isinstance(oferta["imagem"], str) and oferta["imagem"].startswith("/tmp/"):
                    with open(oferta["imagem"], 'rb') as photo:
                        await context.bot.send_photo(
                            CHANNEL_ID,
                            photo,
                            caption=msg
                        )
                    try:
                        os.remove(oferta["imagem"])
                    except:
                        pass
                else:
                    await context.bot.send_photo(
                        CHANNEL_ID,
                        oferta["imagem"],
                        caption=msg
                    )
                logger.info(f"✅ Oferta publicada com imagem por {user_id}")
            else:
                await context.bot.send_message(CHANNEL_ID, msg)
                logger.info(f"✅ Oferta publicada sem imagem por {user_id}")
            
            await query.edit_message_text("✅ **Publicado com sucesso!**")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            await query.edit_message_text(f"❌ Erro ao publicar: {str(e)}")
        
        ofertas.pop(user_id, None)
        
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text("🎟 **Envie o código do cupom:**")
        
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        await query.edit_message_text("❌ **Oferta cancelada.**")
