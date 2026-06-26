import logging
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import gerar_link_afiliado, extrair_imagem, gerar_titulo
from PIL import Image

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
# FUNÇÃO: VALIDAR IMAGEM
# =========================

def validar_imagem(caminho_imagem: str):
    """Verifica se a imagem é válida"""
    try:
        if not caminho_imagem or not os.path.exists(caminho_imagem):
            return False
        
        img = Image.open(caminho_imagem)
        img.verify()
        
        tamanho = os.path.getsize(caminho_imagem)
        if tamanho < 100:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Imagem inválida: {e}")
        return False

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
        
        imagem_valida = False
        if imagem and validar_imagem(imagem):
            imagem_valida = True
            logger.info(f"✅ Imagem validada: {imagem}")
        else:
            imagem = None
            logger.warning("⚠️ Imagem inválida")
        
        ofertas[user_id] = {
            "link": link_afiliado,
            "titulo": titulo_limpo,
            "imagem": imagem,
            "imagem_valida": imagem_valida,
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
# MOSTRA PRÉVIA
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
    
    if oferta.get("imagem") and oferta.get("imagem_valida"):
        try:
            with open(oferta["imagem"], 'rb') as foto:
                await update.message.reply_photo(
                    foto,
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
    else:
        await update.message.reply_text(
            mensagem,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# =========================
# BOTÕES
# =========================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    oferta = ofertas.get(user_id)
    
    if query.data == "publicar":
        if not oferta:
            try:
                await query.edit_message_text("❌ Nenhuma oferta encontrada.")
            except:
                pass
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
            
            if oferta.get("imagem") and oferta.get("imagem_valida"):
                try:
                    with open(oferta["imagem"], 'rb') as foto:
                        await context.bot.send_photo(
                            CHANNEL_ID,
                            foto,
                            caption=mensagem
                        )
                    logger.info(f"✅ Oferta publicada com imagem por {user_id}")
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar imagem: {e}")
                    await context.bot.send_message(CHANNEL_ID, mensagem)
            else:
                await context.bot.send_message(CHANNEL_ID, mensagem)
                logger.info(f"✅ Oferta publicada sem imagem por {user_id}")
            
            try:
                await query.edit_message_text("✅ Publicado com sucesso!")
            except:
                pass
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            try:
                await query.edit_message_text(f"❌ Erro ao publicar: {str(e)}")
            except:
                pass
        
        ofertas.pop(user_id, None)
    
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        try:
            await query.edit_message_text(
                "🎟 Envie o código do cupom:\n\n"
                "Digite apenas o código (ex: OFERTA10)"
            )
        except:
            pass
    
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        try:
            await query.edit_message_text("❌ Oferta cancelada.")
        except:
            pass
