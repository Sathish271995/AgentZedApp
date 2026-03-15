"""
demo_seed.py  —  Run after starting the backend to populate demo data.

Usage:
    python demo_seed.py
"""
import requests, time

BASE = "http://localhost:8000"

PAYMENTS = [
    {"amount":250.00,"currency":"USD","customer_id":"CUST-001","description":"Order #1042"},
    {"amount":1500.00,"currency":"USD","customer_id":"CUST-002","description":"Subscription annual"},
    {"amount":89.99,"currency":"USD","customer_id":"CUST-001","description":"Order #1043"},
    {"amount":3200.00,"currency":"USD","customer_id":"CUST-003","description":"Enterprise license"},
    {"amount":45.00,"currency":"USD","customer_id":"CUST-004","description":"Order #1044"},
]

PRS = [
    {"pr_id":"PR-120","title":"Add payment CRUD API with validation",
     "files_changed":["routers/payments.py","database.py","api/models.py"],
     "author":"Sathish271995","repo":"Sathish271995/AgentZed",
     "event_type":"approved","reviewer":"senior-dev",
     "base_branch":"main","head_branch":"feature/payment-crud",
     "body":"Implements full CRUD for payments with amount validation and refund support."},
    {"pr_id":"PR-098","title":"Fix auth token expiry handling",
     "files_changed":["auth_service.py","middleware/auth.py","utils/token_utils.py"],
     "author":"jane-dev","repo":"Sathish271995/AgentZed",
     "event_type":"approved","reviewer":"tech-lead",
     "base_branch":"main","head_branch":"fix/auth-expiry",
     "body":"Critical fix — tokens not invalidated on expiry."},
    {"pr_id":"PR-115","title":"Add email notification for order updates",
     "files_changed":["notification_service.py","utils/smtp_utils.py"],
     "author":"Sathish271995","repo":"Sathish271995/AgentZed",
     "event_type":"merged","reviewer":"","base_branch":"main","head_branch":"feature/notifications",
     "body":"Sends emails on order status change using SMTP with retry logic."},
]

COMMENTS = [
    {"author":"Sathish271995","comment":"Amount validation should also reject values above 999999","comment_type":"bug","file_ref":"routers/payments.py:35"},
    {"author":"Sathish271995","comment":"Should we add pagination to the list endpoint?","comment_type":"suggestion","file_ref":"routers/payments.py:52"},
]

def seed():
    print("🌱 Seeding demo data...\n")

    # Payments
    print("── Creating payments ──")
    payment_ids = []
    for p in PAYMENTS:
        r = requests.post(f"{BASE}/api/payments/", json=p)
        if r.status_code == 201:
            pid = r.json()["payment"]["id"]
            payment_ids.append(pid)
            print(f"  ✅ Payment #{pid}: ${p['amount']} — {p['description']}")
        else:
            print(f"  ❌ {r.text[:80]}")

    # Mark first 2 as completed
    for pid in payment_ids[:2]:
        requests.put(f"{BASE}/api/payments/{pid}", json={"status":"completed"})
        print(f"  ✅ Payment #{pid} → completed")

    # PR Analyses
    print("\n── Running Agent Zed on PRs ──")
    pr_ids = []
    for pr in PRS:
        print(f"  Running agents on {pr['pr_id']}: {pr['title']}")
        r = requests.post(f"{BASE}/run-agent-zed", json=pr, timeout=60)
        if r.status_code == 200:
            d = r.json()
            db_id = d.get("db_id")
            pr_ids.append(db_id)
            print(f"  ✅ Saved id={db_id}  risk={d.get('PR Review',{}).get('risk_level')}  teams={d.get('Impact Analysis',{}).get('impacted_teams')}")
        else:
            print(f"  ❌ {r.text[:100]}")
        time.sleep(1)

    # Comments
    if pr_ids:
        print(f"\n── Adding comments to PR id={pr_ids[0]} ──")
        for c in COMMENTS:
            r = requests.post(f"{BASE}/api/pr-analyses/{pr_ids[0]}/comments", json=c, timeout=30)
            if r.status_code == 200:
                ai = r.json().get("ai_response","")
                print(f"  ✅ Comment: \"{c['comment'][:50]}...\"")
                print(f"     🤖 Agent Zed: \"{ai[:80]}...\"")
            time.sleep(0.5)

    print(f"\n✅ Done! Open http://localhost:5173")
    print(f"   Payments: {len(payment_ids)} | PR Analyses: {len([x for x in pr_ids if x])}")

if __name__ == "__main__":
    seed()
