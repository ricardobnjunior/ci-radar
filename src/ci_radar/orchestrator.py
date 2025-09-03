from utils import save_csv
from settings import OUTPUT_CSV

PROMPT = """
  You are the Planner of the Competitive Intelligence Radar.

Goal: Find recent updates on competitors for high-end laptops. I need a comprehensive performance and pricing comparison, including processing power (CPU), graphics (GPU), memory (RAM), battery life, and current pricing. Include links to reviews or official pages (2-3 sources).

Available Tools:
- DuckDuckGoSearchTool: Search the web for information
- http_get: Fetch raw HTML content from URLs
- parse_titles: Extract titles and links from HTML using CSS selectors
- dedup: Remove duplicate items from lists
- VisitWebpageTool: Extract main content from web pages

Steps:
1) Use DuckDuckGoSearchTool to search for "high-end laptop performance comparison 2025" and similar queries
2) From the search results, identify 3-5 reliable tech review sites
3) For each promising URL from search results:
   a) Use http_get to fetch the HTML content
   b) Use VisitWebpageTool to extract the main readable text
4) Analyze the extracted text to find:
   - Laptop models and brands
   - CPU specifications (processor names, cores, speeds)
   - GPU specifications (graphics cards, VRAM)
   - RAM amounts (8GB, 16GB, 32GB, etc.)
   - Battery life estimates (hours)
   - Current pricing information
5) Compile findings focusing on performance metrics and pricing
6) Create a summary with:
   - Markdown list of key findings (5 main points)
   - JSON array with laptop data including: model, CPU, GPU, RAM, battery_life, price, source_url
7) When ready to save data, print: SAVE_CSV=<json_array>

Important Notes:
- Search results from DuckDuckGoSearchTool come as a list, not formatted strings
- Always handle HTTP errors gracefully (403, 404, etc.)
- If a site blocks access, try alternative sources
- Extract specific model names, not just generic terms
- Include price ranges when exact prices aren't available
- Verify information across multiple sources when possible

Constraints:
- Focus on comparing CPU, GPU, RAM, battery life, and price
- Only use articles from reliable tech review sources
- Include source URLs for verification

FALLBACK STRATEGIES:
- If HTTP requests return "ACCESS_BLOCKED", skip that source and continue
- If no detailed specs are found, use general information from search results
- If fewer than 3 sources work, prioritize the available data over completeness
- Create comparison table even with partial data, marking missing fields as "N/A"

MINIMUM VIABLE OUTPUT:
Even if scraping fails, create a report with:
- At least 3 laptop models from search results
- Basic specs extracted from search snippets
- Price ranges from search descriptions
- Source links from the original search results  
"""

def run_ci(agent):
    result = agent.run(PROMPT)
    # Capture rows printed as JSON inside the result (simple heuristic)
    rows = []
    try:
        import re, json
        m = re.search(r"SAVE_CSV=(\[.*?\])", result, re.DOTALL | re.MULTILINE)
        if m:
            rows = json.loads(m.group(1))
    except Exception:
        pass
    if rows:
        print(save_csv(rows, OUTPUT_CSV))
    return result
