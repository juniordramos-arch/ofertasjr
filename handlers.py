import logging
import random
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from services import gerar_link_afiliado, detectar_advertiser

logger = logging.getLogger(__name__)

# =========================
# MEMÓRIA DO BOT
# =========================

ofertas = {}
aguardando_cupom = {}
aguardando_imagem = {}
aguardando_texto = {}

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
# FUNÇÃO: EXTRAIR LINK DO TEXTO
# =========================

def extrair_link(texto: str):
    """Extrai o primeiro link (URL) do texto"""
    padrao = r'https?://[^\s]+'
    matches = re.findall(padrao, texto)
    if matches:
        return matches[0]
    return None

# =========================
# FUNÇÃO: REMOVER LINK DO TEXTO
# =========================

def remover_link(texto: str):
    """Remove links do texto"""
    padrao = r'https?://[^\s]+'
    return re.sub(padrao, '', texto).strip()

# =========================
# COMANDO /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Bot de Repost Profissional!**\n\n"
        "**Como usar:**\n"
        "1️⃣ Envie a **imagem** do produto\n"
        "2️⃣ Envie o **texto** da oferta (com link)\n"
        "3️⃣ O bot vai converter o link para seu link afiliado\n"
        "4️⃣ Publica no canal com formatação profissional\n\n"
        "**Comandos:**\n"
        "/start - Mostra este menu\n"
        "/cancelar - Cancela a operação\n"
        "/ajuda - Mais informações"
    )

# =========================
# COMANDO /ajuda
# =========================

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Como criar uma oferta:**\n\n"
        "**1. Envie a imagem**\n"
        "Envie uma foto do produto\n\n"
        "**2. Envie o texto**\n"
        "Digite o texto da oferta com o link\n"
        "Exemplo:\n"
        "Tênis Air Jordan 1 Low\n"
        "💰 Preço: R$ 599,99\n"
        "https://www.nike.com.br/produto\n\n"
        "**3. O bot converte**\n"
        "O link é convertido para seu link afiliado AWIN\n\n"
        "**4. Publique**\n"
        "Clique em 'Publicar'"
    )

# =========================
# COMANDO /cancelar
# =========================

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ofertas.pop(user_id, None)
    aguardando_cupom.pop(user_id, None)
    aguardando_imagem.pop(user_id, None)
    aguardando_texto.pop(user_id, None)
    await update.message.reply_text("❌ Operação cancelada.")

# =========================
# RECEBE IMAGEM
# =========================

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("❌ Por favor, envie uma imagem (foto)")
        return
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    temp_file = f"/tmp/oferta_{user_id}.jpg"
    await file.download_to_drive(temp_file)
    
    aguardando_imagem[user_id] = temp_file
    await update.message.reply_text(
        "✅ **Imagem recebida!**\n\n"
        "Agora envie o **texto da oferta** com o link:\n"
        "Exemplo:\n"
        "Tênis Air Jordan 1 Low\n"
        "💰 Preço: R$ 599,99\n"
        "https://www.nike.com.br/produto\n\n"
        "⚠️ O bot vai converter o link para seu link afiliado!"
    )

# =========================
# RECEBE TEXTO (COM CONVERSÃO DE LINK)
# =========================

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in aguardando_imagem:
        await update.message.reply_text("❌ Primeiro envie a imagem usando /start")
        return
    
    texto_original = update.message.text.strip()
    
    # =========================
    # EXTRAI O LINK E CONVERTE
    # =========================
    link_original = extrair_link(texto_original)
    texto_sem_link = remover_link(texto_original)
    
    if link_original:
        # Converte para link afiliado
        link_convertido = gerar_link_afiliado(link_original)
        logger.info(f"🔗 Link convertido: {link_original} -> {link_convertido}")
        
        # Detecta o advertiser
        advertiser = detectar_advertiser(link_original)
        if advertiser:
            logger.info(f"🏷️ Advertiser detectado: {advertiser}")
        
        # Texto final com link convertido
        texto_final = f"{texto_sem_link}\n\n🔗 {link_convertido}"
    else:
        # Se não encontrou link, mantém o texto original
        texto_final = texto_original
        await update.message.reply_text("⚠️ Nenhum link encontrado no texto. Envie o texto com o link.")
        return
    
    # Salva a oferta
    ofertas[user_id] = {
        "imagem": aguardando_imagem[user_id],
        "texto": texto_final,
        "texto_original": texto_original,
        "link_original": link_original,
        "link_convertido": link_convertido if link_original else None,
        "cupom": ""
    }
    
    # Mostra a prévia
    await mostrar_previa(update, user_id)

# =========================
# MOSTRA PRÉVIA
# =========================

async def mostrar_previa(update: Update, user_id: int):
    oferta = ofertas.get(user_id)
    if not oferta:
        await update.message.reply_text("❌ Oferta não encontrada.")
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Publicar", callback_data="publicar")],
        [InlineKeyboardButton("🎟 Adicionar Cupom", callback_data="cupom")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    
    gancho = random.choice(GANCHOS)
    
    # Monta a mensagem final
    mensagem = f"{gancho}\n\n"
    mensagem += oferta["texto"]
    
    if oferta.get("cupom"):
        mensagem += f"\n\n🎟 **Cupom:** {oferta['cupom']}"
    
    # Mostra info da conversão
    if oferta.get("link_convertido"):
        mensagem += f"\n\n🔄 Link convertido para afiliado ✅"
    
    # Envia a prévia
    try:
        with open(oferta["imagem"], 'rb') as foto:
            await update.message.reply_photo(
                foto,
                caption=mensagem,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        logger.info(f"✅ Prévia enviada para {user_id}")
    except Exception as e:
        logger.error(f"❌ Erro ao enviar prévia: {e}")
        await update.message.reply_text(
            mensagem,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# =========================
# PROCESSAMENTO DE MENSAGENS
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Verifica se está aguardando cupom
    if user_id in aguardando_cupom:
        await receive_cupom(update, context)
        return
    
    # Se tem imagem aguardando, é texto
    if user_id in aguardando_imagem:
        await receive_text(update, context)
        return
    
    # Se é uma imagem
    if update.message.photo:
        await receive_image(update, context)
        return
    
    # Qualquer outra mensagem
    await update.message.reply_text(
        "❌ Comando não reconhecido.\n"
        "Use /start para começar."
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
            await query.edit_message_text("❌ Nenhuma oferta encontrada.")
            return
        
        try:
            from config import CHANNEL_ID
            
            gancho = random.choice(GANCHOS)
            mensagem = f"{gancho}\n\n"
            mensagem += oferta["texto"]
            
            if oferta.get("cupom"):
                mensagem += f"\n\n🎟 **Cupom:** {oferta['cupom']}"
            
            # Envia para o canal
            with open(oferta["imagem"], 'rb') as foto:
                await context.bot.send_photo(
                    CHANNEL_ID,
                    foto,
                    caption=mensagem
                )
            
            logger.info(f"✅ Oferta publicada por {user_id}")
            logger.info(f"🔗 Link convertido: {oferta.get('link_original')} -> {oferta.get('link_convertido')}")
            await query.edit_message_text("✅ **Publicado com sucesso!**")
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar: {e}")
            await query.edit_message_text(f"❌ Erro ao publicar: {str(e)}")
        
        # Limpa
        ofertas.pop(user_id, None)
        aguardando_imagem.pop(user_id, None)
        aguardando_texto.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
    
    elif query.data == "cupom":
        aguardando_cupom[user_id] = True
        await query.edit_message_text(
            "🎟 **Envie o código do cupom:**\n\n"
            "Digite apenas o código (ex: OFERTA10)"
        )
    
    elif query.data == "cancelar":
        ofertas.pop(user_id, None)
        aguardando_imagem.pop(user_id, None)
        aguardando_texto.pop(user_id, None)
        aguardando_cupom.pop(user_id, None)
        await query.edit_message_text("❌ **Oferta cancelada.**")

# =========================
# RECEBE CUPOM
# =========================

async def receive_cupom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id in aguardando_cupom:
        ofertas[user_id]["cupom"] = text
        del aguardando_cupom[user_id]
        await update.message.reply_text(f"✅ Cupom salvo: **{text}**")
        await mostrar_previa(update, user_id)
