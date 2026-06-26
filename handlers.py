import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import gerar_link_afiliado, extrair_imagem, gerar_titulo

logger = logging.getLogger(__name__)

# =========================
# MEMÓRIA DO BOT (guarda as ofertas temporariamente)
# =========================

ofertas = {}
aguardando_cupom = {}

# =========================
# LISTA DE GANCHOS (frases chamativas)
# =========================

GANCHOS = [
    "🏋️‍♂️ ACHADO BOM DEMAIS 😮",
    "🔥 OFERTA IMPERDÍVEL!",
    "💥 OPORTUNIDADE ÚNICA!",
    "🎯 CORRE QUE É POUCO!",
    "⚡ PROMOÇÃO RELÂMPAGO!",
    "🛒 COMPRE AGORA E ECONOMIZE!",
    "💰 PREÇO QUE CABE NO BOLSO!",
    "🚀 OFERTA EXCLUSIVA!",
    "🎉 APROVEITE ENQUANTO DURA!",
    "🏆 MELHOR PREÇO GARANTIDO!"
]

# =========================
# COMANDO /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /start"""
    await update.message.reply_text(
        "🚀 **OfertasJR Pro Online!**\n\n"
        "Envie um link de produto para criar uma oferta.\n"
        "Suporta: Shopee, Mercado Livre, Amazon, Kabum e mais!\n\n"
        "💡 Dica: Links da AWIN são convertidos automaticamente."
    )

# =========================
# RECEBE O LINK DO PRODUTO
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o link do produto enviado pelo usuário"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Verifica se o usuário está enviando um cupom
    if user_id in aguardando_cupom:
        ofertas[user_id]["cupom"] = text
        del aguardando_cupom[user_id]
        await update.message.reply_text(f"✅ Cupom salvo: **{text}**")
        
        # Mostra a prévia atualizada com o cupom
        oferta = ofertas.get(user_id)
        if oferta:
            await mostrar_previa(update, user_id, oferta)
        return
    
    try:
        # Processa o link
        link_afiliado = gerar_link_afiliado(text)
        titulo = gerar_titulo(text)
        imagem, preco, beneficio = extrair_imagem(text)
        
        # Limpa o título
        titulo_limpo = titulo.replace(".Html", "").replace(".html", "").strip()
        
        # Salva a oferta na memória
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

# =========================
# MOSTRA A PRÉVIA DA OFERTA
# =========================

async def mostrar_previa(update: Update, user_id: int, oferta: dict):
    """Mostra a prévia formatada da oferta com botões"""
    
    # Botões
    keyboard = [
        [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
        [InlineKeyboardButton("🎟 Adicionar Cupom", callback_data="cupom")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    
    # =========================
    # CONSTRÓI A MENSAGEM DA PRÉVIA
    # =========================
    
    # Escolhe um gancho aleatório
    gancho = random.choice(GANCHOS)
    
    mensagem = f"🔥 **PRÉVIA DA OFERTA**\n\n"
    mensagem += f"{gancho}\n\n"
    mensagem += f"**{oferta['titulo']}**\n\n"
    
    # Preço (se encontrado)
    if oferta.get("preco"):
        preco = oferta["preco"]
        if "~" in preco or "por" in preco.lower():
            mensagem += f"💰 **PREÇO:** {preco}\n\n"
        else:
            mensagem += f"💰 **Preço:** {preco}\n\n"
    
    # Benefício (se encontrado)
    if oferta.get("beneficio"):
        mensagem += f"🎯 {oferta['beneficio']}\n\n"
    
    # Cupom (se já tiver sido adicionado)
    if oferta.get("cupom"):
        mensagem += f"🎟 **Cupom:** {oferta['cupom']}\n\n"
    
    # Link (sempre aparece)
    mensagem += f"🔗 {oferta['link']}"
    
    # =========================
    # ENVIA A MENSAGEM COM OU SEM IMAGEM
    # =========================
    
    if oferta.get("imagem"):
        try:
            # Tenta enviar com imagem
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

# =========================
# PROCESSA OS BOTÕES
# =========================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa os cliques nos botões (Publicar, Cupom, Cancelar)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    oferta = ofertas.get(user_id)
    
    # =========================
    # BOTÃO: PUBLICAR
    # =========================
    if query.data == "publicar":
        if not oferta:
            await query.edit_message_text("❌ Nenhuma oferta encontrada.")
            return
        
        try:
            from config import CHANNEL_ID
            
            # =========================
            # CONSTRÓI A MENSAGEM FINAL
            # =========================
            
            gancho = random.choice(GANCHOS)
            
            mensagem = f"{gancho}\n\n"
            mensagem += f"**{oferta['titulo']}**\n\n"
            
            # Preço
            if oferta.get("preco"):
                preco = oferta["preco"]
                if "~" in preco or "por" in preco.lower():
                    mensagem += f"💰 **PREÇO:** {preco}\n\n"
                else:
                    mensagem += f"💰 **Preço:** {preco}\n\n"
            
            # Benefício
            if oferta.get("beneficio"):
                mensagem += f"🎯 {oferta['beneficio']}\n\n"
            
            # Cupom
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
                    # Fallback: envia só texto
                    await context.bot.send_message(CHANNEL_ID, mensagem)
            else:
                await context.bot.send_message(CHANNEL_ID, mensagem)
                logger.info(f"✅ Oferta publicada sem imagem por {user_id}")
            
            # Confirma para o usuário
            await query.edit_message_text("✅ **Publicado com sucesso!**")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            await query.edit_message_text(f"❌ Erro ao publicar: {str(e)}")
        
        # Remove a oferta da memória
        ofertas.pop(user_id, None)
    
    # =========================
    # BOTÃO: ADICIONAR CUPOM
    # =========================
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text(
            "🎟 **Envie o código do cupom:**\n\n"
            "Digite apenas o código (ex: OFERTA10)"
        )
    
    # =========================
    # BOTÃO: CANCELAR
    # =========================
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        await query.edit_message_text("❌ **Oferta cancelada.**")
