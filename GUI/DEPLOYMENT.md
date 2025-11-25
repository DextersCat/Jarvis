# Deploying Jarvis AI Console to Raspberry Pi 5

## Quick Start

1. **Transfer the archive to your Raspberry Pi:**
   ```bash
   scp jarvis-ai-console.tar.gz pi@raspberrypi.local:~/
   ```

2. **On your Raspberry Pi, extract the files:**
   ```bash
   cd ~
   tar -xzf jarvis-ai-console.tar.gz
   cd jarvis-ai-console
   ```

3. **Install Node.js (if not already installed):**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

4. **Install dependencies:**
   ```bash
   npm install
   ```

5. **Build for production:**
   ```bash
   npm run build
   ```

6. **Start the server:**
   ```bash
   npm start
   ```

7. **Access the HUD:**
   Open a browser and navigate to:
   - From the Pi itself: `http://localhost:5000`
   - From another device on your network: `http://raspberrypi.local:5000`

## Running in Development Mode

If you want to make changes and see them live:

```bash
npm run dev
```

This will start the development server with hot module reloading.

## Running as a Service (Auto-start on boot)

To make Jarvis start automatically when your Pi boots:

1. **Create a systemd service file:**
   ```bash
   sudo nano /etc/systemd/system/jarvis-hud.service
   ```

2. **Add this content** (adjust paths as needed):
   ```ini
   [Unit]
   Description=Jarvis AI Console HUD
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/jarvis-ai-console
   Environment=NODE_ENV=production
   Environment=PORT=5000
   ExecStart=/usr/bin/npm start
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl enable jarvis-hud
   sudo systemctl start jarvis-hud
   ```

4. **Check status:**
   ```bash
   sudo systemctl status jarvis-hud
   ```

5. **View logs:**
   ```bash
   sudo journalctl -u jarvis-hud -f
   ```

## Testing the Integration

Once the HUD is running, test it with curl from your Python environment:

```bash
# Add an event
curl -X POST http://localhost:5000/api/jarvis/event \
  -H "Content-Type: application/json" \
  -d '{"message": "Testing from Python backend"}'

# Update core state
curl -X POST http://localhost:5000/api/jarvis/core-state \
  -H "Content-Type: application/json" \
  -d '{"state": "listening"}'
```

If you see these updates in the HUD, your integration is working!

## Python Integration

See `JARVIS_INTEGRATION.md` for complete Python integration examples.

Quick example to add to your Ai-Pi code:

```python
import requests

class JarvisHUD:
    def __init__(self):
        self.base_url = "http://localhost:5000/api/jarvis"
    
    def update_state(self, state):
        try:
            requests.post(f"{self.base_url}/core-state", 
                         json={"state": state}, 
                         timeout=0.5)
        except:
            pass  # HUD offline, ignore
    
    def add_event(self, message):
        try:
            requests.post(f"{self.base_url}/event", 
                         json={"message": message}, 
                         timeout=0.5)
        except:
            pass

# Usage
hud = JarvisHUD()
hud.add_event("Jarvis started")
hud.update_state("online")
```

## Performance Tips for Raspberry Pi 5

- The HUD is already optimized for Pi 5 performance
- Uses Canvas instead of heavy 3D graphics
- Minimal animations to keep CPU usage low
- If you notice slowness, you can reduce the neural network node count in `client/src/components/NeuralNetwork.tsx` (line 55, change `nodeCount` from 20 to 15)

## Troubleshooting

**Port 5000 already in use:**
```bash
# Change the port
PORT=8080 npm start
```

**Cannot access from other devices:**
```bash
# Check firewall
sudo ufw allow 5000
```

**HUD not updating from Python:**
- Check that the HUD server is running: `curl http://localhost:5000/api/jarvis/event -d '{"message":"test"}' -H "Content-Type: application/json"`
- Verify your Python code is sending to the correct URL
- Check server logs for errors

## File Structure

```
jarvis-ai-console/
├── client/              # Frontend React application
├── server/              # Express.js backend with WebSocket
├── shared/              # Shared TypeScript types
├── package.json         # Dependencies and scripts
├── JARVIS_INTEGRATION.md # Python integration guide
└── DEPLOYMENT.md        # This file
```

## Need Help?

- Check the browser console for frontend errors
- Check server logs: `journalctl -u jarvis-hud -f` (if running as service) or terminal output
- Test API endpoints with curl to isolate issues
