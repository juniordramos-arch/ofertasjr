import os  # <-- LINHA ADICIONADA
import requests
import logging
import re
import json
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
# API DE CAPTURA DE TELA (GRATUITA)
# =========================

SCREENSHOT_API_KEY = os.getenv("SCREENSHOT_API_KEY", "")  # Opcional
SCREENSHOT_API_URL = "https://api.screenshotapi.net/screenshot"

def capturar_tela_site(url: str):
    """Captura a tela do site usando API gratuita"""
    try:
        # Tenta usar a API do ScreenshotAPI
        if SCREENSHOT_API_KEY:
            params = {
                "url": url,
                "token": SCREENSHOT_API_KEY,
                "width": 800,
                "height": 600,
                "output": "image",
                "format": "png"
            }
            response = requests.get(SCREENSHOT_API_URL, params=params, timeout=30)
            if response.status_code == 200:
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()
                logger.info(f"✅ Captura de tela salva: {temp_file.name}")
                return temp_file.name
        
        # Fallback: tenta o serviço gratuito do MiniWebTool
        fallback_url = f"https://api.miniwebtool.com/screenshot/?url={url}&width=800&height=600"
        response = requests.get(fallback_url, timeout=30)
        if response.status_code == 200:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(response.content)
            temp_file.close()
            logger.info(f"✅ Captura de tela (fallback): {temp_file.name}")
            return temp_file.name
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro na captura de tela: {e}")
        return None

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

def extrair_imagem(link: str):
    """Extrai imagem do produto usando múltiplas estratégias"""
    
    # =========================
    # ESTRATÉGIA 1: Tentar captura de tela (mais confiável)
    # =========================
    logger.info(f"📸 Tentando captura de tela para: {link}")
    screenshot = capturar_tela_site(link)
    if screenshot:
        return screenshot
    
    # =========================
    # ESTRATÉGIA 2: Extrair do HTML
    # =========================
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        logger.info(f"🔍 Buscando imagem no HTML para: {link}")
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
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
                                logger.info(f"✅ Imagem via JSON-LD (lista): {img[:50]}...")
                                return img
            except:
                pass
        
        # Nike específico
        if "nike.com" in link.lower():
            padrao_nike = r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)[^\s"\']*(?:\?[^\s"\']*)?'
            matches = re.findall(padrao_nike, html, re.IGNORECASE)
            
            for url_imagem in matches:
                if "product" in url_imagem.lower() or "image" in url_imagem.lower():
                    if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                        logger.info(f"✅ Imagem Nike específica: {url_imagem[:50]}...")
                        return url_imagem
            
            for url_imagem in matches:
                if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                    logger.info(f"✅ Imagem Nike (fallback): {url_imagem[:50]}...")
                    return url_imagem
        
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
                            logger.info(f"✅ Imagem via CSS ({selector}): {url_imagem[:50]}...")
                            return url_imagem
                        elif url_imagem.startswith("//"):
                            url_imagem = f"https:{url_imagem}"
                            logger.info(f"✅ Imagem via CSS (HTTPS): {url_imagem[:50]}...")
                            return url_imagem
        
        # Regex geral
        padroes = [
            r'https?://[^\s"\']+product[^\s"\']+\.(?:jpg|jpeg|png|webp)',
            r'https?://[^\s"\']+image[^\s"\']+\.(?:jpg|jpeg|png|webp)',
            r'https?://[^\s"\']+imagem[^\s"\']+\.(?:jpg|jpeg|png|webp)',
            r'https?://[^\s"\']+foto[^\s"\']+\.(?:jpg|jpeg|png|webp)',
            r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\']*)?',
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, html, re.IGNORECASE)
            for url_imagem in matches:
                if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                    if "thumbnail" not in url_imagem.lower():
                        logger.info(f"✅ Imagem via Regex: {url_imagem[:50]}...")
                        return url_imagem
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao extrair imagem: {e}")
        return None

def baixar_imagem_para_telegram(url_imagem: str):
    """Verifica se a imagem é válida para enviar ao Telegram"""
    try:
        if not url_imagem:
            return False
        
        if url_imagem.startswith("/tmp/"):
            return True
        
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url_imagem, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "image" in content_type:
                return True
        
        return False
    except:
        return False

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
