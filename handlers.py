import logging
import random
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
# LISTA DE GANCHOS
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
    await update.message.reply_text(
        "🚀 **OfertasJR Pro Online!**\n\n"
        "Envie um link de produto para criar uma oferta.\n"
        "Suporta: Shopee, Mercado Livre, Amazon, Kabum e mais!\n\n"
        "💡 Dica: Links da AWIN são convertidos automaticamente."
    )

# =========================
# RECEBE O LINK
# =========================

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Verifica se é cupom
    if user_id in aguardando_cupom:
        ofertas[user_id]["cupom"] = text
        del aguardando_cupom[user_id]
        await update.message.reply_text(f"✅ Cupom salvo: {text}")
        
        oferta = ofertas.get(user_id)
        if oferta:
            await mostrar_previa(update, user_id, oferta)
        return
    
    try:
        link_afiliado = gerar_link_afiliado(text)
        titulo = gerar_titulo(text)
        imagem, preco, beneficio = extrair_imagem(text)
        
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
        await mostrar_previa(update, user_id, ofertas[user_id])
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar link: {e}")
        await update.message.reply_text("❌ Erro ao processar o link. Verifique se é válido.")

# =========================
# MOSTRA PRÉVIA (SEM ASTERISCOS)
# =========================

async def mostrar_previa(update: Update, user_id: int, oferta: dict):
    keyboard = [
        [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
        [InlineKeyboardButton("🎟 Adicionar Cupom", callback_data="cupom")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    
    gancho = random.choice(GANCHOS)
    
    mensagem = f"🔥 PRÉVIA DA OFERTA\n\n"
    mensagem += f"{gancho}\n\n"
    mensagem += f"{oferta['titulo']}\n\n"
    
    if oferta.get("preco"):
        preco = oferta["preco"]
        if "~" in preco or "por" in preco.lower():
            mensagem += f"💰 PREÇO: {preco}\n\n"
        else:
            mensagem += f"💰 Preço: {preco}\n\n"
    
    if oferta.get("beneficio"):
        mensagem += f"🎯 {oferta['beneficio']}\n\n"
    
    if oferta.get("cupom"):
        mensagem += f"🎟 Cupom: {oferta['cupom']}\n\n"
    
    mensagem += f"🔗 {oferta['link']}"
    
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
            await update.message.reply_text(
                mensagem,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text("⚠️ Não foi possível carregar a imagem do produto.")
    else:
        await update.message.reply_text(
            mensagem,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# =========================
# BOTÕES (SEM ASTERISCOS)
# =========================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            
            gancho = random.choice(GANCHOS)
            
            mensagem = f"{gancho}\n\n"
            mensagem += f"{oferta['titulo']}\n\n"
            
            if oferta.get("preco"):
                preco = oferta["preco"]
                if "~" in preco or "por" in preco.lower():
                    mensagem += f"💰 PREÇO: {preco}\n\n"
                else:
                    mensagem += f"💰 Preço: {preco}\n\n"
            
            if oferta.get("beneficio"):
                mensagem += f"🎯 {oferta['beneficio']}\n\n"
            
            if oferta.get("cupom"):
                mensagem += f"🎟 Cupom: {oferta['cupom']}\n\n"
            
            mensagem += f"🔗 {oferta['link']}"
            
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
            
            await query.edit_message_text("✅ Publicado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            await query.edit_message_text(f"❌ Erro ao publicar: {str(e)}")
        
        ofertas.pop(user_id, None)
    
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text(
            "🎟 Envie o código do cupom:\n\n"
            "Digite apenas o código (ex: OFERTA10)"
        )
    
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        await query.edit_message_text("❌ Oferta cancelada.")
