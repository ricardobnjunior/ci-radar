from utils import save_csv
from settings import OUTPUT_CSV

PROMPT = """
You are the Planner of the Competitive Intelligence Radar.

Goal: find recent updates on competitors' pricing and release notes (2–3 sources).
Steps:
1) Use DuckDuckGoSearchTool to find official pages (pricing, release notes, blog).
2) For each page: use http_get to fetch HTML.
3) Extract items with parse_titles using selectors like 'h2 a', 'article h2 a', 'h3 a'.
4) Merge and dedup results with dedup.
5) Return a short Markdown summary (5 bullets) and a compact JSON with the first 15 items.
6) Print: SAVE_CSV=<rows> when you have the list of rows to persist.

Constraints:
- Keep outputs concise. Titles + links are enough if dates aren't obvious.
"""

def run_ci(agent):
    result = agent.run(PROMPT)
    # Capture rows printed as JSON inside the result (simple heuristic)
    rows = []
    try:
        import re, json
        m = re.search(r"SAVE_CSV=(\[.*\])", result, re.DOTALL)
        if m:
            rows = json.loads(m.group(1))
    except Exception:
        pass
    if rows:
        print(save_csv(rows, OUTPUT_CSV))
    return result
