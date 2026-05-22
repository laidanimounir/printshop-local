import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SHOP_NAME = "LAIDANI PHONE"
SHOP_SLOGAN = "طباعة سريعة واحترافية"

COMPUTERS = {
    "PC1": {"ip": "192.168.1.101", "name": "Station 1", "worker": "worker1"},
    "PC2": {"ip": "192.168.1.102", "name": "Station 2", "worker": "worker2"},
    "PC3": {"ip": "192.168.1.103", "name": "Station 3", "worker": "worker3"},
    "PC4": {"ip": "192.168.1.104", "name": "Station 4", "worker": "worker4"},
}
SERVER_PORT = 5000
WIFI_SSID = "LAIDANI_PRINT"
WIFI_PASSWORD = "laidani2024"

PRICE_BW_PER_PAGE = 10
PRICE_COLOR_PER_PAGE = 30
PRICE_A3_MULTIPLIER = 2

MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "docx", "xlsx", "pptx"]
AUTO_DELETE_DAYS = 7

COLOR_PRIMARY = "#6B3F1F"
COLOR_SECONDARY = "#8B5E3C"
COLOR_ACCENT = "#F5C518"
COLOR_DARK = "#2C1A0E"
COLOR_LIGHT = "#FFF8F0"

SECRET_KEY = "laidani-printshop-secret-key-change-in-production"

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
QR_FOLDER = os.path.join(BASE_DIR, "qrcodes")
DB_PATH = os.path.join(BASE_DIR, "db", "printshop.db")
LOGS_FOLDER = os.path.join(BASE_DIR, "logs")

SUPABASE_ENABLED = False
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

UPLOAD_RATE_LIMIT = 10
