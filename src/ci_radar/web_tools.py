from smolagents import tool, DuckDuckGoSearchTool
import requests
from bs4 import BeautifulSoup
from settings import HTTP_TIMEOUT, USER_AGENT
from utils import stable_key

def builtin_search_tool():
    """
    Searches the web using DuckDuckGo for relevant links based on a query.
    """
    return DuckDuckGoSearchTool()

@tool
def http_get(url: str) -> str:
    """
    Fetches raw HTML content from a given URL.
    Args:
        url (str): The full HTTP/HTTPS address of the page to download.
    Returns:
        str: The decoded HTML content of the page.
    """
    r = requests.get(url, timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text

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
