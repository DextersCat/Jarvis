#!/usr/bin/env python3
"""
JARVIS Brain WebSocket Server - Phase C3
Receives audio from AI-Pi, processes with brain, returns TTS

Protocol: JSON messages over WebSocket (UTF-8 text frames)
Audio Format: 16-bit PCM, mono, 16 kHz
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
import time  # C4.D: Import time for performance metrics
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor  # C4.D: For async STT

# Load environment FIRST (before importing JARVISBrain)
env_path = Path.home() / 'JARVIS' / 'config' / '.env'
load_dotenv(env_path)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="google.api_core._python_version_support",
)

# Add JARVIS core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'core'))

from jarvis_brain import JARVISBrain
from openai import OpenAI
from faster_whisper import WhisperModel

# Configure logging
log_dir = Path.home() / 'JARVIS' / 'runtime' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f'phase_c3_server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JARVISWebSocketServer:
    """
    WebSocket server for JARVIS voice terminal integration
    Handles audio streaming from AI-Pi, processes with brain, returns TTS
    """
    
    def __init__(self, host='0.0.0.0', port=8765):
        """
        Initialize WebSocket server
        
        Args:
            host: Server host address (0.0.0.0 = all interfaces)
            port: Server port number
        """
        self.host = host
        self.port = port
        self.brain = None
        self.openai_client = None
        self.whisper_model = None  # C4.B: Local GPU Whisper
        self.executor = ThreadPoolExecutor(max_workers=2)  # C4.D
        self.active_connections = set()
        
        # Audio configuration
        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2  # 16-bit = 2 bytes
        
        logger.info(f"Initializing JARVIS WebSocket Server on {host}:{port}")
        
    def initialize_brain(self):
        """Initialize JARVIS brain, OpenAI client, and Whisper model"""
        try:
            logger.info("Initializing JARVIS brain...")
            try:
                import services.email_service as es

                logger.info(
                    "Email service module: %s | SCOPES=%s",
                    getattr(es, "__file__", "(none)"),
                    getattr(es, "SCOPES", None),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Email service introspection failed: %s", exc)
            self.brain = JARVISBrain()
            self.openai_client = OpenAI()
            
            # C4.B: Load faster-whisper model on CPU
            # Note: GPU requires cuDNN 9.x (we have 8.x), CPU still faster than cloud
            logger.info("Loading faster-whisper model (medium.en) on CPU...")
            self.whisper_model = WhisperModel(
                "medium.en",
                device="cpu",
                compute_type="int8"
            )
            logger.info("Whisper model loaded successfully")
            
            logger.info("Brain initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize brain: {e}")
            raise
    
    async def handle_client(self, websocket):
        """
        Handle individual client connection
        
        Args:
            websocket: WebSocket connection
        """
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        path = websocket.request.path if hasattr(websocket, 'request') else '/'
        logger.debug(f"Connection path: {path}")
        logger.info(f"Client connected: {client_addr}")
        self.active_connections.add(websocket)
        
        # Audio buffer for current utterance
        audio_buffer = []
        is_receiving_audio = False
        
        try:
            async for message in websocket:
                try:
                    # Parse JSON message
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    logger.debug(f"Received message type: {msg_type}")
                    
                    if msg_type == 'ping':
                        # Health check
                        await websocket.send(json.dumps({'type': 'pong'}))
                        
                    elif msg_type == 'audio_start':
                        # Start of new utterance
                        logger.info("Audio utterance started")
                        audio_buffer = []
                        is_receiving_audio = True
                        await websocket.send(json.dumps({'type': 'ack', 'message': 'audio_start acknowledged'}))
                        
                    elif msg_type == 'audio_chunk':
                        # Audio data chunk
                        if is_receiving_audio:
                            chunk_b64 = data.get('data', '')
                            chunk_bytes = base64.b64decode(chunk_b64)
                            audio_buffer.append(chunk_bytes)
                            logger.debug(f"Received audio chunk: {len(chunk_bytes)} bytes")
                        
                    elif msg_type == 'audio_end':
                        # End of utterance - process it
                        logger.info("Audio utterance ended")
                        is_receiving_audio = False
                        
                        if audio_buffer:
                            # Process the complete audio
                            await self.process_audio(websocket, audio_buffer)
                        else:
                            logger.warning("No audio data received")
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': 'No audio data received'
                            }))
                        
                        audio_buffer = []

                    elif msg_type == 'chat':
                        logger.info(f"Handling chat message: {data}")
                        text = data.get('text', '')
                        if not text:
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': 'No text provided'
                            }))
                            continue
                        response_payload = await self.brain.process_text_input(text)
                        response_text = response_payload.get("spoken_text") if isinstance(response_payload, dict) else response_payload
                        response_text = response_text or ""
                        logger.info(f"JARVIS response: '{response_text}'")
                        await self.send_tts_audio(websocket, response_text)

                    elif msg_type == "simple_local_reply":
                        text = data.get("text") or ""
                        logger.info("Handling simple_local_reply as chat-response passthrough: '%s'", text)
                        await self.send_tts_audio(websocket, text)

                    else:
                        logger.warning(f"Unknown message type: {msg_type}")
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': f'Unknown message type: {msg_type}'
                            }))

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            self.active_connections.remove(websocket)
            logger.info(f"Connection closed: {client_addr}")
    
    async def process_audio(self, websocket, audio_buffer):
        """
        Process complete audio utterance through Whisper -> Brain -> TTS
        
        Args:
            websocket: Client WebSocket connection
            audio_buffer: List of audio byte chunks
        """
        try:
            # Combine audio chunks
            audio_data = b''.join(audio_buffer)
            logger.info(f"Processing audio: {len(audio_data)} bytes ({len(audio_data)/self.sample_rate/self.sample_width:.2f}s)")
            
            # Step 1: Transcribe with Whisper
            transcription = await self.transcribe_audio(audio_data)
            if not transcription:
                logger.warning("Empty transcription")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Could not transcribe audio'
                }))
                return
            
            logger.info(f"Transcription: '{transcription}'")
            
            # Step 2: Process with JARVIS brain
            response_payload = await self.brain.process_text_input(transcription)
            response_text = response_payload.get("spoken_text") if isinstance(response_payload, dict) else response_payload
            response_text = response_text or ""
            logger.info(f"JARVIS response: '{response_text}'")
            
            # Step 3: Generate TTS audio
            await self.send_tts_audio(websocket, response_text)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Processing error: {str(e)}'
            }))
    
    async def transcribe_audio(self, audio_data):
        """
        Transcribe audio using faster-whisper (local GPU)
        
        Args:
            audio_data: Raw PCM audio bytes (16-bit, mono, 16kHz)
            
        Returns:
            Transcribed text or None
        """
        try:
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            # Seek to beginning
            wav_buffer.seek(0)
            
            # C4.D: Run transcription in executor to avoid blocking
            logger.info("Transcribing with faster-whisper (GPU)...") 
            import time
            start_time = time.time()
            
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                self.executor,
                lambda: self.whisper_model.transcribe(
                    wav_buffer,
                    language="en",
                    beam_size=5,
                    vad_filter=True
                )
            )
            
            # Combine all segments
            text = " ".join([seg.text for seg in segments]).strip()
            
            elapsed = time.time() - start_time
            logger.info(f"Transcription complete in {elapsed:.2f}s: '{text}'")
            
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    async def send_tts_audio(self, websocket, text):
        """
        Generate TTS audio and stream to client
        
        Args:
            websocket: Client WebSocket connection
            text: Text to convert to speech
        """
        try:
            logger.info(f"Generating TTS for: '{text[:50]}...'")
            
            # Generate TTS audio using brain's method
            tts_audio = self.brain.generate_audio(text)
            
            if not tts_audio:
                logger.error("TTS generation failed")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'TTS generation failed'
                }))
                return
            
            # OpenAI TTS returns MP3 - convert to PCM for AI-Pi playback
            # Use pydub to decode MP3 and convert to raw PCM
            from pydub import AudioSegment
            from io import BytesIO
            
            # Load MP3 from bytes
            audio_segment = AudioSegment.from_file(BytesIO(tts_audio), format="mp3")
            
            # Convert to 16kHz mono 16-bit PCM (matching AI-Pi playback format)
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Export as raw PCM
            pcm_audio = audio_segment.raw_data
            
            logger.info(f"Converted MP3 ({len(tts_audio)} bytes) to PCM ({len(pcm_audio)} bytes)")
            
            # Stream in chunks
            chunk_size = 4096  # 4KB chunks
            total_sent = 0
            
            for i in range(0, len(pcm_audio), chunk_size):
                chunk = pcm_audio[i:i+chunk_size]
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                
                await websocket.send(json.dumps({
                    'type': 'tts_chunk',
                    'data': chunk_b64
                }))
                
                total_sent += len(chunk)
                logger.debug(f"Sent TTS chunk: {len(chunk)} bytes")
            
            # Send end marker
            await websocket.send(json.dumps({'type': 'tts_end'}))
            logger.info(f"TTS streaming complete: {total_sent} bytes sent")
            
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'TTS error: {str(e)}'
            }))
    
    async def start_server(self):
        """Start the WebSocket server"""
        # Initialize brain first
        self.initialize_brain()
        
        logger.info("=" * 60)
        logger.info("JARVIS BRAIN WEBSOCKET SERVER")
        logger.info("=" * 60)
        logger.info(f"Server starting on ws://{self.host}:{self.port}")
        logger.info(f"Audio format: {self.sample_rate}Hz, {self.channels}ch, {self.sample_width*8}-bit PCM")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 60)
        logger.info("Waiting for AI-Pi connections...")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever


async def main():
    """Main entry point"""
    # Get configuration from environment
    host = os.getenv('JARVIS_WS_HOST', '0.0.0.0')
    port = int(os.getenv('JARVIS_WS_PORT', '8765'))
    
    server = JARVISWebSocketServer(host=host, port=port)
    await server.start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nServer shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
