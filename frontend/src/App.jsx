import { useState, useEffect } from "react";
import Topbar      from "./components/Topbar";
import StatsRow    from "./components/StatsRow";
import TabNav      from "./components/TabNav";
import PaymentsTab from "./pages/PaymentsTab";
import PRTab       from "./pages/PRTab";
import PRDrawer    from "./components/PRDrawer";
import { fetchStats } from "./api";

export default function App() {
  const [tab,     setTab]     = useState("payments");
  const [stats,   setStats]   = useState(null);
  const [selPR,   setSelPR]   = useState(null);
  const [refresh, setRefresh] = useState(0);

  const reload = () => setRefresh(r => r + 1);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => {});
    const id = setInterval(() => fetchStats().then(setStats).catch(() => {}), 12000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div style={{ minHeight:"100vh", background:"#070b14", color:"#c9d1d9", fontFamily:"'IBM Plex Sans',sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
        body{background:#070b14;}
        ::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:#0d1117;}::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px;}
        @keyframes fadeIn{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
        @keyframes slideInRight{from{transform:translateX(110%);}to{transform:translateX(0);}}
        @keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.3;}}
        @keyframes shimmer{0%{background-position:-400px 0;}100%{background-position:400px 0;}}
        input,select,textarea{font-family:'IBM Plex Mono',monospace;}
        button{font-family:'IBM Plex Sans',sans-serif;}
      `}</style>

      <Topbar onRefresh={reload} />
      <div style={{ maxWidth:1200, margin:"0 auto", padding:"0 20px 60px" }}>
        <StatsRow stats={stats} />
        <TabNav tab={tab} setTab={setTab} />

        {tab === "payments" && <PaymentsTab key={refresh} onDataChange={reload} />}
        {tab === "pr"       && <PRTab       key={refresh} onSelect={setSelPR} onDataChange={reload} />}
      </div>

      {selPR && <PRDrawer pr={selPR} onClose={() => setSelPR(null)} onDataChange={reload} />}
    </div>
  );
}
