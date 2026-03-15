// Pulse animation is defined here (self-contained — no implicit dependency on App.jsx)
const TOPBAR_STYLE = `
  @keyframes topbar-pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
`;

export default function Topbar({ onRefresh }) {
  return (
    <>
      <style>{TOPBAR_STYLE}</style>
      <div style={{
        background: "#0d1117", borderBottom: "1px solid #21262d",
        padding: "0 24px", display: "flex", alignItems: "center",
        gap: 14, height: 58,
      }}>
        {/* Logo */}
        <div style={{
          width: 38, height: 38, borderRadius: 10,
          background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 22, flexShrink: 0,
        }}>🤖</div>

        {/* Title */}
        <div>
          <span style={{ fontFamily: "'IBM Plex Mono',monospace", fontWeight: 700, fontSize: 17, color: "#e6edf3" }}>
            Agent <span style={{ color: "#3b82f6" }}>Zed</span>
          </span>
          <span style={{ fontSize: 11, color: "#6b7280", marginLeft: 10 }}>
            Payment Intelligence · GitHub PR Analysis
          </span>
        </div>

        <div style={{ flex: 1 }} />

        {/* Pipeline breadcrumb */}
        <div style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 11, color: "#6b7280", flexWrap: "wrap" }}>
          {["💳 Payment CRUD", "→", "📡 GitHub PR", "→", "🤖 4 AI Agents", "→", "🗄 PostgreSQL", "→", "📧 Email Teams"].map((s, i) => (
            <span key={i} style={{ color: s === "→" ? "#374151" : "#9ca3af" }}>{s}</span>
          ))}
        </div>

        {/* Live indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#22c55e" }}>
          <span style={{
            width: 7, height: 7, borderRadius: "50%",
            background: "#22c55e", display: "inline-block",
            animation: "topbar-pulse 2s infinite",
          }} />
          Live
        </div>

        {/* Refresh button */}
        <button onClick={onRefresh} style={btnStyle}>⟳ Refresh</button>
      </div>
    </>
  );
}

const btnStyle = {
  background: "#21262d", border: "1px solid #8b949e40", color: "#8b949e",
  padding: "7px 14px", borderRadius: 8, cursor: "pointer", fontSize: 12,
  fontFamily: "'IBM Plex Sans',sans-serif",
};
