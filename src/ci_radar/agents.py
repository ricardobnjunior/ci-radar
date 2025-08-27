from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from langchain.text_splitter import RecursiveCharacterTextSplitter
from .llm import LLMClient
from .settings import SETTINGS, logger
from .utils import parse_jsonish
from .web_tools import web_search, web_read

@dataclass
class PageDoc:
    url: str
    title: str
    snippet: str
    content: str

class PlannerAgent:
    """Decomposes the user query into 3–7 sub-queries + criteria."""
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def plan(self, query: str) -> Tuple[List[str], str]:
        sys = (
            "You are a planning agent that decomposes a user query into 3–7 effective web search sub-queries. "
            "Return STRICT JSON: {\"subtasks\": [\"...\"], \"relevance_criteria\": \"...\"}."
        )
        usr = (
            f"PLANNER_JSON\nUser query: {query}\n"
            "- Generate 3–7 concise, distinct sub-queries (<=12 words each)\n"
            "- Include recent developments and competitive landscape\n"
            "- Provide a one-line relevance_criteria\n"
            "Return STRICT JSON only."
        )
        out = self.llm.chat([{"role": "system", "content": sys}, {"role": "user", "content": usr}])
        try:
            data = parse_jsonish(out)
            subs = [s.strip() for s in data.get("subtasks", []) if isinstance(s, str) and s.strip()]
            crit = str(data.get("relevance_criteria", "")).strip()
        except Exception:
            logger.debug("Planner JSON parse failed; using fallback.")
            subs = [query, f"{query} latest", f"{query} competitors", f"{query} risks", f"{query} opportunities"][:5]
            crit = "Prefer recent, authoritative, non-spam pages."
        subs = subs[:7]
        if len(subs) < 3:
            subs += [f"{query} overview", f"{query} pricing"]
            subs = subs[:3]
        return subs, crit

class BrowserAgent:
    """Searches and reads the web; returns curated PageDocs."""
    def __init__(self):
        pass

    def browse(self, queries: List[str]) -> List[PageDoc]:
        collected: Dict[str, PageDoc] = {}
        total_pages = 0
        for q in queries:
            if total_pages >= SETTINGS.max_total_pages:
                break
            results = web_search(q, k=SETTINGS.search_top_k)
            urls = [r["url"] for r in results][: SETTINGS.max_pages_per_query]
            pages = web_read(urls)
            for p in pages:
                if total_pages >= SETTINGS.max_total_pages:
                    break
                if not p.get("content") or len(p["content"]) < 400:
                    continue
                if p["url"] not in collected:
                    collected[p["url"]] = PageDoc(
                        url=p["url"], title=p.get("title", p["url"])[:300], snippet=p.get("snippet", "")[:400], content=p["content"]
                    )
                    total_pages += 1
        return list(collected.values())

class AnalystAgent:
    """Synthesizes concise bullets and attaches citations."""
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=150)

    @staticmethod
    def _quick_quotes(bullet: str, docs: List[PageDoc], limit: int = 2) -> List[str]:
        quotes: List[str] = []
        normalized = bullet.lower().split()[:6]
        for d in docs:
            sentences = re.split(r"(?<=[\.\!\?])\s+", d.content)
            for s in sentences:
                hit = sum(1 for w in normalized if w in s.lower())
                if hit >= max(2, len(normalized) // 2):
                    quotes.append(f"{d.url} :: {s.strip()}")
                    if len(quotes) >= limit:
                        return quotes
        for d in docs:  # fallback
            snippet = d.content.strip().split("\n", 3)[0][:300]
            quotes.append(f"{d.url} :: {snippet}")
            if len(quotes) >= limit:
                break
        return quotes

    def analyze(self, query: str, docs: List[PageDoc]) -> Dict[str, Any]:
        joined_sources = "\n".join([f"- {d.title} ({d.url})" for d in docs[:12]])
        condensed = "\n\n".join([d.content[:1500] for d in docs[:6]])

        sys = (
            "You are an analyst that produces action-oriented bullet points from multiple web sources. "
            "Cross-check claims. Return STRICT JSON: {\"bullets\": [\"...\"], \"citations\": {}} "
            "Bullets <= 25 words, factual, useful."
        )
        usr = (
            f"ANALYST_JSON\nUser query: {query}\n\nSources:\n{joined_sources}\n\n"
            f"Content excerpts:\n{condensed}\n\n"
            "Requirements:\n- 5–8 bullets\n- Prefer claims supported by ≥2 sources\n- Return STRICT JSON only"
        )
        out = self.llm.chat([{"role": "system", "content": sys}, {"role": "user", "content": usr}])

        try:
            data = parse_jsonish(out)
            bullets = [b.strip() for b in data.get("bullets", []) if isinstance(b, str) and b.strip()]
        except Exception:
            logger.debug("Analyst JSON parse failed; using heuristic bullets.")
            bullets = []
            for d in docs[:8]:
                t = re.sub(r"\s+", " ", d.title).strip()
                if t and t not in bullets:
                    bullets.append(t)
                if len(bullets) >= 6:
                    break

        citations: Dict[str, List[str]] = {}
        for b in bullets:
            citations[b] = self._quick_quotes(b, docs, limit=2)

        return {
            "bullets": bullets,
            "citations": citations,
            "sources": [{"url": d.url, "title": d.title} for d in docs]
        }
