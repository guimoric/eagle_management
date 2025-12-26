# Eagle PM — Stack + Estrutura de Arquivos

## Stack
- Python 3.11
- FastAPI + Uvicorn
- Jinja2 (SSR) + HTMX
- SQLite
- SQLAlchemy
- Export CSV (stdlib) + XLSX opcional (openpyxl)
- PyInstaller (empacotar .exe e abrir no browser)

---

## Estrutura de diretórios/arquivos

eagle-pm/
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ .gitignore
├─ eagle_pm/
│  ├─ __init__.py
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ main.py
│  │  ├─ db.py
│  │  ├─ models.py
│  │  ├─ rules.py
│  │  ├─ crud.py
│  │  ├─ export.py
│  │  ├─ routes.py
│  │  ├─ templates/
│  │  │  ├─ base.html
│  │  │  ├─ daily_meeting.html
│  │  │  ├─ project_control.html
│  │  │  ├─ members.html
│  │  │  ├─ releases.html
│  │  │  ├─ projects.html
│  │  │  ├─ activities.html
│  │  │  └─ components.html
│  │  └─ static/
│  │     ├─ app.css
│  │     └─ app.js
│  └─ launcher/
│     └─ run.py
└─ scripts/
   ├─ build_exe.spec
   └─ build_exe.ps1

---