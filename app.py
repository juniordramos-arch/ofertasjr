import os
import time
import requests
from threading import Thread
from urllib.parse import urlparse

from flask import Flask
from bs4 import BeautifulSoup

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG ENV
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANEL_ID = os.getenv("CHANEL_ID")
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")
AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")

# =========================
# MEMÓRIA LOCAL
# =========================

ofertas = {}
aguardando_cupom = {}

# =========================
# AWIN MAP
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
# DETECTAR LOJA
# =========================

def detectar_advertiser(link: str):
    try:
        domain = urlparse(link).netloc.replace("www.", "")

        for key in AWIN_ADVERTISERS:
            if key in domain:
                return AWIN_ADVERTISERS[key]

        return None

    except:
        return None


# =========================
# LINK AFILIADO
# =========================

def gerar_link_afiliado(link: str):
    try:
        if not AWIN_API_TOKEN:
            return link

        advertiser_id = detectar_advertiser(link)

        if not advertiser_id:
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

        r = requests.post(url, json=payload, headers=headers, timeout=20)

        if r.status_code == 200:
            data = r.json()
            return data.get("shortUrl") or data.get("url") or link

        return link

    except Exception as e:
        print("ERRO AWIN:", e)
        return link


# =========================
# IMAGEM
# =========================

def extrair_imagem(link):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(link, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        twitter = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter and twitter.get("content"):
            return twitter["content"]

        return None

    except:
        return None


# =========================
# TÍTULO
# =========================

def gerar_titulo(link: str):
    try:
        path = urlparse(link).path
        slug = path.split("/")[-1]

        titulo = slug.replace("-", " ").replace("_", " ")
        return titulo.title() if titulo else "Produto em Oferta"

    except:
        return "Produto em Oferta"


# =========================
# FLASK KEEP ALIVE
# =========================

web_app = Flask(__name__)
