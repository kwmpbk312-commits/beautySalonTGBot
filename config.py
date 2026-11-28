from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("TOKEN")

DB_CONFIG = {
    "host":     getenv("DB_HOST", "localhost"),
    "port":     int(getenv("DB_PORT", "5432")),
    "database": getenv("DB_NAME", "beautySalon"),
    "user":     getenv("DB_USER", "postgres"),
    "password": getenv("DB_PASSWORD"),
}