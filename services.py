import os
import logging
import re
import json
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# =========================
# CONFIGURAÇÃO DE LOG (DEFINIDO PRIMEIRO)
# =========================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# TENTAR IMPORTAR SELENIUM (OPCIONAL)
# =========================

SELENIUM_DISPONIVEL = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_DISPONIVEL = True
    logger.info("✅ Selenium disponível")
except ImportError as e:
    logger.warning(f"⚠️ Selenium não disponível: {e}")
except Exception as e:
    logger.warning(f"⚠️ Erro ao importar Selenium: {e}")

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

def extrair_imagem_com_selenium(link: str):
    """Extrai a imagem do produto usando Selenium (se disponível)"""
    if not SELENIUM_DISPONIVEL:
        logger.warning("⚠️ Selenium não disponível")
        return None
    
    driver = None
    try:
        logger.info(f"📸 Iniciando Selenium para: {link}")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Tenta usar o ChromeDriver
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            # Fallback: tenta usar o Chrome já instalado
            chrome_options.binary_location = "/usr/bin/google-chrome"
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.get(link)
        time.sleep(3)
        
        # Tenta encontrar a imagem
        script_js = """
        function encontrarImagemProduto() {
            const imagens = document.querySelectorAll('img');
            let maior = null;
            let maiorArea = 0;
            
            for (let img of imagens) {
                const src = img.src || '';
                if (src.includes('logo') || src.includes('icon') || src.includes('avatar')) {
                    continue;
                }
                
                const width = img.naturalWidth || img.width || 0;
                const height = img.naturalHeight || img.height || 0;
                const area = width * height;
                
                if (area > maiorArea && area > 10000) {
                    maiorArea = area;
                    maior = src;
                }
            }
            return maior;
        }
        return encontrarImagemProduto();
        """
        
        url_imagem = driver.execute_script(script_js)
        if url_imagem and url_imagem.startswith("http"):
            logger.info(f"✅ Imagem via Selenium: {url_imagem[:50]}...")
            return url_imagem
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro no Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def extrair_imagem_bs4(link: str):
    """Extrai imagem usando BeautifulSoup (fallback)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        logger.info(f"🔍 Buscando imagem com BS4: {link}")
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        
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
                                logger.info(f"✅ Imagem via JSON-LD (lista): {img[:50]}...")
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
                            logger.info(f"✅ Imagem via CSS (HTTPS): {url_imagem[:50]}...")
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
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro no BS4: {e}")
        return None

def extrair_imagem(link: str):
    """Extrai imagem do produto - tenta Selenium primeiro, depois BS4"""
    
    # Tenta Selenium primeiro
    imagem = extrair_imagem_com_selenium(link)
    if imagem:
        return imagem
    
    # Fallback: BeautifulSoup
    imagem = extrair_imagem_bs4(link)
    if imagem:
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
