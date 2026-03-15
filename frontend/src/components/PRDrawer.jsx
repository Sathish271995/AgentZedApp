import { useState, useEffect } from "react";
import { fetchPRById, fetchComments, postComment, putComment, deleteComment } from "../api";

const RC  = { High:"#ef4444",Medium:"#f59e0b",Low:"#22c55e",Unknown:"#6b7280" };
const TC  = { "Payments Team":"#3b82f6","QA Payments":"#f59e0b","Platform Team":"#22c55e","Release Manager":"#8b5cf6","Security Team":"#ef4444","Backend Team":"#06b6d4","QA Lead":"#ec4899","DBA Team":"#f97316" };
const CMT = { bug:"🐛",style:"🎨",suggestion:"💡",question:"❓",general:"💬" };
const CTC = { bug:"#ef4444",style:"#f59e0b",suggestion:"#10b981",question:"#3b82f6",general:"#8b949e" };

function ago(iso) {
  const m=Math.floor((Date.now()-new Date(iso))/60000);
  if(m<1) return "just now"; if(m<60) return `${m}m ago`;
  const h=Math.floor(m/60); return h<24?`${h}h ago`:`${Math.floor(h/24)}d ago`;
}

export default function PRDrawer({ pr: init, onClose, onDataChange }) {
  const [pr,       setPr]       = useState(init);
  const [tab,      setTab]      = useState("review");
  const [comments, setComments] = useState([]);
  const [newC,     setNewC]     = useState({ author:"", comment:"", comment_type:"general", file_ref:"" });
  const [posting,  setPosting]  = useState(false);
  const [aiReply,  setAiReply]  = useState("");
  const [editId,   setEditId]   = useState(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    fetchPRById(init.id).then(setPr).catch(()=>{});
    loadComments();
  }, [init.id]);

  const loadComments = async () => {
    setComments(await fetchComments(init.id).catch(()=>[]));
  };

  const rv = pr.full_result?.["PR Review"]            ?? {};
  const ia = pr.full_result?.["Impact Analysis"]      ?? {};
  const ri = pr.full_result?.["Release Intelligence"] ?? {};
  const rg = pr.full_result?.["RAG Knowledge"]        ?? {};

  const TABS = [
    { id:"review",   label:"🕵️ PR Review",    badge: rv.risk_level||"?" },
    { id:"impact",   label:"🎯 Impact",        badge: `${(ia.impacted_teams||[]).length} teams` },
    { id:"release",  label:"🚀 Release",       badge: ri.release_conflict?"⚠ Conflict":"✓ Clear" },
    { id:"rag",      label:"🧠 RAG",           badge: `${(rg.patterns||[]).length} patterns` },
    { id:"comments", label:"💬 Comments",      badge: comments.length },
  ];

  async function handlePost() {
    if (!newC.comment.trim() || !newC.author.trim()) return;
    setPosting(true);
    try {
      const res = await postComment(init.id, newC);
      setAiReply(res.ai_response||"");
      setNewC(c=>({...c, comment:"", comment_type:"general", file_ref:""}));
      await loadComments();
    } catch(e) { alert(e.message); }
    setPosting(false);
  }

  async function handleEditSave(cid) {
    await putComment(init.id, cid, { comment: editText });
    setEditId(null);
    await loadComments();
  }

  async function handleDeleteComment(cid) {
    if (!confirm("Delete comment?")) return;
    await deleteComment(init.id, cid);
    await loadComments();
  }

  return (
    <>
      <div onClick={onClose} style={{ position:"fixed",inset:0,background:"rgba(0,0,0,0.55)",zIndex:99 }} />
      <div style={{ position:"fixed",top:0,right:0,bottom:0,width:"min(700px,100vw)",background:"#0d1117",borderLeft:"1px solid #21262d",overflowY:"auto",zIndex:100,animation:"slideInRight 0.28s cubic-bezier(0.16,1,0.3,1)",display:"flex",flexDirection:"column" }}>

        {/* PR Header */}
        <div style={{ padding:"22px 24px 0",flexShrink:0 }}>
          <button onClick={onClose} style={{ position:"absolute",top:14,right:16,background:"#21262d",border:"1px solid #30363d",color:"#8b949e",borderRadius:8,width:32,height:32,cursor:"pointer",fontSize:18 }}>×</button>

          <div style={{ display:"flex",gap:8,flexWrap:"wrap",alignItems:"center",marginBottom:8 }}>
            <Badge label={`#${pr.pr_id}`}      color="#3b82f6" />
            <Badge label={(pr.event_type||"").toUpperCase()} color="#6b7280" />
            <Badge label={rv.risk_level||pr.risk_level||"?"} color={RC[rv.risk_level||pr.risk_level]||"#6b7280"} />
            {rv.approval_recommendation && (
              <Badge label={rv.approval_recommendation}
                color={rv.approval_recommendation==="Approve"?"#22c55e":rv.approval_recommendation==="Request Changes"?"#ef4444":"#f59e0b"} />
            )}
          </div>

          <h2 style={{ color:"#e6edf3",fontSize:18,fontWeight:700,lineHeight:1.4,marginBottom:10,paddingRight:40 }}>{pr.title}</h2>

          <div style={{ display:"flex",flexWrap:"wrap",gap:12,fontSize:12,color:"#6b7280",marginBottom:12 }}>
            <span>👤 {pr.author}</span>
            {pr.reviewer && <span>✅ {pr.reviewer}</span>}
            <span>📦 {pr.repo}</span>
            <span>🕐 {ago(pr.created_at)}</span>
          </div>

          {/* Files */}
          <div style={{ display:"flex",flexWrap:"wrap",gap:6,marginBottom:6 }}>
            {(pr.files_changed||[]).map(f=>(
              <span key={f} style={{ display:"inline-flex",alignItems:"center",gap:4,background:"#1a1f2e",border:"1px solid #2a3347",borderRadius:5,padding:"3px 9px",color:"#c9d1d9",fontFamily:"monospace",fontSize:11 }}>
                <span style={{ color:{py:"#4ec9b0",js:"#f0c040",ts:"#569cd6"}[f.split(".").pop()]||"#aaa",fontSize:8 }}>●</span>{f}
              </span>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display:"flex",gap:1,padding:"14px 24px 0",borderBottom:"1px solid #21262d",flexShrink:0,overflowX:"auto" }}>
          {TABS.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} style={{
              background:tab===t.id?"#1e3a5f":"transparent",
              border:"none",borderBottom:`2px solid ${tab===t.id?"#3b82f6":"transparent"}`,
              color:tab===t.id?"#93c5fd":"#6b7280",
              padding:"8px 14px",cursor:"pointer",fontSize:12,fontFamily:"inherit",whiteSpace:"nowrap",
              display:"flex",alignItems:"center",gap:6,
            }}>
              {t.label}
              <span style={{ background:"#1f2937",color:"#9ca3af",borderRadius:10,padding:"1px 7px",fontSize:10 }}>{t.badge}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div style={{ flex:1,overflowY:"auto",padding:"20px 24px" }}>

          {/* ── PR REVIEW ─────────────────────────────────── */}
          {tab==="review" && (
            <div style={{ animation:"fadeIn 0.2s ease" }}>
              <AgentHdr icon="🕵️" title="PR FIRST RESPONDER AGENT" color="#3b82f6" conf={rv.confidence} />
              <p style={{ color:"#c9d1d9",fontSize:13,lineHeight:1.8,marginBottom:14 }}>{rv.summary||"No summary available."}</p>
              {rv.approval_reasoning && (
                <InfoBox color="#3b82f6" title="📋 Recommendation">
                  <strong style={{ color:rv.approval_recommendation==="Approve"?"#22c55e":"#ef4444" }}>{rv.approval_recommendation}</strong>
                  {" — "}{rv.approval_reasoning}
                </InfoBox>
              )}
              {rv.merge_conflicts && (
                <InfoBox color="#8b5cf6" title="🔀 Merge Conflict Risk">
                  Potential conflicts in: <strong>{(rv.merge_conflict_files||[]).join(", ")||"one or more files"}</strong>
                </InfoBox>
              )}
              <SubList title="🐛 Cosmetic / Style Issues" items={rv.cosmetic_issues} color="#f59e0b" />
              <SubList title="🧪 Missing Tests"           items={rv.missing_tests}   color="#06b6d4" />
              <SubList title="📝 Missing Documentation"   items={rv.missing_docs}    color="#8b5cf6" />
            </div>
          )}

          {/* ── IMPACT ────────────────────────────────────── */}
          {tab==="impact" && (
            <div style={{ animation:"fadeIn 0.2s ease" }}>
              <AgentHdr icon="🎯" title="IMPACT ANALYSIS AGENT" color="#f59e0b" conf={ia.confidence} />
              <div style={{ marginBottom:14 }}>
                <Lbl>Impacted Teams</Lbl>
                <div style={{ display:"flex",flexWrap:"wrap",gap:6 }}>{(ia.impacted_teams||[]).map(t=><TeamPill key={t} name={t} />)}</div>
              </div>
              <div style={{ display:"flex",gap:8,marginBottom:14,flexWrap:"wrap" }}>
                <Badge label={`Dependency: ${ia.dependency_risk}`} color={RC[ia.dependency_risk]||"#6b7280"} />
                {ia.signoff_required && <Badge label="🔒 Sign-off Required" color="#ef4444" />}
              </div>
              <InfoBox color="#f59e0b" title="📌 Why These Teams?">
                <span style={{ whiteSpace:"pre-line",lineHeight:1.8 }}>{ia.impact_reasoning}</span>
              </InfoBox>
            </div>
          )}

          {/* ── RELEASE ───────────────────────────────────── */}
          {tab==="release" && (
            <div style={{ animation:"fadeIn 0.2s ease" }}>
              <AgentHdr icon="🚀" title="RELEASE INTELLIGENCE AGENT" color="#ef4444" conf={ri.confidence} />
              <div style={{ display:"flex",gap:8,marginBottom:14,flexWrap:"wrap" }}>
                <Badge label={ri.release_conflict?"⚠ Conflict Detected":"✓ No Conflicts"} color={ri.release_conflict?"#ef4444":"#22c55e"} />
              </div>
              {(ri.conflicting_release_dates||[]).length>0 && (
                <InfoBox color="#ef4444" title="📅 Conflicting Dates">
                  {ri.conflicting_release_dates.join(", ")}
                </InfoBox>
              )}
              <div style={{ marginBottom:14 }}>
                <Lbl>Required Sign-offs</Lbl>
                <div style={{ display:"flex",flexWrap:"wrap",gap:6 }}>{(ri.suggested_stakeholders||[]).map(t=><TeamPill key={t} name={t} />)}</div>
              </div>
              <InfoBox color="#ef4444" title="⚡ Precaution">{ri.precaution}</InfoBox>
              <InfoBox color="#6b7280" title="📊 Release Analysis">
                <span style={{ whiteSpace:"pre-line",lineHeight:1.8 }}>{ri.release_reasoning}</span>
              </InfoBox>
            </div>
          )}

          {/* ── RAG ───────────────────────────────────────── */}
          {tab==="rag" && (
            <div style={{ animation:"fadeIn 0.2s ease" }}>
              <AgentHdr icon="🧠" title="RAG KNOWLEDGE AGENT" color="#10b981" />
              <InfoBox color="#10b981" title="🔍 Historical Insight">
                {rg.historical_insight||"No patterns yet. More PRs build the knowledge base."}
              </InfoBox>
              {(rg.patterns||[]).length>0 && (
                <div style={{ marginBottom:14 }}>
                  <Lbl>Senior Decision Patterns Captured</Lbl>
                  {(rg.patterns||[]).map((p,i)=>(
                    <div key={i} style={{ background:"#0f1724",border:"1px solid #10b98130",borderRadius:8,padding:"10px 14px",marginBottom:8,fontSize:13,color:"#d1fae5",lineHeight:1.6,display:"flex",gap:8 }}>
                      <span style={{ color:"#10b981",flexShrink:0 }}>#{i+1}</span><span>{p}</span>
                    </div>
                  ))}
                </div>
              )}
              {(rg.similar_prs||[]).length>0 && (
                <div>
                  <Lbl>Similar Past PRs</Lbl>
                  {rg.similar_prs.map((s,i)=>(
                    <div key={i} style={{ background:"#0d1117",border:"1px solid #21262d",borderRadius:8,padding:"10px 14px",marginBottom:8,fontSize:12 }}>
                      <div style={{ color:"#3b82f6",fontWeight:600,marginBottom:3 }}>#{s.pr_id}: {s.title}</div>
                      <div style={{ color:"#9ca3af" }}>Decision: {s.decision}</div>
                    </div>
                  ))}
                </div>
              )}
              <div style={{ fontSize:11,color:"#6b7280",textAlign:"right",marginTop:8 }}>
                Knowledge base: {rg.knowledge_base_size||0} entries
              </div>
            </div>
          )}

          {/* ── COMMENTS ──────────────────────────────────── */}
          {tab==="comments" && (
            <div style={{ animation:"fadeIn 0.2s ease" }}>
              <AgentHdr icon="💬" title="PR REVIEW COMMENTS" color="#8b5cf6" />
              <p style={{ fontSize:12,color:"#6b7280",marginBottom:16 }}>Post a comment — Agent Zed responds with AI reasoning specific to this PR.</p>

              {/* New comment form */}
              <div style={{ background:"#070b14",border:"1px solid #21262d",borderRadius:10,padding:16,marginBottom:20 }}>
                <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:10 }}>
                  <div><Lbl>Your Name</Lbl>
                    <input value={newC.author} onChange={e=>setNewC(c=>({...c,author:e.target.value}))} placeholder="Sathish271995" style={IS} /></div>
                  <div><Lbl>Type</Lbl>
                    <select value={newC.comment_type} onChange={e=>setNewC(c=>({...c,comment_type:e.target.value}))} style={IS}>
                      {Object.keys(CMT).map(t=><option key={t} value={t}>{CMT[t]} {t}</option>)}
                    </select></div>
                </div>
                <div style={{ marginBottom:10 }}>
                  <Lbl>File Reference (optional)</Lbl>
                  <input value={newC.file_ref} onChange={e=>setNewC(c=>({...c,file_ref:e.target.value}))} placeholder="payments.py:45" style={IS} />
                </div>
                <div style={{ marginBottom:12 }}>
                  <Lbl>Comment</Lbl>
                  <textarea value={newC.comment} onChange={e=>setNewC(c=>({...c,comment:e.target.value}))}
                    placeholder="Amount validation should reject values above 999999..." rows={3} style={{ ...IS,resize:"vertical" }} />
                </div>
                <button onClick={handlePost} disabled={posting} style={{ background:posting?"#1e3a5f":"linear-gradient(135deg,#1d4ed8,#4c1d95)",border:"none",color:"#fff",padding:"10px 20px",borderRadius:8,cursor:posting?"wait":"pointer",fontSize:13,fontWeight:600 }}>
                  {posting?"🤖 Agent Zed responding...":"📨 Post Comment"}
                </button>

                {aiReply && (
                  <div style={{ marginTop:14,background:"#0f2a1a",border:"1px solid #10b98150",borderRadius:8,padding:"12px 14px" }}>
                    <div style={{ fontSize:11,color:"#10b981",fontWeight:700,marginBottom:6 }}>🤖 AGENT ZED REPLIED</div>
                    <p style={{ fontSize:13,color:"#d1fae5",lineHeight:1.7 }}>{aiReply}</p>
                  </div>
                )}
              </div>

              {/* Comments list */}
              {comments.length===0 ? (
                <div style={{ color:"#6b7280",fontSize:13,textAlign:"center",padding:"24px 0" }}>No comments yet.</div>
              ) : comments.map(c=>(
                <div key={c.id} style={{ background:"#0d1117",border:`1px solid ${CTC[c.comment_type]||"#21262d"}30`,borderLeft:`3px solid ${CTC[c.comment_type]||"#6b7280"}`,borderRadius:8,padding:14,marginBottom:12 }}>
                  <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8,flexWrap:"wrap",gap:6 }}>
                    <div style={{ display:"flex",gap:8,alignItems:"center",flexWrap:"wrap" }}>
                      <span style={{ color:"#e6edf3",fontWeight:600,fontSize:13 }}>👤 {c.author}</span>
                      <span style={{ background:`${CTC[c.comment_type]||"#6b7280"}20`,color:CTC[c.comment_type]||"#6b7280",padding:"2px 8px",borderRadius:10,fontSize:11 }}>
                        {CMT[c.comment_type]} {c.comment_type}
                      </span>
                      {c.file_ref && <span style={{ fontFamily:"monospace",fontSize:11,color:"#06b6d4" }}>📄 {c.file_ref}</span>}
                      <span style={{ fontSize:11,color:"#6b7280" }}>{ago(c.created_at)}</span>
                    </div>
                    <div style={{ display:"flex",gap:6 }}>
                      <button onClick={()=>{ setEditId(c.id); setEditText(c.comment); }} style={{ background:"#21262d",border:"1px solid #30363d",color:"#8b949e",padding:"3px 10px",borderRadius:6,cursor:"pointer",fontSize:11 }}>✏ Edit</button>
                      <button onClick={()=>handleDeleteComment(c.id)} style={{ background:"#2d1010",border:"1px solid #ef444440",color:"#ef4444",padding:"3px 10px",borderRadius:6,cursor:"pointer",fontSize:11 }}>🗑</button>
                    </div>
                  </div>

                  {editId===c.id ? (
                    <div>
                      <textarea value={editText} onChange={e=>setEditText(e.target.value)} rows={2} style={{ ...IS,marginBottom:8,resize:"vertical" }} />
                      <div style={{ display:"flex",gap:6 }}>
                        <button onClick={()=>handleEditSave(c.id)} style={{ background:"#1d4ed8",border:"none",color:"#fff",padding:"5px 14px",borderRadius:6,cursor:"pointer",fontSize:12 }}>Save</button>
                        <button onClick={()=>setEditId(null)} style={{ background:"#21262d",border:"1px solid #30363d",color:"#8b949e",padding:"5px 14px",borderRadius:6,cursor:"pointer",fontSize:12 }}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <p style={{ fontSize:13,color:"#c9d1d9",lineHeight:1.7,marginBottom:c.ai_response?10:0 }}>{c.comment}</p>
                  )}

                  {c.ai_response && editId!==c.id && (
                    <div style={{ background:"#0a1f14",border:"1px solid #10b98130",borderRadius:6,padding:"10px 12px",marginTop:10 }}>
                      <div style={{ fontSize:10,color:"#10b981",fontWeight:700,marginBottom:4 }}>🤖 AGENT ZED</div>
                      <p style={{ fontSize:12,color:"#a7f3d0",lineHeight:1.7 }}>{c.ai_response}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {pr.pr_url && pr.pr_url!="#" && (
          <div style={{ padding:"14px 24px",borderTop:"1px solid #21262d",flexShrink:0 }}>
            <a href={pr.pr_url} target="_blank" rel="noreferrer" style={{ display:"block",textAlign:"center",padding:"11px",background:"linear-gradient(135deg,#1d4ed8,#4c1d95)",color:"#fff",textDecoration:"none",borderRadius:8,fontSize:13,fontWeight:600 }}>
              View on GitHub →
            </a>
          </div>
        )}
      </div>
    </>
  );
}

// ── Reusable micro-components ─────────────────────────────────────────────────
function AgentHdr({ icon, title, color, conf }) {
  return (
    <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14 }}>
      <div style={{ fontSize:11,fontWeight:700,letterSpacing:"0.07em",color }}>{icon}  {title}</div>
      {conf!=null && <div style={{ fontSize:11,color:"#6b7280" }}>
        Confidence: <span style={{ color:conf>=0.85?"#22c55e":conf>=0.7?"#f59e0b":"#ef4444",fontWeight:700 }}>{Math.round(conf*100)}%</span>
      </div>}
    </div>
  );
}
function InfoBox({ color, title, children }) {
  return (
    <div style={{ background:`${color}08`,border:`1px solid ${color}30`,borderRadius:8,padding:"12px 14px",marginBottom:14 }}>
      <div style={{ fontSize:11,fontWeight:700,color,marginBottom:6 }}>{title}</div>
      <div style={{ fontSize:13,color:"#c9d1d9",lineHeight:1.7 }}>{children}</div>
    </div>
  );
}
function SubList({ title, items, color }) {
  if (!items?.length) return null;
  return (
    <div style={{ marginBottom:14 }}>
      <Lbl>{title}</Lbl>
      {items.map((s,i)=>(
        <div key={i} style={{ display:"flex",gap:7,fontSize:13,color,marginBottom:6,lineHeight:1.6 }}>
          <span style={{ flexShrink:0 }}>•</span><span>{s}</span>
        </div>
      ))}
    </div>
  );
}
function Badge({ label, color }) {
  return <span style={{ display:"inline-block",fontSize:11,fontWeight:700,padding:"3px 10px",borderRadius:20,background:`${color}18`,color,border:`1px solid ${color}40` }}>{label}</span>;
}
function TeamPill({ name }) {
  const c = TC[name]||"#9ca3af";
  return <span style={{ display:"inline-block",fontSize:12,padding:"4px 12px",borderRadius:20,background:`${c}18`,color:c,border:`1px solid ${c}40` }}>{name}</span>;
}
function Lbl({ children }) {
  return <div style={{ fontSize:10,fontWeight:700,color:"#6b7280",letterSpacing:"0.07em",marginBottom:6,textTransform:"uppercase" }}>{children}</div>;
}
const IS = { width:"100%",background:"#0d1117",border:"1px solid #30363d",borderRadius:7,padding:"8px 11px",color:"#e6edf3",fontSize:13,outline:"none",fontFamily:"'IBM Plex Mono',monospace" };
