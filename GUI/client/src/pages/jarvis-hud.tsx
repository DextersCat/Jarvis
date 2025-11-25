import { useState, useEffect, useCallback } from 'react';

const API_URL = 'http://localhost:8766/api';

const HexDump = () => {
  const [codes, setCodes] = useState(Array(12).fill("00 00 00 00"));
  useEffect(() => {
    const interval = setInterval(() => {
      setCodes(prev => [...prev.slice(1), Array(4).fill(0).map(() => Math.floor(Math.random()*255).toString(16).padStart(2,'0').toUpperCase()).join(' ')]);
    }, 150);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="font-mono text-[10px] text-cyan-900/70 overflow-hidden h-full leading-relaxed select-none">
      {codes.map((c, i) => <div key={i} className="whitespace-nowrap">{`0x${(32768 + i * 16).toString(16).toUpperCase()}: ${c}`}</div>)}
    </div>
  );
};

const ProgressBar = ({ label, value, color = "bg-cyan-400" }: { label: string; value: number; color?: string }) => (
  <div className="mb-4 group">
    <div className="flex justify-between text-xs mb-1 text-cyan-600 font-bold tracking-widest font-['Rajdhani'] group-hover:text-cyan-400 transition-colors">
      <span>{label}</span>
      <span>{Math.round(value)}%</span>
    </div>
    <div className="h-1.5 w-full bg-cyan-900/20 rounded-sm overflow-hidden border border-cyan-900/30">
      <div className={`h-full ${color} shadow-[0_0_8px_currentColor] transition-all duration-500 ease-out`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  </div>
);

const StatusRow = ({ label, value, active }: { label: string; value: string; active?: boolean }) => (
  <div className="flex justify-between items-center py-2 border-b border-cyan-900/30 text-xs hover:bg-cyan-900/10 px-2 transition-colors">
    <span className="text-cyan-700 font-semibold tracking-wide font-['Rajdhani']">{label}</span>
    <span className={`font-['Roboto_Mono'] ${active ? "text-green-400 font-bold drop-shadow-[0_0_8px_rgba(74,222,128,0.6)]" : "text-cyan-400"}`}>{value}</span>
  </div>
);

export default function JarvisHUD() {
  const [coreState, setCoreState] = useState('OFFLINE');
  const [isBrainOnline, setIsBrainOnline] = useState(false);
  const [modelLabel, setModelLabel] = useState('Unknown');
  const [lastBrainAction, setLastBrainAction] = useState('Waiting...');
  const [events, setEvents] = useState<any[]>([]);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const [cpu, setCpu] = useState(0);
  const [ram, setRam] = useState(0);
  const [gamingMode, setGamingMode] = useState(false);
  const [healthSummary, setHealthSummary] = useState<string | null>(null);
  const [shuttingDown, setShuttingDown] = useState(false);
  const [queueItems, setQueueItems] = useState<any[]>([]);
  const [queueLength, setQueueLength] = useState(0);
  const [queueLoading, setQueueLoading] = useState(false);
  
  // Codex text entry field
  const [codexInput, setCodexInput] = useState('');
  
  // Reply options for conversational interactions
  const [replyOptions, setReplyOptions] = useState<string[]>([
    'Affirmative, proceed',
    'Negative, cancel operation',
    'Provide more details',
    'Execute command now'
  ]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchQueue = useCallback(async () => {
    try {
      setQueueLoading(true);
      const res = await fetch(`${API_URL}/queue`);
      if (res.ok) {
        const data = await res.json();
        setQueueItems(Array.isArray(data.queue) ? data.queue : []);
        if (typeof data.count === 'number') setQueueLength(data.count);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setQueueLoading(false);
    }
  }, []);

  useEffect(() => {
    const pollAPI = async () => {
      try {
        const stateRes = await fetch(`${API_URL}/state`);
        if (stateRes.ok) {
          const state = await stateRes.json();
          setCoreState(state.core_state ? state.core_state.toUpperCase() : 'OFFLINE');
          setIsBrainOnline(state.brain_connected);
          setModelLabel(state.model_label || 'Ollama Llama 3');
          if (state.last_brain_action) setLastBrainAction(state.last_brain_action);
          if (state.cpu !== undefined) setCpu(state.cpu);
          if (state.ram !== undefined) setRam(state.ram);
          if (typeof state.queue_length === 'number') {
            setQueueLength(state.queue_length);
          } else if (Array.isArray(state.queue)) {
            setQueueLength(state.queue.length);
          }
          if (typeof state.gaming_mode === 'boolean') {
            setGamingMode(state.gaming_mode);
          }
        }
        const eventsRes = await fetch(`${API_URL}/events`);
        if (eventsRes.ok) {
          const eventsData = await eventsRes.json();
          if (eventsData.events) setEvents(eventsData.events.slice().reverse().slice(0, 50));
        }
      } catch (e) {
        setCoreState('DISCONNECTED');
        setIsBrainOnline(false);
      }
    };
    const interval = setInterval(pollAPI, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, [fetchQueue]);

  const sendAction = async (action: string) => {
    try {
      const res = await fetch(`${API_URL}/action`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action}) });
      if (!res.ok) throw new Error(`Action ${action} failed`);
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  };

  const handleClearQueue = async () => {
    try {
      const res = await fetch(`${API_URL}/queue`, { method: 'DELETE' });
      if (!res.ok) throw new Error('REST clear failed');
      setQueueItems([]);
      setQueueLength(0);
    } catch (e) {
      console.error(e);
      await sendAction('clear_queue');
    }
    fetchQueue();
  };

  const handleRemoveQueueItem = async (id: any) => {
    try {
      const res = await fetch(`${API_URL}/queue/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('REST delete failed');
    } catch (e) {
      console.error(e);
    }
    fetchQueue();
  };

  const formatHealthSummary = (summary: any) => {
    if (!summary) return '';
    return `Wake word: ${summary.wake_word_status} • Queue: ${summary.queue_length} • Mic: ${summary.mic_status} • Brain: ${summary.brain_status}`;
  };

  const handleInitialize = async () => {
    try {
      const res = await fetch(`${API_URL}/initialize`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const text = data.summary_text || formatHealthSummary(data.summary);
        if (text) setHealthSummary(text);
        else setHealthSummary('Health check completed.');
      } else {
        setHealthSummary('Health check failed.');
      }
    } catch (e) {
      console.error(e);
      setHealthSummary('Health check failed.');
    }
  };

  const handleGamingToggle = async () => {
    try {
      const res = await fetch(`${API_URL}/gaming`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setGamingMode(!!data.gaming_mode);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleShutdown = async () => {
    try {
      setShuttingDown(true);
      const res = await fetch(`${API_URL}/shutdown`, { method: 'POST' });
      if (!res.ok) throw new Error('Shutdown failed');
      setHealthSummary('Shutdown initiated. Jarvis Lite will exit.');
    } catch (e) {
      console.error(e);
      setHealthSummary('Shutdown request failed.');
    }
  };

  const handleCodexSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!codexInput.trim()) return;
    
    try {
      // Send codex input to backend (placeholder for Codex integration)
      const res = await fetch(`${API_URL}/codex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: codexInput })
      });
      
      if (res.ok) {
        setCodexInput('');
        // Could add confirmation feedback here
      }
    } catch (e) {
      console.error('Codex submit error:', e);
    }
  };

  const handleReplyOptionClick = async (option: string) => {
    try {
      // Send selected reply option to backend (placeholder for Codex integration)
      await fetch(`${API_URL}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reply: option })
      });
    } catch (e) {
      console.error('Reply option error:', e);
    }
  };

  const isListening = coreState === 'LISTENING';
  const isProcessing = coreState === 'PROCESSING' || coreState === 'ANALYZING';

  return (
    <div className="h-screen w-screen bg-[#020408] text-[#00F0FF] flex flex-col overflow-hidden selection:bg-cyan-900/50 font-['Rajdhani'] relative">
      
      {/* BACKGROUND GRID */}
      <div className="absolute inset-0 pointer-events-none opacity-10" 
           style={{backgroundImage: 'linear-gradient(#00f0ff 1px, transparent 1px), linear-gradient(90deg, #00f0ff 1px, transparent 1px)', backgroundSize: '40px 40px'}}>
      </div>

      {/* HEADER */}
      <div className="h-16 flex items-center justify-between px-8 border-b border-cyan-500/20 bg-[#050a14]/90 backdrop-blur-sm shrink-0 z-10">
        <div className="flex items-center gap-4">
           <div className="w-2 h-8 bg-cyan-500 shadow-[0_0_15px_rgba(0,240,255,0.8)]"></div>
           <div className="text-2xl font-bold tracking-[0.4em] text-cyan-400 font-['Orbitron'] drop-shadow-[0_0_10px_rgba(0,240,255,0.5)]">
             JARVIS<span className="text-xs align-top opacity-50 ml-2 text-cyan-600">MK-IV</span>
           </div>
        </div>
        <div className="text-3xl font-bold tracking-widest text-white font-['Orbitron']">
            {currentTime}
        </div>
      </div>

      {/* MAIN CONTENT (Optimized for 2560x1440) */}
      <div className="flex-1 grid grid-cols-[420px_1fr_420px] gap-8 p-8 min-h-0 overflow-hidden z-0">
        
        {/* LEFT PANEL */}
        <div className="flex flex-col gap-4 h-full border-r border-cyan-500/10 pr-4 overflow-hidden">
          <div className="p-5 border border-cyan-500/20 bg-[#050a14]/60 relative backdrop-blur-md shrink-0">
            <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-cyan-500"></div>
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-cyan-500"></div>
            <h2 className="text-sm font-bold mb-6 tracking-[0.2em] text-cyan-400 border-b border-cyan-900/50 pb-2">DIAGNOSTICS</h2>
            <ProgressBar label="CPU CORE LOAD" value={cpu} />
            <ProgressBar label="RAM ALLOCATION" value={ram} />
            <ProgressBar label="AUDIO SENSITIVITY" value={60} color="bg-cyan-300" />
            <ProgressBar label="NEURAL BRIDGE" value={isBrainOnline ? 100 : 0} color={isBrainOnline ? "bg-green-400" : "bg-red-500"} />
          </div>
          
          {/* Reply Options Panel - Mirrors Queue Panel */}
          <div className="flex-1 min-h-0 p-4 border-l-2 border-cyan-900/30 bg-[#050a14]/40 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center mb-2 shrink-0">
              <h2 className="text-[10px] text-cyan-400 tracking-widest">REPLY OPTIONS</h2>
            </div>
            <div className="text-xs flex-1 min-h-0 overflow-y-auto leading-relaxed space-y-2 scrollbar-thin pr-2">
               {replyOptions.length === 0 ? (
                 <span className="text-cyan-900 italic opacity-50">{'>'} No active options</span>
               ) : (
                 replyOptions.map((option, i) => (
                   <button
                     key={i}
                     onClick={() => handleReplyOptionClick(option)}
                     data-testid={`button-reply-option-${i}`}
                     className="w-full border border-cyan-500/40 bg-cyan-900/20 rounded px-3 py-2 text-left hover:bg-cyan-500/20 hover:border-cyan-400 transition-all hover:shadow-[0_0_12px_rgba(0,240,255,0.3)] group"
                   >
                     <div className="flex items-center gap-2">
                       <span className="text-cyan-600 font-bold group-hover:text-cyan-400">#{i + 1}</span>
                       <span className="text-cyan-300 group-hover:text-cyan-100 font-['Rajdhani'] tracking-wide">{option}</span>
                     </div>
                   </button>
                 ))
               )}
            </div>
          </div>
        </div>

        {/* CENTER STAGE - EXPANDED NEURAL NETWORK */}
        <div className="flex flex-col items-center justify-center relative">
          <div className="relative w-full h-full max-h-[1100px] aspect-square flex items-center justify-center">
             <div className={`absolute inset-0 border border-cyan-500/10 rounded-full ${isListening ? 'animate-spin duration-[20s]' : ''}`}></div>
             <div className={`absolute inset-8 border border-cyan-500/15 rounded-full ${isListening ? 'animate-spin duration-[30s]' : ''}`}></div>
             <div className={`absolute inset-16 border border-cyan-500/20 rounded-full border-dashed ${isProcessing ? 'animate-spin-reverse duration-[4s]' : ''}`}></div>
             
             {/* MUCH LARGER Neural Network GIF */}
             <img 
               src="/assets/neural.gif" 
               className={`w-[85%] h-[85%] object-contain mix-blend-screen transition-all duration-500 ${isListening ? 'scale-105 brightness-125 opacity-100' : ''} ${isProcessing ? 'animate-pulse brightness-150 opacity-100' : ''} ${!isListening && !isProcessing ? 'opacity-50 grayscale-[50%]' : ''}`} 
               alt="NEURAL" 
               onError={(e) => (e.target as HTMLImageElement).style.display='none'} 
             />
             
             <div className="absolute bottom-8 left-0 right-0 text-center">
               <div className={`inline-block bg-black/90 backdrop-blur-xl px-12 py-3 border-x-2 border-cyan-500/50 text-2xl tracking-[0.4em] font-bold glow shadow-[0_0_30px_rgba(0,240,255,0.15)] font-['Orbitron'] ${isProcessing ? 'text-yellow-400 border-yellow-500/50' : 'text-cyan-400'}`}>
                 {coreState}
               </div>
             </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex flex-col gap-4 h-full border-l border-cyan-500/10 pl-4 overflow-hidden">
          <div className="p-5 border border-cyan-500/20 bg-[#050a14]/60 relative backdrop-blur-md shrink-0">
             <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-cyan-500"></div>
             <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-cyan-500"></div>
            <h2 className="text-sm font-bold mb-6 tracking-[0.2em] text-cyan-500 border-b border-cyan-900/50 pb-2 text-right">NEURAL UPLINK</h2>
            <StatusRow label="LINK STATUS" value={isBrainOnline ? "ONLINE" : "OFFLINE"} active={isBrainOnline} />
            <StatusRow label="CORE MODEL" value={modelLabel} />
            <StatusRow label="LATENCY" value={isBrainOnline ? "12ms" : "--"} />
            <StatusRow label="THREAD COUNT" value="8" />
            <StatusRow label="PROTOCOL" value="WEBSOCKET" />
            <StatusRow label="GAMING MODE" value={gamingMode ? "ON" : "OFF"} active={gamingMode} />
          </div>
          
          {/* Queue Panel */}
          <div className="flex-1 min-h-0 p-4 border-r-2 border-cyan-900/30 bg-[#050a14]/40 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center mb-2 shrink-0 gap-2">
              <h2 className="text-[10px] text-cyan-400 tracking-widest">OFFLINE QUEUE ({queueLength})</h2>
              <div className="flex gap-2">
                <button onClick={fetchQueue} data-testid="button-queue-refresh" className="text-[9px] text-cyan-400 border border-cyan-500/40 px-2 hover:bg-cyan-900/30 uppercase tracking-wide">
                  Refresh
                </button>
                {queueLength > 0 && (
                  <button onClick={handleClearQueue} data-testid="button-queue-purge-all" className="text-[9px] text-red-400 border border-red-500/30 px-2 hover:bg-red-900/30 uppercase tracking-wide">
                    Purge all
                  </button>
                )}
              </div>
            </div>
            <div className="text-xs font-mono text-cyan-500/80 flex-1 min-h-0 overflow-y-auto leading-relaxed space-y-2 scrollbar-thin pr-2">
               {queueLoading ? (
                 <span className="text-cyan-900 italic opacity-50">{'>'} Loading queue...</span>
               ) : queueItems.length === 0 ? (
                 <span className="text-cyan-900 italic opacity-50">{'>'} Buffer empty</span>
               ) : (
                 queueItems.map((item, i) => (
                   <div key={item.id ?? i} className="border border-cyan-900/30 rounded px-2 py-1 flex justify-between items-start gap-2">
                     <div>
                       <span className="text-cyan-700 mr-2">#{i + 1}</span>
                       <span className="text-cyan-300 break-words">{item.text}</span>
                     </div>
                     <button
                       onClick={() => handleRemoveQueueItem(item.id ?? i)}
                       data-testid={`button-queue-purge-${item.id ?? i}`}
                       className="text-[9px] text-red-400 border border-red-500/30 px-1.5 py-0.5 uppercase tracking-wide hover:bg-red-900/30 flex-shrink-0"
                     >
                       Purge
                     </button>
                   </div>
                 ))
               )}
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM: SPLIT SECTION - Event Log (Left) + Codex Input (Right) */}
      <div className="h-72 bg-[#03060a] border-t border-cyan-500/30 p-6 relative shrink-0 z-20 shadow-[0_-10px_40px_rgba(0,0,0,0.8)] grid grid-cols-2 gap-8">
        
        {/* LEFT HALF: EVENT LOG */}
        <div className="flex flex-col h-full overflow-hidden border-r border-cyan-500/20 pr-6">
           <div className="text-[10px] font-bold text-cyan-600 border-b border-cyan-900/30 pb-1 mb-3 tracking-widest uppercase flex justify-between items-center">
             <span>System Event Stream</span>
             <span className="text-cyan-700 font-normal">{events.length} events</span>
           </div>
           {healthSummary && (
             <div className="text-[11px] text-cyan-200 border border-cyan-500/30 bg-cyan-900/10 px-3 py-2 rounded-sm mb-3">
               <span className="text-cyan-400 font-bold">STATUS:</span> {healthSummary}
             </div>
           )}
           <div className="flex-1 overflow-y-auto font-mono text-sm space-y-2 pr-2 scrollbar-thin" data-testid="log-container">
             {events.map((ev, i) => (
               <div key={i} data-testid={`event-${i}`} className="flex gap-4 border-l-2 border-cyan-900/50 pl-3 text-cyan-500/90 items-start hover:bg-cyan-900/5 p-1 rounded transition-colors">
                 <span className="opacity-40 min-w-[80px] text-xs mt-0.5 font-bold">[{ev.timestamp}]</span>
                 <span className="text-cyan-100 tracking-wide">{ev.message}</span>
               </div>
             ))}
           </div>
        </div>

        {/* RIGHT HALF: CODEX TEXT ENTRY + CONTROLS */}
        <div className="flex flex-col h-full overflow-hidden pl-6">
          <div className="text-[10px] font-bold text-cyan-600 border-b border-cyan-900/30 pb-1 mb-3 tracking-widest uppercase flex justify-between items-center">
            <span>Codex Interface</span>
            <span className="text-cyan-700 font-normal">Neural Link Active</span>
          </div>
          
          {/* Codex Input Field */}
          <form onSubmit={handleCodexSubmit} className="flex-1 flex flex-col gap-3">
            <div className="flex-1 relative">
              <textarea
                value={codexInput}
                onChange={(e) => setCodexInput(e.target.value)}
                data-testid="input-codex"
                placeholder="Enter command or query for Jarvis..."
                className="w-full h-full bg-[#050a14]/80 border border-cyan-500/30 rounded-sm px-4 py-3 text-cyan-100 font-['Roboto_Mono'] text-sm placeholder-cyan-900 focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_15px_rgba(0,240,255,0.2)] transition-all resize-none scrollbar-thin"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleCodexSubmit();
                  }
                }}
              />
              <div className="absolute bottom-2 right-2 text-[9px] text-cyan-900 font-mono">
                Ctrl+Enter to submit
              </div>
            </div>
            
            {/* Control Buttons Row */}
            <div className="flex gap-3">
              <button 
                type="submit"
                data-testid="button-codex-submit"
                className="flex-1 py-2.5 bg-cyan-900/20 border border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/20 text-xs font-bold tracking-[0.2em] transition-all hover:shadow-[0_0_15px_rgba(0,240,255,0.2)]"
              >
                TRANSMIT
              </button>
              <button 
                onClick={handleInitialize}
                data-testid="button-initialize"
                type="button"
                className="px-4 py-2.5 bg-cyan-900/20 border border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/20 text-xs font-bold tracking-[0.2em] transition-all hover:shadow-[0_0_15px_rgba(0,240,255,0.2)]"
              >
                INIT
              </button>
              <button
                onClick={handleGamingToggle}
                data-testid="button-gaming-toggle"
                type="button"
                className={`px-4 py-2.5 border text-xs font-bold tracking-[0.2em] transition-all hover:shadow-[0_0_15px_rgba(255,165,0,0.2)] ${
                  gamingMode
                    ? 'bg-orange-500/30 border-orange-400 text-orange-100'
                    : 'bg-orange-900/10 border-orange-500/40 text-orange-400 hover:bg-orange-500/20'
                }`}
              >
                {gamingMode ? 'GMG' : 'GAME'}
              </button>
              <button
                onClick={handleShutdown}
                data-testid="button-shutdown"
                disabled={shuttingDown}
                type="button"
                className="px-4 py-2.5 bg-red-900/10 border border-red-500/40 text-red-400 hover:bg-red-500/20 disabled:opacity-60 disabled:cursor-not-allowed text-xs font-bold tracking-[0.2em] transition-all hover:shadow-[0_0_15px_rgba(255,50,50,0.2)]"
              >
                EXIT
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
