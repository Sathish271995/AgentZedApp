const BASE = "http://localhost:8000";

async function req(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// ── Stats ──────────────────────────────────────────────────────────────────
export const fetchStats = () => req("GET", "/api/stats");

// ── Payments ───────────────────────────────────────────────────────────────
export const fetchPayments  = (qs = "") => req("GET", `/api/payments/${qs}`);
export const createPayment  = (data)    => req("POST", "/api/payments/", data);
export const updatePayment  = (id,data) => req("PUT",  `/api/payments/${id}`, data);
export const deletePayment  = (id)      => req("DELETE",`/api/payments/${id}`);
export const refundPayment  = (id)      => req("POST", `/api/payments/${id}/refund`);

// ── PR Analyses ────────────────────────────────────────────────────────────
export const fetchPRs       = ()     => req("GET",    "/api/pr-analyses");
export const fetchPRById    = (id)   => req("GET",    `/api/pr-analyses/${id}`);
export const deletePR       = (id)   => req("DELETE", `/api/pr-analyses/${id}`);
export const rerunPR        = (id)   => req("POST",   `/api/pr-analyses/${id}/rerun`);
export const runAgentZed    = (data) => req("POST",   "/run-agent-zed", data);

// ── PR Comments ────────────────────────────────────────────────────────────
export const fetchComments  = (prId)        => req("GET",    `/api/pr-analyses/${prId}/comments`);
export const postComment    = (prId, data)  => req("POST",   `/api/pr-analyses/${prId}/comments`, data);
export const putComment     = (prId,cId,d)  => req("PUT",    `/api/pr-analyses/${prId}/comments/${cId}`, d);
export const deleteComment  = (prId, cId)   => req("DELETE", `/api/pr-analyses/${prId}/comments/${cId}`);
