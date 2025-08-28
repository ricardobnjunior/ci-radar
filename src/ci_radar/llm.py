from smolagents import InferenceClientModel
from .settings import (
    PROVIDER, OPENAI_API_KEY, HF_API_TOKEN, MODEL_ID,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL,
    OPENROUTER_SITE, OPENROUTER_APP_NAME,
)

def get_model():
    if PROVIDER == "openai":
        return InferenceClientModel(
            provider="openai",
            model=MODEL_ID,
            api_key=OPENAI_API_KEY,
        )
    if PROVIDER == "hf":
        return InferenceClientModel(
            provider="hf",
            model=MODEL_ID,
            api_key=HF_API_TOKEN,
        )
    if PROVIDER == "openrouter":
        return InferenceClientModel(
            provider="openai",
            model=OPENROUTER_MODEL,
            api_key=OPENROUTER_API_KEY,
            api_base=OPENROUTER_BASE_URL,
            extra_headers={
                # estes headers são recomendados pelo OpenRouter
                "HTTP-Referer": OPENROUTER_SITE,
                "X-Title": OPENROUTER_APP_NAME,
            },
        )
    raise ValueError(f"Unsupported PROVIDER={PROVIDER}")
