import requests
import logging
import re
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
    """Extrai imagem do produto com múltiplas estratégias"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        logger.info(f"🔍 Buscando imagem para: {link}")
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # =========================
        # ESTRATÉGIA 1: Open Graph
        # =========================
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            url_imagem = og_image["content"]
            if url_imagem.startswith("http"):
                logger.info(f"✅ Imagem via OG: {url_imagem[:50]}...")
                return url_imagem
        
        # =========================
        # ESTRATÉGIA 2: Twitter Card
        # =========================
        tw_image = soup.find("meta", property="twitter:image")
        if tw_image and tw_image.get("content"):
            url_imagem = tw_image["content"]
            if url_imagem.startswith("http"):
                logger.info(f"✅ Imagem via Twitter: {url_imagem[:50]}...")
                return url_imagem
        
        # =========================
        # ESTRATÉGIA 3: JSON-LD (estrutura de dados)
        # =========================
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if "image" in data:
                    url_imagem = data["image"]
                    if isinstance(url_imagem, str) and url_imagem.startswith("http"):
                        logger.info(f"✅ Imagem via JSON-LD: {url_imagem[:50]}...")
                        return url_imagem
                    elif isinstance(url_imagem, list) and len(url_imagem) > 0:
                        url_imagem = url_imagem[0]
                        if url_imagem.startswith("http"):
                            logger.info(f"✅ Imagem via JSON-LD (lista): {url_imagem[:50]}...")
                            return url_imagem
            except:
                pass
        
        # =========================
        # ESTRATÉGIA 4: Imagem principal (CSS)
        # =========================
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
        ]
        
        for selector in selectores:
            img = soup.select_one(selector)
            if img:
                # Tenta vários atributos
                for attr in ["src", "data-src", "data-image", "content"]:
                    url_imagem = img.get(attr)
                    if url_imagem:
                        if url_imagem.startswith("http"):
                            logger.info(f"✅ Imagem via CSS ({attr}): {url_imagem[:50]}...")
                            return url_imagem
                        elif url_imagem.startswith("//"):
                            url_imagem = f"https:{url_imagem}"
                            logger.info(f"✅ Imagem via CSS (HTTPS): {url_imagem[:50]}...")
                            return url_imagem
        
        # =========================
        # ESTRATÉGIA 5: Buscar qualquer imagem grande
        # =========================
        images = soup.find_all("img")
        for img in images:
            url_imagem = img.get("src") or img.get("data-src")
            if url_imagem:
                if url_imagem.startswith("http") and "logo" not in url_imagem.lower():
                    # Filtra imagens muito pequenas
                    width = img.get("width")
                    if width and int(width) > 100:
                        logger.info(f"✅ Imagem via busca geral: {url_imagem[:50]}...")
                        return url_imagem
                    # Pega a primeira imagem grande
                    if "product" in url_imagem.lower() or "image" in url_imagem.lower():
                        logger.info(f"✅ Imagem via busca geral (produto): {url_imagem[:50]}...")
                        return url_imagem
        
        # =========================
        # ESTRATÉGIA 6: Regex no HTML (último recurso)
        # =========================
        html = response.text
        padroes = [
            r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\']*)?',
            r'https?://[^\s"\']+product[^\s"\']+\.(?:jpg|jpeg|png|webp)',
            r'https?://[^\s"\']+image[^\s"\']+\.(?:jpg|jpeg|png|webp)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, html, re.IGNORECASE)
            if match:
                url_imagem = match.group(0)
                if "logo" not in url_imagem.lower() and "icon" not in url_imagem.lower():
                    logger.info(f"✅ Imagem via Regex: {url_imagem[:50]}...")
                    return url_imagem
        
        # =========================
        # FALLBACK: Imagem padrão do site
        # =========================
        logger.warning("⚠️ Nenhuma imagem encontrada")
        return None
        
    except requests.Timeout:
        logger.warning("⏰ Timeout ao buscar imagem")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao extrair imagem: {e}")
        return None

def gerar_titulo(link: str):
    """Gera título a partir do link"""
    try:
        parsed = urlparse(link)
        path = parsed.path.strip("/")
        
        if not path:
            return "Produto"
        
        # Pega o último segmento
        titulo = path.split("/")[-1]
        
        # Remove extensões e caracteres especiais
        titulo = titulo.replace("-", " ").replace("_", " ").replace(".html", "").replace(".Html", "")
        
        # Remove números de ID
        import re
        titulo = re.sub(r'\d+', '', titulo)
        titulo = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', titulo)
        
        # Capitaliza
        titulo = titulo.strip().title()
        
        if not titulo or len(titulo) < 3:
            titulo = parsed.netloc.replace("www.", "").split(".")[0].title()
        
        logger.info(f"📝 Título gerado: {titulo}")
        return titulo
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar título: {e}")
        return "Produto"
