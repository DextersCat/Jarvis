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
import uuid
import math
import socket
import contextlib
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
link_log_file = log_dir / 'neural_link.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
link_logger = logging.getLogger("neural_link")
if not link_logger.handlers:
    link_logger.setLevel(logging.INFO)
link_handler = logging.FileHandler(link_log_file)
link_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
link_logger.addHandler(link_handler)

HEARTBEAT_INTERVAL = 15  # seconds between pings (more forgiving during long TTS/HUD work)
HEARTBEAT_TIMEOUT = 20   # seconds to await pong (reduce false timeouts during TTS)
TCP_KEEPIDLE = 30        # seconds before kernel keepalive probes
TCP_KEEPINTVL = 10       # seconds between probes
TCP_KEEPCNT = 5          # probe count before drop


def cleanup_old_logs(directory: Path, hours: int = 72) -> None:
    """Remove log files older than the provided age."""
    if not directory.exists():
        return
    cutoff = datetime.now().timestamp() - (hours * 3600)
    removed = 0
    for path in directory.iterdir():
        if path.is_dir():
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
                removed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Log cleanup failed for %s: %s", path, exc)
    if removed:
        logger.info("[LOG_CLEANUP] Removed %d log files older than %dh from %s", removed, hours, directory)


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

    def _enable_tcp_keepalive(self, websocket, connection_id: str):
        """Enable TCP keepalive on the underlying socket for this connection."""
        try:
            sock = websocket.transport.get_extra_info("socket")
            if not sock:
                link_logger.warning("[LINK %s] No socket found to apply TCP keepalive", connection_id)
                return
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if hasattr(socket, "TCP_KEEPIDLE"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, TCP_KEEPIDLE)
            if hasattr(socket, "TCP_KEEPINTVL"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, TCP_KEEPINTVL)
            if hasattr(socket, "TCP_KEEPCNT"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, TCP_KEEPCNT)
            link_logger.info(
                "[LINK %s] TCP keepalive enabled idle=%s intvl=%s cnt=%s",
                connection_id,
                TCP_KEEPIDLE,
                TCP_KEEPINTVL,
                TCP_KEEPCNT,
            )
        except Exception as exc:  # noqa: BLE001
            link_logger.warning("[LINK %s] Failed to set TCP keepalive: %s", connection_id, exc)

    async def _heartbeat_loop(self, websocket, connection_id: str):
        """Send periodic pings and enforce pong timeout."""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                if websocket.closed:
                    link_logger.info("[HEARTBEAT] Link %s already closed; stopping ping loop", connection_id)
                    return
                try:
                    link_logger.debug("[HEARTBEAT] Sending ping link=%s", connection_id)
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=HEARTBEAT_TIMEOUT)
                    link_logger.debug("[HEARTBEAT] Pong received link=%s", connection_id)
                except asyncio.TimeoutError:
                    link_logger.warning("[HEARTBEAT] Missed pong; closing link=%s reason=ping_timeout", connection_id)
                    await websocket.close(code=1001, reason="ping_timeout")
                    link_logger.warning("[HEARTBEAT] Closed link=%s with code=1001 reason=ping_timeout", connection_id)
                    return
                except Exception as exc:  # noqa: BLE001
                    link_logger.error("[HEARTBEAT] Ping failed link=%s error=%s", connection_id, exc)
                    with contextlib.suppress(Exception):
                        await websocket.close(code=1001, reason="ping_error")
                        link_logger.warning("[HEARTBEAT] Closed link=%s with code=1001 reason=ping_error", connection_id)
                    return
        except asyncio.CancelledError:
            link_logger.info("[HEARTBEAT] Ping loop cancelled link=%s", connection_id)
            raise
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
        connection_id = uuid.uuid4().hex[:8]
        session_start = time.time()
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        path = websocket.request.path if hasattr(websocket, 'request') else '/'
        logger.debug(f"Connection path: {path}")
        logger.info(f"Client connected: {client_addr} (link={connection_id})")
        link_logger.info("[LINK %s] Connected client=%s path=%s", connection_id, client_addr, path)
        link_logger.info("[LINK %s] handshake start", connection_id)
        self.active_connections.add(websocket)
        self._enable_tcp_keepalive(websocket, connection_id)
        ping_task = None
        try:
            ping_task = asyncio.create_task(self._heartbeat_loop(websocket, connection_id))
        except Exception as exc:  # noqa: BLE001
            link_logger.warning("[LINK %s] Failed to start heartbeat loop: %s", connection_id, exc)

        # HUD / event sink (per-connection) for follow-up choices
        async def hud_event_sink(payload: dict):
            try:
                outgoing = payload
                if payload.get("type") == "followup_choices":
                    outgoing = {
                        "type": "updateReplyOptions",
                        "question_id": payload.get("question_id"),
                        "topic": payload.get("topic"),
                        "choices": payload.get("choices"),
                    }
                await websocket.send(json.dumps(outgoing))
                if outgoing.get("type") == "updateReplyOptions":
                    choices_obj = outgoing.get("choices")
                    if isinstance(choices_obj, dict):
                        choice_summary = list((choices_obj or {}).keys())
                    elif isinstance(choices_obj, list):
                        choice_summary = f"list(len={len(choices_obj)})"
                    else:
                        choice_summary = str(type(choices_obj))
                    link_logger.info(
                        "[HUD] updateReplyOptions sent link=%s question_id=%s choices=%s",
                        connection_id,
                        outgoing.get("question_id"),
                        choice_summary,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("[LINK %s] Failed to send HUD event: %s", connection_id, exc)

        # Attach sink to brain for this session
        self.brain.hud_event_sink = hud_event_sink
        
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
                        logger.info("Audio utterance started (link=%s)", connection_id)
                        link_logger.info("[LINK %s] audio_start", connection_id)
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
                        logger.info("Audio utterance ended (link=%s)", connection_id)
                        is_receiving_audio = False
                        total_bytes = sum(len(chunk) for chunk in audio_buffer)
                        link_logger.info(
                            "[LINK %s] audio_end received; chunks=%d total_bytes=%d",
                            connection_id,
                            len(audio_buffer),
                            total_bytes,
                        )
                        
                        if audio_buffer:
                            # Process the complete audio
                            await self.process_audio(websocket, audio_buffer, connection_id)
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
                        await self.send_tts_audio(websocket, response_text, connection_id)

                    elif msg_type == "followup_choice":
                        choices = data.get("choices") or []
                        question_id = data.get("question_id")
                        logger.info("Handling followup_choice msg: qid=%s choices=%s", question_id, choices)
                        try:
                            response_text = await self.brain.process_followup_choice(question_id, choices)
                        except Exception as exc:  # noqa: BLE001
                            logger.error("Error handling followup_choice: %s", exc, exc_info=True)
                            response_text = f"I hit an error handling that follow-up: {exc}"
                        response_text = response_text or ""
                        link_logger.info(
                            "[LINK %s] followup_choice response len=%d preview='%s'",
                            connection_id,
                            len(response_text),
                            response_text[:120] + ("..." if len(response_text) > 120 else "")
                        )
                        await self.send_tts_audio(websocket, response_text, connection_id)

                    elif msg_type == "simple_local_reply":
                        text = data.get("text") or ""
                        logger.info("Handling simple_local_reply as chat-response passthrough: '%s'", text)
                        await self.send_tts_audio(websocket, text, connection_id)

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
                    
        except websockets.exceptions.ConnectionClosed as exc:
            logger.info(f"Client disconnected: {client_addr} code={getattr(exc, 'code', None)} reason={getattr(exc, 'reason', None)}")
            link_logger.warning(
                "[LINK %s] Connection closed mid-session code=%s reason=%s",
                connection_id,
                getattr(exc, "code", None),
                getattr(exc, "reason", None),
            )
        except Exception as e:
            logger.error(f"Connection error: {e}")
            link_logger.error("[LINK %s] Connection error: %s", connection_id, e)
        finally:
            if ping_task:
                ping_task.cancel()
                with contextlib.suppress(Exception):
                    await ping_task
            self.active_connections.discard(websocket)
            elapsed = time.time() - session_start
            logger.info(f"Connection closed: {client_addr}")
            link_logger.info("[LINK %s] Session closed after %.2fs", connection_id, elapsed)
    
    async def process_audio(self, websocket, audio_buffer, connection_id: str | None = None):
        """
        Process complete audio utterance through Whisper -> Brain -> TTS
        
        Args:
            websocket: Client WebSocket connection
            audio_buffer: List of audio byte chunks
            connection_id: Link/session identifier for logging
        """
        try:
            # Combine audio chunks
            audio_data = b''.join(audio_buffer)
            logger.info(f"Processing audio: {len(audio_data)} bytes ({len(audio_data)/self.sample_rate/self.sample_width:.2f}s) (link={connection_id})")
            link_logger.info(
                "[LINK %s] Processing audio bytes=%d duration=%.2fs",
                connection_id or "unknown",
                len(audio_data),
                len(audio_data) / self.sample_rate / self.sample_width,
            )
            
            # Step 1: Transcribe with Whisper
            transcription = await self.transcribe_audio(audio_data)
            if not transcription:
                logger.warning("Empty transcription")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Could not transcribe audio'
                }))
                link_logger.warning("[LINK %s] Transcription returned empty", connection_id or "unknown")
                return
            
            logger.info(f"Transcription: '{transcription}'")
            link_logger.info(
                "[LINK %s] Transcription len=%d preview='%s'",
                connection_id or "unknown",
                len(transcription),
                transcription[:120] + ("..." if len(transcription) > 120 else "")
            )
            
            # Step 2: Process with JARVIS brain
            response_payload = await self.brain.process_text_input(transcription)
            response_text = response_payload.get("spoken_text") if isinstance(response_payload, dict) else response_payload
            response_text = response_text or ""
            logger.info(f"JARVIS response: '{response_text}'")
            link_logger.info(
                "[LINK %s] Brain response len=%d preview='%s'",
                connection_id or "unknown",
                len(response_text),
                response_text[:120] + ("..." if len(response_text) > 120 else "")
            )
            
            # Step 3: Generate TTS audio
            await self.send_tts_audio(websocket, response_text, connection_id)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            link_logger.error("[LINK %s] Error processing audio: %s", connection_id or "unknown", e)
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
    
    async def send_tts_audio(self, websocket, text, connection_id: str | None = None):
        """
        Generate TTS audio and stream to client
        
        Args:
            websocket: Client WebSocket connection
            text: Text to convert to speech
            connection_id: Link/session identifier for logging
        """
        try:
            logger.info(f"Generating TTS for: '{text[:50]}...'")
            link_logger.info(
                "[LINK %s] TTS start text_len=%d preview='%s'",
                connection_id or "unknown",
                len(text or ""),
                (text or "")[:120] + ("..." if text and len(text) > 120 else "")
            )
            
            # Generate TTS audio using brain's method
            tts_audio = self.brain.generate_audio(text)
            
            if not tts_audio:
                logger.error("TTS generation failed")
                link_logger.error("[LINK %s] TTS generation failed (no audio)", connection_id or "unknown")
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
            link_logger.info(
                "[LINK %s] TTS audio ready mp3_bytes=%d pcm_bytes=%d",
                connection_id or "unknown",
                len(tts_audio),
                len(pcm_audio),
            )
            
            # Stream in chunks
            chunk_size = 4096  # 4KB chunks
            total_sent = 0
            chunk_count = math.ceil(len(pcm_audio) / chunk_size) if chunk_size else 0
            link_logger.info(
                "[LINK %s] TTS streaming start chunk_size=%d chunks=%d",
                connection_id or "unknown",
                chunk_size,
                chunk_count,
            )
            
            for i in range(0, len(pcm_audio), chunk_size):
                chunk = pcm_audio[i:i+chunk_size]
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                try:
                    await websocket.send(json.dumps({
                        'type': 'tts_chunk',
                        'data': chunk_b64
                    }))
                except Exception as exc:  # noqa: BLE001
                    link_logger.error(
                        "[LINK %s] ERROR during send (chunk): %s: %s",
                        connection_id or "unknown",
                        exc.__class__.__name__,
                        exc,
                    )
                    raise

                total_sent += len(chunk)
                logger.debug(f"Sent TTS chunk: {len(chunk)} bytes")
            
            # Send end marker
            try:
                await websocket.send(json.dumps({'type': 'tts_end'}))
            except Exception as exc:  # noqa: BLE001
                link_logger.error(
                    "[LINK %s] ERROR during send (tts_end): %s: %s",
                    connection_id or "unknown",
                    exc.__class__.__name__,
                    exc,
                )
                raise
            logger.info(f"TTS streaming complete: {total_sent} bytes sent")
            link_logger.info(
                "[LINK %s] TTS streaming complete bytes=%d chunks=%d",
                connection_id or "unknown",
                total_sent,
                chunk_count,
            )
            
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            if isinstance(e, websockets.exceptions.ConnectionClosed):
                link_logger.warning(
                    "[LINK %s] TTS stream interrupted after %d bytes; code=%s reason=%s",
                    connection_id or "unknown",
                    total_sent if 'total_sent' in locals() else 0,
                    getattr(e, "code", None),
                    getattr(e, "reason", None),
                )
            else:
                link_logger.error(
                    "[LINK %s] TTS error: %s",
                    connection_id or "unknown",
                    e,
                )
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
        cleanup_old_logs(log_dir, hours=72)

        server_kwargs = {
            "ping_interval": None,  # manual heartbeat loop
            "ping_timeout": None,
            "close_timeout": 15,
            "max_queue": None,
        }
        logger.info(
            "WebSocket server settings: ping_interval=%s ping_timeout=%s close_timeout=%s max_queue=%s",
            server_kwargs["ping_interval"],
            server_kwargs["ping_timeout"],
            server_kwargs["close_timeout"],
            server_kwargs["max_queue"],
        )

        async with websockets.serve(self.handle_client, self.host, self.port, **server_kwargs):
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
