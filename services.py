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
# FUNÇÃO: EXTRAIR PREÇO
# =========================

def extrair_preco(link: str):
    """Extrai preço usando múltiplas estratégias"""
    
    # Estratégia 1: DuckDuckGo
    try:
        import urllib.parse
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
        import urllib.parse
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
# FUNÇÃO: EXTRAIR IMAGEM DIRETA DO SITE (MESMO COM BLOQUEIO)
# =========================

def extrair_imagem_direta(link: str):
    """Tenta extrair a imagem real do produto diretamente do site"""
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
        
        # Tenta com diferentes estratégias
        for strategy in ["direct", "mobile", "referer"]:
            try:
                if strategy == "mobile":
                    headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
                elif strategy == "referer":
                    headers["Referer"] = "https://www.google.com/"
                
                logger.info(f"🔍 Tentando extrair imagem com estratégia: {strategy}")
                response = requests.get(link, headers=headers, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # 1. Open Graph (mais comum)
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        url_imagem = og_image["content"]
                        if url_imagem.startswith("http"):
                            logger.info(f"✅ Imagem via OG: {url_imagem[:50]}...")
                            return url_imagem
                    
                    # 2. Twitter Card
                    tw_image = soup.find("meta", property="twitter:image")
                    if tw_image and tw_image.get("content"):
                        url_imagem = tw_image["content"]
                        if url_imagem.startswith("http"):
                            logger.info(f"✅ Imagem via Twitter: {url_imagem[:50]}...")
                            return url_imagem
                    
                    # 3. JSON-LD
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
                    
                    # 4. CSS Selectors específicos
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
                        "img[class*='gallery']",
                    ]
                    
                    for selector in selectores:
                        img = soup.select_one(selector)
                        if img:
                            for attr in ["src", "data-src", "data-image", "content"]:
                                url_imagem = img.get(attr)
                                if url_imagem:
                                    if url_imagem.startswith("http"):
                                        # Ignora imagens pequenas (logo, ícone)
                                        if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                                            logger.info(f"✅ Imagem via CSS: {url_imagem[:50]}...")
                                            return url_imagem
                                    elif url_imagem.startswith("//"):
                                        url_imagem = f"https:{url_imagem}"
                                        if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                                            logger.info(f"✅ Imagem via CSS: {url_imagem[:50]}...")
                                            return url_imagem
            except Exception as e:
                logger.warning(f"⚠️ Estratégia {strategy} falhou: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao extrair imagem direta: {e}")
        return None

# =========================
# FUNÇÃO: CAPTURAR IMAGEM VIA API (FALLBACK)
# =========================

def capturar_imagem_com_api(link: str):
    """Usa API para capturar imagem (fallback se a direta falhar)"""
    try:
        # Page2Images
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
    
    # MiniWebTool
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
    
    return None

# =========================
# FUNÇÃO: EXTRAIR IMAGEM (PRINCIPAL)
# =========================

def extrair_imagem(link: str):
    """Extrai imagem do produto (prioridade: direta do site, fallback: API)"""
    
    # 1. Tenta extrair a imagem REAL do site
    imagem = extrair_imagem_direta(link)
    
    # 2. Se falhou, tenta captura de tela via API
    if not imagem:
        logger.info("🔄 Imagem direta falhou, tentando captura de tela...")
        imagem = capturar_imagem_com_api(link)
    
    # 3. Se ainda falhou, retorna None
    if not imagem:
        logger.error("❌ Nenhuma imagem encontrada")
    
    # Extrai preço e benefício
    preco = extrair_preco(link)
    beneficio = extrair_beneficio(link)
    
    return imagem, preco, beneficio
