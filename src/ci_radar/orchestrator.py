from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from urllib.parse import urlparse

from langgraph.graph import StateGraph, END
from .settings import SETTINGS, logger
from .llm import LLMClient
from .agents import PlannerAgent, BrowserAgent, AnalystAgent, PageDoc

class RadarState(TypedDict, total=False):
    query: str
    tasks: List[str]
    relevance_criteria: str
    raw_pages: List[Dict[str, Any]]
    summary: Dict[str, Any]
    coverage: float
    browse_iterations: int
    errors: List[str]

class Orchestrator:
    """LangGraph pipeline: plan → browse (repeat) → analyze → done."""
    def __init__(self):
        self.llm = LLMClient()
        self.planner = PlannerAgent(self.llm)
        self.browser = BrowserAgent()
        self.analyst = AnalystAgent(self.llm)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(RadarState)

        def plan_node(state: RadarState) -> RadarState:
            try:
                tasks, criteria = self.planner.plan(state["query"])
                state["tasks"] = tasks
                state["relevance_criteria"] = criteria
                state.setdefault("errors", [])
                state.setdefault("browse_iterations", 0)
                logger.info(f"Planner: {len(tasks)} subtasks.")
            except Exception as e:
                state.setdefault("errors", []).append(f"plan_error:{e}")
                logger.exception("Planner failed.")
            return state

        def browse_node(state: RadarState) -> RadarState:
            try:
                tasks = state.get("tasks", [state["query"]])
                docs = self.browser.browse(tasks)
                state["raw_pages"] = [{"url": d.url, "title": d.title, "snippet": d.snippet, "content": d.content} for d in docs]
                domains = {urlparse(d["url"]).netloc for d in state["raw_pages"]}
                denom = max(3, len(tasks))
                state["coverage"] = min(1.0, len(domains) / float(denom))
                state["browse_iterations"] = int(state.get("browse_iterations", 0)) + 1
                logger.info(f"Browser: {len(docs)} pages / {len(domains)} domains. coverage={state['coverage']:.2f}")
            except Exception as e:
                state.setdefault("errors", []).append(f"browse_error:{e}")
                logger.exception("Browser failed.")
            return state

        def analyze_node(state: RadarState) -> RadarState:
            try:
                docs = [PageDoc(**d) for d in state.get("raw_pages", [])]
                summary = self.analyst.analyze(state["query"], docs)
                state["summary"] = summary
                logger.info(f"Analyst: {len(summary.get('bullets', []))} bullets.")
            except Exception as e:
                state.setdefault("errors", []).append(f"analyze_error:{e}")
                logger.exception("Analyst failed.")
            return state

        graph.add_node("plan", plan_node)
        graph.add_node("browse", browse_node)
        graph.add_node("analyze", analyze_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "browse")

        def need_more_browse(state: RadarState) -> str:
            coverage = float(state.get("coverage", 0.0))
            iters = int(state.get("browse_iterations", 0))
            if coverage < SETTINGS.coverage_threshold and iters < SETTINGS.max_browse_iterations:
                # Português (curto): re-busca se cobertura baixa, com limite de iterações
                logger.info(f"Coverage {coverage:.2f} < threshold {SETTINGS.coverage_threshold:.2f} → re-browse (iter {iters}).")
                return "browse"
            return "analyze"

        graph.add_conditional_edges("browse", need_more_browse, {"browse": "browse", "analyze": "analyze"})
        graph.add_edge("analyze", END)
        return graph.compile()

    def run(self, query: str) -> Dict[str, Any]:
        initial: RadarState = {"query": query}
        final: RadarState = self.graph.invoke(initial)

        tasks = final.get("tasks", [])
        summary = final.get("summary", {}) or {}
        sources = summary.get("sources", [])
        bullets = summary.get("bullets", [])
        citations = summary.get("citations", {})
        errors = final.get("errors", [])
        relevance = final.get("relevance_criteria", "")

        return {
            "query": query,
            "subtasks": tasks,
            "relevance_criteria": relevance,
            "sources": [{"url": s.get("url", ""), "title": s.get("title", "")} for s in sources],
            "summary_bullets": bullets,
            "cross_citations": citations,
            "errors": errors,
        }
