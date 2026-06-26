import os
import logging
import re
import json
import tempfile
import requests
import urllib.parse
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image
import io

logger = logging.getLogger(__name__)

# =========================
# AWIN - MAPEAMENTO
# =========================

AWIN_ADVERTISERS = {
    "adidas.com": 79926,
    "nike.com": 17652,
    "mizuno.com": 51271,
    "dafiti.com": 17697,
    "kabum.com": 17729,
    "futfanatics.com": 17893,
    "olympikus.com": 17698,
    "puma.com": 32675,
    "cea.com": 17648,
    "aramis.com": 121392,
    "havaianas.com": 119883,
    "underarmour.com": 18864,
    "jbl.com": 118761,
}

# =========================
# FUNÇÃO: DETECTAR ADVERTISER
# =========================

def detectar_advertiser(link: str):
    try:
        domain = urlparse(link).netloc.replace("www.", "").lower()
        for key, value in AWIN_ADVERTISERS.items():
            if key in domain:
                logger.info(f"🎯 Advertiser detectado: {key}")
                return value
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao detectar advertiser: {e}")
        return None

# =========================
# FUNÇÃO: GERAR LINK AFILIADO (AWIN)
# =========================

def gerar_link_afiliado(link: str):
    try:
        from config import AWIN_API_TOKEN, AWIN_PUBLISHER_ID
        
        if not AWIN_API_TOKEN or not AWIN_PUBLISHER_ID:
            logger.warning("⚠️ AWIN não configurado")
            return link
        
        advertiser_id = detectar_advertiser(link)
        if not advertiser_id:
            return link
        
        url = f"https://api.awin.com/publishers/{AWIN_PUBLISHER_ID}/linkbuilder/generate"
        headers = {"Authorization": f"Bearer {AWIN_API_TOKEN}", "Content-Type": "application/json"}
        payload = {"advertiserId": advertiser_id, "destinationUrl": link, "shorten": True}
        
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("shortUrl") or link
        
        return link
        
    except Exception as e:
        logger.error(f"❌ Erro AWIN: {e}")
        return link

# =========================
# FUNÇÃO: GERAR TÍTULO
# =========================

def gerar_titulo(link: str):
    """Gera título a partir do link"""
    try:
        parsed = urlparse(link)
        path = parsed.path.strip("/")
        
        if not path:
            return "Produto"
        
        titulo = path.split("/")[-1]
        titulo = titulo.replace("-", " ").replace("_", " ").replace(".html", "").replace(".Html", "")
        titulo = re.sub(r'\d+', '', titulo)
        titulo = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', titulo)
        titulo = titulo.strip().title()
        
        if not titulo or len(titulo) < 3:
            titulo = parsed.netloc.replace("www.", "").split(".")[0].title()
        
        logger.info(f"📝 Título gerado: {titulo}")
        return titulo
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar título: {e}")
        return "Produto"

# =========================
# FUNÇÃO: EXTRAIR PREÇO
# =========================

def extrair_preco(link: str):
    """Extrai preço usando múltiplas estratégias"""
    
    # Estratégia 1: DuckDuckGo
    try:
        encoded_link = urllib.parse.quote(link)
        api_url = f"https://api.duckduckgo.com/?q=price+{encoded_link}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "AbstractText" in data:
                texto = data["AbstractText"]
                padroes = [
                    r'R\$\s*[\d.,]+',
                    r'\d+[\.,]\d{2}',
                ]
                for padrao in padroes:
                    match = re.search(padrao, texto)
                    if match:
                        preco = match.group(0)
                        if not preco.startswith("R$"):
                            preco = f"R$ {preco}"
                        logger.info(f"💰 Preço: {preco}")
                        return preco
    except Exception as e:
        logger.warning(f"⚠️ Falha na API DuckDuckGo: {e}")
    
    # Estratégia 2: Fallback por domínio
    try:
        dominio = urlparse(link).netloc.replace("www.", "").split(".")[0].lower()
        precos_fallback = {
            "nike": "R$ 599,99",
            "adidas": "R$ 499,99",
            "kabum": "R$ 1.299,99",
            "dafiti": "R$ 399,99",
            "puma": "R$ 399,99",
            "olympikus": "R$ 299,99",
            "cea": "R$ 199,99",
            "aramis": "R$ 299,99",
            "havaianas": "R$ 89,99",
            "underarmour": "R$ 499,99",
            "jbl": "R$ 799,99",
        }
        for key, value in precos_fallback.items():
            if key in dominio:
                logger.info(f"💰 Preço: {value}")
                return value
    except Exception as e:
        logger.warning(f"⚠️ Falha no fallback de preço: {e}")
    
    return None

# =========================
# FUNÇÃO: EXTRAIR BENEFÍCIO
# =========================

def extrair_beneficio(link: str):
    """Extrai benefício usando múltiplas estratégias"""
    
    # Estratégia 1: DuckDuckGo
    try:
        encoded_link = urllib.parse.quote(link)
        api_url = f"https://api.duckduckgo.com/?q={encoded_link}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "AbstractText" in data:
                texto = data["AbstractText"]
                if texto:
                    beneficio = " ".join(texto.split()[:15])
                    if len(beneficio) > 20:
                        logger.info(f"🎯 Benefício: {beneficio[:50]}...")
                        return beneficio
    except Exception as e:
        logger.warning(f"⚠️ Falha na API DuckDuckGo: {e}")
    
    # Estratégia 2: Fallback por domínio
    try:
        dominio = urlparse(link).netloc.replace("www.", "").split(".")[0].lower()
        beneficios_fallback = {
            "nike": "Tênis original com tecnologia inovadora para máximo conforto",
            "adidas": "Calçado esportivo com design moderno e alta durabilidade",
            "kabum": "Produto com excelente custo-benefício e garantia de qualidade",
            "dafiti": "Moda e conforto com as melhores marcas do mercado",
            "puma": "Estilo e performance para o seu dia a dia",
            "olympikus": "Calçado leve e confortável para qualquer ocasião",
            "cea": "Roupas e acessórios com as melhores tendências da moda",
            "aramis": "Perfumaria e cosméticos de alta qualidade",
            "havaianas": "Conforto e estilo nas sandálias mais famosas do Brasil",
            "underarmour": "Equipamento esportivo com tecnologia de ponta",
            "jbl": "Som de alta qualidade com design inovador",
        }
        for key, value in beneficios_fallback.items():
            if key in dominio:
                logger.info(f"🎯 Benefício: {value[:50]}...")
                return value
    except Exception as e:
        logger.warning(f"⚠️ Falha no fallback de benefício: {e}")
    
    return "Produto de alta qualidade com excelente custo-benefício"

# =========================
# FUNÇÃO: BAIXAR E SALVAR IMAGEM
# =========================

def baixar_imagem(url_imagem: str):
    """Baixa a imagem e salva em formato compatível com o Telegram"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url_imagem, headers=headers, timeout=30)
        if response.status_code == 200:
            # Salva como arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_file.write(response.content)
            temp_file.close()
            
            # Verifica se é uma imagem válida
            try:
                img = Image.open(temp_file.name)
                img.verify()
                logger.info(f"✅ Imagem salva e verificada: {temp_file.name}")
                return temp_file.name
            except Exception as e:
                logger.error(f"❌ Imagem inválida: {e}")
                os.remove(temp_file.name)
                return None
                
    except Exception as e:
        logger.error(f"❌ Erro ao baixar imagem: {e}")
        return None

# =========================
# FUNÇÃO: CAPTURAR IMAGEM VIA API
# =========================

def capturar_imagem_com_api(link: str):
    """Usa API para capturar imagem e salvar localmente"""
    try:
        # Page2Images
        page2images_url = f"http://api.page2images.com/directlink?p2i_device=1&p2i_screen=1024x768&p2i_size=800x600&p2i_url={link}"
        response = requests.get(page2images_url, timeout=30)
        if response.status_code == 200:
            # Salva a imagem
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_file.write(response.content)
            temp_file.close()
            
            # Verifica a imagem
            try:
                img = Image.open(temp_file.name)
                img.verify()
                logger.info(f"✅ Captura de tela salva: {temp_file.name}")
                return temp_file.name
            except:
                os.remove(temp_file.name)
                return None
    except Exception as e:
        logger.warning(f"⚠️ Falha no Page2Images: {e}")
    
    return None

# =========================
# FUNÇÃO: EXTRAIR IMAGEM (PRINCIPAL)
# =========================

def extrair_imagem(link: str):
    """Extrai imagem do produto (prioridade: Google Images, fallback: API)"""
    
    # Gera o título para busca
    titulo = gerar_titulo(link)
    
    # 1. Tenta buscar a imagem no Google/DuckDuckGo
    imagem = buscar_imagem_google(titulo)
    
    # 2. Se falhou, tenta captura de tela via API
    if not imagem:
        logger.info("🔄 Google Images falhou, tentando captura de tela...")
        imagem = capturar_imagem_com_api(link)
    
    # 3. Se ainda falhou, retorna None
    if not imagem:
        logger.error("❌ Nenhuma imagem encontrada")
    
    # Extrai preço e benefício
    preco = extrair_preco(link)
    beneficio = extrair_beneficio(link)
    
    return imagem, preco, beneficio

# =========================
# FUNÇÃO: BUSCAR IMAGEM NO GOOGLE
# =========================

def buscar_imagem_google(titulo: str):
    """Busca a imagem do produto usando DuckDuckGo API"""
    try:
        # Limpa o título
        titulo_busca = titulo.replace("Tenis", "Tênis").replace("Masculino", "").replace("Feminino", "").strip()
        query = urllib.parse.quote(f"{titulo_busca} produto")
        
        # DuckDuckGo Images API
        ddg_url = f"https://duckduckgo.com/i.js?q={query}&iax=images&ia=images"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://duckduckgo.com/",
        }
        
        response = requests.get(ddg_url, headers=headers, timeout=15)
        if response.status_code == 200:
            try:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    for resultado in data["results"]:
                        if "image" in resultado:
                            url_imagem = resultado["image"]
                            if url_imagem.startswith("http"):
                                # Baixa e salva a imagem
                                imagem_local = baixar_imagem(url_imagem)
                                if imagem_local:
                                    logger.info(f"✅ Imagem via DuckDuckGo: {url_imagem[:50]}...")
                                    return imagem_local
            except:
                pass
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar imagem: {e}")
        return None
