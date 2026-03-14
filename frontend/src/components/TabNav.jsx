export default function TabNav({ tab, setTab }) {
  const tabs = [
    { id:"payments", label:"💳 Payment CRUD",        desc:"Create · Read · Update · Delete" },
    { id:"pr",       label:"🤖 Agent Zed — PR Analysis", desc:"4 AI Agents · GitHub Webhook" },
  ];
  return (
    <div style={{ display:"flex", gap:4, marginBottom:20, borderBottom:"1px solid #21262d", paddingBottom:0 }}>
      {tabs.map(t => (
        <button key={t.id} onClick={() => setTab(t.id)} style={{
          background: tab===t.id ? "#1e3a5f" : "transparent",
          border: "none",
          borderBottom: `3px solid ${tab===t.id ? "#3b82f6" : "transparent"}`,
          color: tab===t.id ? "#93c5fd" : "#6b7280",
          padding:"12px 20px 14px", cursor:"pointer",
          fontFamily:"'IBM Plex Sans',sans-serif", fontSize:14, fontWeight:600,
          display:"flex", flexDirection:"column", alignItems:"flex-start", gap:2,
        }}>
          {t.label}
          <span style={{ fontSize:10, fontWeight:400, color: tab===t.id ? "#6b7280" : "#374151" }}>
            {t.desc}
          </span>
        </button>
      ))}
    </div>
  );
}
