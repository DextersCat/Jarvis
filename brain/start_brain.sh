#!/bin/bash
# To use Python 3.11 env, set USE_JARVIS_ENV=311 before running.
if [ "$USE_JARVIS_ENV" = "311" ]; then
  source /root/jarvis_env311/bin/activate
else
  source /root/jarvis_env/bin/activate
fi
cd /root/JARVIS/api
PYTHONPATH=/root/JARVIS/brain-source:${PYTHONPATH} python server.py
