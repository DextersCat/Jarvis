import { useState, useEffect } from 'react';

// --- COMPONENTS ---

const ProgressBar = ({ label, value, color = "bg-cyan-400" }) => (
  <div className="mb-4">
    <div className="flex justify-between text-xs mb-1 text-cyan-500/70 font-bold tracking-wider">
      <span>{label}</span>
      <span>{value}%</span>
    </div>
    <div className="h-1.5 w-full bg-cyan-900/30 rounded-full overflow-hidden">
      <div 
        className={`h-full ${color} shadow-[0_0_10px_currentColor] transition-all duration-1000 ease-out`} 
        style={{ width: `${value}%` }}
      />
    </div>
  </div>
);

const StatusRow = ({ label, value, active }) => (
  <div className="flex justify-between items-center py-2 border-b border-cyan-500/10 text-sm">
    <span className="text-cyan-500/60 font-semibold tracking-wide">{label}</span>
    <span className={active ? "text-green-400 font-bold drop-shadow-[0_0_8px_rgba(74,222,128,0.6)]" : "text-cyan-300"}>
      {value}
    </span>
  </div>
);

export default function JarvisHUD() {
  const [coreState, setCoreState] = useState('OFFLINE');
  const [isBrainOnline, setIsBrainOnline] = useState(false);
  const [modelLabel, setModelLabel] = useState('Unknown');
  const [lastBrainAction, setLastBrainAction] = useState('Waiting...');
  const [events, setEvents] = useState([]);
  
  // Simulated Health Data for Visual Polish
  const [cpu, setCpu] = useState(24);
  const [ram, setRam] = useState(46);

  // --- DATA LOOP ---
  useEffect(() => {
    const pollAPI = async () => {
      try {
        // 1. Get State from Python (Port 8766)
        const stateRes = await fetch('http://localhost:8766/api/state');
        if (stateRes.ok) {
          const state = await stateRes.json();
          setCoreState(state.core_state.toUpperCase());
          setIsBrainOnline(state.brain_connected);
          setModelLabel(state.model_label || 'Ollama Llama 3');
          if (state.last_brain_action) setLastBrainAction(state.last_brain_action);
        }

        // 2. Get Events
        const eventsRes = await fetch('http://localhost:8766/api/events');
        if (eventsRes.ok) {
          const eventsData = await eventsRes.json();
          if (eventsData.events) setEvents(eventsData.events.slice().reverse().slice(0, 6));
        }
      } catch (e) {
        setCoreState('DISCONNECTED');
        setIsBrainOnline(false);
      }
    };

    // Animate Health Bars randomly to look alive
    const healthInterval = setInterval(() => {
      setCpu(prev => Math.min(100, Math.max(10, prev + (Math.random() * 10 - 5))));
      setRam(prev => Math.min(100, Math.max(30, prev + (Math.random() * 6 - 3))));
    }, 2000);

    // Poll every 1s
    const interval = setInterval(pollAPI, 1000);
    return () => { clearInterval(interval); clearInterval(healthInterval); };
  }, []);

  // --- CONTROLS ---
  const sendAction = async (action) => {
    try {
      await fetch('http://localhost:8766/api/action', {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action: action})
      });
    } catch (e) { console.error(e); }
  };

  return (
    <div className="h-screen w-screen bg-[#050A14] text-[#00F0FF] font-mono flex flex-col overflow-hidden selection:bg-cyan-900/50">
      
      {/* TOP BAR */}
      <div className="h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent w-full"></div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[350px_1fr_350px] gap-6 p-8">
        
        {/* LEFT: SYSTEM HEALTH */}
        <div className="p-6 border-r border-b border-cyan-500/20 bg-slate-900/20 backdrop-blur-sm rounded-br-3xl">
          <h2 className="text-lg font-bold mb-6 tracking-[0.2em] text-cyan-400 border-l-4 border-cyan-500 pl-3">
            SYSTEM HEALTH
          </h2>
          
          <div className="space-y-6">
            <ProgressBar label="CPU USAGE" value={Math.round(cpu)} />
            <ProgressBar label="RAM USAGE" value={Math.round(ram)} />
            <ProgressBar label="SENSITIVITY" value={60} color="bg-cyan-300" />
            <ProgressBar label="NEURAL LOAD" value={isBrainOnline ? 88 : 0} color="bg-yellow-400" />
          </div>

          <div className="mt-12 pt-6 border-t border-cyan-500/20">
            <div className="text-xs text-cyan-500/50 mb-1">SYSTEM UPTIME</div>
            <div className="text-2xl tracking-widest text-cyan-100">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* CENTER: VISUALIZATION */}
        <div className="flex flex-col items-center justify-start relative pt-4">
          <div className="relative w-full max-w-[56rem] aspect-square flex items-center justify-center -translate-y-4 md:-translate-y-10 mb-8">
             {/* The GIF */}
             <img 
               src="/assets/neural.gif" 
               className={`w-full h-full object-contain mix-blend-screen transition-all duration-500 ${coreState === 'LISTENING' || coreState === 'ONLINE' ? 'opacity-100 scale-105 brightness-125' : 'opacity-60 grayscale-[50%]'}`}
               alt="NEURAL NETWORK"
               onError={(e) => e.target.style.display='none'}
             />
             
             {/* Status Overlay */}
             <div className="absolute bottom-0 left-0 right-0 text-center">
               <div className="inline-block bg-black/60 backdrop-blur-md px-6 py-2 border border-cyan-500/30 rounded text-sm tracking-[0.3em] font-bold text-yellow-400 glow shadow-[0_0_15px_rgba(250,204,21,0.4)]">
                 {coreState}
               </div>
             </div>
          </div>
        </div>

        {/* RIGHT: BRAIN STATUS */}
        <div className="p-6 border-l border-b border-cyan-500/20 bg-slate-900/20 backdrop-blur-sm rounded-bl-3xl">
          <h2 className="text-lg font-bold mb-6 tracking-[0.2em] text-cyan-400 border-r-4 border-cyan-500 pr-3 text-right">
            BRAIN STATUS
          </h2>
          
          <div className="flex flex-col gap-1">
            <StatusRow label="CONNECTION" value={isBrainOnline ? "● ONLINE" : "● OFFLINE"} active={isBrainOnline} />
            <StatusRow label="MODEL" value={modelLabel} />
            <StatusRow label="LATENCY" value={isBrainOnline ? "144ms" : "--"} />
            <StatusRow label="NEURAL CORES" value="8/8" />
            <StatusRow label="PROCESSING UNITS" value="ACTIVE" />
          </div>
        </div>

      </div>

      {/* BOTTOM: EVENT LOG */}
      <div className="h-48 bg-[#020408] border-t border-cyan-500/30 p-6 relative">
        <div className="absolute top-0 left-0 px-4 py-1 bg-cyan-900/30 text-xs font-bold tracking-widest text-cyan-400 border-r border-b border-cyan-500/30">
          EVENT LOG
        </div>
        <div className="h-full overflow-hidden flex flex-col justify-end font-mono text-sm space-y-1 pl-4 pt-4">
          {events.map((ev, i) => (
            <div key={i} className="flex gap-4 text-cyan-500/80 border-l-2 border-cyan-500/10 pl-2 hover:border-cyan-400 transition-colors">
              <span className="opacity-50 min-w-[80px] text-xs">[{ev.timestamp}]</span>
              <span className="text-cyan-100">{ev.message}</span>
            </div>
          ))}
        </div>
        
        {/* CONTROLS (Overlay on Right) */}
        <div className="absolute bottom-6 right-6 flex gap-3">
            <button onClick={() => sendAction('start')} className="px-4 py-2 bg-cyan-900/30 border border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/20 text-xs font-bold tracking-wider">
                INITIALIZE
            </button>
             <button onClick={() => sendAction('stop')} className="px-4 py-2 bg-red-900/30 border border-red-500/50 text-red-400 hover:bg-red-500/20 text-xs font-bold tracking-wider">
                TERMINATE
            </button>
        </div>
      </div>
    </div>
  );
}
