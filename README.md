# MESSMate — BH3 Shivalik Hostel

A Python + Streamlit multipage prototype for the BH3 – Shivalik Hostel meal-planning and billing-transparency BPM project.

## Included pages
1. Dashboard with student count, semester fee, today's meal intentions, waste records and CSV exports.
2. Weekly Menu with the supplied BH3 menu and fixed meal timings.
3. Meal Reservations with a strict one-day-ahead booking rule.
4. Billing simulator comparing fixed fee, meal-allocation and hybrid scenarios, including an illustrative balance versus ₹22,500.
5. Kitchen Planning with per-meal allocation proxies (₹30 breakfast, ₹35 lunch, ₹25 snacks, ₹35 dinner), recommended servings, outcome entry, saved outcome history and CSV download.
6. Animated BPMN with vertical responsibility swimlanes, process nodes, play/pause/step controls, explanations and a visible quantity approval loop in the To-Be view.
7. ER Diagram with larger, top-to-bottom Graphviz layout.

## Run locally on Windows PowerShell
From the extracted project folder:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If script activation is blocked, skip activation and use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Persistence and deployment
SQLite stores records in `data/messmate.db` for local development. For shared cloud deployment with many users, migrate to a managed persistent PostgreSQL database. The role selector is a demonstration switch, not real authentication. Add secure login, role-based authorization, backups and privacy safeguards before public use.

## Important assumptions
- Hostel: BH3 – Shivalik Hostel; 250 students; session July–December 2026.
- Reported fixed semester fee: ₹22,500. Meal allocation: breakfast ₹30, lunch ₹35, snacks ₹25, dinner ₹35 (₹125/day).
- Billing alternatives are simulations only and do not alter official charges. The hybrid scenario means a fixed base share plus a reduced variable meal-allocation share; the displayed balance is hypothetical, not an actual refund.
- The one-day-ahead reservation rule is an application requirement and must be aligned with actual mess rules before operational use.
- The menu was transcribed from the supplied photo and should be checked against the official menu.
- The eight provided student names/roll numbers are a best-effort transcription and should be verified. The other 242 students are not fabricated.
- The As-Is BPMN is a conceptual baseline; validate it with mess staff before claiming it depicts the official process.
- The meal allocation values are proxies for planning and are not verified ingredient costs.
