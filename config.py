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

# =========================
# LOGS
# =========================

print("=" * 50)
print("✅ CONFIGURAÇÕES CARREGADAS:")
print(f"   BOT_TOKEN: {'OK' if BOT_TOKEN else '❌'}")
print(f"   CHANNEL_ID: {'OK' if CHANNEL_ID else '❌'}")
print(f"   AWIN_API_TOKEN: {'OK' if AWIN_API_TOKEN else '❌'}")
print(f"   AWIN_PUBLISHER_ID: {'OK' if AWIN_PUBLISHER_ID else '❌'}")
print(f"   PORT: {PORT}")
print("=" * 50)
