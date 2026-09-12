import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "mock")
CURRENT_TOPIC_REQUIRES_SEARCH = os.getenv("CURRENT_TOPIC_REQUIRES_SEARCH", "true").lower() == "true"
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
SEARCH_MAX_AGE_DAYS = int(os.getenv("SEARCH_MAX_AGE_DAYS", "30"))
SEARCH_TIMEOUT_SECONDS = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "10"))
AI_RETRY_ATTEMPTS = int(os.getenv("AI_RETRY_ATTEMPTS", "2"))
GENERATION_MODE = os.getenv("GENERATION_MODE", "offline")
STORAGE = os.getenv("STORAGE", "memory")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_APPSECRET = os.getenv("WECHAT_APPSECRET", "")
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/zhiguan")

if SEARCH_PROVIDER == "tavily" and not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY is required when SEARCH_PROVIDER=tavily")
