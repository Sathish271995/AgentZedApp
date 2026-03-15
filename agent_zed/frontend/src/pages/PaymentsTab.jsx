import { useState, useEffect, useRef } from "react";
import { fetchPayments, createPayment, updatePayment, deletePayment, refundPayment } from "../api";

const STATUS_COLOR = { pending: "#f59e0b", completed: "#22c55e", failed: "#ef4444", refunded: "#8b5cf6" };
const STATUS_ICON  = { pending: "⏳", completed: "✅", failed: "❌", refunded: "↩️" };

export default function PaymentsTab({ reloadSignal, onDataChange }) {
  const [payments,   setPayments]   = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [showForm,   setShowForm]   = useState(false);
  const [editItem,   setEditItem]   = useState(null);
  const [filter,     setFilter]     = useState("");
  const [custFilter, setCustFilter] = useState("");
  const [error,      setError]      = useState("");
  const [confirmModal, setConfirmModal] = useState(null); // { type, id, msg }

  // Debounce customer filter — avoids firing an API call on every keystroke
  const debounceRef = useRef(null);
  const debouncedCust = useRef(custFilter);

  const load = async (signal) => {
    setLoading(true);
    setError("");
    try {
      const qs = [
        filter               && `status=${filter}`,
        debouncedCust.current && `customer_id=${debouncedCust.current}`,
      ].filter(Boolean).join("&");
      const res = await fetchPayments(qs ? `?${qs}` : "", signal);
      setPayments(res.payments || []);
    } catch (ex) {
      if (ex.name !== "AbortError") setError(ex.message);
    } finally {
      setLoading(false);
    }
  };

  // Reload when filter or reloadSignal changes
  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [filter, reloadSignal]);

  // Debounce customer ID filter
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      debouncedCust.current = custFilter;
      load();
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [custFilter]);

  // Confirm modal helpers
  const askConfirm = (type, id, msg) => setConfirmModal({ type, id, msg });
  const clearConfirm = () => setConfirmModal(null);

  async function handleConfirmed() {
    const { type, id } = confirmModal;
    clearConfirm();
    try {
      if (type === "delete") await deletePayment(id);
      if (type === "refund") await refundPayment(id);
      load();
      onDataChange();
    } catch (ex) {
      setError(ex.message);
    }
  }

  const handleStatus = async (id, status) => {
    try {
      await updatePayment(id, { status });
      load();
      onDataChange();
    } catch (ex) {
      setError(ex.message);
    }
  };

  return (
    <div style={{ animation: "fadeIn 0.2s ease" }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
        <div>
          <h2 style={{ color: "#e6edf3", fontSize: 16, fontWeight: 700 }}>💳 Payment Management</h2>
          <p style={{ fontSize: 12, color: "#6b7280", marginTop: 3 }}>
            Full CRUD — create, view, update, delete, refund payments
          </p>
        </div>
        <button
          onClick={() => { setEditItem(null); setShowForm(true); }}
          style={primaryBtn}
        >
          + New Payment
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
        <select value={filter} onChange={e => setFilter(e.target.value)} style={selectStyle}>
          <option value="">All statuses</option>
          {["pending", "completed", "failed", "refunded"].map(s => (
            <option key={s} value={s}>{STATUS_ICON[s]} {s}</option>
          ))}
        </select>
        <input
          placeholder="Filter by customer ID..."
          value={custFilter}
          onChange={e => setCustFilter(e.target.value)}
          style={inputStyle}
        />
        <button onClick={load} style={secBtn}>⟳ Reload</button>
      </div>

      {error && <Alert msg={error} onClose={() => setError("")} />}

      {/* Table */}
      <div style={{ background: "#0d1117", border: "1px solid #21262d", borderRadius: 10, overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "60px 1fr 100px 80px 110px 100px 180px", padding: "10px 16px", borderBottom: "1px solid #21262d", fontSize: 11, color: "#6b7280", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>
          <span>ID</span>
          <span>Description / Customer</span>
          <span>Amount</span>
          <span>Currency</span>
          <span>Status</span>
          <span>Created</span>
          <span>Actions</span>
        </div>

        {loading ? <Skeleton /> : payments.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "#6b7280" }}>
            No payments found. Click <b>+ New Payment</b> to create one.
          </div>
        ) : payments.map(p => (
          <div key={p.id} style={{ display: "grid", gridTemplateColumns: "60px 1fr 100px 80px 110px 100px 180px", alignItems: "center", padding: "12px 16px", borderBottom: "1px solid #161b22", animation: "fadeIn 0.2s ease" }}>
            <span style={{ fontFamily: "monospace", fontSize: 12, color: "#3b82f6" }}>#{p.id}</span>

            <div>
              <div style={{ color: "#e6edf3", fontSize: 13, fontWeight: 500 }}>{p.description || "—"}</div>
              <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>👤 {p.customer_id}</div>
            </div>

            <div style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 700, color: "#22c55e" }}>
              ${Number(p.amount).toFixed(2)}
            </div>

            <div style={{ fontSize: 12, color: "#9ca3af" }}>{p.currency}</div>

            <div>
              <span style={{ background: `${STATUS_COLOR[p.status] || "#6b7280"}20`, color: STATUS_COLOR[p.status] || "#6b7280", border: `1px solid ${STATUS_COLOR[p.status] || "#6b7280"}40`, padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700 }}>
                {STATUS_ICON[p.status]} {p.status}
              </span>
            </div>

            <div style={{ fontSize: 11, color: "#6b7280" }}>
              {new Date(p.created_at).toLocaleDateString()}
            </div>

            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {p.status === "pending" && (
                <button onClick={() => handleStatus(p.id, "completed")} style={actBtn("#0f2a1a", "#22c55e")} title="Mark completed">✓</button>
              )}
              {p.status === "pending" && (
                <button onClick={() => handleStatus(p.id, "failed")} style={actBtn("#2d1010", "#ef4444")} title="Mark failed">✗</button>
              )}
              {p.status === "completed" && (
                <button onClick={() => askConfirm("refund", p.id, `Refund payment #${p.id} ($${p.amount})?`)} style={actBtn("#1a0a2e", "#8b5cf6")} title="Refund">↩</button>
              )}
              <button onClick={() => { setEditItem(p); setShowForm(true); }} style={actBtn("#1e3a5f", "#3b82f6")} title="Edit">✏</button>
              <button onClick={() => askConfirm("delete", p.id, `Delete payment #${p.id}? This cannot be undone.`)} style={actBtn("#2d1010", "#ef4444")} title="Delete">🗑</button>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 10, fontSize: 12, color: "#6b7280" }}>
        Total: {payments.length} payments
      </div>

      {/* Confirm modal (replaces native browser confirm()) */}
      {confirmModal && (
        <ConfirmModal
          msg={confirmModal.msg}
          onConfirm={handleConfirmed}
          onCancel={clearConfirm}
        />
      )}

      {showForm && (
        <PaymentForm
          item={editItem}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load(); onDataChange(); }}
        />
      )}
    </div>
  );
}

// ── Payment Create/Edit Form ──────────────────────────────────────────────────
function PaymentForm({ item, onClose, onSaved }) {
  const isEdit = !!item;
  const [form, setForm] = useState({
    amount:      item?.amount    ?? "",
    currency:    item?.currency  ?? "USD",
    customer_id: item?.customer_id ?? "",
    description: item?.description ?? "",
    status:      item?.status    ?? "pending",
  });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit() {
    const amt = parseFloat(form.amount);
    if (!form.customer_id.trim()) {
      setError("Customer ID is required");
      return;
    }
    if (isNaN(amt) || amt <= 0) {
      setError("Amount must be a positive number");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload = { ...form, amount: amt };
      if (isEdit) await updatePayment(item.id, payload);
      else        await createPayment(payload);
      onSaved();
    } catch (ex) {
      setError(ex.message);
      setLoading(false);
    }
  }

  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 199 }} />
      <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", background: "#0d1117", border: "1px solid #30363d", borderRadius: 14, padding: "26px 28px", width: "min(480px,95vw)", zIndex: 200, animation: "fadeIn 0.2s ease" }}>
        <h3 style={{ color: "#e6edf3", fontSize: 16, marginBottom: 16 }}>
          {isEdit ? "✏️ Edit Payment" : "💳 New Payment"}
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <Label>Amount ($) *</Label>
            <input
              type="number" step="0.01" min="0.01"
              value={form.amount}
              onChange={e => set("amount", e.target.value)}
              style={inputStyle}
              placeholder="250.00"
            />
          </div>
          <div>
            <Label>Currency</Label>
            <select value={form.currency} onChange={e => set("currency", e.target.value)} style={inputStyle}>
              {["USD", "EUR", "GBP", "INR"].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <Label>Customer ID *</Label>
          <input value={form.customer_id} onChange={e => set("customer_id", e.target.value)} style={inputStyle} placeholder="CUST-001" />
        </div>
        <div style={{ marginBottom: 12 }}>
          <Label>Description</Label>
          <input value={form.description} onChange={e => set("description", e.target.value)} style={inputStyle} placeholder="Order #1042" />
        </div>
        {isEdit && (
          <div style={{ marginBottom: 12 }}>
            <Label>Status</Label>
            <select value={form.status} onChange={e => set("status", e.target.value)} style={inputStyle}>
              {["pending", "completed", "failed", "refunded"].map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
        )}

        {error && <Alert msg={error} onClose={() => setError("")} />}

        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 16 }}>
          <button onClick={onClose} style={secBtn}>Cancel</button>
          <button onClick={handleSubmit} disabled={loading} style={primaryBtn}>
            {loading ? "Saving..." : isEdit ? "Update Payment" : "Create Payment"}
          </button>
        </div>
      </div>
    </>
  );
}

// ── Confirm Modal (replaces native browser confirm()) ─────────────────────────
function ConfirmModal({ msg, onConfirm, onCancel }) {
  return (
    <>
      <div onClick={onCancel} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 299 }} />
      <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", background: "#0d1117", border: "1px solid #30363d", borderRadius: 12, padding: "24px 28px", width: "min(380px,95vw)", zIndex: 300, animation: "fadeIn 0.15s ease" }}>
        <p style={{ color: "#e6edf3", fontSize: 14, marginBottom: 20, lineHeight: 1.6 }}>{msg}</p>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onCancel}  style={secBtn}>Cancel</button>
          <button onClick={onConfirm} style={{ ...primaryBtn, background: "#7f1d1d", border: "1px solid #ef444460" }}>Confirm</button>
        </div>
      </div>
    </>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function Skeleton() {
  return (
    <>
      {[1, 2, 3, 4].map(i => (
        <div key={i} style={{ height: 60, margin: "1px 0", background: "linear-gradient(90deg,#161b22 25%,#21262d 50%,#161b22 75%)", backgroundSize: "400px 100%", animation: "shimmer 1.4s infinite" }} />
      ))}
    </>
  );
}

function Alert({ msg, onClose }) {
  return (
    <div style={{ background: "#1a0a0a", border: "1px solid #ef444440", borderRadius: 8, padding: "8px 14px", fontSize: 12, color: "#f87171", marginBottom: 12, display: "flex", justifyContent: "space-between" }}>
      ❌ {msg}
      <button onClick={onClose} style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer" }}>×</button>
    </div>
  );
}

function Label({ children }) {
  return <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.05em" }}>{children}</div>;
}

const inputStyle  = { width: "100%", background: "#070b14", border: "1px solid #30363d", borderRadius: 8, padding: "8px 12px", color: "#e6edf3", fontSize: 13, outline: "none", fontFamily: "'IBM Plex Mono',monospace" };
const selectStyle = { background: "#0d1117", border: "1px solid #30363d", borderRadius: 8, padding: "8px 12px", color: "#e6edf3", fontSize: 12, outline: "none", fontFamily: "inherit" };
const primaryBtn  = { background: "linear-gradient(135deg,#1d4ed8,#4c1d95)", border: "none", color: "#fff", padding: "9px 20px", borderRadius: 8, cursor: "pointer", fontSize: 13, fontWeight: 600 };
const secBtn      = { background: "#21262d", border: "1px solid #30363d", color: "#8b949e", padding: "9px 18px", borderRadius: 8, cursor: "pointer", fontSize: 13 };
const actBtn      = (bg, c) => ({ background: bg, border: `1px solid ${c}40`, color: c, padding: "5px 9px", borderRadius: 6, cursor: "pointer", fontSize: 12 });
