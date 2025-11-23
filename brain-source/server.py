#!/usr/bin/env python3
"""
JARVIS Brain WebSocket Server - FABLE VOICE PRIORITY
Handles simple local commands by bypassing GPT and streaming Fable TTS.
"""
import asyncio
import websockets
import json
import base64
import logging
import wave
import io
import struct
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment # Added for MP3 to PCM conversion

# CRITICAL IMPORTS
try:
    from jarvis_brain import JARVISBrain
    from openai import OpenAI
except ImportError:
    # Minimal logging if core components fail
    print("FATAL ERROR: Core JARVIS modules missing. Please check WSL paths.")
    sys.exit(1)

# Configuration Setup
env_path = Path.home() / 'JARVIS' / 'config' / '.env'
load_dotenv(env_path)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'core'))
logger = logging.getLogger(__name__)

class JARVISWebSocketServer:
    
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.brain = None
        self.tts_client = None
        self.sample_rate = 16000
        self.sample_width = 2
        self.channels = 1
        self.executor = ThreadPoolExecutor(max_workers=2)

    def initialize_brain(self):
        try:
            self.brain = JARVISBrain()
            self.tts_client = OpenAI() # Real OpenAI client for Fable TTS
            logger.info("✅ OpenAI TTS client loaded for Fable voice")
            logger.info("Brain initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize brain: {e}")
            raise

    # NEW PROTOCOL HANDLER: Bypasses GPT, uses Fable TTS
    async def handle_simple_local_reply(self, websocket, text):
        """Generates Fable voice audio for simple replies and streams it back."""
        try:
            logger.info(f"Local TTS request received: '{text}'")
            
            # Use Brain's TTS engine to generate Fable audio bytes
            tts_audio = self.brain.generate_audio(text) 
            
            if tts_audio:
                await self.send_tts_audio(websocket, text, tts_audio)
            else:
                raise Exception("TTS generation failed.")
        except Exception as e:
            logger.error(f"Local TTS processing error: {e}")
            
    async def send_tts_audio(self, websocket, text, tts_audio_bytes):
        """Generates TTS audio and streams it to client."""
        # This function converts MP3 bytes to raw PCM and streams it to Pi
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(tts_audio_bytes), format="mp3")
            audio_segment = audio_segment.set_frame_rate(self.sample_rate).set_channels(self.channels).set_sample_width(self.sample_width)
            pcm_audio = audio_segment.raw_data
            
            chunk_size = 4096
            for i in range(0, len(pcm_audio), chunk_size):
                chunk = pcm_audio[i:i+chunk_size]
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                await websocket.send(json.dumps({'type': 'tts_chunk', 'data': chunk_b64}))
            
            await websocket.send(json.dumps({'type': 'tts_end', 'expect_response': text.strip().endswith('?')}))
            logger.info(f"TTS complete: {len(pcm_audio)} bytes streamed.")
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")

    async def handle_client(self, websocket):
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_addr}")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'simple_local_reply':
                    # NEW PROTOCOL HANDLED HERE
                    await self.handle_simple_local_reply(websocket, data.get('text'))

                elif msg_type == 'chat':
                    # EXISTING CHAT PROTOCOL
                    response_payload = await self.brain.process_text_input(data.get('text'))
                    response_text = response_payload.get("spoken_text") if isinstance(response_payload, dict) else response_payload
                    response_text = response_text or ""
                    tts_audio = self.brain.generate_audio(response_text) 
                    await self.send_tts_audio(websocket, response_text, tts_audio)
                
                else:
                    logger.warning(f"Unknown message type received: {msg_type}")
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            logger.info(f"Connection closed: {client_addr}")

    async def start_server(self):
        self.initialize_brain()
        # ... (startup logs)
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()

async def main():
    host = os.getenv('JARVIS_WS_HOST', '0.0.0.0')
    port = int(os.getenv('JARVIS_WS_PORT', '8765'))
    server = JARVISWebSocketServer(host=host, port=port)
    await server.start_server()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("\nServer shutdown requested")
