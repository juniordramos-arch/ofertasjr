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
# HEADERS AVANÇADOS
# =========================

HEADERS = {
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
        # Fallback por domínio
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
# FUNÇÃO: BAIXAR E VALIDAR IMAGEM
# =========================

def baixar_e_validar_imagem(url_imagem: str):
    """Baixa a imagem e valida se é uma imagem válida"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url_imagem, headers=headers, timeout=15)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            temp_file.write(response.content)
            temp_file.close()
            
            try:
                img = Image.open(temp_file.name)
                img.verify()
                tamanho = os.path.getsize(temp_file.name)
                if tamanho > 100:
                    logger.info(f"✅ Imagem válida: {temp_file.name}")
                    return temp_file.name
                else:
                    os.remove(temp_file.name)
                    return None
            except:
                os.remove(temp_file.name)
                return None
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao baixar imagem: {e}")
        return None

# =========================
# FUNÇÃO: CRIAR IMAGEM FALLBACK
# =========================

def criar_imagem_fallback(titulo: str):
    """Cria uma imagem genérica com o título do produto"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Cria uma imagem 800x600 com fundo gradiente
        img = Image.new('RGB', (800, 600), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Tenta usar uma fonte padrão
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                font = ImageFont.load_default()
        
        # Texto central
        texto = f"{titulo}\n\nOferta JR Pro"
        bbox = draw.textbbox((0, 0), texto, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (800 - text_width) // 2
        y = (600 - text_height) // 2
        
        # Desenha o texto
        draw.text((x, y), texto, fill='white', font=font)
        
        # Salva a imagem
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(temp_file.name, 'JPEG', quality=85)
        temp_file.close()
        
        logger.info(f"🖼️ Imagem fallback criada: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar imagem fallback: {e}")
        return None

# =========================
# FUNÇÃO: EXTRAIR IMAGEM (COM FALLBACK)
# =========================

def extrair_imagem(link: str):
    """Extrai imagem do produto com fallback garantido"""
    
    # Gera o título
    titulo = gerar_titulo(link)
    imagem = None
    
    # =========================
    # TENTA EXTRAIR IMAGEM DO SITE
    # =========================
    try:
        logger.info(f"🔍 Tentando extrair imagem de: {link}")
        
        # Tenta diferentes User-Agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        for user_agent in user_agents:
            try:
                headers = HEADERS.copy()
                headers["User-Agent"] = user_agent
                
                response = requests.get(link, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Open Graph
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        url_imagem = og_image["content"]
                        if url_imagem.startswith("http"):
                            imagem = baixar_e_validar_imagem(url_imagem)
                            if imagem:
                                break
                    
                    if not imagem:
                        # Twitter Card
                        tw_image = soup.find("meta", property="twitter:image")
                        if tw_image and tw_image.get("content"):
                            url_imagem = tw_image["content"]
                            if url_imagem.startswith("http"):
                                imagem = baixar_e_validar_imagem(url_imagem)
                                if imagem:
                                    break
                    
                    if not imagem:
                        # JSON-LD
                        script_tags = soup.find_all("script", type="application/ld+json")
                        for script in script_tags:
                            try:
                                data = json.loads(script.string)
                                if "image" in data:
                                    url_imagem = data["image"]
                                    if isinstance(url_imagem, str) and url_imagem.startswith("http"):
                                        imagem = baixar_e_validar_imagem(url_imagem)
                                        if imagem:
                                            break
                                    elif isinstance(url_imagem, list) and len(url_imagem) > 0:
                                        for img in url_imagem:
                                            if isinstance(img, str) and img.startswith("http"):
                                                imagem = baixar_e_validar_imagem(img)
                                                if imagem:
                                                    break
                            except:
                                pass
                    if imagem:
                        break
            except Exception as e:
                logger.warning(f"⚠️ Tentativa com User-Agent falhou: {e}")
    except Exception as e:
        logger.error(f"❌ Erro ao extrair imagem: {e}")
    
    # =========================
    # SE NÃO ENCONTROU, CRIA FALLBACK
    # =========================
    if not imagem:
        logger.info("🔄 Criando imagem fallback...")
        imagem = criar_imagem_fallback(titulo)
    
    # Extrai preço e benefício
    preco = extrair_preco(link)
    beneficio = extrair_beneficio(link)
    
    return imagem, preco, beneficio
