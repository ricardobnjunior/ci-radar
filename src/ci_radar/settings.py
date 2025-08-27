from __future__ import annotations
import logging
from pydantic import BaseSettings, Field, validator
from typing import Literal, Optional

DEFAULT_USER_AGENT = "CI-Radar/0.1 (+https://example.com/contact)"

class Settings(BaseSettings):
    # LLM
    model_provider = Field(default="openai", env="MODEL_PROVIDER")
    openai_api_key = Field(default=None, env="OPENAI_API_KEY")
    openai_model = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    # Search/crawl
    search_top_k = Field(default=5, env="SEARCH_TOP_K")
    max_pages_per_query = Field(default=3, env="MAX_PAGES_PER_QUERY")
    max_total_pages = Field(default=10, env="MAX_TOTAL_PAGES")
    http_timeout = Field(default=15, env="HTTP_TIMEOUT")
    rate_limit_seconds = Field(default=1.0, env="RATE_LIMIT_SECONDS")
    cache_ttl_seconds = Field(default=3600, env="CACHE_TTL_SECONDS")
    enable_robots_txt: bool = Field(default=True, env="ENABLE_ROBOTS_TXT")

    # Guards
    user_agent = Field(default=DEFAULT_USER_AGENT, env="USER_AGENT")
    allowed_domains = Field(default=None, env="ALLOWED_DOMAINS")
    coverage_threshold = Field(default=0.6, env="COVERAGE_THRESHOLD")
    max_browse_iterations = Field(default=2, env="MAX_BROWSE_ITERATIONS")

    # Logging
    log_level = Field(default="INFO", env="LOG_LEVEL")

    @validator("allowed_domains")
    def normalize_domains(cls, v):
        if v is None:
            return None
        cleaned = ",".join(sorted({d.strip().lower() for d in v.split(",") if d.strip()}))
        return cleaned if cleaned else None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

SETTINGS = Settings()
logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ci_radar")
