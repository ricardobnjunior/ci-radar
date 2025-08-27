# CI Radar (Competitive Intelligence Radar)

Multi-agent system (LangChain + LangGraph) to monitor competitors/market:
**Planner → Browser → Analyst**.  
Uses only one API key (OpenAI). Search/reading uses DuckDuckGo + requests+BS4 (no keys).

## Features
- PlannerAgent: 3–7 sub-queries + relevance criteria
- BrowserAgent: DuckDuckGo search, HTML fetch, robots.txt, retries, caching, rate limit
- AnalystAgent: action-oriented bullets + cross-citations (bullet → url :: excerpt)
- Orchestration: LangGraph (`plan → browse → analyze`, auto re-browse if coverage low)
- Output: JSON with subtasks, sources, bullets, citations, errors

## Setup
``` 
pip install -r requirements.txt
# Edit .env and set OPENAI_API_KEY=sk-...
```

## Run

```
python src/ci_radar/main.py --query "electric-vehicle charging market trends 2025"
```

