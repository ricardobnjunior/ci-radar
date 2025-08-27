from __future__ import annotations
import html
import json
import re
from typing import Any, Dict
from bs4 import BeautifulSoup

def clean_html(html_text):
    """Extract readable text from HTML."""

    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def parse_jsonish(text):
    """Extract first JSON object from model output safely."""

    fence = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    raw = fence.group(1) if fence else None
    if not raw:
        brace = re.search(r"\{.*\}", text, flags=re.DOTALL)
        raw = brace.group(0) if brace else None
    if not raw:
        raise ValueError("No JSON found.")
    try:
        return json.loads(raw)
    except Exception:
        fixed = re.sub(r"(\w+):", r'"\1":', raw)
        return json.loads(fixed)
