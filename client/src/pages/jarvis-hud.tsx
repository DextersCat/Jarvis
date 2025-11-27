/**
 * Phase 4.6.5 HUD layout update wraps the reply/email list with a dedicated
 * context panel. The left focus list now drives a selection state that powers
 * the new right-hand detail view without disrupting the existing reply flow.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';

const API_URL = 'http://localhost:8766/api';
const WS_URL = 'ws://localhost:5000/jarvis-ws';

type ChoiceCode = string;
type ReplyChoice = {
  code: ChoiceCode;
  label: string;
  description?: string | null;
  details?: string | null;
};
type EmailSearchResult = {
  id: string;
  subject: string;
  from: string;
  date?: string | null;
  snippet?: string | null;
  body?: string | null;
};
type ReplyOptionsState = {
  questionId: string | null;
  topic: string | null;
  choices: ReplyChoice[];
  emailResults: EmailSearchResult[] | null;
};
type PresenceState = 'present' | 'away' | 'unknown';

const isRecord = (value: unknown): value is Record<string, any> =>
  !!value && typeof value === 'object' && !Array.isArray(value);

const sanitizeString = (value: unknown): string | null => {
  if (typeof value === 'string' || typeof value === 'number') {
    const trimmed = String(value).trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  return null;
};

const pickFirstString = (record: Record<string, any>, fields: string[]): string | null => {
  for (const field of fields) {
    const value = sanitizeString(record[field]);
    if (value) return value;
  }
  return null;
};

const normalizeEmailResults = (items: any[]): EmailSearchResult[] => {
  if (!Array.isArray(items)) return [];

  return items.map((entry, idx) => {
    if (!isRecord(entry)) {
      return {
        id: `email-${idx}`,
        subject: `Result ${idx + 1}`,
        from: 'Unknown sender',
        date: '',
        snippet: '',
        body: '',
      };
    }

    const id =
      pickFirstString(entry, ['id', 'message_id', 'messageId', 'thread_id', 'threadId']) ??
      `email-${idx}`;
    const subject = pickFirstString(entry, ['subject', 'title']) ?? `Result ${idx + 1}`;
    const from = pickFirstString(entry, ['from', 'sender']) ?? 'Unknown sender';
    const date = pickFirstString(entry, ['date', 'received', 'sent']) ?? '';
    const snippet = pickFirstString(entry, ['snippet', 'preview', 'summary']) ?? '';
    const body = pickFirstString(entry, ['body', 'content', 'text', 'description']) ?? snippet ?? '';

    return {
      id,
      subject,
      from,
      date,
      snippet,
      body,
    };
  });
};

const normalizeReplyButtonChoices = (raw: any): ReplyChoice[] => {
  const normalized: ReplyChoice[] = [];
  if (!raw) return normalized;

  const pushChoice = (candidate: Partial<ReplyChoice>) => {
    const code = sanitizeString(candidate.code);
    const label = sanitizeString(candidate.label);
    if (!code || !label) return;
    const description = sanitizeString(candidate.description ?? null);
    const details = sanitizeString(candidate.details ?? null);
    normalized.push({
      code,
      label,
      description: description ?? null,
      details: details ?? null,
    });
  };

  if (Array.isArray(raw)) {
    raw.forEach((entry) => {
      if (!isRecord(entry)) return;
      const code = pickFirstString(entry, ['code', 'id', 'key', 'letter', 'value']);
      const label = pickFirstString(entry, ['label', 'text', 'title', 'value']);
      const description = pickFirstString(entry, ['description', 'detail', 'summary', 'subtitle']);
      const details = pickFirstString(entry, ['body', 'content', 'snippet', 'extra']);
      pushChoice({ code, label, description, details });
    });
  } else if (isRecord(raw)) {
    Object.entries(raw).forEach(([key, value]) => {
      const code = sanitizeString(key);
      if (!code) return;

      if (typeof value === 'string' || typeof value === 'number') {
        pushChoice({ code, label: sanitizeString(value) });
      } else if (isRecord(value)) {
        const label = pickFirstString(value, ['label', 'text', 'title', 'value']);
        const description = pickFirstString(value, ['description', 'detail', 'summary', 'subtitle']);
        const details = pickFirstString(value, ['body', 'content', 'snippet', 'extra']);
        pushChoice({ code, label, description, details });
      }
    });
  }

  const seen = new Set<string>();
  return normalized.filter((choice) => {
    if (!choice.code || !choice.label || seen.has(choice.code)) {
      return false;
    }
    seen.add(choice.code);
    return true;
  });
};

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

type ReplyDetailPanelProps = {
  topic: string | null;
  questionId: string | null;
  selectedChoice: ReplyChoice | null;
  selectedEmailResult: EmailSearchResult | null;
};

const ReplyDetailPanel = ({
  topic,
  questionId,
  selectedChoice,
  selectedEmailResult,
}: ReplyDetailPanelProps) => {
  const isEmailTopic = topic === 'email.search';

  const emptyState = (
    <div className="h-full flex flex-col items-center justify-center text-center text-cyan-900/70 text-xs tracking-[0.3em] uppercase">
      Select an item to see details.
    </div>
  );

  let content = emptyState;

  if (isEmailTopic) {
    if (selectedEmailResult) {
      content = (
        <div className="flex flex-col h-full gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.4em] text-cyan-500">Subject</div>
            <div className="text-2xl font-bold text-cyan-100">{selectedEmailResult.subject}</div>
          </div>
          <div className="text-[11px] text-cyan-400 uppercase tracking-[0.3em]">
            {selectedEmailResult.from}
            {selectedEmailResult.date ? ` • ${selectedEmailResult.date}` : ''}
          </div>
          {selectedEmailResult.snippet && (
            <div className="text-sm text-cyan-200 leading-relaxed border border-cyan-500/20 bg-cyan-900/10 px-3 py-2 rounded">
              {selectedEmailResult.snippet}
            </div>
          )}
          {selectedEmailResult.body && (
            <div className="flex-1 overflow-y-auto border border-cyan-500/30 bg-cyan-950/30 px-3 py-3 rounded text-sm text-cyan-100 leading-relaxed whitespace-pre-line scrollbar-thin">
              {selectedEmailResult.body}
            </div>
          )}
        </div>
      );
    }
  } else if (selectedChoice) {
    const hasDescription = Boolean(selectedChoice.description);
    const hasDetails =
      Boolean(selectedChoice.details) &&
      selectedChoice.details?.trim() !== selectedChoice.description?.trim();

    content = (
      <div className="flex flex-col gap-4 text-cyan-100">
        <div>
          <div className="text-[10px] uppercase tracking-[0.4em] text-cyan-500">Selection</div>
          <div className="text-2xl font-bold text-cyan-100">{selectedChoice.label}</div>
        </div>
        <div className="text-[11px] text-cyan-400 uppercase tracking-[0.3em]">
          CODE #{selectedChoice.code}
        </div>
        {hasDescription && (
          <div className="text-sm text-cyan-200 border border-cyan-500/20 bg-cyan-900/20 px-3 py-2 rounded whitespace-pre-line">
            {selectedChoice.description}
          </div>
        )}
        {hasDetails && (
          <div className="text-xs text-cyan-300 border border-cyan-500/10 bg-cyan-950/40 px-3 py-2 rounded whitespace-pre-line">
            {selectedChoice.details}
          </div>
        )}
        {!hasDescription && !hasDetails && (
          <div className="text-sm text-cyan-500 italic">Selected: {selectedChoice.label}</div>
        )}
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 p-5 border border-cyan-500/20 bg-[#050a14]/60 relative backdrop-blur-md flex flex-col overflow-hidden">
      <div className="flex justify-between items-center border-b border-cyan-900/40 pb-2 mb-4">
        <h2 className="text-[10px] font-bold tracking-[0.3em] text-cyan-400">
          {isEmailTopic ? 'EMAIL CONTEXT' : 'REPLY DETAIL'}
        </h2>
        {questionId && (
          <span className="text-[9px] text-cyan-700 font-['Roboto_Mono']">QID: {questionId}</span>
        )}
      </div>
      <div className="flex-1 min-h-0">{content}</div>
    </div>
  );
};

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
  const [presenceState, setPresenceState] = useState<PresenceState>('unknown');
  const [presenceLastUpdate, setPresenceLastUpdate] = useState<string | null>(null);
  
  // Codex text entry field
  const [codexInput, setCodexInput] = useState('');
  
  // Reply options for conversational interactions
  const [replyState, setReplyState] = useState<ReplyOptionsState>({
    questionId: null,
    topic: null,
    choices: [],
    emailResults: null,
  });
  const [replyPending, setReplyPending] = useState(false);
  const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(null);
  const clearReplyOptions = useCallback(() => {
    setReplyState({ questionId: null, topic: null, choices: [], emailResults: null });
    setReplyPending(false);
    setSelectedChoiceId(null);
  }, []);

  const activeChoiceButtons = useMemo(() => {
    if (!replyState.questionId) return [];
    return replyState.choices
      .map((choice) => {
        const code = typeof choice.code === 'string' ? choice.code.trim() : '';
        const label = typeof choice.label === 'string' ? choice.label.trim() : '';
        if (!code || !label) return null;
        const description =
          typeof choice.description === 'string'
            ? choice.description.trim()
            : choice.description ?? null;
        const details =
          typeof choice.details === 'string' ? choice.details.trim() : choice.details ?? null;
        return { code, label, description, details };
      })
      .filter(Boolean) as ReplyChoice[];
  }, [replyState]);
  const hasReplyOptions = Boolean(replyState.questionId && activeChoiceButtons.length > 0);
  const hasEmailResults =
    replyState.topic === 'email.search' &&
    Array.isArray(replyState.emailResults) &&
    replyState.emailResults.length > 0;
  const hasReplyContent = hasReplyOptions || hasEmailResults;
  const presenceDisplayTime = useMemo(() => {
    if (!presenceLastUpdate) return '—';
    const parsed = new Date(presenceLastUpdate);
    if (Number.isNaN(parsed.getTime())) return '—';
    return parsed.toLocaleTimeString();
  }, [presenceLastUpdate]);

  useEffect(() => {
    if (!replyState.questionId) {
      setSelectedChoiceId(null);
      return;
    }

    if (replyState.topic === 'email.search') {
      const firstResult = replyState.emailResults?.[0];
      setSelectedChoiceId(firstResult ? firstResult.id : null);
    } else if (activeChoiceButtons.length > 0) {
      setSelectedChoiceId(activeChoiceButtons[0].code);
    } else {
      setSelectedChoiceId(null);
    }
  }, [replyState.questionId, replyState.topic, replyState.emailResults, activeChoiceButtons]);

  const selectedChoice = useMemo(() => {
    if (!selectedChoiceId) return null;
    return activeChoiceButtons.find((choice) => choice.code === selectedChoiceId) ?? null;
  }, [activeChoiceButtons, selectedChoiceId]);

  const selectedEmailResult = useMemo(() => {
    if (replyState.topic !== 'email.search') return null;
    if (!replyState.emailResults || replyState.emailResults.length === 0) return null;
    if (!selectedChoiceId) return replyState.emailResults[0];
    return (
      replyState.emailResults.find((result) => result.id === selectedChoiceId) ??
      replyState.emailResults[0]
    );
  }, [replyState.topic, replyState.emailResults, selectedChoiceId]);

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
          if (state.presence_state) {
            setPresenceState(
              ['present', 'away', 'unknown'].includes(String(state.presence_state).toLowerCase())
                ? (String(state.presence_state).toLowerCase() as PresenceState)
                : 'unknown',
            );
          }
          if (typeof state.presence_last_update === 'string') {
            setPresenceLastUpdate(state.presence_last_update);
          }
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

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let active = true;

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'replyOptions' || message.type === 'updateReplyOptions') {
          const rawChoices = message.choices ?? message.items ?? message.options ?? null;
          const incomingQuestionId = message.questionId ?? message.question_id ?? null;
          const incomingTopic = message.topic ?? null;

          if (incomingTopic === 'email.search' && Array.isArray(rawChoices)) {
            const sanitizedResults = normalizeEmailResults(rawChoices);
            setReplyState({
              questionId: incomingQuestionId,
              topic: incomingTopic,
              choices: [],
              emailResults: sanitizedResults,
            });
            setReplyPending(false);
            setEvents((prev) => {
              const previous = Array.isArray(prev) ? prev : [];
              const count = sanitizedResults.length;
              const entry = {
                timestamp: new Date().toLocaleTimeString(),
                message: count > 0 ? `Email search: ${count} result${count === 1 ? '' : 's'}.` : 'Email search: no matching messages found.',
              };
              return [entry, ...previous].slice(0, 50);
            });
            return;
          }

          if (!rawChoices || (Array.isArray(rawChoices) && rawChoices.length === 0)) {
            clearReplyOptions();
            return;
          }

          const normalizedChoices = normalizeReplyButtonChoices(rawChoices);
          if (incomingQuestionId && normalizedChoices.length > 0) {
            setReplyState({
              questionId: incomingQuestionId,
              topic: incomingTopic,
              choices: normalizedChoices,
              emailResults: null,
            });
            setReplyPending(false);
          } else {
            clearReplyOptions();
          }
        } else if (message.type === 'clearReplyOptions' || message.type === 'connected') {
          clearReplyOptions();
        } else if (message.type === 'updatePresence') {
          if (typeof message.state === 'string') {
            const normalized = message.state.toLowerCase();
            if (['present', 'away', 'unknown'].includes(normalized)) {
              setPresenceState(normalized as PresenceState);
            }
          }
          if (typeof message.last_update === 'string') {
            setPresenceLastUpdate(message.last_update);
          }
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        clearReplyOptions();
      };
      ws.onmessage = handleMessage;
      ws.onclose = () => {
        if (!active) return;
        clearReplyOptions();
        reconnectTimer = setTimeout(connect, 2000);
      };
      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      active = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close();
      }
    };
  }, [clearReplyOptions]);

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

  const handleReplyOptionClick = async (code: ChoiceCode) => {
    if (!replyState.questionId || replyPending) return;
    setReplyPending(true);
    try {
      await fetch(`${API_URL}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: replyState.questionId, choices: [code] })
      });
    } catch (e) {
      console.error('Reply option error:', e);
      setReplyPending(false);
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
      <div className="flex-1 grid grid-cols-[320px_360px_minmax(0,1fr)_360px_320px] gap-8 p-8 min-h-0 overflow-hidden z-0 items-start">
        
        {/* DIAGNOSTICS COLUMN */}
        <div className="flex flex-col gap-4 h-full border-r border-cyan-500/10 pr-4">
          <div className="p-5 border border-cyan-500/20 bg-[#050a14]/60 relative backdrop-blur-md">
            <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-cyan-500"></div>
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-cyan-500"></div>
            <h2 className="text-sm font-bold mb-6 tracking-[0.2em] text-cyan-400 border-b border-cyan-900/50 pb-2">DIAGNOSTICS</h2>
            <ProgressBar label="CPU CORE LOAD" value={cpu} />
            <ProgressBar label="RAM ALLOCATION" value={ram} />
            <ProgressBar label="AUDIO SENSITIVITY" value={60} color="bg-cyan-300" />
            <ProgressBar label="NEURAL BRIDGE" value={isBrainOnline ? 100 : 0} color={isBrainOnline ? "bg-green-400" : "bg-red-500"} />
          </div>
        </div>

        {/* COLUMN A - REPLY OPTIONS */}
        <div className="flex flex-col h-full min-h-0">
          <div className="flex-1 min-h-0 p-4 border-l-2 border-cyan-900/30 bg-[#050a14]/40 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center mb-2 shrink-0">
              <h2 className="text-[10px] text-cyan-400 tracking-widest">REPLY OPTIONS</h2>
              {hasReplyOptions && (
                <span
                  className={`text-[9px] ${
                    replyPending ? 'text-yellow-400' : 'text-cyan-500'
                  }`}
                >
                  {replyPending ? 'Processing selection…' : 'Awaiting your choice'}
                </span>
              )}
            </div>
            <div className="text-xs flex-1 min-h-0 overflow-y-auto leading-relaxed space-y-2 scrollbar-thin pr-2">
               {!hasReplyContent ? (
                 <span className="text-cyan-900 italic opacity-50">{'>'} No active follow-ups</span>
               ) : (
                 <>
                  {replyState.topic && (
                    <div className="text-[11px] text-cyan-200 border border-cyan-500/20 bg-cyan-950/30 px-3 py-2 rounded">
                      <span className="uppercase tracking-[0.3em] text-cyan-500 text-[9px]">Active Topic</span>
                      <div className="mt-1 text-cyan-100 font-semibold">{replyState.topic}</div>
                    </div>
                  )}
                  {hasEmailResults && (
                    <div className="border border-cyan-500/40 bg-cyan-900/10 rounded px-3 py-2">
                      <div className="flex justify-between items-center text-cyan-300 text-[11px] uppercase tracking-[0.3em]">
                        <span>Email search results ({replyState.emailResults?.length ?? 0})</span>
                      </div>
                      <div className="mt-2 space-y-2">
                        {replyState.emailResults?.map((result, idx) => {
                          const isSelected = selectedChoiceId === result.id;
                          return (
                            <button
                              type="button"
                              key={result.id}
                              onClick={() => setSelectedChoiceId(result.id)}
                              className={`w-full text-left border rounded px-2 py-2 transition-all ${
                                isSelected
                                  ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_12px_rgba(0,240,255,0.2)]'
                                  : 'border-cyan-500/20 bg-cyan-950/30 hover:border-cyan-400 hover:bg-cyan-900/40'
                              }`}
                            >
                              <div className="font-semibold text-cyan-50">
                                {result.subject || `Result ${idx + 1}`}
                              </div>
                              <div className="text-cyan-400 text-[10px]">
                                {result.from || 'Unknown sender'}
                                {result.date ? ` • ${result.date}` : ''}
                              </div>
                              {result.snippet && (
                                <div className="mt-1 text-cyan-200 text-[10px] leading-snug whitespace-pre-line">
                                  {result.snippet}
                                </div>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {hasReplyOptions &&
                    activeChoiceButtons.map((option, idx) => {
                      const isSelected = selectedChoiceId === option.code;
                      return (
                        <button
                          type="button"
                          key={option.code}
                          onClick={() => {
                            setSelectedChoiceId(option.code);
                            handleReplyOptionClick(option.code);
                          }}
                          data-testid={`button-reply-option-${idx}`}
                          disabled={replyPending}
                          className={`w-full border rounded px-3 py-2 text-left transition-all group ${
                            replyPending
                              ? 'opacity-60 cursor-not-allowed border-cyan-500/20 bg-cyan-900/10'
                              : isSelected
                              ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_12px_rgba(0,240,255,0.3)]'
                              : 'border-cyan-500/40 bg-cyan-900/20 hover:bg-cyan-500/20 hover:border-cyan-400 hover:shadow-[0_0_12px_rgba(0,240,255,0.3)]'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-cyan-600 font-bold group-hover:text-cyan-400">#{option.code}</span>
                            <span className="text-cyan-300 group-hover:text-cyan-100 font-['Rajdhani'] tracking-wide">{option.label}</span>
                          </div>
                          {option.description && (
                            <div className="mt-1 text-[11px] text-cyan-200 leading-snug">
                              {option.description}
                            </div>
                          )}
                        </button>
                      );
                    })}
                </>
                )}
            </div>
          </div>
        </div>

        {/* COLUMN B - CENTER STAGE */}
        <div className="flex flex-col items-center justify-center relative min-h-0">
          <div className="relative w-full h-full max-h-[1100px] aspect-square flex items-center justify-center">
             <div className={`absolute inset-0 border border-cyan-500/10 rounded-full ${isListening ? 'animate-spin spin-duration-20s' : ''}`}></div>
             <div className={`absolute inset-8 border border-cyan-500/15 rounded-full ${isListening ? 'animate-spin spin-duration-30s' : ''}`}></div>
             <div className={`absolute inset-16 border border-cyan-500/20 rounded-full border-dashed ${isProcessing ? 'animate-spin-reverse spin-duration-4s' : ''}`}></div>
             
             {/* MUCH LARGER Neural Network GIF */}
             <img 
               src="/assets/ai-center.gif" 
               className={`max-w-[800px] max-h-[800px] w-[70%] h-[70%] object-contain transition-all duration-500 ${isListening ? 'scale-105 brightness-125 opacity-100' : ''} ${isProcessing ? 'animate-pulse brightness-150 opacity-100' : ''} ${!isListening && !isProcessing ? 'opacity-50' : ''}`} 
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

        {/* COLUMN C - DETAIL PANEL */}
        <div className="flex flex-col h-full min-h-0">
          <ReplyDetailPanel
            topic={replyState.topic}
            questionId={replyState.questionId}
            selectedChoice={selectedChoice}
            selectedEmailResult={selectedEmailResult}
          />
        </div>

        {/* NEURAL UPLINK COLUMN */}
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
            <StatusRow label="PRESENCE" value={presenceState.toUpperCase()} active={presenceState === 'present'} />
            <div className="text-[10px] text-cyan-600 text-right mt-1">
              Last update: {presenceDisplayTime}
            </div>
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
