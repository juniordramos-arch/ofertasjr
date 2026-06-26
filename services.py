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
    """Extrai preço usando fallback por domínio"""
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
    """Extrai benefício usando fallback por domínio"""
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
# FUNÇÃO: BUSCAR IMAGEM NO BING (GRATUITO)
# =========================

def buscar_imagem_bing(titulo: str):
    """Busca imagem no Bing Images (gratuito, sem chave)"""
    try:
        # Limpa o título
        titulo_busca = titulo.replace("Tenis", "Tênis").replace("Masculino", "").replace("Feminino", "").strip()
        query = urllib.parse.quote(f"{titulo_busca} produto")
        
        # API do Bing (gratuita)
        bing_url = f"https://www.bing.com/images/search?q={query}&form=HDRSC3"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        response = requests.get(bing_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Busca imagens no Bing
            # O Bing usa imagens com classe "mimg"
            imagens = soup.find_all("img", {"class": "mimg"})
            for img in imagens:
                src = img.get("src")
                if src and src.startswith("https") and "logo" not in src.lower():
                    # Baixa a imagem
                    img_response = requests.get(src, headers=headers, timeout=15)
                    if img_response.status_code == 200:
                        # Salva a imagem
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        temp_file.write(img_response.content)
                        temp_file.close()
                        
                        # Verifica se é uma imagem válida
                        try:
                            img_verify = Image.open(temp_file.name)
                            img_verify.verify()
                            logger.info(f"✅ Imagem via Bing: {src[:50]}...")
                            return temp_file.name
                        except:
                            os.remove(temp_file.name)
                            continue
            
            # Fallback: tenta outro seletor
            imagens = soup.find_all("img", {"class": "img_cont"})
            for img in imagens:
                src = img.get("src")
                if src and src.startswith("https") and "logo" not in src.lower():
                    img_response = requests.get(src, headers=headers, timeout=15)
                    if img_response.status_code == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        temp_file.write(img_response.content)
                        temp_file.close()
                        try:
                            img_verify = Image.open(temp_file.name)
                            img_verify.verify()
                            logger.info(f"✅ Imagem via Bing (fallback): {src[:50]}...")
                            return temp_file.name
                        except:
                            os.remove(temp_file.name)
                            continue
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar imagem no Bing: {e}")
        return None

# =========================
# FUNÇÃO: BUSCAR IMAGEM NO WIKIMEDIA (FALLBACK)
# =========================

def buscar_imagem_wikimedia(titulo: str):
    """Busca imagem no Wikimedia Commons (gratuito)"""
    try:
        query = urllib.parse.quote(titulo)
        wikimedia_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
        
        response = requests.get(wikimedia_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "query" in data and "search" in data["query"]:
                for resultado in data["query"]["search"]:
                    titulo_imagem = resultado["title"]
                    # Pega a URL da imagem
                    image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{titulo_imagem}"
                    return image_url
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar imagem no Wikimedia: {e}")
        return None

# =========================
# FUNÇÃO: EXTRAIR IMAGEM (PRINCIPAL)
# =========================

def extrair_imagem(link: str):
    """Extrai imagem do produto (prioridade: Bing, fallback: None)"""
    
    # Gera o título para busca
    titulo = gerar_titulo(link)
    
    # 1. Tenta buscar a imagem no Bing
    imagem = buscar_imagem_bing(titulo)
    
    # 2. Se falhou, tenta Wikimedia
    if not imagem:
        logger.info("🔄 Bing falhou, tentando Wikimedia...")
        imagem = buscar_imagem_wikimedia(titulo)
    
    # 3. Se ainda falhou, retorna None
    if not imagem:
        logger.error("❌ Nenhuma imagem encontrada")
    
    # Extrai preço e benefício
    preco = extrair_preco(link)
    beneficio = extrair_beneficio(link)
    
    return imagem, preco, beneficio
