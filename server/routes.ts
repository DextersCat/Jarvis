import type { Express } from "express";
import { createServer, type Server } from "http";
import { execFile } from "child_process";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";

type ReplyChoiceMap = Record<string, string>;
type PresenceState = "present" | "away" | "unknown";
type PresenceSnapshot = {
  state: PresenceState;
  last_update: string;
};

const normalizeReplyChoices = (raw: any): ReplyChoiceMap | null => {
  if (!raw) return null;

  const map: ReplyChoiceMap = {};

  if (Array.isArray(raw)) {
    for (const entry of raw) {
      if (!entry || typeof entry !== 'object') continue;
      const code = String(
        entry.code ?? entry.id ?? entry.key ?? entry.letter ?? '',
      )
        .trim()
        .toUpperCase();
      const label = String(entry.label ?? entry.text ?? entry.value ?? '').trim();
      if (code && label) {
        map[code] = label;
      }
    }
  } else if (typeof raw === 'object') {
    for (const [key, value] of Object.entries(raw)) {
      const code = key.trim().toUpperCase();
      if (typeof value === 'string' && code && value.trim()) {
        map[code] = value.trim();
      }
    }
  }

  return Object.keys(map).length ? map : null;
};

const openUrlInBrowser = (url: string): Promise<void> =>
  new Promise((resolve, reject) => {
    execFile("xdg-open", [url], (error) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });

const VALID_PRESENCE_STATES: PresenceState[] = ["present", "away", "unknown"];

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);
  const wss = new WebSocketServer({ server: httpServer, path: '/jarvis-ws' });

  // Store connected clients
  const clients = new Set<WebSocket>();
  let presenceSnapshot: PresenceSnapshot = {
    state: "unknown",
    last_update: new Date().toISOString(),
  };

  const broadcastPresence = () => {
    broadcast({
      type: "updatePresence",
      state: presenceSnapshot.state,
      last_update: presenceSnapshot.last_update,
    });
  };

  const notifyPresenceChanged = async (nextState: PresenceState, reason?: string) => {
    const normalized = VALID_PRESENCE_STATES.includes(nextState)
      ? nextState
      : "unknown";
    const previous = presenceSnapshot.state;
    presenceSnapshot = {
      state: normalized,
      last_update: new Date().toISOString(),
    };

    if (previous !== normalized) {
      broadcast({
        type: "addEventLog",
        message: `[Presence] state → ${normalized.toUpperCase()}${reason ? ` (${reason})` : ""}`,
      });
    }

    broadcastPresence();

    try {
      await fetch("http://127.0.0.1:8766/api/presence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: normalized,
          source: "hud-presence",
        }),
      });
    } catch (error) {
      console.error("Presence notify error:", error);
    }
  };

  wss.on('connection', (ws: WebSocket) => {
    console.log('Client connected to Jarvis WebSocket');
    clients.add(ws);

    ws.on('message', (message: string) => {
      try {
        const data = JSON.parse(message.toString());
        console.log('Received from client:', data);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    });

    ws.on('close', () => {
      console.log('Client disconnected from Jarvis WebSocket');
      clients.delete(ws);
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
      clients.delete(ws);
    });

    // Send initial connection confirmation
    ws.send(JSON.stringify({ type: 'connected', timestamp: new Date().toISOString() }));
    ws.send(JSON.stringify({
      type: "updatePresence",
      state: presenceSnapshot.state,
      last_update: presenceSnapshot.last_update,
    }));
  });

  // Helper function to broadcast to all connected clients
  const broadcast = (message: any) => {
    const payload = JSON.stringify(message);
    clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(payload);
      }
    });
  };

  // API endpoints that Python backend can call
  app.post('/api/jarvis/core-state', (req, res) => {
    const { state } = req.body;
    broadcast({ type: 'updateCoreState', state });
    res.json({ success: true });
  });

  app.post('/api/jarvis/loop-state', (req, res) => {
    const { isRunning } = req.body;
    broadcast({ type: 'updateLoopState', isRunning });
    res.json({ success: true });
  });

  app.post('/api/jarvis/brain-status', (req, res) => {
    const { isOnline, modelLabel, lastAction } = req.body;
    broadcast({ type: 'updateBrainStatus', isOnline, modelLabel, lastAction });
    res.json({ success: true });
  });

  app.post('/api/jarvis/ai-pi-status', (req, res) => {
    const { wakeMode, lastAudioTime } = req.body;
    broadcast({ type: 'updateAiPiStatus', wakeMode, lastAudioTime });
    res.json({ success: true });
  });

  app.post('/api/jarvis/event', (req, res) => {
    const { message } = req.body;
    broadcast({ type: 'addEventLog', message });
    res.json({ success: true });
  });
  app.get('/api/jarvis/presence', (_req, res) => {
    res.json(presenceSnapshot);
  });

  app.post('/api/jarvis/presence', async (req, res) => {
    const desired = String(req.body?.state || '').toLowerCase();
    const reason = req.body?.reason ? String(req.body.reason) : undefined;
    if (!VALID_PRESENCE_STATES.includes(desired as PresenceState)) {
      return res.status(400).json({ success: false, message: 'Invalid presence state' });
    }
    await notifyPresenceChanged(desired as PresenceState, reason);
    res.json({ success: true, state: presenceSnapshot.state, last_update: presenceSnapshot.last_update });
  });

  app.post('/api/jarvis/open-url', async (req, res) => {
    const url = typeof req.body?.url === 'string' ? req.body.url.trim() : '';
    const source = req.body?.source ? String(req.body.source) : 'unknown';
    const reason = req.body?.reason ? String(req.body.reason) : undefined;

    if (!url) {
      return res.status(400).json({ success: false, message: 'URL required' });
    }

    let parsed: URL;
    try {
      parsed = new URL(url);
    } catch {
      return res.status(400).json({ success: false, message: 'Invalid URL' });
    }

    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return res.status(400).json({ success: false, message: 'Unsupported protocol' });
    }

    try {
      await openUrlInBrowser(parsed.toString());
      broadcast({
        type: 'addEventLog',
        message: `[HUD] Opening URL from ${source}: ${parsed.toString()}${reason ? ` (${reason})` : ''}`,
      });
      res.json({ success: true });
    } catch (error) {
      console.error('Open URL error:', error);
      res.status(500).json({ success: false, message: 'Failed to open URL' });
    }
  });

  app.post('/api/jarvis/reply-options', (req, res) => {
    const { type, questionId, question_id, topic } = req.body || {};
    const rawChoices = req.body?.choices ?? req.body?.options ?? null;
    const normalizedQuestionId =
      typeof question_id === 'string'
        ? question_id
        : typeof questionId === 'string'
          ? questionId
          : null;
    const normalizedChoices = normalizeReplyChoices(rawChoices);
    const hasChoices = !!(
      normalizedChoices && Object.keys(normalizedChoices).length > 0
    );
    const shouldClear =
      type === 'clearReplyOptions' || !normalizedQuestionId || !hasChoices;

    if (shouldClear) {
      broadcast({ type: 'clearReplyOptions' });
    } else {
      broadcast({
        type: 'updateReplyOptions',
        question_id: normalizedQuestionId,
        topic: topic ?? null,
        choices: normalizedChoices,
      });
    }

    res.json({ success: true });
  });

  app.post('/api/jarvis/hud-panel-update', (req, res) => {
    const payload = (req.body && typeof req.body === 'object') ? req.body : {};
    const panel = typeof payload.panel === 'string' ? payload.panel : null;
    const mode = typeof payload.mode === 'string' ? payload.mode : null;
    const source = typeof payload.source === 'string' ? payload.source : null;

    if (!panel || !mode || !source) {
      return res.status(400).json({ success: false, message: 'Missing panel/mode/source' });
    }

    const message: any = {
      type: 'hud_panel_update',
      panel,
      mode,
      source,
    };
    if (Array.isArray(payload.items)) {
      message.items = payload.items;
    }
    if (typeof payload.markdown === 'string' && payload.markdown.length > 0) {
      message.markdown = payload.markdown;
    }
    if (payload.meta && typeof payload.meta === 'object' && !Array.isArray(payload.meta)) {
      message.meta = payload.meta;
    }

    broadcast(message);
    res.json({ success: true });
  });

  return httpServer;
}
