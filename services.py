import os
import logging
import re
import json
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# =========================
# CONFIGURAÇÃO DO SELENIUM
# =========================

def criar_driver():
    """Cria e configura o driver do Chrome em modo headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Modo sem interface gráfica
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # Tenta usar o driver gerenciado automaticamente
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"❌ Erro ao criar driver: {e}")
        return None

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
    """Extrai a imagem do produto usando Selenium (renderiza JavaScript)"""
    driver = None
    try:
        logger.info(f"📸 Iniciando Selenium para: {link}")
        driver = criar_driver()
        
        if not driver:
            logger.error("❌ Falha ao criar driver Selenium")
            return None
        
        # Carrega a página
        driver.get(link)
        
        # Aguarda o carregamento da página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Aguarda imagens carregarem (tempo extra)
        time.sleep(3)
        
        # =========================
        # ESTRATÉGIA 1: Open Graph (via meta tags)
        # =========================
        try:
            og_image = driver.find_element(By.XPATH, "//meta[@property='og:image']")
            if og_image:
                url_imagem = og_image.get_attribute("content")
                if url_imagem and url_imagem.startswith("http"):
                    logger.info(f"✅ Imagem via OG (Selenium): {url_imagem[:50]}...")
                    return url_imagem
        except:
            pass
        
        # =========================
        # ESTRATÉGIA 2: Twitter Card
        # =========================
        try:
            tw_image = driver.find_element(By.XPATH, "//meta[@property='twitter:image']")
            if tw_image:
                url_imagem = tw_image.get_attribute("content")
                if url_imagem and url_imagem.startswith("http"):
                    logger.info(f"✅ Imagem via Twitter (Selenium): {url_imagem[:50]}...")
                    return url_imagem
        except:
            pass
        
        # =========================
        # ESTRATÉGIA 3: Imagens do produto (JavaScript)
        # =========================
        # Usa JavaScript para encontrar imagens grandes
        script_js = """
        function encontrarImagemProduto() {
            // Pega todas as imagens
            const imagens = document.querySelectorAll('img');
            const imagensFiltradas = [];
            
            // Filtra imagens grandes (mais de 200px)
            for (let img of imagens) {
                const width = img.naturalWidth || img.width || 0;
                const height = img.naturalHeight || img.height || 0;
                
                // Ignora logos, ícones, etc.
                const src = img.src || '';
                if (src.includes('logo') || src.includes('icon') || src.includes('avatar')) {
                    continue;
                }
                
                // Se for grande, considera
                if (width > 200 || height > 200) {
                    imagensFiltradas.push({
                        src: src,
                        width: width,
                        height: height,
                        area: width * height
                    });
                }
            }
            
            // Ordena por área (maior primeiro)
            imagensFiltradas.sort((a, b) => b.area - a.area);
            
            // Retorna a maior imagem
            if (imagensFiltradas.length > 0) {
                return imagensFiltradas[0].src;
            }
            return null;
        }
        return encontrarImagemProduto();
        """
        
        url_imagem = driver.execute_script(script_js)
        if url_imagem and url_imagem.startswith("http"):
            logger.info(f"✅ Imagem via JavaScript (Selenium): {url_imagem[:50]}...")
            return url_imagem
        
        # =========================
        # ESTRATÉGIA 4: CSS Selectors
        # =========================
        selectores = [
            "img[class*='product-image']",
            "img[class*='main-image']",
            "img[class*='product-img']",
            "img[class*='produto']",
            "img[itemprop='image']",
            "img[data-testid='product-image']",
            "img[data-image]",
            "img[class*='product-card']",
            "img[class*='product']",
            "img[class*='image']",
            "img[class*='photo']",
        ]
        
        for selector in selectores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    url_imagem = elemento.get_attribute("src") or elemento.get_attribute("data-src")
                    if url_imagem and url_imagem.startswith("http"):
                        # Ignora imagens pequenas
                        if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                            logger.info(f"✅ Imagem via CSS (Selenium): {url_imagem[:50]}...")
                            return url_imagem
            except:
                pass
        
        # =========================
        # ESTRATÉGIA 5: Regex no HTML renderizado
        # =========================
        html = driver.page_source
        padroes = [
            r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\']*)?',
            r'https?://[^\s"\']+product[^\s"\']+\.(?:jpg|jpeg|png|webp)',
            r'https?://[^\s"\']+image[^\s"\']+\.(?:jpg|jpeg|png|webp)',
        ]
        
        for padrao in padroes:
            matches = re.findall(padrao, html, re.IGNORECASE)
            for url_imagem in matches:
                if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                    if "thumbnail" not in url_imagem.lower():
                        logger.info(f"✅ Imagem via Regex (Selenium): {url_imagem[:50]}...")
                        return url_imagem
        
        logger.warning("⚠️ Nenhuma imagem encontrada com Selenium")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro no Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            logger.info("🔒 Driver Selenium fechado")

def extrair_imagem(link: str):
    """Extrai imagem do produto - PRIORIDADE: Selenium + fallback BeautifulSoup"""
    
    # =========================
    # TENTATIVA 1: Selenium (renderiza JavaScript)
    # =========================
    logger.info(f"📸 Tentando Selenium para: {link}")
    imagem = extrair_imagem_com_selenium(link)
    
    if imagem:
        logger.info(f"✅ Imagem encontrada com Selenium: {imagem[:50]}...")
        return imagem
    
    # =========================
    # TENTATIVA 2: BeautifulSoup (fallback)
    # =========================
    logger.info(f"🔍 Fallback: BeautifulSoup para: {link}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Open Graph
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            url_imagem = og_image["content"]
            if url_imagem.startswith("http"):
                logger.info(f"✅ Imagem via OG (fallback): {url_imagem[:50]}...")
                return url_imagem
        
        # Twitter Card
        tw_image = soup.find("meta", property="twitter:image")
        if tw_image and tw_image.get("content"):
            url_imagem = tw_image["content"]
            if url_imagem.startswith("http"):
                logger.info(f"✅ Imagem via Twitter (fallback): {url_imagem[:50]}...")
                return url_imagem
        
        # CSS Selectors
        selectores = [
            "img[class*='product-image']",
            "img[class*='main-image']",
            "img[class*='product-img']",
            "img[class*='produto']",
            "img[itemprop='image']",
        ]
        
        for selector in selectores:
            img = soup.select_one(selector)
            if img:
                url_imagem = img.get("src") or img.get("data-src")
                if url_imagem:
                    if url_imagem.startswith("http"):
                        logger.info(f"✅ Imagem via CSS (fallback): {url_imagem[:50]}...")
                        return url_imagem
                    elif url_imagem.startswith("//"):
                        url_imagem = f"https:{url_imagem}"
                        logger.info(f"✅ Imagem via CSS (fallback HTTPS): {url_imagem[:50]}...")
                        return url_imagem
        
    except Exception as e:
        logger.error(f"❌ Erro no fallback BeautifulSoup: {e}")
    
    # =========================
    # SE NADA FUNCIONOU
    # =========================
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
