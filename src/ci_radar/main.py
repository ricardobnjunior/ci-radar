from __future__ import annotations
import argparse
import json
from .settings import SETTINGS, logger
from .orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="Competitive Intelligence Radar (multi-agent, LangChain + LangGraph)")
    parser.add_argument("--query", required=True, help="Initial business/market topic to investigate")
    args = parser.parse_args()

    # Português (curto): chave de API é lida do ambiente (.env)
    if SETTINGS.model_provider == "openai" and not SETTINGS.openai_api_key:
        logger.warning("OPENAI_API_KEY is not set. The app will fall back to a fake LLM.")

    orch = Orchestrator()
    result = orch.run(args.query)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
