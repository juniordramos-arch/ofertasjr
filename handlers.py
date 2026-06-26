import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import gerar_link_afiliado, extrair_imagem, gerar_titulo, extrair_preco

logger = logging.getLogger(__name__)

# =========================
# MEMÓRIA
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
        
        # Atualiza a prévia com o cupom
        await update.message.reply_text(f"✅ Cupom salvo: **{text}**")
        
        # Mostra a prévia atualizada
        oferta = ofertas.get(user_id)
        if oferta:
            await mostrar_previa(update, user_id, oferta)
        return
    
    try:
        link_afiliado = gerar_link_afiliado(text)
        titulo = gerar_titulo(text)
        imagem, preco, beneficio = extrair_imagem(text)
        
        # Remove extensões e caracteres especiais do título
        titulo_limpo = titulo.replace(".Html", "").replace(".html", "").strip()
        
        ofertas[user_id] = {
            "link": link_afiliado,
            "titulo": titulo_limpo,
            "imagem": imagem,
            "preco": preco,
            "beneficio": beneficio,
            "cupom": ""
        }
        
        logger.info(f"📥 Novo link de {user_id}: {titulo_limpo}")
        
        # Mostra a prévia
        await mostrar_previa(update, user_id, ofertas[user_id])
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar link: {e}")
        await update.message.reply_text("❌ Erro ao processar o link. Verifique se é válido.")

async def mostrar_previa(update: Update, user_id: int, oferta: dict):
    """Mostra a prévia formatada da oferta"""
    
    keyboard = [
        [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
        [InlineKeyboardButton("🎟 Adicionar Cupom", callback_data="cupom")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    
    # =========================
    # MENSAGEM FORMATADA
    # =========================
    mensagem = "🔥 **PRÉVIA DA OFERTA**\n\n"
    
    # Gancho (frase chamativa)
    ganchos = [
        "🏋️‍♂️ ACHADO BOM DEMAIS 😮",
        "🔥 OFERTA IMPERDÍVEL!",
        "💥 OPORTUNIDADE ÚNICA!",
        "🎯 CORRE QUE É POUCO!",
        "⚡ PROMOÇÃO RELÂMPAGO!"
    ]
    import random
    mensagem += f"{random.choice(ganchos)}\n\n"
    
    # Título
    mensagem += f"**{oferta['titulo']}**\n\n"
    
    # Preço (se disponível)
    if oferta.get("preco"):
        preco = oferta["preco"]
        if "~" in preco:  # Tem desconto
            mensagem += f"💰 **PREÇO:** {preco}\n\n"
        else:
            mensagem += f"💰 **Preço:** {preco}\n\n"
    
    # Benefício (se disponível)
    if oferta.get("beneficio"):
        mensagem += f"🎯 {oferta['beneficio']}\n\n"
    
    # Cupom (se adicionado)
    if oferta.get("cupom"):
        mensagem += f"🎟 **Cupom:** {oferta['cupom']}\n\n"
    
    # Link (sempre aparece)
    mensagem += f"🔗 {oferta['link']}"
    
    # =========================
    # ENVIA A MENSAGEM
    # =========================
    if oferta.get("imagem"):
        try:
            await update.message.reply_photo(
                oferta["imagem"],
                caption=mensagem,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info(f"✅ Prévia com imagem enviada para {user_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar imagem: {e}")
            # Fallback: envia só texto
            await update.message.reply_text(
                mensagem,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text("⚠️ Não foi possível carregar a imagem do produto.")
    else:
        # Sem imagem, envia só texto
        await update.message.reply_text(
            mensagem,
            reply_markup=InlineKeyboardMarkup(keyboard)
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
            
            # =========================
            # MENSAGEM FINAL
            # =========================
            mensagem = "🏋️‍♂️ **ACHADO BOM DEMAIS** 😮\n\n"
            
            # Gancho
            ganchos = [
                "🏋️‍♂️ ACHADO BOM DEMAIS 😮",
                "🔥 OFERTA IMPERDÍVEL!",
                "💥 OPORTUNIDADE ÚNICA!",
                "🎯 CORRE QUE É POUCO!",
                "⚡ PROMOÇÃO RELÂMPAGO!"
            ]
            import random
            mensagem = f"{random.choice(ganchos)}\n\n"
            
            # Título
            mensagem += f"**{oferta['titulo']}**\n\n"
            
            # Preço (se disponível)
            if oferta.get("preco"):
                preco = oferta["preco"]
                if "~" in preco:  # Tem desconto
                    mensagem += f"💰 **PREÇO:** {preco}\n\n"
                else:
                    mensagem += f"💰 **Preço:** {preco}\n\n"
            
            # Benefício (se disponível)
            if oferta.get("beneficio"):
                mensagem += f"🎯 {oferta['beneficio']}\n\n"
            
            # Cupom (se adicionado)
            if oferta.get("cupom"):
                mensagem += f"🎟 **Cupom:** {oferta['cupom']}\n\n"
            
            # Link
            mensagem += f"🔗 {oferta['link']}"
            
            # =========================
            # ENVIA PARA O CANAL
            # =========================
            if oferta.get("imagem"):
                try:
                    await context.bot.send_photo(
                        CHANNEL_ID,
                        oferta["imagem"],
                        caption=mensagem
                    )
                    logger.info(f"✅ Oferta publicada com imagem por {user_id}")
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar imagem: {e}")
                    await context.bot.send_message(CHANNEL_ID, mensagem)
            else:
                await context.bot.send_message(CHANNEL_ID, mensagem)
                logger.info(f"✅ Oferta publicada sem imagem por {user_id}")
            
            await query.edit_message_text("✅ **Publicado com sucesso!**")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            await query.edit_message_text(f"❌ Erro ao publicar: {str(e)}")
        
        ofertas.pop(user_id, None)
        
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text("🎟 **Envie o código do cupom:**\n\nDigite apenas o código (ex: OFERTA10)")
        
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        await query.edit_message_text("❌ **Oferta cancelada.**")
