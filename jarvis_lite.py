import argparse
import asyncio
import websockets
import json
import os
import logging
import pvporcupine
import pyaudio
import struct
import subprocess
import base64
import wave
import psutil
import numpy as np
from array import array
from datetime import datetime
import aiohttp
from aiohttp import web
import aiohttp_cors

# --- CONFIGURATION ---
BRAIN_URL = "ws://192.168.1.26:8765"
API_PORT = 8766
ASSET_PATH = "/home/spencer/jarvis_v2/assets/audio/"
QUEUE_FILE = "/home/spencer/jarvis_v2/queue.json"
TEMP_AUDIO_FILE = "/home/spencer/jarvis_v2/temp_input.wav"
RUNTIME_DIR = "/home/spencer/jarvis_v2/runtime"
SESSION_STATE_FILE = os.path.join(RUNTIME_DIR, "session_state.json")

CAPTURE_SAMPLE_RATE = 48000
CAPTURE_CHANNELS = 1
CAPTURE_SAMPLE_WIDTH = 2  # bytes (16-bit PCM)
CAPTURE_MAX_DURATION = 10  # seconds
CAPTURE_CHUNK_MS = 100
SILENCE_TIMEOUT_MS = 800
SILENCE_TAIL_MS = 250
SILENCE_THRESHOLD = 550
MIN_CAPTURE_SECONDS = 3.0
MIN_VALID_UTTERANCE_SECONDS = 0.7
DIAGNOSTIC_CAPTURE_SECONDS = 6.0
TARGET_ALSA_DEVICE = "hw:Wave3,0"
TARGET_DEVICE_HINTS = ["wave:3", "wave3", "elgato wave"]
PLAYBACK_DEVICE = "plughw:1,0"
PLAYBACK_DEVICE_LABEL = "HDMI"
WHISPER_SAMPLE_RATE = 16000
MIC_SAMPLE_RATE = 48000
MIC_CHANNELS = 1
DIAGNOSTIC_CAPTURE_ENABLED = os.environ.get('JARVIS_DIAGNOSTIC_CAPTURE', '0') == '1'
CAPTURE_LOG_DIR = os.path.join(RUNTIME_DIR, 'captures')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [LITE] %(message)s')
logger = logging.getLogger("JarvisLite")
logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
logging.getLogger('aiohttp.server').setLevel(logging.WARNING)
logging.getLogger('aiohttp.web').setLevel(logging.WARNING)

class JarvisLite:
    MIC_MODE_WAKE = "wake"
    MIC_MODE_AWAIT_REPLY = "await_reply"
    MIC_MODE_LOCKED = "locked"

    def __init__(self):
        self.ws = None
        self.connected = False
        self.queue = self.load_queue()
        self.status_text = "INITIALIZING"
        self.loop_running = True
        self.events = []
        self.audio_player_process = None
        self.is_speaking = False
        self.gaming_mode = False
        self.shutdown_requested = False
        self.api_runner = None
        self.pa = None
        self.audio_stream = None
        self.playback_queue = asyncio.Queue()
        self.playback_sample_rate = 48000
        self.current_utterance_id = None
        self.awaiting_ack = False
        self.pending_resend_id = None
        self.awaiting_reply_request_id = None
        self.presence_state = "unknown"
        self.presence_last_update = None
        self.mic_mode = self.MIC_MODE_WAKE
        self.interrupted_playback_id = None
        self.offline_alerted = False
        self.mainframe_handshake_done = False
        self.session_state = self.load_session_state()
        self.shutdown_sound_played = False
        self.await_reply_timeout_task = None
        self.awaiting_reply_context = None
        self.last_sent_text = None
        self.capture_device_index = None
        self.capture_device_name = None
        self.capture_sample_rate = CAPTURE_SAMPLE_RATE
        
        # Audio Setup
        try:
            key = os.environ.get("PORCUPINE_ACCESS_KEY")
            self.porcupine = pvporcupine.create(access_key=key, keywords=['jarvis'], sensitivities=[0.6])
            self.pa = pyaudio.PyAudio()
            mic_index, mic_name = self._select_input_device()
            self.capture_device_index = mic_index
            self.capture_device_name = mic_name or "Mic"
            self.capture_sample_rate = CAPTURE_SAMPLE_RATE
            self.wake_chunk_size = max(1, int(self.porcupine.frame_length * MIC_SAMPLE_RATE / self.porcupine.sample_rate))
            self.wake_stream_kwargs = dict(
                rate=MIC_SAMPLE_RATE,
                channels=MIC_CHANNELS,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.wake_chunk_size
            )
            if mic_index is not None:
                self.wake_stream_kwargs["input_device_index"] = mic_index
            self._open_wake_stream()
            self._configure_playback_device()
        except Exception as e:
            self.add_event(f"Audio Error: {e}")

        # STT Setup
        try:
            from faster_whisper import WhisperModel
            self.stt_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
            self.add_event("Ears Ready")
        except Exception as e:
            self.add_event(f"STT Error: {e}")

    # --- HELPERS ---
    def _open_wake_stream(self):
        if not self.pa:
            return
        try:
            stream = self.pa.open(**self.wake_stream_kwargs)
            self.audio_stream = stream
            descriptor = self.capture_device_name if self.capture_device_name else "Mic"
            if self.capture_device_index is not None:
                descriptor = f"{descriptor} [index {self.capture_device_index}]"
            self.add_event(f"Microphone Initialized ({descriptor})")
            self.add_event(f"Capture Sample Rate set to {self.capture_sample_rate} Hz")
            self.add_event(
                f"Capture Source Locked ({self.capture_device_name or 'Mic'}) target {TARGET_ALSA_DEVICE} @ {self.capture_sample_rate}Hz mono 16-bit"
            )
            self.log_aipi("Wave:3 microphone locked at 48000 Hz")
            wake_device = self.capture_device_index if self.capture_device_index is not None else 'default'
            self.log_aipi(f"Wake stream opened: device={wake_device} rate={MIC_SAMPLE_RATE} channels={MIC_CHANNELS}")
        except Exception as wake_err:
            self.audio_stream = None
            self.add_event(f"Wake stream error: {wake_err}")
            raise

    def _pause_wake_stream(self):
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

    def _resume_wake_stream(self):
        self._open_wake_stream()

    def _configure_playback_device(self):
        rate = 48000
        try:
            if self.pa and self.capture_device_index is not None:
                info = self.pa.get_device_info_by_index(self.capture_device_index)
            elif self.pa:
                info = self.pa.get_default_input_device_info()
            else:
                info = None
            if info:
                reported = info.get("defaultSampleRate")
                if reported:
                    rate = int(float(reported))
        except Exception as playback_err:
            self.add_event(f"Playback device info error: {playback_err}")
        self.playback_sample_rate = rate
        self.log_aipi(f"Playback Source Locked: {PLAYBACK_DEVICE} ({PLAYBACK_DEVICE_LABEL})")
        self.log_aipi(f"Output rate confirmed: {self.playback_sample_rate} Hz")

    def is_playing(self):
        if self.audio_player_process:
            if self.audio_player_process.poll() is None:
                return True
        return False

    def add_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(message)
        self.events.append({"timestamp": timestamp, "message": message})
        if len(self.events) > 20: self.events.pop(0)

    async def forward_reply_options(self, payload):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    "http://localhost:5000/api/jarvis/reply-options",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3)
                )
        except Exception as e:
            self.add_event(f"HUD reply options forward error: {e}")

    async def forward_hud_panel_update(self, payload):
        if not isinstance(payload, dict):
            self.add_event("[HUD] hud_panel_update payload ignored (not a dict)")
            return
        panel = payload.get("panel")
        mode = payload.get("mode")
        source = payload.get("source")
        missing = [name for name, value in (("panel", panel), ("mode", mode), ("source", source)) if not value]
        if missing:
            self.add_event(f"[HUD] hud_panel_update missing fields: {', '.join(missing)}")
            return
        normalized_panel = str(panel)
        normalized_mode = str(mode)
        normalized_source = str(source)
        hud_payload = {
            "type": "hud_panel_update",
            "panel": normalized_panel,
            "mode": normalized_mode,
            "source": normalized_source,
        }
        raw_items = payload.get("items")
        items = raw_items if isinstance(raw_items, list) else None
        if items is not None:
            hud_payload["items"] = items
        markdown = payload.get("markdown")
        if isinstance(markdown, str) and markdown:
            hud_payload["markdown"] = markdown
        meta = payload.get("meta")
        if isinstance(meta, dict) and meta:
            hud_payload["meta"] = meta
        item_count = len(items) if items is not None else 0
        self.add_event(
            f"[HUD] panel={normalized_panel} mode={normalized_mode} source={normalized_source} items={item_count}"
        )
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    "http://localhost:5000/api/jarvis/hud-panel-update",
                    json=hud_payload,
                    timeout=aiohttp.ClientTimeout(total=3)
                )
        except Exception as e:
            self.add_event(f"HUD panel update forward error: {e}")

    def log_aipi(self, message):
        self.add_event(f"[AiPi] {message}")

    async def set_presence_state(self, state, source="api"):
        normalized = (state or "unknown").strip().lower()
        if normalized not in ("present", "away", "unknown"):
            return False
        timestamp = datetime.now().isoformat()
        changed = normalized != self.presence_state
        self.presence_state = normalized
        self.presence_last_update = timestamp
        self.add_event(f"[Presence] state → {normalized.upper()} (source: {source})")
        if changed and self.connected:
            await self.brain_send({
                "type": "presence_state",
                "state": normalized,
                "timestamp": timestamp,
            })
        return True

    def _select_input_device(self):
        try:
            if not hasattr(self, "pa"):
                return (None, None)
            preferred = None
            fallback = None
            for idx in range(self.pa.get_device_count()):
                info = self.pa.get_device_info_by_index(idx)
                if info.get("maxInputChannels", 0) < 1:
                    continue
                name = info.get("name", "Mic")
                lname = name.lower()
                if fallback is None:
                    fallback = (idx, name)
                if TARGET_ALSA_DEVICE.lower() in lname or any(h in lname for h in TARGET_DEVICE_HINTS):
                    preferred = (idx, name)
                    break
            return preferred or fallback or (None, None)
        except Exception as e:
            self.add_event(f"Audio Device Scan Error: {e}")
            return (None, None)

    # Queue structure example (stored as plain text entries):
    # [
    #   "Wake me up at 7",
    #   "Jarvis, remind me to email Sam"
    # ]
    def load_queue(self):
        if os.path.exists(QUEUE_FILE):
            try: return json.load(open(QUEUE_FILE))
            except: return []
        return []

    def save_queue(self):
        json.dump(self.queue, open(QUEUE_FILE, 'w'))

    def queue_snapshot(self):
        return [{"id": str(idx), "text": text} for idx, text in enumerate(self.queue)]

    def clear_queue_items(self):
        cleared = len(self.queue)
        self.queue = []
        self.save_queue()
        self.add_event(f"Queue Event: cleared ({cleared} items)")
        if cleared:
            # Audible confirmation that the backlog was purged.
            asyncio.create_task(self.play_sound("queue_purged.mp3"))
        return cleared

    def remove_queue_item_by_id(self, item_id):
        try:
            idx = int(item_id)
        except (TypeError, ValueError):
            return None
        if 0 <= idx < len(self.queue):
            removed = self.queue.pop(idx)
            self.save_queue()
            self.add_event(f"Queue Event: removed item {item_id}")
            return removed
        return None

    def get_health_summary(self):
        summary = {
            "wake_word_status": "running" if self.loop_running and not self.gaming_mode else "paused",
            "queue_length": len(self.queue),
            "rest_api_status": "online",
            "mic_status": "available" if self.audio_stream else "not available",
            "brain_status": "reachable" if self.connected else "not reachable",
            "gaming_mode": self.gaming_mode
        }
        return summary

    def format_health_summary(self, summary):
        return (
            f"Health Check → wake_word={summary['wake_word_status']}, "
            f"queue={summary['queue_length']}, mic={summary['mic_status']}, "
            f"brain={summary['brain_status']}, api={summary['rest_api_status']}"
        )

    def load_session_state(self):
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        if os.path.exists(SESSION_STATE_FILE):
            try:
                with open(SESSION_STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.add_event(f"Session state load error: {e}")
        return {"last_session_date": None, "last_good_morning": None}

    def save_session_state(self):
        try:
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            with open(SESSION_STATE_FILE, "w") as f:
                json.dump(self.session_state, f)
        except Exception as e:
            self.add_event(f"Session state save error: {e}")

    def set_gaming_mode(self, enabled: bool):
        if enabled == self.gaming_mode:
            return self.gaming_mode
        self.gaming_mode = enabled
        if enabled:
            self.status_text = "GAMING"
            self.add_event("🎮 Gaming Mode Enabled")
            # Audio cue confirming voice capture is paused for gaming focus.
            asyncio.create_task(self.play_sound("gaming_on.mp3"))
        else:
            self.status_text = "ONLINE"
            self.add_event("🎮 Gaming Mode Disabled")
            # Restore confirmation that voice control is back online.
            asyncio.create_task(self.play_sound("gaming_off.mp3"))
        return self.gaming_mode

    async def initiate_shutdown(self):
        if self.shutdown_requested:
            return
        self.shutdown_requested = True
        self.loop_running = False
        self.gaming_mode = False
        self.add_event("Shutdown requested by HUD")
        if not self.shutdown_sound_played:
            self.shutdown_sound_played = True
            # Graceful shutdown tone is reserved for orderly exits.
            await self.play_sound("shutdown.mp3")
        try:
            if self.ws:
                await self.ws.close()
        except:
            pass
        self.close_audio_player()
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None
        if self.pa:
            try:
                self.pa.terminate()
            except:
                pass
            self.pa = None
        if self.api_runner:
            try:
                await self.api_runner.cleanup()
            except:
                pass

    async def delayed_shutdown(self):
        await self.initiate_shutdown()
        await asyncio.sleep(0.2)
        os._exit(0)

    async def play_sound(self, file_name):
        full_path = os.path.join(ASSET_PATH, file_name)
        logger.info(f"[Audio] play_sound requested → {file_name} ({full_path})")
        if not os.path.exists(full_path):
            logger.error(f"[Audio] Missing asset: {full_path}")
            return
        try:
            env = os.environ.copy()
            env.setdefault('SDL_AUDIODRIVER', 'alsa')
            env.setdefault('AUDIODEV', PLAYBACK_DEVICE)
            proc = await asyncio.create_subprocess_exec(
                "ffplay", "-nodisp", "-autoexit", full_path,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
            )
            await proc.wait()
            logger.info(f"[Audio] Completed playback for {file_name}")
        except Exception:
            logger.exception(f"[Audio] Failed during playback for {file_name}")
            raise

    # --- BRAIN LINK ---
    async def connect_brain(self):
        while not self.shutdown_requested:
            try:
                if self.loop_running and not self.connected:
                    async with websockets.connect(BRAIN_URL) as ws:
                        self.ws = ws
                        self.connected = True
                        self.offline_alerted = False
                        self.add_event("✅ Neural Link Established")

                        if not self.mainframe_handshake_done:
                            self.mainframe_handshake_done = True
                            # First true handshake after boot to confirm the mainframe link.
                            await self.play_sound("mainframe_online.mp3")

                        await self.handle_daily_greeting()
                        
                        if self.pending_resend_id:
                            await self.request_resend_for(self.pending_resend_id)
                        
                        if self.queue:
                            for item in self.queue:
                                await ws.send(json.dumps({"type": "chat", "text": item}))
                            self.queue = []
                            self.save_queue()

                        async for msg in ws:
                            data = json.loads(msg)
                            if data.get('type') == 'UTTERANCE':
                                await self.handle_utterance(data)
                            elif data.get('type') == 'tts_chunk':
                                self.handle_audio_chunk(data.get('data'))
                            elif data.get('type') == 'tts_end':
                                self.close_audio_player()
                            elif data.get('type') == 'updateReplyOptions':
                                self.log_aipi(f"Forwarding reply options {data.get('question_id')}")
                                asyncio.create_task(self.forward_reply_options(data))
                            elif data.get('type') == 'hud_panel_update':
                                asyncio.create_task(self.forward_hud_panel_update(data))
            except Exception as e:
                if self.connected:
                    self.add_event("⚠️ Neural Link Lost")
                    await self.handle_neural_link_severed()
                self.handle_connection_loss()
                await asyncio.sleep(5)
            
            await asyncio.sleep(1)
        self.connected = False

    def handle_audio_chunk(self, b64_data):
        if not b64_data: return
        try:
            audio_bytes = base64.b64decode(b64_data)
            if not self.is_playing():
                self.audio_player_process = subprocess.Popen(
                    ['aplay', '-D', PLAYBACK_DEVICE, '-r', '16000', '-f', 'S16_LE', '-c', '1'],
                    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL
                )
            self.audio_player_process.stdin.write(audio_bytes)
            self.audio_player_process.stdin.flush()
        except: pass

    def close_audio_player(self):
        if self.audio_player_process:
            try:
                self.audio_player_process.stdin.close()
                self.audio_player_process.wait()
            except: pass
            self.audio_player_process = None

    def parse_utterance_message(self, payload):
        if not isinstance(payload, dict):
            return None
        utterance_id = payload.get("id")
        audio_blob = payload.get("audio")
        if not utterance_id or not audio_blob:
            self.add_event("Received malformed UTTERANCE payload")
            return None
        try:
            audio_bytes = base64.b64decode(audio_blob)
        except Exception as e:
            self.add_event(f"UTTERANCE decode error: {e}")
            return None
        return {
            "id": utterance_id,
            "pcm": audio_bytes,
            "expect_reply": bool(payload.get("expect_reply")),
            "final_in_request": bool(payload.get("final_in_request")),
        }

    async def handle_utterance(self, payload):
        parsed = self.parse_utterance_message(payload)
        if not parsed:
            return
        if self.mic_mode == self.MIC_MODE_LOCKED:
            self.mic_mode = self.MIC_MODE_WAKE
        await self.playback_queue.put(parsed)

    async def playback_loop(self):
        while not self.shutdown_requested:
            try:
                utterance = await asyncio.wait_for(self.playback_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            try:
                await self.play_single_utterance(utterance)
            finally:
                self.playback_queue.task_done()

    async def play_single_utterance(self, utterance):
        utterance_id = utterance["id"]
        audio_bytes = utterance["pcm"]
        expect_reply = utterance["expect_reply"]
        final_flag = utterance["final_in_request"]

        self.current_utterance_id = utterance_id
        self.awaiting_ack = True
        self.is_speaking = True
        self.log_aipi(f"Playing {utterance_id}")
        try:
            await asyncio.to_thread(self._play_pcm_audio_sync, audio_bytes)
        except Exception as e:
            self.add_event(f"Playback error for {utterance_id}: {e}")
            raise
        finally:
            self.is_speaking = False

        playback_interrupted = self.interrupted_playback_id == utterance_id
        if playback_interrupted:
            self.log_aipi(f"Playback interrupted for {utterance_id}, awaiting resend")
            self.interrupted_playback_id = None
        else:
            self.log_aipi("Playback complete")

        if playback_interrupted:
            self.awaiting_ack = False
            self.current_utterance_id = None
            self.mic_mode = self.MIC_MODE_LOCKED
            return

        ack_sent = await self.send_ack_message(utterance_id)
        self.awaiting_ack = False
        if ack_sent:
            self.pending_resend_id = None
        self.current_utterance_id = None

        if final_flag:
            self.reset_session_state()
            return

        if expect_reply:
            self.awaiting_reply_request_id = utterance_id
            self.mic_mode = self.MIC_MODE_AWAIT_REPLY
            context = self.last_sent_text or f"request {utterance_id}"
            self.awaiting_reply_context = context
            await self.log_awaiting_reply(context)
            self.start_reply_timeout(utterance_id, context)
        else:
            self.awaiting_reply_request_id = None
            self.mic_mode = self.MIC_MODE_WAKE
            self.awaiting_reply_context = None
            self.clear_reply_timeout()

    def _play_pcm_audio_sync(self, audio_bytes):
        try:
            proc = subprocess.Popen(
                ['aplay', '-D', PLAYBACK_DEVICE, '-r', '16000', '-f', 'S16_LE', '-c', '1'],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.audio_player_process = proc
            if proc.stdin:
                proc.stdin.write(audio_bytes)
                proc.stdin.flush()
                proc.stdin.close()
            proc.wait()
        finally:
            self.audio_player_process = None

    def handle_connection_loss(self):
        if self.awaiting_ack and self.current_utterance_id:
            self.pending_resend_id = self.current_utterance_id
            self.interrupted_playback_id = self.current_utterance_id
            self.log_aipi(f"Playback interrupted for {self.current_utterance_id}, pausing for resend")
            self.close_audio_player()
        self.connected = False
        self.ws = None
        if self.mic_mode == self.MIC_MODE_LOCKED:
            self.mic_mode = self.MIC_MODE_WAKE
        self.clear_reply_timeout()

    async def handle_neural_link_severed(self):
        if self.offline_alerted:
            return
        self.offline_alerted = True
        # Alerts only when the neural link genuinely drops so we avoid spamming.
        await self.play_sound("offline.mp3")

    def reset_session_state(self):
        self.awaiting_reply_request_id = None
        self.mic_mode = self.MIC_MODE_WAKE
        self.awaiting_reply_context = None
        self.clear_reply_timeout()

    def build_ack_payload(self, utterance_id):
        return {"type": "ACK_PLAYED", "id": utterance_id}

    def build_resend_payload(self, utterance_id):
        return {"type": "REQUEST_UTTERANCE_REPLAY", "id": utterance_id}

    def build_user_reply_payload(self, request_id, text):
        return {"type": "USER_REPLY", "request_id": request_id, "text": text or ""}

    def clear_reply_timeout(self):
        if self.await_reply_timeout_task:
            self.await_reply_timeout_task.cancel()
            self.await_reply_timeout_task = None

    def start_reply_timeout(self, request_id, context):
        self.clear_reply_timeout()
        self.await_reply_timeout_task = asyncio.create_task(
            self.reply_timeout_watchdog(request_id, context or "pending request")
        )

    async def reply_timeout_watchdog(self, request_id, context):
        try:
            await asyncio.sleep(120)
        except asyncio.CancelledError:
            return
        if self.awaiting_reply_request_id != request_id:
            return
        warning = "⚠ No reply heard within 2 minutes – cancelling request."
        self.add_event(warning)
        self.log_aipi("No reply heard within 120s – cancelling pending confirmation.")
        await self.send_synthetic_cancel_reply()
        self.awaiting_reply_request_id = None
        self.awaiting_reply_context = None
        self.mic_mode = self.MIC_MODE_WAKE
        self.clear_reply_timeout()

    async def brain_send(self, payload):
        if not self.connected or not self.ws:
            return False
        try:
            await self.ws.send(json.dumps(payload))
            return True
        except Exception as e:
            self.add_event(f"Brain send failed: {e}")
            return False

    async def send_ack_message(self, utterance_id):
        sent = await self.brain_send(self.build_ack_payload(utterance_id))
        if sent:
            self.log_aipi(f"Sent ACK_PLAYED {utterance_id}")
        return sent

    async def request_resend_for(self, utterance_id):
        if await self.brain_send(self.build_resend_payload(utterance_id)):
            self.log_aipi(f"Requested resend of {utterance_id}")
            self.pending_resend_id = None

    async def transmit_user_reply(self, request_id, text):
        self.log_aipi(f"Captured reply for {request_id}: \"{text or ''}\"")
        payload = self.build_user_reply_payload(request_id, text)
        await self.brain_send(payload)
        self.clear_reply_timeout()

    async def send_chat_text(self, text):
        sent = await self.brain_send({"type": "chat", "text": text})
        if sent:
            self.add_event(f"Sent: {text}")
        return sent

    async def send_synthetic_cancel_reply(self):
        cancel_text = "No, cancel that."
        self.log_aipi("Sending synthetic cancel reply to Brain: 'No, cancel that.'")
        await self.send_chat_text(cancel_text)

    async def handle_daily_greeting(self):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        after_morning = now.hour >= 5
        last_good_morning = self.session_state.get("last_good_morning")
        greeting_played = False

        if after_morning and last_good_morning != today:
            # First full session after 5 AM gets the "good morning" cue.
            await self.play_sound("good_morning.mp3")
            self.session_state["last_good_morning"] = today
            greeting_played = True
        elif self.session_state.get("last_session_date"):
            # Any additional reconnect within the same day says welcome back.
            await self.play_sound("welcome_back.mp3")
            greeting_played = True

        if not greeting_played:
            # Before 5 AM or first boot still merits a friendly welcome back.
            await self.play_sound("welcome_back.mp3")

        self.session_state["last_session_date"] = today
        self.save_session_state()
        return greeting_played

    async def log_awaiting_reply(self, context):
        message = f"🕒 Awaiting reply (yes/no) for: {context}"
        self.add_event(message)
        self.log_aipi(f"Awaiting user reply for action: {context}")

    async def send_request(self, text):
        # CHECK LOCAL COMMANDS FIRST
        local_response = self.handle_local_command(text)
        
        # If local command is found AND we are online, send FABLE TTS protocol
        if local_response and self.connected and self.ws:
            self.status_text = "PROCESSING"
            # Send the text to the Brain with a special flag to bypass GPT
            await self.ws.send(json.dumps({"type": "simple_local_reply", "text": local_response}))
            self.add_event(f"Local Reply Sent for Fable TTS")
            return

        # STANDARD BRAIN QUERY (or Offline Queue)
        if self.connected and self.ws:
            try:
                self.status_text = "PROCESSING"
                self.last_sent_text = text
                await self.ws.send(json.dumps({"type": "chat", "text": text}))
                self.add_event(f"Sent: {text}")
            except: self.queue_request(text)
        else:
            self.queue_request(text)

    def handle_local_command(self, text):
        text = text.lower()
        if "time" in text: return f"The time is {datetime.now().strftime('%I:%M %p')}"
        if "date" in text: return f"Today is {datetime.now().strftime('%A, %B %d')}"
        return None

    def queue_request(self, text):
        self.add_event(f"Queued: {text}")
        self.queue.append(text)
        self.save_queue()
        self.last_sent_text = text
        # Play confirmation that we cached the instruction locally.
        asyncio.create_task(self.play_sound("queue_added.mp3"))
        if not self.connected:
            # Special cue for when items are queued because the brain is offline.
            asyncio.create_task(self.play_sound("offline_queued.mp3"))

    def _max_pcm_amplitude(self, pcm_bytes):
        if not pcm_bytes:
            return 0
        samples = array('h', pcm_bytes)
        return max((abs(val) for val in samples), default=0)

    def _resample_to_whisper(self, audio_bytes):
        source_rate = self.capture_sample_rate or CAPTURE_SAMPLE_RATE
        target_rate = WHISPER_SAMPLE_RATE
        if not audio_bytes or source_rate == target_rate:
            return audio_bytes, source_rate
        try:
            samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            if samples.size == 0:
                return audio_bytes, source_rate
            duration = samples.size / source_rate
            target_count = max(1, int(round(duration * target_rate)))
            x_old = np.linspace(0, samples.size - 1, num=samples.size, dtype=np.float32)
            x_new = np.linspace(0, samples.size - 1, num=target_count, dtype=np.float32)
            resampled = np.interp(x_new, x_old, samples).astype(np.int16)
            return resampled.tobytes(), target_rate
        except Exception as e:
            self.add_event(f"Resample error: {e}")
            return audio_bytes, source_rate

    def _resample_for_porcupine(self, pcm_bytes):
        if not pcm_bytes:
            return b""
        try:
            samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
            if samples.size == 0:
                return b""
            duration = samples.size / MIC_SAMPLE_RATE
            target_count = max(1, int(round(duration * self.porcupine.sample_rate)))
            x_old = np.linspace(0, samples.size - 1, num=samples.size, dtype=np.float32)
            x_new = np.linspace(0, samples.size - 1, num=target_count, dtype=np.float32)
            resampled = np.interp(x_new, x_old, samples).astype(np.int16)
            if resampled.size < self.porcupine.frame_length:
                resampled = np.pad(resampled, (0, self.porcupine.frame_length - resampled.size), mode='edge')
            elif resampled.size > self.porcupine.frame_length:
                resampled = resampled[:self.porcupine.frame_length]
            return resampled.tobytes()
        except Exception as e:
            self.add_event(f"Porcupine resample error: {e}")
            return b""

    def record_audio_adaptive(self, max_duration=None):
        if not self.pa:
            return b"", {"duration": 0, "samples": 0, "stop_reason": "uninitialized"}
        max_duration = max_duration or CAPTURE_MAX_DURATION
        sample_rate = self.capture_sample_rate or CAPTURE_SAMPLE_RATE
        chunk_frames = max(1, int(sample_rate * (CAPTURE_CHUNK_MS / 1000)))
        chunk_duration = chunk_frames / sample_rate if sample_rate else 0
        silence_limit = SILENCE_TIMEOUT_MS / 1000.0
        tail_keep = SILENCE_TAIL_MS / 1000.0
        buffer = bytearray()
        silence_bytes = 0
        silence_duration = 0.0
        total_duration = 0.0
        stop_reason = "timeout"
        stream_kwargs = dict(
            rate=sample_rate,
            channels=CAPTURE_CHANNELS,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=chunk_frames
        )
        if self.capture_device_index is not None:
            stream_kwargs["input_device_index"] = self.capture_device_index
        wake_paused = False
        if self.audio_stream:
            self._pause_wake_stream()
            wake_paused = True
        try:
            stream = self.pa.open(**stream_kwargs)
        except Exception as open_err:
            self.add_event(f"Capture stream open failed ({sample_rate}Hz): {open_err}")
            if wake_paused:
                try:
                    self._resume_wake_stream()
                except Exception:
                    pass
            if sample_rate != CAPTURE_SAMPLE_RATE:
                self.capture_sample_rate = CAPTURE_SAMPLE_RATE
                return self.record_audio_adaptive(max_duration=max_duration)
            raise
        try:
            while total_duration < max_duration:
                data = stream.read(chunk_frames, exception_on_overflow=False)
                buffer.extend(data)
                total_duration += chunk_duration
                amplitude = self._max_pcm_amplitude(data)
                if amplitude < SILENCE_THRESHOLD:
                    silence_duration += chunk_duration
                    silence_bytes += len(data)
                    if silence_duration >= silence_limit and total_duration >= 0.3:
                        stop_reason = "silence"
                        break
                else:
                    silence_duration = 0.0
                    silence_bytes = 0
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            if wake_paused:
                try:
                    self._resume_wake_stream()
                except Exception as resume_err:
                    self.add_event(f"Wake stream resume error: {resume_err}")

        if stop_reason == "silence" and silence_bytes > 0:
            tail_keep_bytes = int(sample_rate * tail_keep) * CAPTURE_SAMPLE_WIDTH
            bytes_to_trim = max(0, silence_bytes - tail_keep_bytes)
            if bytes_to_trim > 0 and bytes_to_trim <= len(buffer):
                del buffer[-bytes_to_trim:]

        audio_bytes = bytes(buffer)
        total_samples = len(audio_bytes) // CAPTURE_SAMPLE_WIDTH
        actual_duration = total_samples / sample_rate if sample_rate else 0
        metadata = {
            "duration": actual_duration,
            "samples": total_samples,
            "stop_reason": stop_reason
        }
        self.log_aipi(
            f"Capture summary → {actual_duration:.2f}s, {total_samples} samples, stop={stop_reason}"
        )
        return audio_bytes, metadata

    def transcribe(self, audio_bytes):
        processed_bytes, effective_rate = self._resample_to_whisper(audio_bytes)
        target_rate = WHISPER_SAMPLE_RATE if effective_rate != WHISPER_SAMPLE_RATE else effective_rate
        with wave.open(TEMP_AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(CAPTURE_CHANNELS)
            wf.setsampwidth(CAPTURE_SAMPLE_WIDTH)
            wf.setframerate(target_rate)
            wf.writeframes(processed_bytes)
        from faster_whisper import WhisperModel
        segments, _ = self.stt_model.transcribe(TEMP_AUDIO_FILE, beam_size=5)
        return " ".join([s.text for s in segments]).strip()

    async def capture_reply_utterance(self):
        request_id = self.awaiting_reply_request_id
        if not request_id:
            self.mic_mode = self.MIC_MODE_LOCKED
            return
        if not self.audio_stream:
            self.mic_mode = self.MIC_MODE_LOCKED
            self.awaiting_reply_request_id = None
            return

        try:
            self.status_text = "LISTENING"
            await asyncio.sleep(0.05)
            audio_data, _ = await asyncio.to_thread(self.record_audio_adaptive)
            self.status_text = "ANALYZING"
            text = await asyncio.to_thread(self.transcribe, audio_data)
            await self.transmit_user_reply(request_id, text)
        except Exception as e:
            self.add_event(f"Reply capture error: {e}")
        finally:
            self.status_text = "ONLINE"
            self.awaiting_reply_request_id = None
            self.mic_mode = self.MIC_MODE_LOCKED
            self.awaiting_reply_context = None
            self.clear_reply_timeout()

    async def voice_loop(self):
        while not self.shutdown_requested:
            if self.loop_running:
                if self.gaming_mode:
                    if self.status_text != "GAMING":
                        self.status_text = "GAMING"
                    await asyncio.sleep(0.1)
                    continue
                try:
                    if self.mic_mode == self.MIC_MODE_LOCKED:
                        await asyncio.sleep(0.05)
                        continue

                    if self.mic_mode == self.MIC_MODE_AWAIT_REPLY:
                        await self.capture_reply_utterance()
                        await asyncio.sleep(0.05)
                        continue

                    if self.audio_player_process and self.audio_player_process.poll() is None:
                        self.status_text = "SPEAKING"
                        await asyncio.sleep(0.1)
                        continue

                    if not self.audio_stream:
                        await asyncio.sleep(0.1)
                        continue

                    pcm = self.audio_stream.read(self.wake_chunk_size, exception_on_overflow=False)
                    resampled = self._resample_for_porcupine(pcm)
                    if not resampled:
                        await asyncio.sleep(0.01)
                        continue
                    pcm_unpacked = struct.unpack_from("h" * self.porcupine.frame_length, resampled)
                    if self.porcupine.process(pcm_unpacked) >= 0:
                        self.add_event("⚡ Wake Word Detected")
                        self.status_text = "LISTENING"
                        audio_data, _ = await asyncio.to_thread(self.record_audio_adaptive)
                        
                        self.status_text = "ANALYZING"
                        text = await asyncio.to_thread(self.transcribe, audio_data)
                        
                        if text and len(text) > 2:
                            self.add_event(f"Heard (Jarvis): {text}")
                            await self.send_request(text)
                        self.status_text = "ONLINE"
                except:
                    pass
            else:
                 if self.status_text != "SLEEPING": self.status_text = "SLEEPING"
            await asyncio.sleep(0.01)
        self.status_text = "OFFLINE"

    async def api_server(self):
        app = web.Application()
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=("GET", "POST", "DELETE", "OPTIONS")
            )
        })
        
        async def get_state(r): 
            queue_snapshot = self.queue_snapshot()
            return web.json_response({
                "core_state": self.status_text.lower(), "loop_running": self.loop_running,
                "brain_connected": self.connected, "model_label": "Ollama Llama 3",
                "last_brain_action": self.events[-1]["message"] if self.events else "Monitoring",
                "cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent,
                "queue": self.queue,
                "queue_length": len(self.queue),
                "queue_preview": [item["text"] for item in queue_snapshot[:3]],
                "gaming_mode": self.gaming_mode,
                "presence_state": self.presence_state,
                "presence_last_update": self.presence_last_update
            })
        async def get_events(r): return web.json_response({"events": self.events})
        async def handle_action(r): 
            d = await r.json()
            action = d.get('action')
            if action == 'start': self.loop_running = True
            elif action == 'stop': self.loop_running = False
            elif action == 'gaming': 
                self.set_gaming_mode(not self.gaming_mode)
            elif action == 'clear_queue':
                self.clear_queue_items()
            return web.json_response({"status": "ok"})

        async def get_queue(_r):
            snapshot = self.queue_snapshot()
            return web.json_response({"queue": snapshot, "count": len(self.queue)})

        async def clear_queue(_r):
            cleared = self.clear_queue_items()
            return web.json_response({"status": "ok", "cleared": cleared})

        async def delete_queue_item(r):
            item_id = r.match_info.get("item_id")
            removed = self.remove_queue_item_by_id(item_id)
            if removed is None:
                return web.json_response({"status": "not_found"}, status=404)
            return web.json_response({"status": "ok", "removed_id": item_id})

        async def initialize_check(_r):
            summary = self.get_health_summary()
            summary_text = self.format_health_summary(summary)
            self.add_event(summary_text)
            return web.json_response({"summary": summary, "summary_text": summary_text})

        async def toggle_gaming_mode(r):
            try:
                payload = await r.json()
            except:
                payload = {}
            desired = payload.get("enable")
            if desired is None:
                desired = not self.gaming_mode
            self.set_gaming_mode(bool(desired))
            return web.json_response({"status": "ok", "gaming_mode": self.gaming_mode})

        async def codex_input(r):
            try:
                data = await r.json()
            except Exception:
                data = {}
            text = (data.get('input') or data.get('text') or '').strip()
            if not text:
                return web.json_response({"status": "error", "message": "empty input"}, status=400)
            self.add_event(f"[USER_TYPED] {text}")
            asyncio.create_task(self.send_request(text))
            return web.json_response({"status": "accepted"})

        async def reply_panel(r):
            try:
                data = await r.json()
            except Exception:
                data = {}
            reply = data.get('reply')
            provided_choices = data.get('choices')
            question_id = data.get('question_id') or self.awaiting_reply_request_id
            if provided_choices and isinstance(provided_choices, list):
                choices = [str(c) for c in provided_choices if str(c).strip()]
            elif reply:
                choices = [str(reply)]
            else:
                choices = []
            if not choices:
                return web.json_response({"status": "error", "message": "no reply"}, status=400)
            payload = {"type": "followup_choice", "choices": choices}
            if question_id:
                payload["question_id"] = question_id
            asyncio.create_task(self.brain_send(payload))
            self.add_event(f"[HUD] followup_choice {payload}")
            return web.json_response({"status": "accepted"})

        async def get_presence(_r):
            return web.json_response({
                "state": self.presence_state,
                "last_update": self.presence_last_update
            })

        async def update_presence(r):
            try:
                data = await r.json()
            except Exception:
                data = {}
            desired_state = (data.get("state") or "").strip().lower()
            source = data.get("source") or "api"
            if desired_state not in ("present", "away", "unknown"):
                return web.json_response({"status": "error", "message": "invalid presence state"}, status=400)
            await self.set_presence_state(desired_state, source=source)
            return web.json_response({
                "status": "ok",
                "state": self.presence_state,
                "last_update": self.presence_last_update
            })

        async def shutdown_server(_r):
            asyncio.create_task(self.delayed_shutdown())
            return web.json_response({"status": "ok", "message": "Jarvis Lite shutting down"})

        cors.add(app.router.add_resource("/api/state")).add_route("GET", get_state)
        cors.add(app.router.add_resource("/api/events")).add_route("GET", get_events)
        cors.add(app.router.add_resource("/api/action")).add_route("POST", handle_action)
        cors.add(app.router.add_resource("/api/codex")).add_route("POST", codex_input)
        cors.add(app.router.add_resource("/api/reply")).add_route("POST", reply_panel)
        queue_resource = cors.add(app.router.add_resource("/api/queue"))
        queue_resource.add_route("GET", get_queue)
        queue_resource.add_route("DELETE", clear_queue)
        cors.add(app.router.add_resource("/api/queue/{item_id}")).add_route("DELETE", delete_queue_item)
        cors.add(app.router.add_resource("/api/initialize")).add_route("POST", initialize_check)
        cors.add(app.router.add_resource("/api/gaming")).add_route("POST", toggle_gaming_mode)
        cors.add(app.router.add_resource("/api/shutdown")).add_route("POST", shutdown_server)
        presence_resource = cors.add(app.router.add_resource("/api/presence"))
        presence_resource.add_route("GET", get_presence)
        presence_resource.add_route("POST", update_presence)

        runner = web.AppRunner(app)
        await runner.setup()
        self.api_runner = runner
        await web.TCPSite(runner, '0.0.0.0', API_PORT).start()

    async def run(self):
        await asyncio.gather(
            self.connect_brain(),
            self.voice_loop(),
            self.api_server(),
            self.playback_loop(),
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Lite runtime")
    parser.add_argument(
        "--test-sound",
        metavar="ASSET",
        help="Play a single sound asset (e.g. mainframe_online.mp3) and exit",
    )
    args = parser.parse_args()

    if args.test_sound:
        jl = JarvisLite()
        try:
            asyncio.run(jl.play_sound(args.test_sound))
        except KeyboardInterrupt:
            print("Stopping test...")
    else:
        try:
            asyncio.run(JarvisLite().run())
        except KeyboardInterrupt:
            print("Stopping...")
