from __future__ import annotations
import time
import re
import requests
import urllib.robotparser as robotparser
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from duckduckgo_search import DDGS
from .settings import SETTINGS, logger
from .utils import clean_html

SAFE_SCHEMES = {"http", "https"}
DEFAULT_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

class RateLimiter:
    def __init__(self, min_interval):
        self.min_interval = max(0.0, float(min_interval))
        self._last = 0.0

    def wait(self):
        now = time.time()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.time()

class TTLCache:
    def __init__(self, ttl_seconds):
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def get(self, key):
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key, value):
        self._store[key] = (time.time(), value)

RATE_LIMITER = RateLimiter(SETTINGS.rate_limit_seconds)
PAGE_CACHE = TTLCache(SETTINGS.cache_ttl_seconds)
ROBOTS_CACHE: Dict[str, robotparser.RobotFileParser] = {}

def canonicalize_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in SAFE_SCHEMES:
            return None
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        return urlunparse((parsed.scheme.lower(), netloc, path, "", parsed.query, ""))
    except Exception:
        return None

def is_allowed_domain(url, csv_allow: Optional[str]):
    if not csv_allow:
        return True
    try:
        allowed = {d.strip() for d in csv_allow.split(",") if d.strip()}
        domain = urlparse(url).netloc.lower()
        return any(domain == d or domain.endswith("." + d) for d in allowed)
    except Exception:
        return False

def get_robots_parser(url):
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base in ROBOTS_CACHE:
            return ROBOTS_CACHE[base]
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            RATE_LIMITER.wait()
            rp.read()
        except Exception:
            pass
        ROBOTS_CACHE[base] = rp
        return rp
    except Exception:
        return None

def allowed_by_robots(url, user_agent):
    if not SETTINGS.enable_robots_txt:
        return True
    rp = get_robots_parser(url)
    if rp is None:
        return True
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((requests.RequestException,))
)
def http_get(url, headers: Dict[str, str], timeout: int):
    RATE_LIMITER.wait()
    return requests.get(url, headers=headers, timeout=timeout)

def web_search(query, k):
    """DuckDuckGo-only (no API key)."""
    results = []
    try:
        with DDGS() as ddgs:
            RATE_LIMITER.wait()
            for hit in ddgs.text(query, max_results=k):
                url = hit.get("href") or hit.get("url")
                title = hit.get("title") or url
                body = hit.get("body") or ""
                if not url:
                    continue
                can = canonicalize_url(url)
                if not can:
                    continue
                results.append({"url": can, "title": title, "snippet": body})
    except Exception as e:
        logger.debug(f"DuckDuckGo search failed: {e}")
    # Dedup canonical URLs
    seen, deduped = set(), []
    for r in results:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        deduped.append(r)
    return deduped

def web_read(urls):
    """Requests + BS4 with robots.txt respect and caching."""
    out: List[Dict[str, Any]] = []
    for url in urls:
        can_url = canonicalize_url(url)
        if not can_url:
            continue
        if not is_allowed_domain(can_url, SETTINGS.allowed_domains):
            continue
        if not allowed_by_robots(can_url, SETTINGS.user_agent):
            logger.debug(f"Blocked by robots.txt: {can_url}")
            continue

        cached = PAGE_CACHE.get(can_url)
        if cached:
            out.append(cached)
            continue

        try:
            headers = {**DEFAULT_HEADERS, "User-Agent": SETTINGS.user_agent}
            resp = http_get(can_url, headers=headers, timeout=SETTINGS.http_timeout)
            resp.raise_for_status()
            content = clean_html(resp.text)
            if len(content) < 400:  # filtro de qualidade
                continue
            # naive title
            title = re.search(r"<title[^>]*>(.*?)</title>", resp.text, flags=re.IGNORECASE | re.DOTALL)
            title_text = title.group(1).strip() if title else can_url
            item = {
                "url": can_url,
                "title": title_text[:300],
                "snippet": content[:400].replace("\n", " "),
                "content": content
            }
            PAGE_CACHE.set(can_url, item)
            out.append(item)
        except Exception as e:
            logger.debug(f"Read error {can_url}: {e}")
    return out
