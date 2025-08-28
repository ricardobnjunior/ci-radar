import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
MODEL_ID = os.getenv("MODEL_ID", "gpt-4o-mini")

# ---- OpenRouter ----
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/openai/gpt-4o-mini")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_SITE = os.getenv("OPENROUTER_SITE", "")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "ci-radar")

# Crawling defaults
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "20"))
USER_AGENT = os.getenv("USER_AGENT", "ci-radar/0.1 (+https://example.com)")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "ci_radar_output.csv")
