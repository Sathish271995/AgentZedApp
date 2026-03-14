import os, json
import psycopg2, psycopg2.extras
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    return psycopg2.connect(
        os.getenv("DATABASE_URL","postgresql://postgres:admin123@localhost:5432/agentzed")
    )

def init_db():
    conn = get_conn(); cur = conn.cursor()

    # ── Payments table ────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id          SERIAL PRIMARY KEY,
            amount      NUMERIC(12,2) NOT NULL,
            currency    VARCHAR(5)  DEFAULT 'USD',
            customer_id VARCHAR(100) NOT NULL,
            description TEXT,
            status      VARCHAR(20)  DEFAULT 'pending',
            created_at  TIMESTAMPTZ  DEFAULT NOW(),
            updated_at  TIMESTAMPTZ  DEFAULT NOW()
        )
    """)

    # ── PR Analyses table ─────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pr_analyses (
            id               SERIAL PRIMARY KEY,
            pr_id            VARCHAR(50),
            title            TEXT,
            author           VARCHAR(150),
            repo             VARCHAR(250),
            pr_url           TEXT,
            event_type       VARCHAR(30),
            reviewer         VARCHAR(150),
            base_branch      VARCHAR(100),
            head_branch      VARCHAR(100),
            files_changed    JSONB,
            risk_level       VARCHAR(20),
            impacted_teams   JSONB,
            dependency_risk  VARCHAR(20),
            signoff_required BOOLEAN DEFAULT FALSE,
            release_conflict BOOLEAN DEFAULT FALSE,
            merge_conflicts  BOOLEAN DEFAULT FALSE,
            stakeholders     JSONB,
            ai_summary       TEXT,
            rag_patterns     JSONB,
            full_result      JSONB,
            created_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── PR Comments table ─────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pr_comments (
            id           SERIAL PRIMARY KEY,
            pr_db_id     INTEGER REFERENCES pr_analyses(id) ON DELETE CASCADE,
            author       VARCHAR(150),
            comment      TEXT NOT NULL,
            comment_type VARCHAR(30) DEFAULT 'general',
            file_ref     VARCHAR(300),
            ai_response  TEXT,
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            updated_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    conn.commit(); cur.close(); conn.close()
    print("[DB] All tables ready.")

# ── Payment CRUD ──────────────────────────────────────────────────────────────
def db_create_payment(data: dict) -> dict:
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        INSERT INTO payments (amount, currency, customer_id, description)
        VALUES (%s,%s,%s,%s) RETURNING *
    """, (data["amount"], data.get("currency","USD"), data["customer_id"], data.get("description","")))
    row = _ser(dict(cur.fetchone()))
    conn.commit(); cur.close(); conn.close()
    return row

def db_list_payments(status=None, customer_id=None) -> list:
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    q, params = "SELECT * FROM payments WHERE 1=1", []
    if status:
        q += " AND status=%s"; params.append(status)
    if customer_id:
        q += " AND customer_id=%s"; params.append(customer_id)
    q += " ORDER BY created_at DESC"
    cur.execute(q, params)
    rows = [_ser(dict(r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows

def db_get_payment(pid: int):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM payments WHERE id=%s", (pid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return _ser(dict(row)) if row else None

def db_update_payment(pid: int, data: dict):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    sets, params = [], []
    for k in ("amount","currency","description","status"):
        if data.get(k) is not None:
            sets.append(f"{k}=%s"); params.append(data[k])
    if not sets:
        cur.close(); conn.close(); return None
    sets.append("updated_at=NOW()")
    params.append(pid)
    cur.execute(f"UPDATE payments SET {','.join(sets)} WHERE id=%s RETURNING *", params)
    row = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return _ser(dict(row)) if row else None

def db_delete_payment(pid: int) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE id=%s RETURNING id", (pid,))
    ok = cur.fetchone() is not None
    conn.commit(); cur.close(); conn.close()
    return ok

# ── PR Analyses ───────────────────────────────────────────────────────────────
def save_pr_analysis(result: dict) -> int:
    conn = get_conn(); cur = conn.cursor()
    rv = result.get("PR Review",{})
    ia = result.get("Impact Analysis",{})
    ri = result.get("Release Intelligence",{})
    rg = result.get("RAG Knowledge",{})
    cur.execute("""
        INSERT INTO pr_analyses (
            pr_id,title,author,repo,pr_url,event_type,reviewer,
            base_branch,head_branch,files_changed,
            risk_level,impacted_teams,dependency_risk,
            signoff_required,release_conflict,merge_conflicts,
            stakeholders,ai_summary,rag_patterns,full_result
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        result.get("pr_id"), result.get("title"), result.get("author",""),
        result.get("repo",""), result.get("pr_url",""), result.get("event_type","manual"),
        result.get("reviewer",""), result.get("base_branch","main"), result.get("head_branch",""),
        json.dumps(result.get("files_changed",[])),
        rv.get("risk_level","Unknown"),
        json.dumps(ia.get("impacted_teams",[])),
        ia.get("dependency_risk","Unknown"),
        bool(ia.get("signoff_required",False)),
        bool(ri.get("release_conflict",False)),
        bool(rv.get("merge_conflicts",False)),
        json.dumps(ri.get("suggested_stakeholders",[])),
        rv.get("summary",""),
        json.dumps(rg.get("patterns",[])),
        json.dumps(result),
    ))
    db_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return db_id

def get_all_pr_analyses() -> list:
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM pr_analyses ORDER BY created_at DESC LIMIT 200")
    rows = [_ser(dict(r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    return rows

def get_pr_by_id(db_id: int):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM pr_analyses WHERE id=%s", (db_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return _ser(dict(row)) if row else None

def delete_pr_analysis(db_id: int) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM pr_analyses WHERE id=%s RETURNING id", (db_id,))
    ok = cur.fetchone() is not None
    conn.commit(); cur.close(); conn.close()
    return ok

def get_stats() -> dict:
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT COUNT(*) total,
               COUNT(*) FILTER (WHERE risk_level='High')      high_risk,
               COUNT(*) FILTER (WHERE risk_level='Medium')    medium_risk,
               COUNT(*) FILTER (WHERE risk_level='Low')       low_risk,
               COUNT(*) FILTER (WHERE release_conflict=TRUE)  conflicts,
               COUNT(*) FILTER (WHERE merge_conflicts=TRUE)   merge_conflicts,
               COUNT(*) FILTER (WHERE signoff_required=TRUE)  signoffs_needed
        FROM pr_analyses
    """)
    stats = dict(cur.fetchone())
    cur.execute("SELECT impacted_teams FROM pr_analyses")
    teams = set()
    for r in cur.fetchall():
        if isinstance(r["impacted_teams"], list): teams.update(r["impacted_teams"])
    stats["unique_teams"] = len(teams)
    # Payment stats
    cur.execute("SELECT COUNT(*) total, COUNT(*) FILTER(WHERE status='completed') completed, COUNT(*) FILTER(WHERE status='pending') pending, COALESCE(SUM(amount),0) total_amount FROM payments")
    pstats = dict(cur.fetchone())
    stats["payments"] = {k: str(v) if hasattr(v,"__class__") and v.__class__.__name__=="Decimal" else v for k,v in pstats.items()}
    cur.close(); conn.close()
    return stats

# ── PR Comments ───────────────────────────────────────────────────────────────
def create_pr_comment(pr_db_id,author,comment,comment_type,file_ref,ai_response) -> int:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO pr_comments(pr_db_id,author,comment,comment_type,file_ref,ai_response) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
                (pr_db_id,author,comment,comment_type,file_ref,ai_response))
    cid = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close(); return cid

def get_pr_comments(pr_db_id:int) -> list:
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM pr_comments WHERE pr_db_id=%s ORDER BY created_at", (pr_db_id,))
    rows = [_ser(dict(r)) for r in cur.fetchall()]
    cur.close(); conn.close(); return rows

def update_pr_comment(cid:int, text:str) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE pr_comments SET comment=%s,updated_at=NOW() WHERE id=%s RETURNING id",(text,cid))
    ok = cur.fetchone() is not None; conn.commit(); cur.close(); conn.close(); return ok

def delete_pr_comment(cid:int) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM pr_comments WHERE id=%s RETURNING id",(cid,))
    ok = cur.fetchone() is not None; conn.commit(); cur.close(); conn.close(); return ok

def _ser(row:dict) -> dict:
    for k,v in row.items():
        if hasattr(v,"isoformat"): row[k] = v.isoformat()
        elif hasattr(v,"__class__") and v.__class__.__name__=="Decimal": row[k] = float(v)
    return row
