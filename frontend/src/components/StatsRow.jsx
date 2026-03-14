export default function StatsRow({ stats }) {
  const p = stats?.payments || {};
  const cards = [
    { label:"Payments Total",   value: p.total ?? 0,      icon:"💳", color:"#3b82f6" },
    { label:"Completed",        value: p.completed ?? 0,  icon:"✅", color:"#22c55e" },
    { label:"Pending",          value: p.pending ?? 0,    icon:"⏳", color:"#f59e0b" },
    { label:"Revenue",          value:`$${Number(p.total_amount||0).toFixed(0)}`, icon:"💰", color:"#10b981" },
    { label:"PRs Analyzed",     value: stats?.total ?? 0,         icon:"📊", color:"#8b5cf6" },
    { label:"High Risk PRs",    value: stats?.high_risk ?? 0,     icon:"🔴", color:"#ef4444" },
    { label:"Release Conflicts",value: stats?.conflicts ?? 0,     icon:"⚠️", color:"#f59e0b" },
    { label:"Teams Impacted",   value: stats?.unique_teams ?? 0,  icon:"👥", color:"#06b6d4" },
  ];

  return (
    <div style={{ display:"grid", gridTemplateColumns:"repeat(8,1fr)", gap:10, margin:"18px 0" }}>
      {cards.map(c => (
        <div key={c.label} style={{
          background:"#0d1117", border:"1px solid #21262d", borderRadius:10, padding:"12px 14px",
        }}>
          <div style={{ fontSize:18, marginBottom:4 }}>{c.icon}</div>
          <div style={{ fontSize:24, fontWeight:700, color:c.color, fontFamily:"monospace", lineHeight:1 }}>{c.value}</div>
          <div style={{ fontSize:10, color:"#6b7280", marginTop:4, lineHeight:1.3 }}>{c.label}</div>
        </div>
      ))}
    </div>
  );
}
