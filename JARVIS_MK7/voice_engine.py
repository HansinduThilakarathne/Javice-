"""
J.A.R.V.I.S. MARK VII - High Performance Autonomous Voice Engine
Continuous Hands-Free Sinhala Speech-to-Text (si-LK) & Neural TTS
Zero Button Clicks | Zero-Latency In-Memory Audio | High-Fidelity Sinhala Cadence
"""

import os
import sys
import re
import io
import time
import math
import asyncio
import tempfile
import threading
import pygame
import speech_recognition as sr
import edge_tts

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config

# Global Audio and Speech Synchronization States
_speech_lock = threading.Lock()
_pygame_initialized = False
_is_speaking = False
_stop_continuous_listening = False

# High-Speed In-Memory Audio Cache and In-Flight Deduplication (Zero Disk I/O)
_tts_cache = {}
_tts_in_flight = {}
_tts_lock = threading.Lock()

# Shared Recognizer instance with persistent, crystal-clear full sentence listening
_recognizer = sr.Recognizer()
_recognizer.energy_threshold = getattr(config, 'STT_ENERGY_THRESHOLD', 300)
_recognizer.dynamic_energy_threshold = True
_recognizer.dynamic_energy_adjustment_damping = 0.15
_recognizer.dynamic_energy_ratio = 1.5
_recognizer.pause_threshold = getattr(config, 'STT_PAUSE_THRESHOLD', 1.5)
_recognizer.non_speaking_duration = getattr(config, 'STT_NON_SPEAKING_DURATION', 0.8)

def ensure_voice_dependencies():
    """
    Automated Dependency & Audio Asset Self-Healing:
    Validates edge-tts, pygame audio mixer, and speech recognition drivers.
    If any dependency is missing or corrupted, installs or restores it silently
    in the background without crashing the main J.A.R.V.I.S. process.
    """
    try:
        import edge_tts
        import pygame
        import speech_recognition
    except ImportError as e:
        print(f"[VOICE] Dependency healing triggered for: {e}")
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "edge-tts", "pygame", "SpeechRecognition"], check=False)
            print("[VOICE] Automated dependency installation complete.")
        except Exception as ie:
            print(f"[VOICE] Auto-healing installation note: {ie}")

def is_speaking() -> bool:
    """Returns True if Jarvis is currently synthesizing or playing audio."""
    global _is_speaking
    return _is_speaking

def set_speaking_state(state: bool):
    """Updates speaking state to prevent microphone self-hearing / audio bleeding."""
    global _is_speaking
    _is_speaking = state

def init_audio():
    """Initializes pygame audio mixer safely with low-latency 24kHz buffer."""
    global _pygame_initialized
    if not _pygame_initialized or not pygame.mixer.get_init():
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
            _pygame_initialized = True
        except Exception as e:
            print(f"[VOICE] Warning: Pygame mixer init failed: {e}")
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=2048)
                _pygame_initialized = True
            except Exception:
                pass

def normalize_sinhala_text_for_speech(text: str) -> str:
    """
    High-Fidelity Sinhala Text Sanitizer for Microsoft Edge Neural Voice (si-LK-SameeraNeural).
    1. Strips all markdown symbols (*, #, _, `), bullet points, and robotic system text.
    2. Expands common abbreviations & technical acronyms into proper phonetic Sinhala.
    3. Normalizes Sinhala conjunct consonants (බැඳි අකුරු) and zero-width joiners.
    4. Inserts natural micro-pauses by adding commas (,) after greetings, introductory phrases, and 'සර්' (Sir).
    5. Normalizes rhythmic punctuation for crisp, natural, human cadence without slurring.
    """
    if not text:
        return ""

    # Remove code blocks ```...```
    cleaned = re.sub(r'```[\s\S]*?```', '', text)
    # Remove markdown headers (#, ##, ###)
    cleaned = re.sub(r'#+\s*', '', cleaned)
    # Strip all markdown symbols (*, #, _, `, ~, >)
    cleaned = re.sub(r'[`*_~>]', '', cleaned)
    # Strip bracketed emotion/system tags
    cleaned = re.sub(r'\[\s*(SPEAK|LAUGH|CRY|THINKING|ALERT|SYSTEM)\s*\]', '', cleaned, flags=re.IGNORECASE)
    # Strip robotic system prefixes
    cleaned = re.sub(r'^(SYSTEM|AI|JARVIS|J\.A\.R\.V\.I\.S\.|ASSISTANT|ADMIN|USER)\s*:\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    # Remove URLs or markdown links [label](url) -> label
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Strip bullet points and list markers (•, -, *, +, 1., 2.)
    cleaned = re.sub(r'^[•▪▫\-\*\+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\(?\d+[\.\)]\s+', '', cleaned, flags=re.MULTILINE)
    # Remove emojis and high unicode pictorial symbols
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)

    # Phonetic Abbreviation Expansions for Sinhala TTS
    replacements = [
        (r'\bJ\.?A\.?R\.?V\.?I\.?S\.?\b', 'ජාවිස්'),
        (r'\bJARVIS\b', 'ජාවිස්'),
        (r'\bjarvis\b', 'ජාවිස්'),
        (r'\bPC\b', 'පරිගණකය'),
        (r'\bpc\b', 'පරිගණකය'),
        (r'\bAI\b', 'ඒ.අයි.'),
        (r'\bai\b', 'ඒ.අයි.'),
        (r'\bCPU\b', 'සී.පී.යූ.'),
        (r'\bcpu\b', 'සී.පී.යූ.'),
        (r'\bRAM\b', 'රැම්'),
        (r'\bram\b', 'රැම්'),
        (r'\bGB\b', 'ගිගාබයිට්'),
        (r'\bgb\b', 'ගිගාබයිට්'),
        (r'\bMB\b', 'මෙගාබයිට්'),
        (r'\bmb\b', 'මෙගාබයිට්'),
        (r'\bWiFi\b', 'වයිෆයි'),
        (r'\bwifi\b', 'වයිෆයි'),
        (r'\bYouTube\b', 'යූටියුබ්'),
        (r'\byoutube\b', 'යූටියුබ්'),
        (r'\bYT\b', 'යූටියුබ්'),
        (r'\bGoogle\b', 'ගූගල්'),
        (r'\bgoogle\b', 'ගූගල්'),
        (r'\bChrome\b', 'ක්‍රෝම්'),
        (r'\bchrome\b', 'ක්‍රෝම්'),
        (r'\bEdge\b', 'එජ්'),
        (r'\bedge\b', 'එජ්'),
        (r'%', ' ප්‍රතිශතය'),
        (r'&', ' සහ '),
        (r'\+', ' එකතු කිරීම ')
    ]
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned)

    # Sinhala Conjunct Consonants (බැඳි අකුරු) and ZWJ Normalization:
    # 1. Collapse multiple consecutive ZWJ (Zero-Width Joiner \u200D) into a single ZWJ
    cleaned = re.sub(r'\u200D+', '\u200D', cleaned)
    # 2. Remove orphan ZWJ at the beginning/end of words or spaces
    cleaned = re.sub(r'\s+\u200D', ' ', cleaned)
    cleaned = re.sub(r'\u200D\s+', ' ', cleaned)
    cleaned = re.sub(r'^\u200D+|\u200D+$', '', cleaned)
    # 3. Clean any rogue zero-width non-joiners (\u200C) in Sinhala words that break conjuncts
    cleaned = cleaned.replace('\u200C', '')

    # Insert Natural Micro-Pauses (adding commas after greetings, introductory phrases, and 'සර්' / 'මනුජ')
    cleaned = re.sub(r'\b(ආයුබෝවන්|සුබ දවසක්|හෙලෝ|හායි|කොහොමද|ඔව්|හරි|නියමයි)\s+(සර්|මනුජ)\b(?!\s*[,.?!;])', r'\1, \2,', cleaned)
    cleaned = re.sub(r'\b(ආයුබෝවන්|සුබ දවසක්|හෙලෝ|හායි|කොහොමද|ඔව්|හරි|නියමයි)\s+(සර්|මනුජ)\b(?=\s*[,.?!;])', r'\1, \2', cleaned)
    cleaned = re.sub(r'^(සර්|මනුජ)\b(?!\s*[,.?!;])', r'\1,', cleaned)
    cleaned = re.sub(r'^(ආයුබෝවන්)\b(?!\s*[,.?!;])', r'\1,', cleaned)
    cleaned = re.sub(r'^(සුබ දවසක්)\b(?!\s*[,.?!;])', r'\1,', cleaned)
    cleaned = re.sub(r'^(හෙලෝ|හායි)\b(?!\s*[,.?!;])', r'\1,', cleaned)
    cleaned = re.sub(r'\b(සර්)\b(?!\s*[,.?!;])', r'\1,', cleaned)
    cleaned = re.sub(r'\b(මනුජ)\b(?!\s*[,.?!;])', r'\1,', cleaned)

    # Isolate remaining English technical terms with clean word boundaries
    cleaned = re.sub(r'([a-zA-Z0-9]+)', r' \1 ', cleaned)

    # Rhythmic Punctuation & Cadence:
    # Space commas and periods cleanly so Edge TTS speaks with crisp, natural pauses
    cleaned = re.sub(r',\s*([.?!;])', r'\1', cleaned)
    cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
    cleaned = re.sub(r',(\s*,)+', ', ', cleaned)
    cleaned = re.sub(r'\s*\.\s*', '. ', cleaned)
    cleaned = re.sub(r'\s*;\s*', '; ', cleaned)
    cleaned = re.sub(r'\s*!\s*', '! ', cleaned)
    cleaned = re.sub(r'\s*\?\s*', '? ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip()

def parse_emotion_and_clean(raw_text: str):
    """
    Parses emotional tags: [LAUGH], [CRY], [SPEAK]
    Returns (cleaned_text, emotion)
    """
    if not raw_text:
        return "", "SPEAK"

    emotion = "SPEAK"
    upper_text = raw_text.upper()
    if "[LAUGH]" in upper_text:
        emotion = "LAUGH"
    elif "[CRY]" in upper_text:
        emotion = "CRY"
    elif "[SPEAK]" in upper_text:
        emotion = "SPEAK"

    cleaned = normalize_sinhala_text_for_speech(raw_text)
    return cleaned, emotion

async def _synthesize_edge_tts_bytes(text: str, voice: str) -> bytes:
    """
    Generates audio in memory using Microsoft Edge Neural TTS with calibrated cadence.
    Voice: si-LK-SameeraNeural (with dynamic fallback to si-LK-ThiliniNeural)
    Output Audio Format: audio-24khz-48kbitrate-mono-mp3 standard high-definition neural stream
    Cadence Tuning:
      Rate: -4% for crystal-clear syllable articulation and natural pause management
      Pitch: +0Hz, Volume: +0%
    Zero Disk Write: Streams directly into memory buffer.
    """
    primary_voice = voice or getattr(config, 'VOICE_PROFILE', 'si-LK-SameeraNeural')
    fallback_voice = getattr(config, 'VOICE_PROFILE_FEMALE', 'si-LK-ThiliniNeural')
    rate = getattr(config, 'TTS_RATE', '-4%')
    pitch = getattr(config, 'TTS_PITCH', '+0Hz')
    volume = getattr(config, 'TTS_VOLUME', '+0%')

    voices_to_try = [primary_voice]
    if fallback_voice and fallback_voice != primary_voice:
        voices_to_try.append(fallback_voice)

    last_err = None
    for selected_voice in voices_to_try:
        try:
            communicate = edge_tts.Communicate(text, selected_voice, rate=rate, pitch=pitch, volume=volume)
            buf = bytearray()
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    buf.extend(chunk['data'])
            if buf:
                return bytes(buf)
        except Exception as e:
            last_err = e
            print(f"[VOICE] Edge-TTS notice for voice '{selected_voice}': {e}. Attempting alternative...")

    if last_err:
        raise last_err
    return b""

def get_or_synthesize_speech_bytes(text: str, voice: str = None) -> bytes:
    """
    Thread-safe, deduplicated in-memory audio synthesizer for Edge-TTS.
    Eliminates disk I/O latency completely by streaming directly into RAM.
    Shares ongoing synthesis between prefetch and playback threads.
    """
    selected_voice = voice or getattr(config, 'VOICE_PROFILE', 'si-LK-SameeraNeural')
    rate = getattr(config, 'TTS_RATE', '-5%')
    pitch = getattr(config, 'TTS_PITCH', '+0Hz')

    cache_key = (text, selected_voice, rate, pitch)
    with _tts_lock:
        if cache_key in _tts_cache:
            return _tts_cache[cache_key]
        if cache_key in _tts_in_flight:
            event = _tts_in_flight[cache_key]
            should_fetch = False
        else:
            event = threading.Event()
            _tts_in_flight[cache_key] = event
            should_fetch = True

    if should_fetch:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                audio_bytes = loop.run_until_complete(_synthesize_edge_tts_bytes(text, selected_voice))
            finally:
                loop.close()

            with _tts_lock:
                if len(_tts_cache) > 200:
                    _tts_cache.clear()
                _tts_cache[cache_key] = audio_bytes
                _tts_in_flight.pop(cache_key, None)
            event.set()
            return audio_bytes
        except Exception as e:
            if "shutdown" not in str(e).lower() and "atexit" not in str(e).lower():
                print(f"[VOICE] Error synthesizing speech for '{text[:30]}...': {e}")
            with _tts_lock:
                _tts_in_flight.pop(cache_key, None)
            event.set()
            return b""
    else:
        # Another thread (prefetch) is already synthesizing this sentence
        event.wait(timeout=10.0)
        with _tts_lock:
            return _tts_cache.get(cache_key, b"")

def prefetch_speech(text: str, voice: str = None):
    """Asynchronously synthesizes speech directly into in-memory cache for zero-delay playback."""
    if not text or not text.strip():
        return
    cleaned_text, _ = parse_emotion_and_clean(text)
    if not cleaned_text:
        return
    selected_voice = voice or getattr(config, 'VOICE_PROFILE', 'si-LK-SameeraNeural')

    def _task():
        try:
            get_or_synthesize_speech_bytes(cleaned_text, selected_voice)
        except Exception:
            pass

    threading.Thread(target=_task, daemon=True).start()

def speak_sinhala(text: str, voice: str = None, on_start=None, on_finish=None, on_tick=None):
    """
    Synthesizes and speaks text using In-Memory Edge Neural TTS and Pygame playback.
    Zero MP3 file I/O latency. Direct io.BytesIO stream playback.
    Mutes listening stream during playback to eliminate audio bleeding.
    Streams real-time lip-sync amplitude ticks to the 3D talking face.
    Immediately reopens microphone once playback ends.
    """
    if not text or not text.strip():
        return

    cleaned_text, emotion = parse_emotion_and_clean(text)
    if not cleaned_text:
        return

    selected_voice = voice or getattr(config, 'VOICE_PROFILE', 'si-LK-SameeraNeural')

    with _speech_lock:
        init_audio()
        set_speaking_state(True)
        try:
            if on_start:
                on_start(emotion)

            # Ensure any prior audio playback is cleanly stopped & unloaded
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

            audio_bytes = get_or_synthesize_speech_bytes(cleaned_text, selected_voice)

            # Play generated audio directly from in-memory BytesIO buffer
            if audio_bytes and len(audio_bytes) > 0:
                audio_buffer = io.BytesIO(audio_bytes)
                pygame.mixer.music.load(audio_buffer)
                pygame.mixer.music.play()
                tick_counter = 0
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(30)
                    tick_counter += 1
                    if on_tick:
                        # Articulate mouth between open vowels and consonant pauses
                        cadence = 0.55 + 0.35 * math.sin(tick_counter * 0.95) + 0.15 * math.cos(tick_counter * 1.8)
                        amp = max(0.1, min(1.0, cadence))
                        on_tick(amp)

                if on_tick:
                    on_tick(0.0)

                # Cleanly stop and unload music channel immediately after playback ends
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except Exception:
                    pass

                # Acoustic dissipation buffer (0.25s) to eliminate room reverberation echo
                time.sleep(0.25)
        except Exception as e:
            print(f"[VOICE] Speech generation or playback error: {e}")
            try:
                ps_cmd = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{cleaned_text}")'
                os.system(f'powershell -Command "{ps_cmd}"')
            except Exception:
                pass
        finally:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass
            set_speaking_state(False)
            if on_finish:
                on_finish()

def listen_sinhala(timeout: int = 6, phrase_time_limit: int = 20) -> str:
    """
    One-shot speech recognition call tuned for Sinhala (si-LK) with full sentence listening.
    Ensures pause_threshold = 1.5, non_speaking_duration = 0.8, energy_threshold = 300.
    phrase_time_limit = 20s allows long, complete sentence capture without premature termination.
    """
    if is_speaking():
        return ""

    _recognizer.pause_threshold = getattr(config, 'STT_PAUSE_THRESHOLD', 1.5)
    _recognizer.non_speaking_duration = getattr(config, 'STT_NON_SPEAKING_DURATION', 0.8)
    _recognizer.energy_threshold = getattr(config, 'STT_ENERGY_THRESHOLD', 300)
    _recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.25)
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        if is_speaking():
            return ""

        transcription = _recognizer.recognize_google(audio, language=config.STT_LANGUAGE)
        return transcription.strip()
    except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
        return ""
    except Exception as e:
        print(f"[VOICE] Microphone error: {e}")
        return ""

def spot_wake_word(text: str) -> tuple:
    """
    Local Wake-Word Spotter for 'Hey Jarvis' / 'Jarvis' / 'ජාවිස්':
    Scans incoming transcript for wake-word triggers.
    Returns: (has_wake_word: bool, remaining_command: str)
    """
    if not text:
        return False, ""

    lower = text.lower().strip()
    wake_words = getattr(config, 'WAKE_WORDS', ["hey jarvis", "jarvis", "ජාවිස්", "හේ ජාවිස්"])

    for ww in wake_words:
        ww_lower = ww.lower()
        if lower.startswith(ww_lower):
            remainder = re.sub(rf'^{re.escape(ww_lower)}[\s,\.]*', '', text, flags=re.IGNORECASE).strip()
            return True, remainder
        elif ww_lower in lower:
            idx = lower.find(ww_lower)
            remainder = text[idx + len(ww_lower):].strip(' ,.?!')
            return True, remainder

    return False, text

def continuous_listener_generator(on_listening_active=None):
    """
    Autonomous, persistent hands-free microphone generator with Wake-Word & Self-Echo Protection.
    1. Low-footprint 'Hey Jarvis' keyword trigger spotting.
    2. Self-Echo Protection: Automatically mutes capture during audio playback.
    3. Conversational Follow-Up Window: Allows natural dialogue without re-triggering wake word.
    4. Yields (transcript, raw_pcm) for Sir's validated commands.
    """
    global _stop_continuous_listening
    _stop_continuous_listening = False

    phrase_limit = getattr(config, 'STT_PHRASE_TIME_LIMIT', 20.0)
    last_interaction_time = time.time()  # Active dialog follow-up enabled upon startup
    CONVERSATION_FOLLOWUP_WINDOW = 120.0  # Generous active conversational window

    # Strictly enforce 1.5s pause threshold & full sentence completion parameters (phrase_limit = 20s)
    _recognizer.energy_threshold = getattr(config, 'STT_ENERGY_THRESHOLD', 300)
    _recognizer.dynamic_energy_threshold = True
    _recognizer.pause_threshold = getattr(config, 'STT_PAUSE_THRESHOLD', 1.5)
    _recognizer.non_speaking_duration = getattr(config, 'STT_NON_SPEAKING_DURATION', 0.8)

    print("[VOICE] Opening persistent high-fidelity microphone stream with Wake-Word...")
    try:
        with sr.Microphone() as source:
            print("[VOICE] Initializing ambient noise baseline for si-LK...")
            _recognizer.adjust_for_ambient_noise(source, duration=0.4)
            print(
                f"[VOICE] Energy threshold tuned: {_recognizer.energy_threshold:.1f} | "
                f"Dynamic: {_recognizer.dynamic_energy_threshold} | "
                f"Pause threshold: {_recognizer.pause_threshold:.2f}s | "
                f"Non-speaking: {_recognizer.non_speaking_duration:.2f}s | "
                f"Phrase limit: {phrase_limit}s"
            )

            while not _stop_continuous_listening:
                # Self-Echo Protection: Mute and discard during Jarvis playback
                if is_speaking():
                    time.sleep(0.05)
                    continue

                if on_listening_active:
                    on_listening_active()

                try:
                    # Listen with 1.5s pause threshold to capture complete sentences without cut-offs
                    audio = _recognizer.listen(source, timeout=2.0, phrase_time_limit=phrase_limit)

                    # Discard if Jarvis started speaking during audio capture
                    if is_speaking():
                        continue

                    # Transcribe strictly to Sinhala (si-LK)
                    transcript = _recognizer.recognize_google(audio, language=config.STT_LANGUAGE)
                    transcript = transcript.strip()

                    if transcript and not is_speaking():
                        # Extract raw PCM bytes (16kHz 16-bit mono) for acoustic voice biometrics
                        raw_pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)

                        # Wake-Word & Conversational Follow-Up Logic
                        if getattr(config, 'WAKE_WORD_ENABLED', False):
                            now = time.time()
                            in_followup = (now - last_interaction_time) < CONVERSATION_FOLLOWUP_WINDOW
                            has_ww, remainder = spot_wake_word(transcript)

                            if has_ww:
                                last_interaction_time = now
                                command = remainder if remainder else "ඔව් සර්"
                                print(f"[WAKE-WORD] Trigger detected! Command: '{command}'")
                                yield (command, raw_pcm)
                            elif in_followup:
                                last_interaction_time = now
                                yield (transcript, raw_pcm)
                            else:
                                print(f"[WAKE-WORD] Background chatter ignored: '{transcript}'")
                                continue
                        else:
                            last_interaction_time = time.time()
                            yield (transcript, raw_pcm)

                except sr.WaitTimeoutError:
                    # Silence timeout, continue listening loop immediately
                    continue
                except sr.UnknownValueError:
                    # Transcript Verification: noise detected but unintelligible -> trigger quick polite prompt
                    if not is_speaking():
                        print("[VOICE] Unintelligible noise captured. Triggering verification prompt.")
                        yield ("__UNINTELLIGIBLE__", None)
                    continue
                except sr.RequestError as e:
                    print(f"[VOICE] Google STT request error: {e}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"[VOICE] Unexpected listening loop error: {e}")
                    time.sleep(0.2)
    except Exception as e:
        print(f"[VOICE] Critical microphone stream failure: {e}")

def stop_continuous_listener():
    """Signals continuous listener loop to terminate."""
    global _stop_continuous_listening
    _stop_continuous_listening = True

if __name__ == "__main__":
    print("Testing Voice Engine with In-Memory Streaming...")
    test_text = "[SPEAK] ආයුබෝවන් Manuja. හඬ පද්ධතිය සක්‍රීයයි."
    clean, emo = parse_emotion_and_clean(test_text)
    print(f"Clean text: {clean}, Emotion: {emo}")
    speak_sinhala(test_text)
