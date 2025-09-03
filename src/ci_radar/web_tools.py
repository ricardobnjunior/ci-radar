from smolagents import tool, DuckDuckGoSearchTool, VisitWebpageTool
import requests
from bs4 import BeautifulSoup
from settings import HTTP_TIMEOUT, USER_AGENT
from utils import stable_key
from goose3 import Goose
import time
import random

@tool
def extract_specs_from_search(search_results: list[dict[str, str]] | str) -> list[dict[str, str | None]]:
    """
    Extracts laptop specs from search result snippets when direct scraping fails.

    Args:
        search_results: Either a list of DuckDuckGo result dicts (with keys like 'title'/'snippet')
                        or a newline-joined string of snippets/titles.

    Returns:
        A list of JSON-serializable dicts with keys: text, cpu, gpu, ram, price.
    """
    import re

    lines: list[str] = []
    if isinstance(search_results, list):
        # DDG costuma retornar lista de dicts com 'title'/'link'/'snippet'
        for it in search_results:
            if not isinstance(it, dict):
                continue
            for k in ("title", "snippet"):
                v = it.get(k)
                if isinstance(v, str):
                    lines.append(v)
    elif isinstance(search_results, str):
        lines = search_results.split("\n")

    cpu_pat = r'(Intel Core i[3579]-[\w\-]+|AMD Ryzen [3579]\s*\w+|M[1-4]\s*(Pro|Max)?)'
    gpu_pat = r'(RTX \d{4}|GTX \d{4}|Radeon \w+|Intel Iris|M[1-4]\s*GPU)'
    ram_pat = r'(\d+\s*GB (RAM|memory))'
    price_pat = r'(\$[\d,]+)'

    out: list[dict[str, str | None]] = []
    for line in lines:
        low = line.lower()
        if any(w in low for w in ["laptop", "notebook", "macbook"]):
            cpu = re.search(cpu_pat, line)
            gpu = re.search(gpu_pat, line)
            ram = re.search(ram_pat, line)
            price = re.search(price_pat, line)
            out.append({
                "text": line[:500],
                "cpu": cpu.group(0) if cpu else None,
                "gpu": gpu.group(0) if gpu else None,
                "ram": ram.group(0) if ram else None,
                "price": price.group(0) if price else None,
            })
    return out




@tool
def http_get(url: str) -> str:
    """
    Browser-like HTTP GET with gentle anti-bot behavior.

    Args:
        url (str): Absolute HTTP/HTTPS URL to fetch.

    Returns:
        str: The HTML text (UTF-8). Returns "ACCESS_BLOCKED" on bot-protection
             hints (e.g., CAPTCHA/403/429/Cloudflare) or "ERROR: <message>" on failures.
    """
    import time
    import random
    from urllib.parse import urlparse
    import requests

    # Jitter para parecer humano
    time.sleep(random.uniform(1.0, 2.5))

    parsed = urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else None

    headers: dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        # Evite 'br' se brotli não estiver instalado
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        headers["Referer"] = referer

    retry_statuses = {429, 500, 502, 503, 504}
    backoffs = [0.0, 1.0, 2.0]  # até 3 tentativas

    for attempt, wait in enumerate(backoffs, start=1):
        if wait:
            time.sleep(wait + random.uniform(0.0, 0.5))
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT, headers=headers)
            if r.status_code == 403:
                return "ACCESS_BLOCKED"
            if r.status_code in retry_statuses and attempt < len(backoffs):
                # tenta novamente com backoff
                continue
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            text = r.text

            # Detecção simples de CAPTCHA/bot-protection
            sample = text[:4000].lower()
            if any(token in sample for token in ("captcha", "are you human", "bot protection", "cloudflare")):
                return "ACCESS_BLOCKED"

            return text
        except requests.exceptions.RequestException as e:
            if attempt < len(backoffs):
                continue
            return f"ERROR: {str(e)}"

    return "ERROR: unknown"



@tool
def parse_titles(html: str, css_selector: str) -> list:
    """
    Extracts titles and links from HTML using a CSS selector.
    Args:
        html (str): The raw HTML content of the page.
        css_selector (str): The CSS selector (e.g., 'h2 a', 'article h3 a').
    Returns:
        list[dict]: A list of items with 'title' and 'link'.
    """
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for el in soup.select(css_selector)[:200]:
        title = " ".join(el.get_text(" ", strip=True).split())
        href = el.get("href") or (el.find("a").get("href") if el.find("a") else "")
        out.append({"title": title, "link": href})
    return out

@tool
def dedup(items: list) -> list:
    """
    Deduplicates a list of items based on title+link hash.
    Args:
        items (list): List of dicts with at least 'title' and 'link'.
    Returns:
        list: A list of unique items (duplicates removed).
    """
    seen, out = set(), []
    for it in items:
        key = stable_key(it.get("title",""), it.get("link",""))
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


@tool
def search_alternative_sources(query: str) -> list[dict[str, str]]:
    """
    Search for laptop information in less-protected sources (forums, Reddit, YouTube) using DuckDuckGo.

    Args:
        query (str): Natural-language search phrase describing the laptop topic, model, or comparison.

    Returns:
        list[dict[str, str]]: A flat list of result dictionaries with normalized keys:
            - 'title': Result title (may be empty string if unavailable)
            - 'link': Absolute URL when provided by the search tool (may be empty)
            - 'snippet': Short description excerpt when available (may be empty)
    """
    alternative_queries = [
        f"site:reddit.com {query}",
        f"site:notebookreview.com {query}",
        f"laptop comparison forum {query}",
        f"youtube laptop review {query}",
    ]

    results: list[dict[str, str]] = []
    for alt_query in alternative_queries:
        try:
            search_tool = DuckDuckGoSearchTool()
            alt_results = search_tool(alt_query)  # typically a list of dicts
            if isinstance(alt_results, list):
                for item in alt_results:
                    if isinstance(item, dict):
                        title = str(item.get("title", "")).strip()
                        link = str(item.get("link", "")).strip()
                        snippet = str(item.get("snippet", "")).strip()
                        if title or link or snippet:
                            results.append({"title": title, "link": link, "snippet": snippet})
        except Exception:
            # ignore individual query failures and continue with the next alternative query
            continue

    return results
