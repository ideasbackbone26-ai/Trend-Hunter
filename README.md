# Aanya Trend Hunter — v2.1 repaired package

This package is a **local** Streamlit/SQLite application. It is not yet a public cloud deployment, and Instagram is manual reference-only.

## Installation (PowerShell)

```powershell
cd E:\Aanya\aanya-trend-hunter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # only if .env does not already exist
notepad .env
python diagnose.py
python collect.py --batch morning
streamlit run app.py
```

Never share `.env` or a full API request URL containing a key. The collector now prints sanitized Google API errors. The `diagnose.py` script checks database counts and performs one small API request.

## Preserve existing data

Back up your project first. If upgrading, replace only Python source files and keep your existing `.env` and `data/trends.db`. Do not replace or delete `.venv`. Do not run `Copy-Item .env.example .env` if your configured `.env` already exists.

## What to expect

The Discover view shows up to ten matches when collection succeeds. If empty, set minimum views to 0 and check `python diagnose.py`. Ranking uses titles/descriptions, not video/audio AI analysis. Instagram references are manually entered. Public hosting and persistent shared cloud saves are future work.
