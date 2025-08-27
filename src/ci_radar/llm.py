from __future__ import annotations
from typing import Dict, List
from .settings import SETTINGS, logger

try:
    from langchain_openai import ChatOpenAI
    _OPENAI_OK = True
except Exception:
    _OPENAI_OK = False

class LLMClient:
    """
    Minimal abstraction; exposes chat(messages).
    """

    def __init__(self):
        self.provider = SETTINGS.model_provider
        self.client = None

        if self.provider == "openai" and SETTINGS.openai_api_key and _OPENAI_OK:
            # Env var OPENAI_API_KEY is used by langchain-openai internally.
            self.client = ChatOpenAI(model=SETTINGS.openai_model, temperature=0.2, timeout=60)
            logger.info("LLM: Using OpenAI via langchain-openai.")
        else:
            self.provider = "fake"
            logger.warning("LLM: Using FAKE fallback (rule-based). Set OPENAI_API_KEY to enable OpenAI.")

    def chat(self, messages):
        """
        messages = [{"role": "system"|"user"|"assistant", "content": "..."}]
        """
        if self.provider == "fake":
            # Portuguese (curto): fallback simples quando não há chave
            last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            if "PLANNER_JSON" in last_user:
                topic = last_user.split("User query:", 1)[-1].strip()
                subs = [f"{topic} overview", f"{topic} latest news", f"{topic} pricing", f"{topic} competitors", f"{topic} risks", f"{topic} opportunities"]
                return '{"subtasks": %s, "relevance_criteria":"Prefer authoritative, recent, non-spam sources."}' % (str(subs).replace("'", '"'))
            if "ANALYST_JSON" in last_user:
                return '{"bullets": ["Key market moves observed.", "Competitor launches summarized.", "Action items proposed."], "citations": {}}'
            return "OK"

        # Proper LLM call
        from langchain.schema import HumanMessage, SystemMessage, AIMessage
        lc_msgs = []
        for m in messages:
            if m["role"] == "system":
                lc_msgs.append(SystemMessage(content=m["content"]))
            elif m["role"] == "assistant":
                lc_msgs.append(AIMessage(content=m["content"]))
            else:
                lc_msgs.append(HumanMessage(content=m["content"]))
        resp = self.client.invoke(lc_msgs)  # type: ignore
        return getattr(resp, "content", str(resp))
