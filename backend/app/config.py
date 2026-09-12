import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
STORAGE = os.getenv("STORAGE", "memory")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://zhiguan:zhiguan@localhost:3306/zhiguan")
