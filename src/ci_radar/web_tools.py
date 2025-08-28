from smolagents import tool, DuckDuckGoSearchTool
import requests
from bs4 import BeautifulSoup
from .settings import HTTP_TIMEOUT, USER_AGENT
from .utils import stable_key

def builtin_search_tool():
    return DuckDuckGoSearchTool()

@tool
def http_get(url: str) -> str:
    r = requests.get(url, timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text

@tool
def parse_titles(html: str, css_selector: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for el in soup.select(css_selector)[:200]:
        title = " ".join(el.get_text(" ", strip=True).split())
        href = el.get("href") or (el.find("a").get("href") if el.find("a") else "")
        out.append({"title": title, "link": href})
    return out

@tool
def dedup(items: list) -> list:
    seen, out = set(), []
    for it in items:
        key = stable_key(it.get("title",""), it.get("link",""))
        if key not in seen:
            seen.add(key); out.append(it)
    return out
