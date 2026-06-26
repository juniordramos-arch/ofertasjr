import os
import logging
import requests
import re
import json
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# =========================
# CONFIGURAÇÕES
# =========================

# API de Captura de Tela (gratuita)
SCREENSHOT_API_KEY = os.getenv("SCREENSHOT_API_KEY", "")
# Cache de imagens (evita requisições duplicadas)
CACHE_IMAGENS = {}

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
# FUNÇÕES
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

def capturar_imagem_com_api(link: str):
    """Usa API gratuita para capturar imagem do produto"""
    
    # =========================
    # ESTRATÉGIA 1: ScreenshotAPI (se tiver chave)
    # =========================
    if SCREENSHOT_API_KEY:
        try:
            api_url = "https://api.screenshotapi.net/screenshot"
            params = {
                "url": link,
                "token": SCREENSHOT_API_KEY,
                "width": 800,
                "height": 600,
                "output": "image",
                "format": "png"
            }
            response = requests.get(api_url, params=params, timeout=30)
            if response.status_code == 200:
                # Salva a imagem temporariamente
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()
                logger.info(f"✅ Captura de tela salva: {temp_file.name}")
                return temp_file.name
        except Exception as e:
            logger.error(f"❌ Erro no ScreenshotAPI: {e}")
    
    # =========================
    # ESTRATÉGIA 2: MiniWebTool (gratuito, sem chave)
    # =========================
    try:
        fallback_url = f"https://api.miniwebtool.com/screenshot/?url={link}&width=800&height=600"
        response = requests.get(fallback_url, timeout=30)
        if response.status_code == 200:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            logger.info(f"✅ Captura de tela (MiniWebTool): {temp_file.name}")
            return temp_file.name
    except Exception as e:
        logger.error(f"❌ Erro no MiniWebTool: {e}")
    
    # =========================
    # ESTRATÉGIA 3: Page2Images (gratuito)
    # =========================
    try:
        page2images_url = f"http://api.page2images.com/directlink?p2i_device=1&p2i_screen=1024x768&p2i_size=800x600&p2i_url={link}"
        response = requests.get(page2images_url, timeout=30)
        if response.status_code == 200:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            logger.info(f"✅ Captura de tela (Page2Images): {temp_file.name}")
            return temp_file.name
    except Exception as e:
        logger.error(f"❌ Erro no Page2Images: {e}")
    
    return None

def extrair_imagem_com_bs4_avancado(link: str):
    """Tenta extrair imagem usando BeautifulSoup com headers avançados"""
    try:
        # Headers que imitam um navegador real
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        # Tenta com diferentes estratégias de requisição
        for strategy in ["direct", "mobile", "referer"]:
            try:
                if strategy == "mobile":
                    headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
                elif strategy == "referer":
                    headers["Referer"] = "https://www.google.com/"
                
                logger.info(f"🔍 Tentando BS4 com estratégia: {strategy}")
                response = requests.get(link, headers=headers, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Open Graph
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        url_imagem = og_image["content"]
                        if url_imagem.startswith("http"):
                            logger.info(f"✅ Imagem via OG: {url_imagem[:50]}...")
                            return url_imagem
                    
                    # Twitter Card
                    tw_image = soup.find("meta", property="twitter:image")
                    if tw_image and tw_image.get("content"):
                        url_imagem = tw_image["content"]
                        if url_imagem.startswith("http"):
                            logger.info(f"✅ Imagem via Twitter: {url_imagem[:50]}...")
                            return url_imagem
                    
                    # JSON-LD
                    script_tags = soup.find_all("script", type="application/ld+json")
                    for script in script_tags:
                        try:
                            data = json.loads(script.string)
                            if "image" in data:
                                url_imagem = data["image"]
                                if isinstance(url_imagem, str) and url_imagem.startswith("http"):
                                    logger.info(f"✅ Imagem via JSON-LD: {url_imagem[:50]}...")
                                    return url_imagem
                                elif isinstance(url_imagem, list) and len(url_imagem) > 0:
                                    for img in url_imagem:
                                        if isinstance(img, str) and img.startswith("http"):
                                            logger.info(f"✅ Imagem via JSON-LD: {img[:50]}...")
                                            return img
                        except:
                            pass
                    
                    # CSS Selectors
                    selectores = [
                        "img[class*='product-image']",
                        "img[class*='main-image']",
                        "img[class*='product-img']",
                        "img[class*='produto']",
                        "img[itemprop='image']",
                        "img[data-testid='product-image']",
                        "img[data-image]",
                        "img[data-src]",
                        "img[class*='product-card']",
                        "img[class*='product']",
                        "img[class*='image']",
                        "img[class*='photo']",
                    ]
                    
                    for selector in selectores:
                        img = soup.select_one(selector)
                        if img:
                            for attr in ["src", "data-src", "data-image", "content"]:
                                url_imagem = img.get(attr)
                                if url_imagem:
                                    if url_imagem.startswith("http"):
                                        logger.info(f"✅ Imagem via CSS: {url_imagem[:50]}...")
                                        return url_imagem
                                    elif url_imagem.startswith("//"):
                                        url_imagem = f"https:{url_imagem}"
                                        logger.info(f"✅ Imagem via CSS: {url_imagem[:50]}...")
                                        return url_imagem
                    
                    # Regex
                    padroes = [
                        r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\']*)?',
                        r'https?://[^\s"\']+product[^\s"\']+\.(?:jpg|jpeg|png|webp)',
                        r'https?://[^\s"\']+image[^\s"\']+\.(?:jpg|jpeg|png|webp)',
                    ]
                    
                    for padrao in padroes:
                        matches = re.findall(padrao, response.text, re.IGNORECASE)
                        for url_imagem in matches:
                            if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                                if "thumbnail" not in url_imagem.lower():
                                    logger.info(f"✅ Imagem via Regex: {url_imagem[:50]}...")
                                    return url_imagem
            except Exception as e:
                logger.warning(f"⚠️ Estratégia {strategy} falhou: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro no BS4 Avançado: {e}")
        return None

def extrair_imagem(link: str):
    """Extrai imagem do produto com múltiplas estratégias"""
    
    # =========================
    # ESTRATÉGIA 1: Cache
    # =========================
    if link in CACHE_IMAGENS:
        logger.info(f"📦 Imagem em cache para: {link[:50]}...")
        return CACHE_IMAGENS[link]
    
    # =========================
    # ESTRATÉGIA 2: BeautifulSoup Avançado
    # =========================
    imagem = extrair_imagem_com_bs4_avancado(link)
    if imagem:
        CACHE_IMAGENS[link] = imagem
        return imagem
    
    # =========================
    # ESTRATÉGIA 3: API de Captura
    # =========================
    imagem = capturar_imagem_com_api(link)
    if imagem:
        CACHE_IMAGENS[link] = imagem
        return imagem
    
    logger.error("❌ NENHUMA IMAGEM ENCONTRADA!")
    return None

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
