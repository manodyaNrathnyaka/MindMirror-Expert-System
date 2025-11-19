# MindMirror-Expert-System
MirrorMind is a psychological expert system built to mirror the decision-making of a human psychologist. Its purpose is simple: help you understand your thinking patterns and become more aware of how your mind works.  
# Mind Mirror — Expert System

Self-reflection expert system (Streamlit UI) using rule-based engines and an optional LLM explainer.

This repository contains the rule engines, a Streamlit front-end, and an optional LLM-based explainer module used to generate human-friendly explanations of test results.

## Contents
- `streamlit_app.py` — Streamlit UI (one-question flow, explanation output)
- `main.py` — CLI runner / reference
- `inference_engine.py` — engine runner wrapper
- `llm_explainer.py` — optional LLM explanation helper (requires API key)
- `facts.py` — Fact data model used by the engines
- `kb/` — knowledge-base rule files (overthinking, stress, left_right_brain, question lists)

## Requirements
- Python 3.10+ recommended
- See `requirements.txt` for exact packages (Streamlit, experta, etc.)

## Setup (local)
1. Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r requirements.txt
```

## Running the app
Start the Streamlit app locally:
```powershell
streamlit run streamlit_app.py
```
Open the Local URL printed by Streamlit (e.g. `http://localhost:8501`).

## LLM / Explanation
- The LLM explainer is optional. To enable it, set `OPENAI_API_KEY` in your environment (or add secrets via Streamlit/GitHub Actions):
```powershell
$env:OPENAI_API_KEY = "sk_..."
```
- If no key is present, the app falls back to a deterministic, human-friendly explanation.

## Development notes
- The UI uses `st.session_state` to preserve answers and navigation.
- Rule engines live in `kb/` and expose a `calculate()` method returning a dict with `result`, `alternative`, and `percentage`.

## Contributing
- Please open issues or PRs with small, focused changes.
- Do not commit secrets or API keys. Add them to `.gitignore` if needed.

## License
This repository does not include a license file. Add a `LICENSE` if you want to set terms.

---
If you want, I can:
- Commit this `README.md` and push it to your GitHub (you already have `origin` configured), or
- Create a `README` with extra sections (deployment, CI) — tell me what you'd like added.
# MindMirror-Expert-System
MirrorMind is a psychological expert system built to mirror the decision-making of a human psychologist. Its purpose is simple: help you understand your thinking patterns and become more aware of how your mind works.  
