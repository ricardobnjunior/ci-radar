from smolagents import CodeAgent
from llm import get_model
from web_tools import builtin_search_tool, http_get, parse_titles, dedup

def make_ci_agent():
    model = get_model()
    print(model)
    tools = [builtin_search_tool(), http_get, parse_titles, dedup]

    return CodeAgent(
        tools=tools,
        model=model,
        additional_authorized_imports=["hashlib","csv","json","re","datetime"]
    )
