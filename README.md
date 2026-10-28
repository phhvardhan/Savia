# SAVIA

AI assistant that reads a requirement (documents, recordings, typed text), recommends the SDLC
agents that fit, runs the chosen agent, and takes its output through review, approval and publishing.

- **Backend:** FastAPI (Python 3.10+), in `backend/`, API under `/api/v1`
- **Frontend:** React + Vite + TypeScript (Node 20+), in `frontend/`

This project runs inside the J&J network only (GenAI endpoint and LDAP login are internal).

## Not in git: get these from Harsha

| What | Where it goes |
|---|---|
| `.env` values (keys, LDAP, `SECRET_KEY`) | `backend/.env` (start from `backend/.env.example`) |
| J&J root CA certificate | `backend/certs/JNJ_Private_2048bit_Root_CA_certificate.cer` |
| Whisper model folder | `backend/models/faster-whisper-small.en/` |

LLM provider is chosen in `backend/.env`:

- `LLM_PROVIDER=azure_openai` on the J&J network and on AWS: GenAI endpoint only, no Groq or OpenAI fallback.
- `LLM_PROVIDER=groq` off the J&J network (needs `GROQ_API_KEY`).

## Run locally (Windows, PowerShell)

```powershell
git clone https://sourcecode.jnj.com/scm/~hpeela/savia_poc.git
cd savia_poc\backend

# Backend
copy .env.example .env          # then fill in the values
py -3.11 -m venv C:\savia-venv  # keep the venv outside OneDrive
C:\savia-venv\Scripts\Activate.ps1   # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (second terminal)
cd savia_poc\frontend
npm ci
npx vite --host 0.0.0.0 --port 5173 --strictPort
```

Open http://localhost:5173/work. Swagger docs: http://localhost:8000/docs

## Run locally (Mac / Linux)

```bash
git clone https://sourcecode.jnj.com/scm/~hpeela/savia_poc.git
cd savia_poc/backend
cp .env.example .env            # then fill in the values
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app

# Frontend (second terminal)
cd savia_poc/frontend
npm ci
npx vite --port 5173 --strictPort
```

The dev server proxies `/api` to `127.0.0.1:8000`, so keep the backend on port 8000.

## Orchestration (Temporal)

Every session is a Temporal workflow (`backend/app/orchestration/workflows.py`). The API starts it and sends it
updates (approve, advance, run agent, save edit, recommend); a separate worker runs the LLM calls as retried
activities and writes the JSON files the API reads. **The API needs the server and the worker running.**

```bash
brew install temporal                 # once (Mac); see docs.temporal.io/cli for other OSes
temporal server start-dev             # server on :7233, web UI on http://localhost:8233
cd backend && python -m app.worker    # third terminal, next to uvicorn
```

Set `TEMPORAL_ADDRESS` / `TEMPORAL_NAMESPACE` / `TEMPORAL_TASK_QUEUE` in `backend/.env` to point elsewhere.
Run one worker only: it is the single writer of `workflows.json` / `artifacts.json`. Sessions stay open until
you terminate them in the Temporal UI.

## Deploy on AWS (Linux)

First deploy:

```bash
git clone https://sourcecode.jnj.com/scm/~hpeela/savia_poc.git /opt/savia
cd /opt/savia/backend
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
nano .env        # LLM_PROVIDER=azure_openai, plus the keys
# copy backend/certs and backend/models/faster-whisper-small.en in (see "Not in git")

cd ../frontend && npm ci && npm run build      # outputs frontend/dist

sudo systemctl daemon-reload
sudo systemctl enable --now savia              # backend service (unit below)
sudo systemctl reload nginx                    # serves frontend/dist, proxies /api
```

`/etc/systemd/system/savia.service`:

```ini
[Unit]
Description=SAVIA backend
After=network.target

[Service]
WorkingDirectory=/opt/savia/backend
ExecStart=/opt/savia/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

`/etc/nginx/conf.d/savia.conf`:

```nginx
server {
    listen 80;
    root /opt/savia/frontend/dist;
    location / { try_files $uri /index.html; }
    location /api/ { proxy_pass http://127.0.0.1:8000; client_max_body_size 300m; }
}
```

Every update:

```bash
cd /opt/savia && git pull
cd backend && .venv/bin/pip install -r requirements.txt && sudo systemctl restart savia
cd ../frontend && npm ci && npm run build
```

## Checks

```bash
curl http://localhost:8000/docs                                    # backend is up
cd backend && .venv/bin/python -m pytest -q tests -p no:warnings   # backend tests (Windows: use C:\savia-venv\Scripts\python)
cd frontend && npx tsc -b                                          # frontend typecheck
```
