# Breathe ESG Tech Intern Assignment Prototype

Prototype full-stack app for ingesting and reviewing emissions activity data from:
- SAP (fuel + procurement export CSV)
- Utility portal electricity export CSV
- Corporate travel export CSV

## Stack
- Backend: Django + Django REST Framework + SQLite
- Frontend: React + Vite

## Quickstart

### Backend
1. Create virtualenv and install deps:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r backend/requirements.txt`
2. Migrate + seed:
   - `python backend/manage.py migrate`
   - `python backend/manage.py seed_demo`
3. Run API:
   - `python backend/manage.py runserver`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Open the shown local URL

Frontend expects API at `http://127.0.0.1:8000/api`.

## Deliverable Docs
- `MODEL.md`
- `DECISIONS.md`
- `TRADEOFFS.md`
- `SOURCES.md`

## Demo credentials
- Email: `analyst@demo.local`
- Password: `demo12345`

## Deploy (Render)
1. Push this repo to GitHub.
2. Create a Render Blueprint from `render.yaml`.
3. Set `CORS_ALLOWED_ORIGINS` on the API service to your UI URL (e.g. `https://breathe-esg-ui.onrender.com`).
4. Set `VITE_API_URL` on the static UI service to your API URL (e.g. `https://breathe-esg-api.onrender.com/api`).
5. Share live UI URL + credentials in your submission email.

## Submission checklist
- GitHub repo link (share with Breathe reviewers)
- Live deployed URL
- `MODEL.md`, `DECISIONS.md`, `TRADEOFFS.md`, `SOURCES.md`
- Login credentials for analyst demo
