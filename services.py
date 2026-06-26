import requests
import logging
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
        
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Estratégia 1: Open Graph
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            url_imagem = og_image["content"]
            if url_imagem.startswith("http"):
                logger.info(f"✅ Imagem via OG: {url_imagem[:50]}...")
                return url_imagem
        
        # Estratégia 2: Twitter Card
        tw_image = soup.find("meta", property="twitter:image")
        if tw_image and tw_image.get("content"):
            url_imagem = tw_image["content"]
            if url_imagem.startswith("http"):
                logger.info(f"✅ Imagem via Twitter: {url_imagem[:50]}...")
                return url_imagem
        
        # Estratégia 3: Imagem principal do produto
        selectores = [
            "img[class*='product-image']",
            "img[class*='main-image']",
            "img[class*='product-img']",
            "img[class*='produto']",
            "img[itemprop='image']",
            "img[data-testid='product-image']"
        ]
        
        for selector in selectores:
            img = soup.select_one(selector)
            if img and img.get("src"):
                url_imagem = img["src"]
                if url_imagem.startswith("http"):
                    logger.info(f"✅ Imagem via CSS: {url_imagem[:50]}...")
                    return url_imagem
                elif url_imagem.startswith("//"):
                    url_imagem = f"https:{url_imagem}"
                    logger.info(f"✅ Imagem via CSS (HTTPS): {url_imagem[:50]}...")
                    return url_imagem
        
        logger.warning("⚠️ Nenhuma imagem encontrada")
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
