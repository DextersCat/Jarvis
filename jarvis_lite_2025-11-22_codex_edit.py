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
from datetime import datetime
from aiohttp import web
import aiohttp_cors

# --- CONFIGURATION ---
BRAIN_URL = "ws://192.168.1.26:8765"
API_PORT = 8766
ASSET_PATH = "/home/spencer/jarvis_v2/assets/"
QUEUE_FILE = "/home/spencer/jarvis_v2/queue.json"
TEMP_AUDIO_FILE = "/home/spencer/jarvis_v2/temp_input.wav"
RUNTIME_DIR = "/home/spencer/jarvis_v2/runtime"
SESSION_STATE_FILE = os.path.join(RUNTIME_DIR, "session_state.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s [LITE] %(message)s')
logger = logging.getLogger("JarvisLite")

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
        self.current_utterance_id = None
        self.awaiting_ack = False
        self.pending_resend_id = None
        self.awaiting_reply_request_id = None
        self.mic_mode = self.MIC_MODE_WAKE
        self.interrupted_playback_id = None
        self.offline_alerted = False
        self.mainframe_handshake_done = False
        self.session_state = self.load_session_state()
        self.shutdown_sound_played = False
        
        # Audio Setup
        try:
            key = os.environ.get("PORCUPINE_ACCESS_KEY")
            self.porcupine = pvporcupine.create(access_key=key, keywords=['jarvis'], sensitivities=[0.6])
            self.pa = pyaudio.PyAudio()
            mic_index = self._select_input_device()
            stream_kwargs = dict(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            if mic_index is not None:
                stream_kwargs["input_device_index"] = mic_index
            self.audio_stream = self.pa.open(**stream_kwargs)
            if mic_index is not None:
                device_name = self.pa.get_device_info_by_index(mic_index).get("name", "Mic")
                self.add_event(f"Microphone Initialized ({device_name})")
            else:
                self.add_event("Microphone Initialized (default input)")
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

    def log_aipi(self, message):
        self.add_event(f"[AiPi] {message}")

    def _select_input_device(self):
        try:
            if not hasattr(self, "pa"):
                return None
            fallback = None
            for idx in range(self.pa.get_device_count()):
                info = self.pa.get_device_info_by_index(idx)
                if info.get("maxInputChannels", 0) >= 1:
                    if "usb 2.0 camera" in info.get("name", "").lower():
                        return idx
                    if fallback is None:
                        fallback = idx
            return fallback
        except Exception as e:
            self.add_event(f"Audio Device Scan Error: {e}")
            return None

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
        if os.path.exists(full_path):
            proc = await asyncio.create_subprocess_exec(
                "ffplay", "-nodisp", "-autoexit", full_path,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            await proc.wait()

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
                    ['aplay', '-r', '16000', '-f', 'S16_LE', '-c', '1'],
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
            self.log_aipi("Awaiting user reply")
        else:
            self.awaiting_reply_request_id = None
            self.mic_mode = self.MIC_MODE_WAKE

    def _play_pcm_audio_sync(self, audio_bytes):
        try:
            proc = subprocess.Popen(
                ['aplay', '-r', '16000', '-f', 'S16_LE', '-c', '1'],
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

    async def handle_neural_link_severed(self):
        if self.offline_alerted:
            return
        self.offline_alerted = True
        # Alerts only when the neural link genuinely drops so we avoid spamming.
        await self.play_sound("offline.mp3")

    def reset_session_state(self):
        self.awaiting_reply_request_id = None
        self.mic_mode = self.MIC_MODE_WAKE

    def build_ack_payload(self, utterance_id):
        return {"type": "ACK_PLAYED", "id": utterance_id}

    def build_resend_payload(self, utterance_id):
        return {"type": "REQUEST_UTTERANCE_REPLAY", "id": utterance_id}

    def build_user_reply_payload(self, request_id, text):
        return {"type": "USER_REPLY", "request_id": request_id, "text": text or ""}

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
        # Play confirmation that we cached the instruction locally.
        asyncio.create_task(self.play_sound("queue_added.mp3"))
        if not self.connected:
            # Special cue for when items are queued because the brain is offline.
            asyncio.create_task(self.play_sound("offline_queued.mp3"))

    def record_audio(self, duration=4):
        frames = []
        for _ in range(int(16000 / 512 * duration)):
            try:
                data = self.audio_stream.read(512, exception_on_overflow=False)
                frames.append(data)
            except: pass
        return b''.join(frames)

    def transcribe(self, audio_bytes):
        with wave.open(TEMP_AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_bytes)
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
            audio_data = await asyncio.to_thread(self.record_audio, 4)
            self.status_text = "ANALYZING"
            text = await asyncio.to_thread(self.transcribe, audio_data)
            await self.transmit_user_reply(request_id, text)
        except Exception as e:
            self.add_event(f"Reply capture error: {e}")
        finally:
            self.status_text = "ONLINE"
            self.awaiting_reply_request_id = None
            self.mic_mode = self.MIC_MODE_LOCKED

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

                    pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                    pcm_unpacked = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    if self.porcupine.process(pcm_unpacked) >= 0:
                        self.add_event("⚡ Wake Word Detected")
                        self.status_text = "LISTENING"
                        audio_data = await asyncio.to_thread(self.record_audio, 4)
                        
                        self.status_text = "ANALYZING"
                        text = await asyncio.to_thread(self.transcribe, audio_data)
                        
                        if text and len(text) > 2:
                            self.add_event(f"Heard: {text}")
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
                "gaming_mode": self.gaming_mode
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

        async def shutdown_server(_r):
            asyncio.create_task(self.delayed_shutdown())
            return web.json_response({"status": "ok", "message": "Jarvis Lite shutting down"})

        cors.add(app.router.add_resource("/api/state")).add_route("GET", get_state)
        cors.add(app.router.add_resource("/api/events")).add_route("GET", get_events)
        cors.add(app.router.add_resource("/api/action")).add_route("POST", handle_action)
        queue_resource = cors.add(app.router.add_resource("/api/queue"))
        queue_resource.add_route("GET", get_queue)
        queue_resource.add_route("DELETE", clear_queue)
        cors.add(app.router.add_resource("/api/queue/{item_id}")).add_route("DELETE", delete_queue_item)
        cors.add(app.router.add_resource("/api/initialize")).add_route("POST", initialize_check)
        cors.add(app.router.add_resource("/api/gaming")).add_route("POST", toggle_gaming_mode)
        cors.add(app.router.add_resource("/api/shutdown")).add_route("POST", shutdown_server)

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
    try: asyncio.run(JarvisLite().run())
    except KeyboardInterrupt: print("Stopping...")
