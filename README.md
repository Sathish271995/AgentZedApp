# 🤖 Agent Zed — Payment Intelligence System
### Payment CRUD + GitHub PR Analysis + 4 AI Agents + React Dashboard

---

## Project Structure

```
AgentZedApp/
├── backend/
│   ├── main.py                  ← FastAPI entry point
│   ├── database.py              ← PostgreSQL — payments + pr_analyses + pr_comments
│   ├── notifications.py         ← HTML email notifications
│   ├── demo_seed.py             ← Populate demo data
│   ├── requirements.txt
│   ├── .env                     ← Your keys go here
│   ├── routers/
│   │   ├── payments.py          ← Payment CRUD (create/read/update/delete/refund)
│   │   └── agent_zed.py         ← Webhook + PR analysis CRUD + Comments
│   ├── agents/
│   │   ├── pr_review_agent.py   ← 🕵️ PR First Responder
│   │   ├── impact_analysis_agent.py ← 🎯 Impact Analysis
│   │   ├── release_agent.py     ← 🚀 Release Intelligence
│   │   └── rag_agent.py         ← 🧠 RAG Knowledge
│   ├── data/
│   │   ├── release_calendar.json ← Edit with your release dates
│   │   └── knowledge_base.json   ← Auto-grows with each PR
│   └── utils/json_utils.py
│
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx              ← Root — polls stats every 12s
        ├── api.js               ← All fetch calls
        ├── components/
        │   ├── Topbar.jsx       ← Top navigation bar
        │   ├── StatsRow.jsx     ← 8 stat cards (payments + PRs)
        │   ├── TabNav.jsx       ← Payments | Agent Zed tabs
        │   └── PRDrawer.jsx     ← 5-tab slide panel (Review/Impact/Release/RAG/Comments)
        └── pages/
            ├── PaymentsTab.jsx  ← Full payment CRUD UI
            └── PRTab.jsx        ← PR analysis list + manual trigger
```

---

## STEP 1 — PostgreSQL Setup

Open pgAdmin → Query Tool → run:
```sql
CREATE DATABASE agentzed;
```

---

## STEP 2 — Configure .env

Open `backend/.env`:
```env
OPENAI_API_KEY=sk-proj-your-new-key-here
DATABASE_URL=postgresql://postgres:admin123@localhost:5432/agentzed
GITHUB_WEBHOOK_SECRET=
SMTP_USER=your@gmail.com
SMTP_PASS=your-16-char-app-password
```

---

## STEP 3 — Start Backend

```bash
cd backend
pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8000
```

Expected output:
```
✅ Agent Zed started — all tables ready.
INFO:  Uvicorn running on http://127.0.0.1:8000
```

Test it: http://localhost:8000/docs

---

## STEP 4 — Seed Demo Data

```bash
# In a SECOND terminal (keep backend running):
cd backend
python demo_seed.py
```

This creates 5 payments + runs 3 PR analyses with all 4 agents.

---

## STEP 5 — Start React Dashboard

```bash
# In a THIRD terminal:
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## STEP 6 — GitHub Integration (Full Real Flow)

### A) Expose your backend with ngrok
```bash
ngrok http 8000
# Copy the https URL: e.g. https://edelmira-deltaic-yuriko.ngrok-free.dev
```

### B) Configure GitHub Webhook
1. Go to: `github.com/Sathish271995/AgentZed` → **Settings → Webhooks → Edit**
2. Payload URL: `https://YOUR-NGROK-URL/webhook/github`
3. Content type: `application/json`
4. Secret: *(leave blank)*
5. Events: **Send me everything** (or select: Pull requests + Pull request reviews)
6. Click **Update webhook**

### C) Create a new branch and commit the Payment CRUD code
```bash
cd C:\Source\AgentZed_SourceCode_v2\AgentZed

# Create branch
git checkout -b feature/add-payment-crud

# Copy routers/payments.py into the repo
# Then commit:
git add .
git commit -m "Add payment CRUD API with validation and refund support"
git push origin feature/add-payment-crud
```

### D) Create Pull Request on GitHub
- Go to your repo → click **"Compare & pull request"**
- Title: `Add payment CRUD API with validation`
- Click **Create pull request**

### E) Approve the PR
- Click **Files changed** tab
- Click **Review changes** → **Approve** → **Submit review**

### F) Watch Agent Zed fire automatically!
In your backend terminal you'll see:
```
🔔 GitHub event: pull_request_review / submitted on PR#5
  🕵️  PR First Responder running...
  🎯  Impact Analysis running...
  🚀  Release Intelligence running...
  🧠  RAG Knowledge running...
  ✅  Saved to PostgreSQL id=4
  📧  Payments Team → skipped_no_smtp
```

And your dashboard at **localhost:5173** updates within 12 seconds!

---

## All API Endpoints

### Payment CRUD
| Method | URL | Description |
|--------|-----|-------------|
| POST   | /api/payments/ | Create payment |
| GET    | /api/payments/ | List (filter: ?status=pending&customer_id=X) |
| GET    | /api/payments/{id} | Get one |
| PUT    | /api/payments/{id} | Update |
| DELETE | /api/payments/{id} | Delete |
| POST   | /api/payments/{id}/refund | Refund |

### Agent Zed
| Method | URL | Description |
|--------|-----|-------------|
| POST   | /webhook/github | GitHub fires this on PR events |
| POST   | /run-agent-zed | Manual trigger |
| GET    | /api/pr-analyses | List all |
| GET    | /api/pr-analyses/{id} | Get one with full AI results |
| DELETE | /api/pr-analyses/{id} | Delete |
| POST   | /api/pr-analyses/{id}/rerun | Re-run all 4 agents |
| GET    | /api/pr-analyses/{id}/comments | List comments |
| POST   | /api/pr-analyses/{id}/comments | Add (Agent Zed auto-replies) |
| PUT    | /api/pr-analyses/{id}/comments/{cid} | Edit |
| DELETE | /api/pr-analyses/{id}/comments/{cid} | Delete |
| GET    | /api/stats | Dashboard stats |
