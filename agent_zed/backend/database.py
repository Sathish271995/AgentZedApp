import json
import logging
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("database")

# ── Connection pool (replaces one-connection-per-call anti-pattern) ───────────
_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:Database%40123@localhost:5432/agent_zed_app"
            ),
        )
    return _pool


@contextmanager
def get_conn():
    """Context manager — borrows a connection from the pool and returns it automatically."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ── Schema initialisation ─────────────────────────────────────────────────────
def init_db() -> None:
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id          SERIAL PRIMARY KEY,
                amount      NUMERIC(12,2) NOT NULL,
                currency    VARCHAR(5)    DEFAULT 'USD',
                customer_id VARCHAR(100)  NOT NULL,
                description TEXT,
                status      VARCHAR(20)   DEFAULT 'pending',
                created_at  TIMESTAMPTZ   DEFAULT NOW(),
                updated_at  TIMESTAMPTZ   DEFAULT NOW()
            )
        """)

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
                signoff_required BOOLEAN      DEFAULT FALSE,
                release_conflict BOOLEAN      DEFAULT FALSE,
                merge_conflicts  BOOLEAN      DEFAULT FALSE,
                stakeholders     JSONB,
                ai_summary       TEXT,
                rag_patterns     JSONB,
                full_result      JSONB,
                created_at       TIMESTAMPTZ  DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pr_comments (
                id           SERIAL PRIMARY KEY,
                pr_db_id     INTEGER REFERENCES pr_analyses(id) ON DELETE CASCADE,
                author       VARCHAR(150),
                comment      TEXT NOT NULL,
                comment_type VARCHAR(30)  DEFAULT 'general',
                file_ref     VARCHAR(300),
                ai_response  TEXT,
                created_at   TIMESTAMPTZ  DEFAULT NOW(),
                updated_at   TIMESTAMPTZ  DEFAULT NOW()
            )
        """)

    logger.info("[DB] All tables ready.")


# ── Payments CRUD ─────────────────────────────────────────────────────────────
def db_create_payment(data: dict) -> dict:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO payments (amount, currency, customer_id, description) "
            "VALUES (%s,%s,%s,%s) RETURNING *",
            (data["amount"], data.get("currency", "USD"),
             data["customer_id"], data.get("description", "")),
        )
        return _ser(dict(cur.fetchone()))


def db_list_payments(status=None, customer_id=None) -> list:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        q, params = "SELECT * FROM payments WHERE 1=1", []
        if status:
            q += " AND status=%s"; params.append(status)
        if customer_id:
            q += " AND customer_id=%s"; params.append(customer_id)
        q += " ORDER BY created_at DESC"
        cur.execute(q, params)
        return [_ser(dict(r)) for r in cur.fetchall()]


def db_get_payment(pid: int):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM payments WHERE id=%s", (pid,))
        row = cur.fetchone()
        return _ser(dict(row)) if row else None


def db_update_payment(pid: int, data: dict):
    allowed = {"amount", "currency", "description", "status"}
    sets, params = [], []
    for k in allowed:
        if data.get(k) is not None:
            sets.append(f"{k}=%s")
            params.append(data[k])
    if not sets:
        return None
    sets.append("updated_at=NOW()")
    params.append(pid)
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"UPDATE payments SET {', '.join(sets)} WHERE id=%s RETURNING *",
            params,
        )
        row = cur.fetchone()
        return _ser(dict(row)) if row else None


def db_delete_payment(pid: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM payments WHERE id=%s RETURNING id", (pid,))
        return cur.fetchone() is not None


# ── PR Analyses ───────────────────────────────────────────────────────────────
def save_pr_analysis(result: dict) -> int:
    rv = result.get("PR Review", {})
    ia = result.get("Impact Analysis", {})
    ri = result.get("Release Intelligence", {})
    rg = result.get("RAG Knowledge", {})

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO pr_analyses (
                pr_id, title, author, repo, pr_url, event_type, reviewer,
                base_branch, head_branch, files_changed,
                risk_level, impacted_teams, dependency_risk,
                signoff_required, release_conflict, merge_conflicts,
                stakeholders, ai_summary, rag_patterns, full_result
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            ) RETURNING id
            """,
            (
                result.get("pr_id"),
                result.get("title"),
                result.get("author", ""),
                result.get("repo", ""),
                result.get("pr_url", ""),
                result.get("event_type", "manual"),
                result.get("reviewer", ""),
                result.get("base_branch", "main"),
                result.get("head_branch", ""),
                json.dumps(result.get("files_changed", [])),
                rv.get("risk_level", "Unknown"),
                json.dumps(ia.get("impacted_teams", [])),
                ia.get("dependency_risk", "Unknown"),
                bool(ia.get("signoff_required", False)),
                bool(ri.get("release_conflict", False)),
                bool(rv.get("merge_conflicts", False)),
                json.dumps(ri.get("suggested_stakeholders", [])),
                rv.get("summary", ""),
                json.dumps(rg.get("patterns", [])),
                json.dumps(result),
            ),
        )
        return cur.fetchone()[0]


def get_all_pr_analyses() -> list:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM pr_analyses ORDER BY created_at DESC LIMIT 200")
        return [_ser(dict(r)) for r in cur.fetchall()]


def get_pr_by_id(db_id: int):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM pr_analyses WHERE id=%s", (db_id,))
        row = cur.fetchone()
        return _ser(dict(row)) if row else None


def delete_pr_analysis(db_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pr_analyses WHERE id=%s RETURNING id", (db_id,))
        return cur.fetchone() is not None


def get_stats() -> dict:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                COUNT(*)                                                  AS total,
                COUNT(*) FILTER (WHERE risk_level='High')                 AS high_risk,
                COUNT(*) FILTER (WHERE risk_level='Medium')               AS medium_risk,
                COUNT(*) FILTER (WHERE risk_level='Low')                  AS low_risk,
                COUNT(*) FILTER (WHERE release_conflict = TRUE)           AS conflicts,
                COUNT(*) FILTER (WHERE merge_conflicts  = TRUE)           AS merge_conflicts,
                COUNT(*) FILTER (WHERE signoff_required = TRUE)           AS signoffs_needed
            FROM pr_analyses
        """)
        stats = dict(cur.fetchone())

        # Count unique teams via SQL (avoids pulling all rows into Python)
        cur.execute("""
            SELECT COUNT(DISTINCT team) AS unique_teams
            FROM pr_analyses,
                 jsonb_array_elements_text(impacted_teams) AS team
        """)
        stats["unique_teams"] = cur.fetchone()["unique_teams"]

        # Payment stats
        cur.execute("""
            SELECT
                COUNT(*)                                        AS total,
                COUNT(*) FILTER (WHERE status='completed')      AS completed,
                COUNT(*) FILTER (WHERE status='pending')        AS pending,
                COALESCE(SUM(amount), 0)                        AS total_amount
            FROM payments
        """)
        prow = dict(cur.fetchone())
        stats["payments"] = {
            k: float(v) if hasattr(v, "__class__") and v.__class__.__name__ == "Decimal" else v
            for k, v in prow.items()
        }

    return stats


# ── PR Comments ───────────────────────────────────────────────────────────────
def create_pr_comment(pr_db_id, author, comment, comment_type, file_ref, ai_response) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pr_comments "
            "(pr_db_id, author, comment, comment_type, file_ref, ai_response) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (pr_db_id, author, comment, comment_type, file_ref, ai_response),
        )
        return cur.fetchone()[0]


def get_pr_comments(pr_db_id: int) -> list:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM pr_comments WHERE pr_db_id=%s ORDER BY created_at",
            (pr_db_id,),
        )
        return [_ser(dict(r)) for r in cur.fetchall()]


def update_pr_comment(cid: int, text: str) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE pr_comments SET comment=%s, updated_at=NOW() WHERE id=%s RETURNING id",
            (text, cid),
        )
        return cur.fetchone() is not None


def delete_pr_comment(cid: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pr_comments WHERE id=%s RETURNING id", (cid,))
        return cur.fetchone() is not None


# ── Serialization helper ──────────────────────────────────────────────────────
def _ser(row: dict) -> dict:
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            row[k] = v.isoformat()
        elif hasattr(v, "__class__") and v.__class__.__name__ == "Decimal":
            row[k] = float(v)
    return row
