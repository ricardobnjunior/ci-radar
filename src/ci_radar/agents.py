from smolagents import tool, DuckDuckGoSearchTool, VisitWebpageTool
from smolagents import CodeAgent
from llm import get_model
from web_tools import http_get, parse_titles, dedup, extract_specs_from_search, search_alternative_sources
from bs4 import BeautifulSoup

def make_ci_agent():
    model = get_model()
    print(model)
    tools = [DuckDuckGoSearchTool(), http_get, parse_titles, dedup, VisitWebpageTool(), extract_specs_from_search, search_alternative_sources]

    return CodeAgent(
        tools=tools,
        model=model,
        additional_authorized_imports=["hashlib", "csv", "json", "re", "datetime", "time", "random", "markdownify"]

    )
