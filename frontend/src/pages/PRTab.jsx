import { useState, useEffect } from "react";
import { fetchPRs, deletePR, rerunPR, runAgentZed } from "../api";

const RISK_COLOR = { High:"#ef4444", Medium:"#f59e0b", Low:"#22c55e", Unknown:"#6b7280" };
const EVENT_ICON = { approved:"✅", merged:"🔀", manual:"⚡", opened:"📂", rerun:"🔄" };
const TEAM_COLOR = {
  "Payments Team":"#3b82f6","QA Payments":"#f59e0b","Platform Team":"#22c55e",
  "Release Manager":"#8b5cf6","Security Team":"#ef4444","Backend Team":"#06b6d4",
  "QA Lead":"#ec4899","DBA Team":"#f97316","Orders Team":"#84cc16",
};

function timeAgo(iso) {
  const m = Math.floor((Date.now()-new Date(iso))/60000);
  if(m<1) return "just now"; if(m<60) return `${m}m ago`;
  const h=Math.floor(m/60); if(h<24) return `${h}h ago`;
  return `${Math.floor(h/24)}d ago`;
}

export default function PRTab({ onSelect, onDataChange }) {
  const [prs,        setPrs]        = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [search,     setSearch]     = useState("");
  const [filter,     setFilter]     = useState("all");
  const [showTrigger,setShowTrigger]= useState(false);
  const [actioning,  setActioning]  = useState(null);

  const load = async () => {
    setLoading(true);
    try { setPrs(await fetchPRs()); } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const filtered = prs.filter(pr => {
    const mf = filter==="all" || pr.risk_level?.toLowerCase()===filter || pr.event_type===filter;
    const q  = search.toLowerCase();
    const ms = !q || pr.title?.toLowerCase().includes(q) || pr.pr_id?.includes(q) || pr.author?.toLowerCase().includes(q);
    return mf && ms;
  });

  async function handleDelete(e, id) {
    e.stopPropagation();
    if (!confirm("Delete this PR analysis?")) return;
    setActioning(id);
    try { await deletePR(id); load(); onDataChange(); } catch(ex) { alert(ex.message); }
    setActioning(null);
  }

  async function handleRerun(e, id) {
    e.stopPropagation();
    setActioning(id);
    try { await rerunPR(id); load(); onDataChange(); } catch(ex) { alert(ex.message); }
    setActioning(null);
  }

  return (
    <div style={{ animation:"fadeIn 0.2s ease" }}>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14, flexWrap:"wrap", gap:10 }}>
        <div>
          <h2 style={{ color:"#e6edf3", fontSize:16, fontWeight:700 }}>🤖 Agent Zed — PR Intelligence</h2>
          <p style={{ fontSize:12, color:"#6b7280", marginTop:3 }}>
            GitHub webhooks trigger 4 AI agents automatically on every PR approve/merge
          </p>
        </div>
        <button onClick={() => setShowTrigger(true)} style={{ background:"linear-gradient(135deg,#1d4ed8,#4c1d95)",border:"none",color:"#fff",padding:"9px 18px",borderRadius:8,cursor:"pointer",fontSize:13,fontWeight:600 }}>
          ⚡ Run Agent Manually
        </button>
      </div>

      {/* How it works */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:16 }}>
        {[
          ["🕵️","PR First Responder","Reviews code style, missing tests, merge conflicts","#3b82f6"],
          ["🎯","Impact Analysis","Maps files → teams → dependency risk","#f59e0b"],
          ["🚀","Release Intelligence","Checks calendar conflicts, stakeholders","#ef4444"],
          ["🧠","RAG Knowledge","Captures senior patterns, grows smarter","#10b981"],
        ].map(([icon,name,desc,c]) => (
          <div key={name} style={{ background:"#0d1117",border:`1px solid ${c}25`,borderLeft:`3px solid ${c}`,borderRadius:8,padding:"10px 12px" }}>
            <div style={{ color:c,fontWeight:700,fontSize:12,marginBottom:3 }}>{icon} {name}</div>
            <div style={{ fontSize:11,color:"#6b7280",lineHeight:1.5 }}>{desc}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display:"flex", gap:8, marginBottom:12, flexWrap:"wrap" }}>
        <input placeholder="🔍 Search PR, title, author..."
          value={search} onChange={e=>setSearch(e.target.value)}
          style={{ flex:1,minWidth:200,background:"#0d1117",border:"1px solid #30363d",borderRadius:8,padding:"8px 14px",color:"#e6edf3",fontSize:13,outline:"none",fontFamily:"inherit" }}
        />
        {["all","high","medium","low","approved","merged","manual"].map(f=>(
          <button key={f} onClick={()=>setFilter(f)} style={{
            background:filter===f?"#1e3a5f":"transparent",
            border:`1px solid ${filter===f?"#3b82f6":"#30363d"}`,
            color:filter===f?"#93c5fd":"#6b7280",
            padding:"7px 12px",borderRadius:8,cursor:"pointer",fontSize:11,
            textTransform:"uppercase",letterSpacing:"0.04em",
          }}>{f}</button>
        ))}
      </div>

      {/* Table */}
      <div style={{ background:"#0d1117",border:"1px solid #21262d",borderRadius:10,overflow:"hidden" }}>
        <div style={{ display:"grid",gridTemplateColumns:"44px 1fr 130px 160px 140px 90px 80px",padding:"10px 16px",borderBottom:"1px solid #21262d",fontSize:11,color:"#6b7280",fontWeight:700,textTransform:"uppercase",letterSpacing:"0.06em" }}>
          <span></span><span>PR / Title</span><span>Files</span><span>Teams</span><span>Risk / Status</span><span>Time</span><span>Actions</span>
        </div>

        {loading ? <Skeleton /> : filtered.length===0 ? (
          <div style={{ padding:40,textAlign:"center",color:"#6b7280",fontSize:13 }}>
            {prs.length===0
              ? "⏳ No PR analyses yet. Approve a GitHub PR or click ⚡ Run Agent Manually"
              : "No results match your filter."}
          </div>
        ) : filtered.map(pr => (
          <PRRow key={pr.id} pr={pr}
            onClick={()=>onSelect(pr)}
            onDelete={e=>handleDelete(e,pr.id)}
            onRerun={e=>handleRerun(e,pr.id)}
            isActioning={actioning===pr.id}
          />
        ))}
      </div>

      <div style={{ marginTop:10,fontSize:12,color:"#6b7280" }}>
        {filtered.length} PR analyses shown
      </div>

      {showTrigger && (
        <ManualTriggerModal
          onClose={()=>setShowTrigger(false)}
          onSuccess={()=>{ setShowTrigger(false); load(); onDataChange(); }}
        />
      )}
    </div>
  );
}

function PRRow({ pr, onClick, onDelete, onRerun, isActioning }) {
  const risk = pr.risk_level||"Unknown";
  const rc   = RISK_COLOR[risk]||"#6b7280";
  return (
    <div onClick={onClick} style={{ display:"grid",gridTemplateColumns:"44px 1fr 130px 160px 140px 90px 80px",alignItems:"center",padding:"12px 16px",cursor:"pointer",borderBottom:"1px solid #161b22",transition:"background 0.12s",opacity:isActioning?0.5:1 }}
      onMouseEnter={e=>e.currentTarget.style.background="#0f1724"}
      onMouseLeave={e=>e.currentTarget.style.background="transparent"}
    >
      <div style={{ fontSize:20,textAlign:"center" }}>{EVENT_ICON[pr.event_type]||"📋"}</div>

      <div style={{ minWidth:0 }}>
        <div style={{ display:"flex",gap:8,marginBottom:4,flexWrap:"wrap",alignItems:"center" }}>
          <span style={{ fontFamily:"monospace",fontSize:11,color:"#3b82f6" }}>#{pr.pr_id}</span>
          <span style={{ color:"#e6edf3",fontSize:13,fontWeight:500,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap" }}>{pr.title}</span>
        </div>
        <div style={{ display:"flex",gap:10,fontSize:11,color:"#6b7280",flexWrap:"wrap" }}>
          <span>👤 {pr.author}</span>
          <span>📦 {(pr.repo||"").split("/")[1]||pr.repo}</span>
          {pr.reviewer && <span>✅ {pr.reviewer}</span>}
          <span style={{ background:"#1e3a5f",color:"#93c5fd",padding:"1px 6px",borderRadius:4,fontSize:10,fontFamily:"monospace" }}>{pr.base_branch||"main"}</span>
        </div>
      </div>

      <div>
        {(pr.files_changed||[]).slice(0,2).map(f=>(
          <div key={f} style={{ fontSize:10,background:"#161b22",border:"1px solid #21262d",borderRadius:4,padding:"2px 6px",marginBottom:3,fontFamily:"monospace",color:"#9ca3af",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap" }}>
            {f.split("/").pop()}
          </div>
        ))}
        {(pr.files_changed||[]).length>2 && <div style={{ fontSize:10,color:"#6b7280" }}>+{pr.files_changed.length-2} more</div>}
      </div>

      <div>
        {(pr.impacted_teams||[]).slice(0,2).map(t=>(
          <span key={t} style={{ display:"inline-block",fontSize:10,padding:"2px 7px",borderRadius:10,background:`${TEAM_COLOR[t]||"#9ca3af"}18`,color:TEAM_COLOR[t]||"#9ca3af",border:`1px solid ${TEAM_COLOR[t]||"#9ca3af"}30`,marginBottom:3,marginRight:3,whiteSpace:"nowrap" }}>{t}</span>
        ))}
        {(pr.impacted_teams||[]).length>2 && <div style={{ fontSize:10,color:"#6b7280" }}>+{pr.impacted_teams.length-2}</div>}
      </div>

      <div>
        <span style={{ display:"inline-block",fontSize:11,fontWeight:700,padding:"3px 10px",borderRadius:20,background:`${rc}18`,color:rc,border:`1px solid ${rc}40` }}>{risk}</span>
        <div style={{ marginTop:4,display:"flex",flexDirection:"column",gap:2 }}>
          {pr.release_conflict && <span style={{ fontSize:10,color:"#f59e0b" }}>⚠ Conflict</span>}
          {pr.signoff_required && <span style={{ fontSize:10,color:"#ef4444" }}>🔒 Sign-off</span>}
          {pr.merge_conflicts  && <span style={{ fontSize:10,color:"#8b5cf6" }}>🔀 Merge risk</span>}
        </div>
      </div>

      <div style={{ fontSize:11,color:"#6b7280",textAlign:"center" }}>{timeAgo(pr.created_at)}</div>

      <div style={{ display:"flex",flexDirection:"column",gap:4 }} onClick={e=>e.stopPropagation()}>
        <button onClick={onRerun}  style={{ background:"#1e3a5f",border:"1px solid #3b82f640",color:"#3b82f6",padding:"4px 6px",borderRadius:6,cursor:"pointer",fontSize:12,width:"100%" }} title="Re-run">{isActioning?"⏳":"🔄"}</button>
        <button onClick={onDelete} style={{ background:"#2d1010",border:"1px solid #ef444440",color:"#ef4444",padding:"4px 6px",borderRadius:6,cursor:"pointer",fontSize:12,width:"100%" }} title="Delete">🗑</button>
      </div>
    </div>
  );
}

function ManualTriggerModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({
    pr_id:"PR-121", title:"Add payment CRUD API with validation",
    files:"routers/payments.py\ndatabase.py",
    author:"Sathish271995", repo:"Sathish271995/AgentZed",
    base_branch:"main", head_branch:"feature/payment-crud",
    body:"Implements full payment CRUD with validation.",
  });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");
  const set = (k,v) => setForm(f=>({...f,[k]:v}));

  async function handleRun() {
    setLoading(true); setError("");
    try {
      await runAgentZed({
        pr_id:         form.pr_id.trim(),
        title:         form.title.trim(),
        files_changed: form.files.split("\n").map(s=>s.trim()).filter(Boolean),
        author:        form.author.trim(),
        repo:          form.repo.trim(),
        base_branch:   form.base_branch.trim(),
        head_branch:   form.head_branch.trim(),
        body:          form.body.trim(),
        event_type:    "manual",
      });
      onSuccess();
    } catch(e) { setError(e.message); setLoading(false); }
  }

  return (
    <>
      <div onClick={onClose} style={{ position:"fixed",inset:0,background:"rgba(0,0,0,0.65)",zIndex:199 }} />
      <div style={{ position:"fixed",top:"50%",left:"50%",transform:"translate(-50%,-50%)",background:"#0d1117",border:"1px solid #30363d",borderRadius:14,padding:"26px 28px",width:"min(560px,95vw)",zIndex:200,animation:"fadeIn 0.2s ease",maxHeight:"90vh",overflowY:"auto" }}>
        <h3 style={{ color:"#e6edf3",fontSize:16,marginBottom:4 }}>⚡ Run Agent Zed Manually</h3>
        <p style={{ color:"#6b7280",fontSize:12,marginBottom:18 }}>
          Triggers all 4 AI agents: PR Review → Impact → Release → RAG Knowledge
        </p>

        <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:10 }}>
          <F label="PR ID"       value={form.pr_id}       onChange={v=>set("pr_id",v)} />
          <F label="Author"      value={form.author}      onChange={v=>set("author",v)} />
        </div>
        <F label="PR Title"      value={form.title}       onChange={v=>set("title",v)} />
        <F label="Repository"    value={form.repo}        onChange={v=>set("repo",v)} />
        <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:10 }}>
          <F label="Base Branch" value={form.base_branch} onChange={v=>set("base_branch",v)} />
          <F label="Head Branch" value={form.head_branch} onChange={v=>set("head_branch",v)} />
        </div>
        <div style={{ marginBottom:12 }}>
          <Lbl>Files Changed (one per line)</Lbl>
          <textarea value={form.files} onChange={e=>set("files",e.target.value)} rows={3} style={inp} />
        </div>
        <div style={{ marginBottom:14 }}>
          <Lbl>PR Description</Lbl>
          <textarea value={form.body} onChange={e=>set("body",e.target.value)} rows={2} style={inp} />
        </div>

        {error && <div style={{ background:"#1a0a0a",border:"1px solid #ef444440",borderRadius:6,padding:"8px 12px",fontSize:12,color:"#f87171",marginBottom:12 }}>❌ {error}</div>}

        <div style={{ display:"flex",gap:10,justifyContent:"flex-end" }}>
          <button onClick={onClose} style={{ background:"transparent",border:"1px solid #30363d",color:"#8b949e",padding:"9px 18px",borderRadius:8,cursor:"pointer",fontSize:13 }}>Cancel</button>
          <button onClick={handleRun} disabled={loading} style={{ background:loading?"#1e3a5f":"linear-gradient(135deg,#1d4ed8,#4c1d95)",border:"none",color:"#fff",padding:"9px 22px",borderRadius:8,cursor:loading?"wait":"pointer",fontSize:13,fontWeight:600 }}>
            {loading ? "🤖 Running 4 agents..." : "⚡ Run All Agents"}
          </button>
        </div>
      </div>
    </>
  );
}

function Skeleton() {
  return <>{[1,2,3].map(i=><div key={i} style={{ height:72,margin:"1px 0",background:"linear-gradient(90deg,#161b22 25%,#21262d 50%,#161b22 75%)",backgroundSize:"400px 100%",animation:"shimmer 1.4s infinite" }} />)}</>;
}

function F({ label, value, onChange }) {
  return <div style={{ marginBottom:12 }}><Lbl>{label}</Lbl><input value={value} onChange={e=>onChange(e.target.value)} style={{ ...inp,resize:undefined }} /></div>;
}
function Lbl({ children }) {
  return <div style={{ fontSize:11,color:"#8b949e",marginBottom:5,textTransform:"uppercase",letterSpacing:"0.05em" }}>{children}</div>;
}
const inp = { width:"100%",background:"#070b14",border:"1px solid #30363d",borderRadius:8,padding:"8px 12px",color:"#e6edf3",fontSize:13,outline:"none",fontFamily:"'IBM Plex Mono',monospace",resize:"vertical" };
