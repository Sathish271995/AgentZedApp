export default function Topbar({ onRefresh }) {
  return (
    <div style={{
      background:"#0d1117", borderBottom:"1px solid #21262d",
      padding:"0 24px", display:"flex", alignItems:"center", gap:14, height:58,
    }}>
      <div style={{
        width:38, height:38, borderRadius:10,
        background:"linear-gradient(135deg,#3b82f6,#8b5cf6)",
        display:"flex", alignItems:"center", justifyContent:"center", fontSize:22, flexShrink:0,
      }}>🤖</div>

      <div>
        <span style={{ fontFamily:"'IBM Plex Mono',monospace", fontWeight:700, fontSize:17, color:"#e6edf3" }}>
          Agent <span style={{ color:"#3b82f6" }}>Zed</span>
        </span>
        <span style={{ fontSize:11, color:"#6b7280", marginLeft:10 }}>
          Payment Intelligence · GitHub PR Analysis
        </span>
      </div>

      <div style={{ flex:1 }} />

      {/* Pipeline flow */}
      <div style={{ display:"flex", gap:6, alignItems:"center", fontSize:11, color:"#6b7280", flexWrap:"wrap" }}>
        {["💳 Payment CRUD","→","📡 GitHub PR","→","🤖 4 AI Agents","→","🗄 PostgreSQL","→","📧 Email Teams"].map((s,i)=>(
          <span key={i} style={{ color: s==="→" ? "#374151" : "#9ca3af" }}>{s}</span>
        ))}
      </div>

      <div style={{ display:"flex", alignItems:"center", gap:5, fontSize:12, color:"#22c55e" }}>
        <span style={{ width:7, height:7, borderRadius:"50%", background:"#22c55e", display:"inline-block", animation:"pulse 2s infinite" }} />
        Live
      </div>

      <button onClick={onRefresh} style={btn("#21262d","#8b949e")}>⟳ Refresh</button>
    </div>
  );
}

const btn = (bg,c) => ({
  background:bg, border:`1px solid ${c}40`, color:c,
  padding:"7px 14px", borderRadius:8, cursor:"pointer", fontSize:12,
});
