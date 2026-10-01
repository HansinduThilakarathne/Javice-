"""
J.A.R.V.I.S. MARK VII - Master Autonomous System
Continuous Hands-Free Real-Time Conversational AI
Integrated with PyWebView HUD, Biometric Security Gate, Voice Engine & Gemini 2.5 Flash
Built exclusively for Administrator: Manuja (මනුජ)
"""

import os
import sys
import time
import json
import threading
import webview
from pathlib import Path

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import config
import security
import voice_engine
import system_tools
from brain import JarvisBrain

class JarvisSystemAPI:
    """
    Exposes Python backend methods directly to JavaScript in the PyWebView HUD.
    """
    def __init__(self, system_controller):
        self._system = system_controller

    def on_user_voice_request(self):
        """Manual voice trigger fallback if clicked by Manuja."""
        threading.Thread(target=self._system.process_manual_voice_interaction, daemon=True).start()
        return {"status": "listening_initiated"}

    def on_user_text_command(self, text: str):
        """Called when Manuja submits a command via the HUD text input."""
        threading.Thread(target=self._system.handle_command, args=(text,), daemon=True).start()
        return {"status": "command_received"}

    def on_screenshot_request(self):
        """Takes full screen capture and announces to Manuja."""
        path = system_tools.take_screenshot()
        self._system.ui_append_log("SYSTEM", f"තිර ඡායාරූපය ලබාගන්නා ලදී: {path}", "system")
        self._system.speak_and_display("[SPEAK] හරි සර්, මම තිරයේ ඡායාරූපය සුරකින ලදී.")
        return {"status": "success", "path": path}

    def on_lock_pc_request(self):
        """Locks the workstation instantly."""
        self._system.ui_append_log("SYSTEM", "පරිගණකය අගුලු දමයි...", "alert")
        self._system.speak_and_display("[SPEAK] සර්, පරිගණකය අගුලු දමන ලදී.")
        system_tools.lock_pc()
        return {"status": "locked"}

    def on_launch_app_request(self, app_name: str):
        """Launches requested application."""
        result = system_tools.open_application(app_name)
        self._system.ui_append_log("SYSTEM", result, "system")
        self._system.speak_and_display(f"[SPEAK] {result}")
        return {"status": "launched", "app": app_name}

    def on_run_project_request(self, project_name: str, file_specs: dict, test_command: str = None):
        """Executes autonomous project builder."""
        result = system_tools.build_autonomous_project(project_name, file_specs, test_command)
        self._system.ui_append_log("AUTONOMOUS", result["summary_sinhala"], "ai")
        self._system.speak_and_display(f"[SPEAK] {result['summary_sinhala']}")
        return result

    def on_file_upload(self, file_name: str, file_data_base64: str):
        """Handles drag-and-drop file / vision upload from the HUD."""
        threading.Thread(target=self._system.handle_file_upload, args=(file_name, file_data_base64), daemon=True).start()
        return {"status": "analyzing", "file": file_name}

    def on_screen_analysis_request(self):
        """Manual screen analysis trigger via HUD."""
        threading.Thread(target=self._system.handle_screen_analysis, daemon=True).start()
        return {"status": "analyzing_screen"}

    def toggle_fullscreen(self):
        """Toggles between fullscreen HUD and docked floating desktop widget mode."""
        if self._system.window:
            try:
                self._system.window.toggle_fullscreen()
                print("[UI] Fullscreen toggled.")
            except Exception as e:
                print(f"[UI] Fullscreen toggle error: {e}")
        return {"status": "toggled"}

    def on_close_widget(self):
        """Minimizes the floating desktop widget to the taskbar."""
        if self._system.window:
            try:
                self._system.window.minimize()
            except Exception:
                pass
        return {"status": "minimized"}


class JarvisController:
    """
    Central Controller for J.A.R.V.I.S. MARK VII.
    Manages telemetry loop, autonomous hands-free voice loop, biometric security gate, and HUD.
    """
    def __init__(self):
        self.window = None
        self.brain = JarvisBrain()
        self.security_gate = security.get_security_gate()
        self.is_running = True
        self.is_processing = False
        self.pending_high_risk_action = None
        self.pending_high_risk_desc = ""
        self.api = JarvisSystemAPI(self)

    def set_window(self, window):
        """Assigns the active PyWebView window handle."""
        self.window = window

    # ---------------- UI JS BRIDGE HELPERS ---------------- #

    def evaluate_js_safe(self, script: str):
        """Safely evaluates JS in the webview window."""
        if self.window:
            try:
                self.window.evaluate_js(script)
            except Exception as e:
                # Window may still be mounting or closing
                pass

    def ui_append_log(self, sender: str, message: str, log_type: str = "ai"):
        """Appends a message to the HUD terminal stream."""
        clean_msg = message.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        clean_sender = sender.replace('\\', '\\\\').replace('"', '\\"')
        js = f'window.appendLog("{clean_sender}", "{clean_msg}", "{log_type}");'
        self.evaluate_js_safe(js)

    def ui_set_emotion(self, emotion: str):
        """Sets the 3D Arc Reactor / Core state (LISTENING, THINKING, SPEAKING, etc.)."""
        js = f'window.setEmotionState("{emotion}");'
        self.evaluate_js_safe(js)

    def ui_set_face_state(self, state: str, emotion: str = "SPEAK"):
        """Updates 3D Cyber Face animation state and emotion."""
        js = f'if (window.setFaceState) {{ window.setFaceState("{state}", "{emotion}"); }}'
        self.evaluate_js_safe(js)

    def ui_set_lip_sync(self, amplitude: float):
        """Pushes real-time audio amplitude for 3D mouth lip-sync articulation."""
        js = f'if (window.setFaceLipSync) {{ window.setFaceLipSync({amplitude:.3f}); }}'
        self.evaluate_js_safe(js)

    def ui_set_biometric(self, verified: bool, user: str, detail: str):
        """Updates biometric card state on the HUD."""
        js = f'window.setBiometricStatus({str(verified).lower()}, "{user}", "{detail}");'
        self.evaluate_js_safe(js)

    def ui_update_stats(self, stats: dict):
        """Pushes hardware telemetry data to HUD."""
        stats_json = json.dumps(stats)
        js = f'window.updateStats({stats_json});'
        self.evaluate_js_safe(js)

    # ---------------- TELEMETRY THREAD ---------------- #

    def telemetry_loop(self):
        """Thread 1: Hardware telemetry polling loop feeding psutil data every 2 seconds."""
        print("[TELEMETRY] Hardware diagnostics loop active.")
        time.sleep(1.5)  # Wait for webview DOM to mount
        while self.is_running:
            try:
                stats = system_tools.get_system_stats()
                self.ui_update_stats(stats)
            except Exception as e:
                print(f"[TELEMETRY] Error: {e}")
            time.sleep(config.TELEMETRY_INTERVAL_SECONDS)

    # ---------------- SECURITY & VOICE PROCESSING ---------------- #

    def speak_and_display(self, text_with_emotion: str, emotion_hint: str = None):
        """
        Parses emotional tags, updates 3D face state, logs to terminal, and speaks via edge-tts.
        Streams real-time mouth movement ticks to the 3D Face mesh.
        """
        cleaned_text, parsed_emotion = voice_engine.parse_emotion_and_clean(text_with_emotion)
        emotion = emotion_hint if (emotion_hint and emotion_hint != "SPEAK") else parsed_emotion

        self.ui_set_emotion(emotion)
        self.ui_set_face_state("SPEAKING", emotion)
        self.ui_append_log("J.A.R.V.I.S.", cleaned_text, "ai")

        def on_start(emo):
            self.ui_set_face_state("SPEAKING", emo)
            self.ui_set_emotion(emo)

        def on_finish():
            self.ui_set_lip_sync(0.0)

        def on_tick(amp):
            self.ui_set_lip_sync(amp)

        voice_engine.speak_sinhala(
            cleaned_text,
            on_start=on_start,
            on_finish=on_finish,
            on_tick=on_tick
        )

    def verify_biometric_gate(self, raw_audio=None) -> bool:
        """
        Runtime Security Gate:
        Sole User Biometric Verification for Manuja.
        Camera is verified ONLY ONCE at startup and never touched again.
        Runtime command gates rely strictly on voice signature biometrics.
        External/intruder voices are quietly ignored without triggering camera errors.
        """
        is_verified, details = self.security_gate.verify_user(audio_data=raw_audio)
        if is_verified:
            self.ui_set_biometric(True, config.PRIMARY_USER, "BIOMETRIC MATCH CONFIRMED")
            return True
        else:
            # External/intruder voice quietly ignored
            print(f"[SECURITY] Voice signature verification: {details.get('reason', 'External voice')}. Quietly ignored.")
            return False

    def handle_screen_analysis(self, prompt_instruction: str = ""):
        """
        Screen Vision & Analysis Pipeline:
        Captures active desktop screen and streams Gemini Vision analysis.
        """
        self.ui_set_emotion("THINKING")
        self.ui_set_face_state("THINKING", "THINKING")
        self.ui_append_log("MANUJA", "පරිගණක තිරය විශ්ලේෂණය කරන්න", "user")

        try:
            for sentence_chunk, emotion in self.brain.stream_screen_analysis(prompt_instruction):
                if not self.is_running:
                    break
                if sentence_chunk and sentence_chunk.strip():
                    self.speak_and_display(sentence_chunk, emotion)
        except Exception as e:
            print(f"[SCREEN VISION] Stream error: {e}")

        if self.is_running and not voice_engine.is_speaking():
            self.ui_set_face_state("LISTENING", "IDLE")
            self.ui_set_emotion("LISTENING")

    def handle_command(self, user_command: str, raw_audio=None):
        """
        Processes Manuja's text or voice command through Voice Biometrics,
        Multi-Tier Security Sandbox, and Streaming Cognitive Brain.
        """
        # Transcript Verification: Unintelligible noise / empty speech
        if not user_command or not user_command.strip() or user_command == "__UNINTELLIGIBLE__":
            self.ui_append_log("SYSTEM", "[STT]: Voice detected but unintelligible", "alert")
            unintelligible_msg = "සර්, මට ඔබේ හඬ පැහැදිලිව ඇසුණේ නැත. කරුණාකර නැවත පවසන්න."
            self.ui_append_log("SYSTEM", f"[TTS]: Streaming audio output: {unintelligible_msg}", "system")
            self.speak_and_display(f"[SPEAK] {unintelligible_msg}")
            return

        # Security Check via Voice Biometrics (Camera is permanently closed)
        is_authorized = self.verify_biometric_gate(raw_audio=raw_audio)
        if not is_authorized:
            return

        # 1. Real-time Activity Stream Logging Sync
        self.ui_append_log("SYSTEM", f"[STT]: Voice detected from Sir", "system")
        self.ui_append_log("MANUJA", user_command, "user")

        # 2. Multi-Tier Security Sandbox: Check for Pending High-Risk Confirmation
        if self.pending_high_risk_action:
            lower_cmd = user_command.lower().strip()
            if any(w in lower_cmd for w in ["ඔව්", "yes", "proceed", "හරි", "කරන්න", "ඉදිරියට", "කමක් නෑ"]):
                act = self.pending_high_risk_action
                desc = self.pending_high_risk_desc
                self.pending_high_risk_action = None
                self.pending_high_risk_desc = ""
                system_tools.log_audit_event(act, "HIGH", "CONFIRMED", f"Confirmed by Sir: {desc}")
                self.speak_and_display("[SPEAK] සර්, ඔබගේ අනුමැතිය ලැබුණි. ක්‍රියාත්මක කරමි.")
                ret, stdout, stderr = system_tools.execute_shell_command(act)
                self.speak_and_display(f"[SPEAK] සර්, ක්‍රියාව අවසන් කරන ලදී. {stdout or stderr or 'සාර්ථකයි.'}")
                return
            elif any(w in lower_cmd for w in ["එපා", "no", "cancel", "නවතන්න", "නවත්තන්න", "අවලංගු", "නැහැ"]):
                act = self.pending_high_risk_action
                self.pending_high_risk_action = None
                self.pending_high_risk_desc = ""
                system_tools.log_audit_event(act, "HIGH", "CANCELLED", "Cancelled by Sir")
                self.speak_and_display("[SPEAK] හරි සර්, එම අනතුරුදායක ක්‍රියාව අවලංගු කරන ලදී.")
                return

        # 3. Check Direct Local Tools Interception
        tool_handled, tool_response, emotion = self.brain.parse_intent_and_execute_tools(user_command)
        if tool_handled:
            if tool_response == "__SCREEN_ANALYSIS__":
                self.handle_screen_analysis()
                return
            elif tool_response.startswith("__HIGH_RISK__:"):
                parts = tool_response.split(":", 2)
                reason = parts[1] if len(parts) > 1 else "Unknown"
                cmd = parts[2] if len(parts) > 2 else user_command
                self.pending_high_risk_desc = reason
                self.pending_high_risk_action = cmd
                system_tools.log_audit_event(cmd, "HIGH", "PENDING_CONFIRMATION", reason)
                self.ui_set_face_state("ALERT", "ALERT")
                self.ui_set_emotion("ALERT")
                self.speak_and_display("[SPEAK] සර්, මෙම ක්‍රියාව අනතුරුදායක විය හැක. ඉදිරියට යන්නද?")
                return
            else:
                self.speak_and_display(tool_response, emotion)
                return

        # 4. Conversational Queries: Stream through Gemini Flash
        self.ui_set_emotion("THINKING")
        self.ui_set_face_state("THINKING", "THINKING")
        self.ui_append_log("SYSTEM", "[BRAIN]: Processing response...", "system")

        try:
            for sentence_chunk, emotion in self.brain.stream_think_and_respond(user_command):
                if not self.is_running:
                    break
                if sentence_chunk and sentence_chunk.strip():
                    self.ui_append_log("SYSTEM", f"[TTS]: Streaming audio output", "system")
                    self.speak_and_display(sentence_chunk, emotion)
        except Exception as e:
            print(f"[CONVERSATION] Streaming response error: {e}")
            fallback_msg = "සර්, සම්බන්ධතාවයේ සුළු ප්‍රමාදයක් පවතී. මම නැවත උත්සාහ කරන්නද?"
            self.ui_append_log("SYSTEM", f"[TTS]: Streaming audio output", "system")
            self.speak_and_display(f"[SPEAK] {fallback_msg}")

        # Return to listening state after all sentences finish
        if self.is_running and not voice_engine.is_speaking():
            self.ui_set_face_state("LISTENING", "IDLE")
            self.ui_set_emotion("LISTENING")

    def handle_file_upload(self, file_name: str, file_data_base64: str):
        """
        Multi-Modal Vision & File Analysis Handler:
        Decodes uploaded payload, calls Gemini multimodal vision pipeline,
        and streams spoken analysis in Sinhala addressed exclusively to Sir.
        """
        if not file_data_base64:
            return
        try:
            import base64
            # Strip data URL prefix if present (e.g. data:image/png;base64,...)
            if "," in file_data_base64:
                file_data_base64 = file_data_base64.split(",", 1)[1]
            raw_bytes = base64.b64decode(file_data_base64)
        except Exception as e:
            print(f"[UPLOAD] Base64 decode error: {e}")
            return

        # Visual feedback on HUD
        self.ui_set_emotion("THINKING")
        self.ui_set_face_state("THINKING", "THINKING")
        self.ui_append_log("MANUJA", f"ගොනුව විශ්ලේෂණය සඳහා යොමු කරන ලදී: {file_name}", "user")

        try:
            for sentence_chunk, emotion in self.brain.stream_file_analysis(file_name, raw_bytes):
                if not self.is_running:
                    break
                if sentence_chunk and sentence_chunk.strip():
                    self.speak_and_display(sentence_chunk, emotion)
        except Exception as e:
            print(f"[UPLOAD] File analysis error: {e}")

        if self.is_running and not voice_engine.is_speaking():
            self.ui_set_face_state("LISTENING", "IDLE")
            self.ui_set_emotion("LISTENING")

    def process_manual_voice_interaction(self):
        """Fallback one-shot voice input when button is clicked."""
        if self.is_processing:
            return

        def _manual_worker():
            self.is_processing = True
            try:
                self.ui_set_emotion("LISTENING")
                self.ui_set_face_state("LISTENING", "IDLE")
                spoken_text = voice_engine.listen_sinhala(timeout=6, phrase_time_limit=15)
                if spoken_text and spoken_text.strip():
                    self.handle_command(spoken_text)
                else:
                    self.handle_command("__UNINTELLIGIBLE__")
            finally:
                self.is_processing = False
                if self.is_running and not voice_engine.is_speaking():
                    self.ui_set_emotion("LISTENING")
                    self.ui_set_face_state("LISTENING", "IDLE")

        threading.Thread(target=_manual_worker, daemon=True).start()

    def voice_listener_loop(self):
        """
        Thread 2: 100% Autonomous Hands-Free Real-Time Conversational Loop.
        Zero button clicks: Continuously listens for Manuja, verifies voice biometrics, and responds.
        """
        print("[VOICE] Autonomous hands-free listening loop initialized.")
        time.sleep(2.5)  # Allow HUD window to render

        # 1. ONE-TIME STARTUP CAMERA AUTHENTICATION: executes ONLY ONCE at boot
        try:
            print("[SECURITY] Running One-Time Startup Camera Authentication...")
            is_verified = self.security_gate.one_time_startup_verification()
            if is_verified:
                self.ui_set_biometric(True, config.PRIMARY_USER, "BIOMETRIC MATCH CONFIRMED")
            else:
                self.ui_set_biometric(True, config.PRIMARY_USER, "BIOMETRIC ACTIVE // MANUJA")
        except Exception as e:
            print(f"[SECURITY] Boot verification note: {e}")

        # 2. Boot greeting in calm, clear Sinhala as required
        startup_greeting = (
            "[SPEAK] සුබ දවසක් සර්. පද්ධතිය සක්‍රියයි. මම ඔබගේ සහයට සූදානම්."
        )
        self.speak_and_display(startup_greeting)

        def on_listening_active():
            if not voice_engine.is_speaking() and not self.is_processing:
                self.ui_set_emotion("LISTENING")
                self.ui_set_face_state("LISTENING", "IDLE")

        # Persistent continuous listening generator
        while self.is_running:
            try:
                for item in voice_engine.continuous_listener_generator(on_listening_active=on_listening_active):
                    if not self.is_running:
                        break

                    if isinstance(item, tuple):
                        spoken_text, raw_audio = item
                    else:
                        spoken_text, raw_audio = item, None

                    if not spoken_text or not spoken_text.strip():
                        continue

                    # Don't capture while speaking
                    if voice_engine.is_speaking() or self.is_processing:
                        continue

                    # Dedicated non-blocking execution thread for full pipeline
                    def _async_voice_task(cmd_text, cmd_audio):
                        self.is_processing = True
                        try:
                            self.handle_command(cmd_text, raw_audio=cmd_audio)
                        finally:
                            self.is_processing = False
                            if self.is_running and not voice_engine.is_speaking():
                                self.ui_set_emotion("LISTENING")
                                self.ui_set_face_state("LISTENING", "IDLE")

                    threading.Thread(
                        target=_async_voice_task,
                        args=(spoken_text, raw_audio),
                        daemon=True
                    ).start()

            except Exception as e:
                print(f"[CONVERSATION] Stream cycle error: {e}")
                time.sleep(1.0)


def main():
    print("==================================================")
    print("   J.A.R.V.I.S. MARK VII - INITIALIZING...")
    print(f"   PRIMARY ADMINISTRATOR: {config.PRIMARY_USER}")
    print("   MODE: 100% AUTONOMOUS HANDS-FREE VOICE LOOP")
    print("==================================================")

    # Ensure Windows Auto-Startup integration is installed
    try:
        startup_res = system_tools.enable_windows_startup()
        print(f"[SYSTEM] Auto-startup status: {startup_res.get('message', 'Active')}")
    except Exception as e:
        print(f"[SYSTEM] Startup configuration note: {e}")

    # Initialize controller
    controller = JarvisController()

    # Thread 1: Hardware Telemetry Loop (every 2 seconds)
    telemetry_thread = threading.Thread(target=controller.telemetry_loop, daemon=True)
    telemetry_thread.start()

    # Thread 2: Autonomous Hands-Free Voice & Intelligence Monitor
    voice_thread = threading.Thread(target=controller.voice_listener_loop, daemon=True)
    voice_thread.start()

    # Detect primary screen resolution dynamically
    try:
        import pyautogui
        screen_w, screen_h = pyautogui.size()
    except Exception:
        screen_w, screen_h = 1920, 1080

    if getattr(config, 'WIDGET_MODE', True):
        # Docked Floating Desktop Corner Widget (Bottom-Right Corner)
        widget_w = getattr(config, 'WIDGET_WIDTH', 400)
        widget_h = getattr(config, 'WIDGET_HEIGHT', 580)
        offset_x = getattr(config, 'WIDGET_OFFSET_X', 25)
        offset_y = getattr(config, 'WIDGET_OFFSET_Y', 65)
        widget_x = max(0, screen_w - widget_w - offset_x)
        widget_y = max(0, screen_h - widget_h - offset_y)

        print(f"[UI] Docking J.A.R.V.I.S. at bottom-right corner: {widget_w}x{widget_h} @ ({widget_x}, {widget_y})")

        window = webview.create_window(
            title=config.HUD_WINDOW_TITLE,
            url=config.UI_INDEX_PATH,
            width=widget_w,
            height=widget_h,
            x=widget_x,
            y=widget_y,
            resizable=True,
            frameless=True,
            on_top=True,
            transparent=True,
            easy_drag=True,
            js_api=controller.api,
            background_color='#04090d'
        )
    else:
        # Fullscreen / Standard HUD Dimensions
        window = webview.create_window(
            title=config.HUD_WINDOW_TITLE,
            url=config.UI_INDEX_PATH,
            width=config.HUD_WINDOW_WIDTH,
            height=config.HUD_WINDOW_HEIGHT,
            resizable=True,
            frameless=False,
            easy_drag=True,
            js_api=controller.api,
            background_color='#04090d'
        )

    controller.set_window(window)

    # Start PyWebView native loop
    webview.start(debug=False)

    # Teardown on window close
    controller.is_running = False
    voice_engine.stop_continuous_listener()
    print("[SYSTEM] J.A.R.V.I.S. MARK VII successfully shutdown.")

if __name__ == "__main__":
    main()
