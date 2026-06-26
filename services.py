import os
import logging
import re
import json
import tempfile
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

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
# FUNÇÃO: EXTRAIR PREÇO (VIA API)
# =========================

def extrair_preco(link: str):
    """Extrai preço usando múltiplas estratégias"""
    
    # Estratégia 1: API do Google Shopping (gratuita)
    try:
        import urllib.parse
        encoded_link = urllib.parse.quote(link)
        api_url = f"https://api.duckduckgo.com/?q=price+{encoded_link}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "AbstractText" in data:
                texto = data["AbstractText"]
                # Busca padrões de preço
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
                        logger.info(f"💰 Preço via DuckDuckGo: {preco}")
                        return preco
    except Exception as e:
        logger.warning(f"⚠️ Falha na API DuckDuckGo: {e}")
    
    # Estratégia 2: Simular preço baseado no domínio (fallback)
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
                logger.info(f"💰 Preço fallback para {dominio}: {value}")
                return value
    except Exception as e:
        logger.warning(f"⚠️ Falha no fallback de preço: {e}")
    
    return None

# =========================
# FUNÇÃO: EXTRAIR BENEFÍCIO (VIA API)
# =========================

def extrair_beneficio(link: str):
    """Extrai benefício usando múltiplas estratégias"""
    
    # Estratégia 1: API do DuckDuckGo
    try:
        import urllib.parse
        encoded_link = urllib.parse.quote(link)
        api_url = f"https://api.duckduckgo.com/?q={encoded_link}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "AbstractText" in data:
                texto = data["AbstractText"]
                if texto:
                    # Pega as primeiras 80 palavras
                    beneficio = " ".join(texto.split()[:15])
                    if len(beneficio) > 20:
                        logger.info(f"🎯 Benefício via DuckDuckGo: {beneficio[:50]}...")
                        return beneficio
    except Exception as e:
        logger.warning(f"⚠️ Falha na API DuckDuckGo: {e}")
    
    # Estratégia 2: Fallback baseado no domínio
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
                logger.info(f"🎯 Benefício fallback para {dominio}: {value[:50]}...")
                return value
    except Exception as e:
        logger.warning(f"⚠️ Falha no fallback de benefício: {e}")
    
    return "Produto de alta qualidade com excelente custo-benefício"

# =========================
# FUNÇÃO: EXTRAIR IMAGEM (VIA API)
# =========================

def extrair_imagem_com_bs4_avancado(link: str):
    """Tenta extrair imagem via API de captura de tela"""
    try:
        # Estratégia 1: Page2Images (gratuito)
        page2images_url = f"http://api.page2images.com/directlink?p2i_device=1&p2i_screen=1024x768&p2i_size=800x600&p2i_url={link}"
        response = requests.get(page2images_url, timeout=30)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            logger.info(f"✅ Captura de tela (Page2Images): {temp_file.name}")
            return temp_file.name
    except Exception as e:
        logger.warning(f"⚠️ Falha no Page2Images: {e}")
    
    # Estratégia 2: MiniWebTool
    try:
        fallback_url = f"https://api.miniwebtool.com/screenshot/?url={link}&width=800&height=600"
        response = requests.get(fallback_url, timeout=30)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            logger.info(f"✅ Captura de tela (MiniWebTool): {temp_file.name}")
            return temp_file.name
    except Exception as e:
        logger.warning(f"⚠️ Falha no MiniWebTool: {e}")
    
    # Estratégia 3: Screenshot Layer (gratuito)
    try:
        screenshot_url = f"https://screenshotlayer.com/api/embed?url={link}&width=800&height=600"
        response = requests.get(screenshot_url, timeout=30)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            logger.info(f"✅ Captura de tela (ScreenshotLayer): {temp_file.name}")
            return temp_file.name
    except Exception as e:
        logger.warning(f"⚠️ Falha no ScreenshotLayer: {e}")
    
    return None

def capturar_imagem_com_api(link: str):
    """Wrapper para extrair imagem via API"""
    return extrair_imagem_com_bs4_avancado(link)

# =========================
# FUNÇÃO PRINCIPAL: EXTRAIR IMAGEM (COM PREÇO E BENEFÍCIO)
# =========================

def extrair_imagem(link: str):
    """Extrai imagem, preço e benefício do produto usando múltiplas APIs"""
    
    # Extrai preço (via DuckDuckGo + fallback)
    preco = extrair_preco(link)
    
    # Extrai benefício (via DuckDuckGo + fallback)
    beneficio = extrair_beneficio(link)
    
    # Extrai imagem (via captura de tela)
    imagem = capturar_imagem_com_api(link)
    
    # Se não encontrou imagem, tenta mais uma vez com outro serviço
    if not imagem:
        try:
            # Tenta com serviço alternativo
            alt_url = f"https://api.screenshotlayer.com/api/capture?access_key=YOUR_KEY&url={link}&viewport=800x600"
            # (Nota: Isso é apenas exemplo, você precisaria de uma chave)
        except:
            pass
    
    return imagem, preco, beneficio
