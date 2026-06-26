import os
import requests
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from config import AWIN_API_TOKEN, AWIN_PUBLISHER_ID, AWIN_ADVERTISERS, IMAGE_TIMEOUT, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# =========================
# AWIN - CONVERSÃO DE LINKS
# =========================

def detectar_advertiser(link: str):
    """Detecta o advertiser da AWIN pelo domínio"""
    try:
        domain = urlparse(link).netloc.replace("www.", "").lower()
        for key, value in AWIN_ADVERTISERS.items():
            if key in domain:
                logger.info(f"Advertiser detectado: {key} (ID: {value})")
                return value
        logger.warning(f"Nenhum advertiser encontrado para: {domain}")
        return None
    except Exception as e:
        logger.error(f"Erro ao detectar advertiser: {e}")
        return None

def gerar_link_afiliado(link: str):
    """Gera link afiliado da AWIN"""
    try:
        if not AWIN_API_TOKEN or not AWIN_PUBLISHER_ID:
            logger.warning("AWIN não configurado. Retornando link original.")
            return link
        
        advertiser_id = detectar_advertiser(link)
        if not advertiser_id:
            logger.warning("Advertiser não encontrado. Retornando link original.")
            return link
        
        url = f"https://api.awin.com/publishers/{AWIN_PUBLISHER_ID}/linkbuilder/generate"
        
        headers = {
            "Authorization": f"Bearer {AWIN_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "advertiserId": advertiser_id,
            "destinationUrl": link,
            "shorten": True
        }
        
        logger.info(f"Gerando link afiliado para advertiser {advertiser_id}")
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            short_url = data.get("shortUrl")
            if short_url:
                logger.info(f"Link afiliado gerado: {short_url}")
                return short_url
        
        logger.warning(f"Erro na AWIN: {response.status_code} - {response.text}")
        return link
        
    except requests.Timeout:
        logger.error("Timeout na requisição AWIN")
        return link
    except Exception as e:
        logger.error(f"Erro ao gerar link afiliado: {e}")
        return link

# =========================
# EXTRAÇÃO DE IMAGENS
# =========================

def extrair_imagem(link: str):
    """Extrai imagem do produto via Open Graph"""
    try:
        logger.info(f"Buscando imagem para: {link}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(link, headers=headers, timeout=IMAGE_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Tenta diferentes formas de extrair imagem
        # 1. Open Graph
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            imagem = og_image["content"]
            logger.info(f"Imagem encontrada (og:image): {imagem[:50]}...")
            return imagem
        
        # 2. Twitter Card
        tw_image = soup.find("meta", property="twitter:image")
        if tw_image and tw_image.get("content"):
            imagem = tw_image["content"]
            logger.info(f"Imagem encontrada (twitter:image): {imagem[:50]}...")
            return imagem
        
        # 3. Imagem principal do produto (Shopee, Mercado Livre)
        product_image = soup.find("img", {"class": ["product-image", "main-image", "product-img"]})
        if product_image and product_image.get("src"):
            imagem = product_image["src"]
            logger.info(f"Imagem encontrada (produto): {imagem[:50]}...")
            return imagem
        
        logger.warning("Nenhuma imagem encontrada")
        return None
        
    except requests.Timeout:
        logger.warning("Timeout ao buscar imagem")
        return None
    except Exception as e:
        logger.error(f"Erro ao extrair imagem: {e}")
        return None

# =========================
# GERAÇÃO DE TÍTULOS
# =========================

def gerar_titulo(link: str):
    """Gera título a partir do link"""
    try:
        # Tenta extrair da URL
        parsed = urlparse(link)
        path = parsed.path.strip("/")
        
        if not path:
            return "Produto"
        
        # Pega o último segmento da URL
        titulo = path.split("/")[-1]
        
        # Remove extensões
        titulo = titulo.split(".")[0]
        
        # Remove IDs e números
        titulo = titulo.replace("-", " ").replace("_", " ")
        
        # Remove IDs de produto (ex: "itemid12345")
        import re
        titulo = re.sub(r'\d+', '', titulo)
        
        # Capitaliza
        titulo = titulo.strip().title()
        
        # Se ficou vazio, usa nome do domínio
        if not titulo:
            titulo = parsed.netloc.replace("www.", "").split(".")[0].title()
        
        logger.info(f"Título gerado: {titulo}")
        return titulo
        
    except Exception as e:
        logger.error(f"Erro ao gerar título: {e}")
        return "Produto"
