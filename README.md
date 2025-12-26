# Eagle PM

Web app offline/on-prem (FastAPI + Jinja2/HTMX + SQLite) para gestão de members, releases, projects e activities, com dashboards Daily Meeting e Project Control.

## Rodar em dev
```
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -e .
uvicorn eagle_pm.app.main:app --reload
```

## Empacotar (PyInstaller)
- script: `scripts/build_exe.ps1` (a criar)
