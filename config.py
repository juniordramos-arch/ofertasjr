import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# VARIÁVEIS OBRIGATÓRIAS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN não configurado!")

CHANNEL_ID = os.getenv("CHANNEL_ID")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID não configurado!")

AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")
if not AWIN_API_TOKEN:
    raise ValueError("❌ AWIN_API_TOKEN não configurado!")

AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")
if not AWIN_PUBLISHER_ID:
    raise ValueError("❌ AWIN_PUBLISHER_ID não configurado!")

# =========================
# VARIÁVEIS OPCIONAIS
# =========================

PORT = os.getenv("PORT", "10000")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not WEBHOOK_URL:
    service_name = os.getenv("RENDER_SERVICE_NAME", "ofertasjr")
    WEBHOOK_URL = f"https://{service_name}.onrender.com"
    print(f"🌐 WEBHOOK_URL definido automaticamente: {WEBHOOK_URL}")

# =========================
# CONFIGURAÇÕES DO SISTEMA
# =========================

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
IMAGE_TIMEOUT = int(os.getenv("IMAGE_TIMEOUT", "15"))
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# =========================
# MAPEAMENTO AWIN
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
# LOGS
# =========================

print("=" * 50)
print("✅ CONFIGURAÇÕES CARREGADAS:")
print(f"   BOT_TOKEN: {'OK' if BOT_TOKEN else '❌'}")
print(f"   CHANNEL_ID: {'OK' if CHANNEL_ID else '❌'}")
print(f"   AWIN_API_TOKEN: {'OK' if AWIN_API_TOKEN else '❌'}")
print(f"   AWIN_PUBLISHER_ID: {'OK' if AWIN_PUBLISHER_ID else '❌'}")
print(f"   WEBHOOK_URL: {WEBHOOK_URL}")
print(f"   PORT: {PORT}")
print("=" * 50)
