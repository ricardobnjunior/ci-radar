# CI Radar

**CI Radar (Competitive Intelligence Radar)** is a Python project built with [smolagents](https://huggingface.co/docs/smolagents/index).  
It enables an AI agent to automatically monitor competitor information on the web, fetching relevant pages, extracting titles and links, deduplicating results, and saving them into structured CSV files.

---

## ⭐ Support the Project

If you find this project useful, please consider giving it a **star** on GitHub.  
It helps increase visibility and motivates further improvements.

---

## 📂 Project Structure

- **README.md** — Documentation and usage instructions  
- **requirements.txt** — Project dependencies  
- **.env.example** — Example environment variables configuration  
- **src/ci_radar/** — Source code package  
  - `settings.py` — Centralized configuration and environment variables  
  - `llm.py` — Model initialization (OpenAI, Hugging Face, or OpenRouter)  
  - `utils.py` — Utility functions (e.g., deduplication, save CSV)  
  - `web_tools.py` — Agent tools (HTTP fetch, HTML parsing, deduplication, search)  
  - `agents.py` — CodeAgent creation with tools  
  - `orchestrator.py` — Planner prompt and orchestration logic  
  - `main.py` — Entry point to run the agent  

---

## ⚙️ Prerequisites

- Python **3.10+**  
- Access to an LLM provider (OpenAI, Hugging Face, or OpenRouter)  
- Basic knowledge of Python virtual environments  

---

## 🔧 Installation

1. Clone the repository  
2. Create and activate a virtual environment  
3. Install dependencies from `requirements.txt`  

---

## 🔑 Configuration

1. Copy `.env.example` to `.env`  
2. Fill in your API keys (e.g., `OPENAI_API_KEY`, `HF_API_TOKEN`, or `OPENROUTER_API_KEY`)  
3. Adjust optional parameters (timeouts, user agent, output file name)  

---

## ▶️ Usage

Run the main script to start the agent:

```bash
python -m src.ci_radar.main
