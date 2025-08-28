# CI Radar (Competitive Intelligence)

Monitora páginas públicas (pricing, release notes, blog) com um agente smolagents e salva resultados em CSV.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edite provider, keys e MODEL_ID
```
