import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);
  const wss = new WebSocketServer({ server: httpServer, path: '/jarvis-ws' });

  // Store connected clients
  const clients = new Set<WebSocket>();

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

  return httpServer;
}
