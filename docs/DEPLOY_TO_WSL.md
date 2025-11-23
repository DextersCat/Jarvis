# Deploy to WSL (Jarvis Brain)

Windows workspace is the master; `/root/JARVIS` is a mirrored runtime only. Never edit code in WSL.

## Standard refresh steps
1) Archive existing `/root/JARVIS` contents (keep `/root/jarvis_env`):
   ```bash
   ts=$(date +%Y%m%d_%H%M%S)
   mkdir -p /root/JARVIS_archives/JARVIS_$ts
   find /root/JARVIS -mindepth 1 -maxdepth 1 -exec mv {} /root/JARVIS_archives/JARVIS_$ts/ \;
   ```
2) Sync from Windows workspace:
   ```bash
   rsync -a --delete /mnt/c/Users/spenc/JARVIS-Workspace/ /root/JARVIS/
   ```
3) Copy voice assets (runtime pack):
   ```bash
   mkdir -p /root/JARVIS/voice_assets
   cp /mnt/c/Users/spenc/JARVIS-Workspace/golden_assets/2025-11-22_voice_pack/*.mp3 /root/JARVIS/voice_assets/
   ```
4) Start Brain (example):
   ```bash
   cd /root/JARVIS/api/websocket_server
   source /root/jarvis_env/bin/activate
   python server.py
   ```

## Notes
- Venv path: `/root/jarvis_env` (do not delete or recreate during deploy).
- Voice assets source: `golden_assets/2025-11-22_voice_pack` in the Windows workspace.
- If you need an archive, check `/root/JARVIS_archives/`.
