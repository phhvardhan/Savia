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
| Whisper model folder | `backend/models/faster-whisper-tiny/` |

LLM provider is chosen in `backend/.env`:

- `LLM_PROVIDER=azure_openai` on the J&J network and on AWS: GenAI endpoint only, no Groq or OpenAI fallback.
- `LLM_PROVIDER=groq` off the J&J network (needs `GROQ_API_KEY`).
- `LLM_CA_BUNDLE` points at the J&J root CA so the GenAI endpoint is called with TLS verification on.

Other settings worth knowing (all in `backend/.env.example`):

| Setting | Default | What it does |
|---|---|---|
| `LLM_MAX_OUTPUT_TOKENS` | 8000 | Longest answer an agent may write. A cut-off answer is reported as an error, never patched up. |
| `LLM_INPUT_CHARS` / `LLM_CHUNK_CHARS` | 40000 / 16000 | Inputs longer than this are condensed part by part instead of truncated. |
| `LLM_RETRIES` | 2 | Retries when an answer does not match the agent's output schema. |
| `DB_PATH` | `uploads/savia.db` | SQLite store for workflows, versions, approvals, runs and LLM usage. Old `workflows.json` / `artifacts.json` are imported on first start. |
| `MAX_CONCURRENT_RUNS` | 4 | Agent runs allowed at the same time. |
| `AUTH_REQUIRED` | false | When true every API call needs a login token. Set `VITE_AUTH_REQUIRED=true` for the frontend too. |
| `ALLOW_OFFLINE_LOGIN` | false | Development only: lets `ALLOWED_USERS` sign in when the directory is unreachable. |
| `CORS_ORIGINS` | localhost:5173 | Comma-separated origins allowed to call the API. |

## How a run works

1. `POST /ingestion/upload` turns files into text and creates a workflow.
2. `POST /savia/recommend` ranks the agents and returns a `plan` ordered by what each agent consumes.
3. `POST /agents/{id}/runs` starts the agent in the background; poll `GET /agents/runs/{run_id}`.
   Each agent's answer is validated against its schema, retried with the errors if it does not match,
   and checked for figures and IDs that are not in the input (`quality` on the result).
4. Downstream agents only read **approved** upstream outputs (`upstream_used` / `upstream_unapproved`).
   Approve an output with `POST /workflows/{id}/approve` and its `artifact_id`.
5. Edits and recorded decisions create a new version that needs approval again.
6. `POST /workflows/{id}/advance` is refused while any output in the workflow is unapproved.

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

## Deploy on AWS (Linux)

First deploy:

```bash
git clone https://sourcecode.jnj.com/scm/~hpeela/savia_poc.git /opt/savia
cd /opt/savia/backend
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
nano .env        # LLM_PROVIDER=azure_openai, plus the keys
# copy backend/certs and backend/models/faster-whisper-tiny in (see "Not in git")

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
python agent-test-files/run_all.py                                 # live check of every agent against the sample inputs (backend running)
```
