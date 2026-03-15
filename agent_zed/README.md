# Agent Zed — PR Intelligence + Payment Management

## Project Structure

```
agent_zed/
├── backend/                  ← FastAPI Python backend
│   ├── main.py               ← App entry point
│   ├── database.py           ← PostgreSQL + connection pool
│   ├── notifications.py      ← Email notifications
│   ├── requirements.txt      ← Python dependencies
│   ├── .env.example          ← Copy to .env and fill in secrets
│   │
│   ├── agents/
│   │   ├── pr_review_agent.py
│   │   ├── impact_analysis_agent.py
│   │   ├── release_agent.py
│   │   └── rag_agent.py
│   │
│   ├── routers/
│   │   ├── agent_zed.py      ← GitHub webhook + PR analysis endpoints
│   │   └── payments.py       ← Payment CRUD endpoints
│   │
│   ├── utils/
│   │   └── json_utils.py
│   │
│   └── data/
│       ├── knowledge_base.json      ← Auto-populated by RAG agent
│       └── release_calendar.json   ← Edit to add your release dates
│
└── frontend/                 ← React + Vite frontend
    ├── index.html
    ├── vite.config.js
    ├── package.json
    ├── .env.example          ← Copy to .env
    │
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js
        ├── components/
        │   ├── Topbar.jsx
        │   ├── TabNav.jsx
        │   ├── StatsRow.jsx
        │   └── PRDrawer.jsx
        └── pages/
            ├── PRTab.jsx
            └── PaymentsTab.jsx
```

---

## Setup

### 1. Backend

```bash
cd backend

# Copy and fill in your secrets
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

**Required `.env` keys:**
| Key | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `GITHUB_TOKEN` | Fine-grained PAT — Read access to Pull Requests |
| `GITHUB_WEBHOOK_SECRET` | Same secret set in your GitHub repo webhook |
| `DATABASE_URL` | PostgreSQL connection string |
| `SMTP_USER` / `SMTP_PASS` | Gmail or SMTP credentials for notifications |

---

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies API calls to localhost:8000 automatically)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

### 3. GitHub Webhook

1. Go to your repo → **Settings** → **Webhooks** → **Add webhook**
2. Set **Payload URL** to `https://your-server.com/webhook/github`
   - For local dev: use [ngrok](https://ngrok.com/) → `ngrok http 8000`
3. Set **Content type** to `application/json`
4. Set **Secret** to the same value as `GITHUB_WEBHOOK_SECRET` in `.env`
5. Select events: **Pull requests** + **Pull request reviews**

---

## How It Works

When a PR is opened, approved, or merged on GitHub:

1. GitHub sends a webhook to `/webhook/github`
2. Agent Zed fetches the **real changed files** via GitHub API
3. All 4 agents run **concurrently**:
   - 🕵️ **PR First Responder** — reviews code quality, missing tests, merge risk
   - 🎯 **Impact Analysis** — maps files → teams → dependency risk
   - 🚀 **Release Intelligence** — checks calendar conflicts and stakeholders
   - 🧠 **RAG Knowledge** — learns patterns from past PRs
4. Results are saved to PostgreSQL
5. Email notifications sent to impacted teams
6. Dashboard auto-refreshes to show the analysis
