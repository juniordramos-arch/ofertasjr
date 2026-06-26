import os
import logging
import requests
from urllib.parse import urlparse

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
                return value
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao detectar advertiser: {e}")
        return None

# =========================
# FUNÇÃO: GERAR LINK AFILIADO (AWIN)
# =========================

def gerar_link_afiliado(link: str):
    """
    Converte um link para link afiliado da AWIN
    """
    try:
        from config import AWIN_API_TOKEN, AWIN_PUBLISHER_ID
        
        if not AWIN_API_TOKEN or not AWIN_PUBLISHER_ID:
            logger.warning("⚠️ AWIN não configurado")
            return link
        
        advertiser_id = detectar_advertiser(link)
        if not advertiser_id:
            logger.warning(f"⚠️ Advertiser não encontrado para: {link}")
            return link
        
        url = f"https://api.awin.com/publishers/{AWIN_PUBLISHER_ID}/linkbuilder/generate"
        headers = {
            "Authorization": f"Bearer {AWIN_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "advertiserId": advertiser_id,
            "destinationUrl": link,
            "shorten": True
        }
        
        logger.info(f"🔄 Convertendo link para advertiser {advertiser_id}")
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            link_convertido = data.get("shortUrl") or link
            logger.info(f"✅ Link convertido: {link_convertido}")
            return link_convertido
        
        logger.error(f"❌ Erro AWIN: {response.status_code} - {response.text}")
        return link
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar link afiliado: {e}")
        return link
