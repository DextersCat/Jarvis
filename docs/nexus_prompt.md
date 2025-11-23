🌙 NEXUS — TOMORROW’S PROMPT (Safe, Clean, Zero Stress)

Paste this into Nexus tomorrow morning.

Nexus, load the architecture from docs/STATE_OF_JARVIS.md and prepare for one single task:
Wire the existing Jarvis HUD to the REST API on port 8766.

Your allowed actions:

Start the GUI server
At ~/jarvis_gui/jarvis-ai-console, run the correct command so the HUD loads at:
http://raspberrypi.local:5000

Make sure the REST API endpoints exist in Python

GET /api/state

GET /api/events

POST /api/action
Do not add new endpoints.
Use the existing state from persistent_client.py.

Make the HUD poll the REST API

Poll /api/state every 1–2 seconds

Poll /api/events every 1–2 seconds

Wire HUD buttons to actions
Each button should POST to /api/action with one of:

start

stop

test_time

check_brain

You must not:

Modify audio, recorder, or playback

Touch voice_session.py

Change PC Brain

Rewrite Mode A / Mode B

Add new behaviours

Update any architecture or documentation

Convert Jarvis into a text interface

Drift beyond the instructions above

When done:

Report only:

The commands you ran

Whether the HUD updates live

Whether the buttons trigger the correct REST actions

Any errors encountered

Nothing else.

✔ End of Instructions