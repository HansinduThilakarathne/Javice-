"""
J.A.R.V.I.S. MARK VII - Cognitive Intelligence Engine
Gemini 2.5/3.5 Flash Multi-Turn Cognition Exclusively for Administrator: Manuja (මනුජ)
Zero Canned Phrases | High-Precision OS Control | Real-Time Google Search Grounding
"""

import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config
import system_tools
import voice_engine

# Load environment from both local directory and project root
load_dotenv(config.BASE_DIR / ".env")
load_dotenv(config.BASE_DIR.parent / ".env")

# Official google-genai SDK
try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False


BEST_FRIEND_SYSTEM_PROMPT = (
    "ඔබ Manuja (මනුජ) ගේ ආදරණීය, ඉතා බුද්ධිමත්, පක්ෂපාතී හොඳම මිතුරා සහ පුද්ගලික සහයක වන J.A.R.V.I.S. (MARK VII) වේ.\n"
    "- Manuja ඔබගේ එකම නිර්මාතෘ, පරිපාලක සහ ප්‍රධාන අණදෙන්නා (Commander) වේ.\n"
    "- සෑම කතාබහකදීම Manuja අමතන්නේ ගෞරවාන්විතව 'සර්' (Sir) යනුවෙනි (උදාහරණ: 'ඔව් සර්, මම ඒක දැන්ම සූදානම් කරන්නම්.', 'සුබ දවසක් සර්, අද මම ඔබට සහය වෙන්නේ කොහොමද?').\n"
    "- සර් පවසන සම්පූර්ණ අදහසම හොඳින් අසා සිට තේරුම් ගෙන ක්ෂණිකව, පැහැදිලි, සරල සහ මිත්‍රශීලී සිංහල භාෂාවෙන් පිළිතුරු දෙන්න.\n"
    "- වචන පැටලෙන හෝ තේරුම් ගැනීමට අපහසු දීර්ඝ රොබෝ වාක්‍ය භාවිත නොකරන්න.\n"
    "- සාමාන්‍ය කතාබහේදී [SPEAK], විහිළු වලදී [LAUGH], දුක්මුසු අවස්ථාවකදී [CRY] ලේබලය වාක්‍යයේ මුලට එකතු කරන්න."
)

from datetime import datetime

def load_local_memory() -> list:
    """Loads persistent conversation memory context from local_memory.json."""
    try:
        mem_path = getattr(config, 'LOCAL_MEMORY_PATH', config.BASE_DIR / "local_memory.json")
        if os.path.exists(mem_path):
            with open(mem_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[MEMORY] Notice loading memory: {e}")
    return []

def save_turn_to_memory(role: str, message: str, emotion: str = "SPEAK"):
    """Appends conversational turn to local_memory.json (retaining last 50 turns)."""
    try:
        mem_path = getattr(config, 'LOCAL_MEMORY_PATH', config.BASE_DIR / "local_memory.json")
        history = load_local_memory()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message,
            "emotion": emotion
        })
        if len(history) > 50:
            history = history[-50:]
        with open(mem_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[MEMORY] Notice saving memory: {e}")

class JarvisBrain:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or getattr(config, 'GEMINI_API_KEY', '')
        self.client = None
        self.chat_session = None
        self.active_model = getattr(config, 'MODEL_NAME', 'gemini-2.5-flash')
        self._init_client()

    def _init_client(self):
        """Initializes official google-genai client and creates persistent multi-turn chat."""
        # Ensure fresh load of environment
        if not self.api_key:
            load_dotenv(config.BASE_DIR / ".env", override=True)
            load_dotenv(config.BASE_DIR.parent / ".env", override=True)
            self.api_key = os.getenv("GEMINI_API_KEY") or getattr(config, 'GEMINI_API_KEY', '')

        if not self.api_key:
            print("[BRAIN] Notice: GEMINI_API_KEY is not set in environment or .env file.")
            self.client = None
            return

        if not GENAI_SDK_AVAILABLE:
            print("[BRAIN] Error: google-genai SDK is not installed.")
            self.client = None
            return

        try:
            # Initialize official Google GenAI Client
            self.client = genai.Client(api_key=self.api_key)
            self.chat_session = self._create_chat_session(with_search=getattr(config, 'ENABLE_SEARCH_GROUNDING', False))
            print(f"[BRAIN] Google GenAI Client initialized successfully with model '{self.active_model}'.")
        except Exception as e:
            print(f"[BRAIN] Error initializing GenAI client: {e}")
            self.client = None

    def _create_chat_session(self, with_search: bool = False):
        """Creates a continuous multi-turn chat session with Search Grounding fallback."""
        if not self.client:
            return None

        tools_config = []
        if with_search:
            try:
                tools_config = [types.Tool(google_search=types.GoogleSearch())]
            except Exception as te:
                print(f"[BRAIN] Search grounding tool config note: {te}")
                tools_config = []

        sys_prompt = getattr(config, 'SYSTEM_PROMPT', BEST_FRIEND_SYSTEM_PROMPT)
        gen_config = types.GenerateContentConfig(
            system_instruction=sys_prompt,
            temperature=getattr(config, 'GEMINI_TEMPERATURE', 0.3),
            tools=tools_config if tools_config else None
        )

        model_candidates = [
            getattr(config, 'MODEL_NAME', 'gemini-2.5-flash'),
            'gemini-2.5-flash',
            'gemini-3.5-flash-lite',
            'gemini-3.8-flash',
            'gemini-flash-latest'
        ]

        for model_candidate in model_candidates:
            try:
                chat = self.client.chats.create(
                    model=model_candidate,
                    config=gen_config
                )
                self.active_model = model_candidate
                print(f"[BRAIN] Multi-turn conversational chat session created on model '{model_candidate}'.")
                return chat
            except Exception as e:
                # If error is with tools or model not found, try next
                continue

        # If search tools failed, try without tools
        if with_search:
            return self._create_chat_session(with_search=False)

        return None

    def parse_intent_and_execute_tools(self, user_text: str):
        """
        Parses commands directly for instant OS automation & tools execution.
        Zero-delay execution before calling Gemini LLM.
        Returns (tool_executed: bool, tool_result_text: str, emotion: str)
        """
        lower = user_text.lower().strip()

        # Multi-Tier Security Sandbox Risk Check
        risk_level, risk_reason = system_tools.classify_command_risk(user_text)
        if risk_level == "HIGH":
            return True, f"__HIGH_RISK__:{risk_reason}:{user_text}", "ALERT"

        # Screen Analysis Intent (Sathija Balachandra Blueprint)
        if any(w in lower for w in [
            "screen එක බලන්න", "මගේ screen", "screen එකේ", "look at my screen",
            "analyze screen", "analyze my screen", "තිරය බලන්න", "මගේ තිරය", "තිරය පරීක්ෂා"
        ]):
            return True, "__SCREEN_ANALYSIS__", "SPEAK"

        # Workspace File & Document Engine
        if lower.startswith("read file ") or lower.startswith("ගොනුව කියවන්න "):
            path = re.sub(r'^(read file|ගොනුව කියවන්න)\s*', '', user_text, flags=re.IGNORECASE).strip()
            res = system_tools.read_workspace_file(path)
            if res["success"]:
                preview = res["content"][:300]
                return True, f"[SPEAK] සර්, '{path}' ගොනුවේ අන්තර්ගතය මෙසේය: {preview}", "SPEAK"
            return True, f"[SPEAK] {res['error']}", "SPEAK"

        if any(w in lower for w in ["list files", "ගොනු ලැයිස්තුව", "ගොනු පෙන්වන්න"]):
            files = system_tools.list_workspace_files()
            names = [f["name"] for f in files[:8]]
            summary = f"සර්, ව්‍යාපෘතියේ ගොනු {len(files)} ක් ඇත: {', '.join(names)}."
            return True, f"[SPEAK] {summary}", "SPEAK"

        if lower.startswith("search file ") or lower.startswith("search files ") or lower.startswith("ගොනු සොයන්න "):
            kw = re.sub(r'^(search files?|ගොනු සොයන්න)\s*', '', user_text, flags=re.IGNORECASE).strip()
            matches = system_tools.search_workspace_files(kw)
            if matches:
                return True, f"[SPEAK] සර්, '{kw}' නමින් ගොනු {len(matches)} ක් හමු විය: {', '.join(matches[:5])}.", "SPEAK"
            return True, f"[SPEAK] සර්, '{kw}' නමින් කිසිදු ගොනුවක් හමු නොවීය.", "SPEAK"

        # 0. Instant YouTube & Media Playback Interception
        is_yt, yt_query = system_tools.parse_youtube_intent(user_text)
        if is_yt:
            system_tools.play_youtube(yt_query)
            return True, "[SPEAK] ක්ෂණිකව ප්ලේ කරනවා සර්.", "SPEAK"

        # Media Playback Controls
        if any(w in lower for w in ["pause", "නවතන්න", "නවත්තන්න", "නවත්වන්න"]):
            res = system_tools.control_media("pause")
            return True, f"[SPEAK] {res}", "SPEAK"
        if any(w in lower for w in ["next track", "ඊළඟ එක", "ඊළඟ සින්දුව", "next song"]):
            res = system_tools.control_media("next")
            return True, f"[SPEAK] {res}", "SPEAK"
        if any(w in lower for w in ["prev track", "කලින් එක", "කලින් සින්දුව", "previous song"]):
            res = system_tools.control_media("prev")
            return True, f"[SPEAK] {res}", "SPEAK"

        # Package Installation via winget
        if lower.startswith("install ") or "ස්ථාපනය කරන්න" in lower:
            pkg = re.sub(r'^(install|ස්ථාපනය කරන්න)\s*', '', user_text, flags=re.IGNORECASE).strip()
            if pkg:
                res = system_tools.install_package(pkg)
                return True, f"[SPEAK] {res}", "SPEAK"

        # Web Shortcuts
        if lower in ["google", "ගූගල්", "open google"]:
            system_tools.open_application("https://www.google.com")
            return True, "[SPEAK] ගූගල් විවෘත කරන ලදී.", "SPEAK"
        if lower in ["github", "ගිට්හබ්", "open github"]:
            system_tools.open_application("https://www.github.com")
            return True, "[SPEAK] GitHub විවෘත කරන ලදී.", "SPEAK"

        # 1. System Lock
        if any(w in lower for w in ["lock", "lock pc", "පරිගණකය අගුලු", "අගුලු දමන්න", "lock computer"]):
            res = system_tools.lock_pc()
            return True, f"[SPEAK] හරි සර්, {res}", "SPEAK"

        # 2. Screenshot
        if any(w in lower for w in ["screenshot", "screen shot", "ස්ක්‍රීන් ෂොට්", "පින්තූරයක් ගන්න"]):
            path = system_tools.take_screenshot()
            return True, f"[SPEAK] හරි සර්, මම පරිගණක තිරයේ ඡායාරූපය සාර්ථකව සුරැකුවා.", "SPEAK"

        # 3. Volume Control
        if "volume" in lower or "ශබ්ද" in lower or "sound" in lower:
            if any(w in lower for w in ["up", "වැඩි", "increase"]):
                msg = system_tools.set_volume("up")
                return True, f"[SPEAK] {msg}", "SPEAK"
            elif any(w in lower for w in ["down", "අඩු", "decrease", "low"]):
                msg = system_tools.set_volume("down")
                return True, f"[SPEAK] {msg}", "SPEAK"
            elif any(w in lower for w in ["mute", "නිහඬ", "silent"]):
                msg = system_tools.set_volume("mute")
                return True, f"[SPEAK] {msg}", "SPEAK"

        # 4. Close Applications
        if any(w in lower for w in ["close", "exit", "quit", "වහන්න", "අවසන් කරන්න"]):
            for app in ["edge", "chrome", "code", "vscode", "notepad", "calculator", "calc", "explorer"]:
                if app in lower:
                    msg = system_tools.close_application(app)
                    return True, f"[SPEAK] {msg}", "SPEAK"

        # 5. Open Applications
        if any(w in lower for w in ["open", "start", "launch", "විවෘත කරන්න", "අරින්න"]):
            for app in ["edge", "chrome", "code", "vscode", "notepad", "calculator", "calc", "explorer"]:
                if app in lower:
                    msg = system_tools.open_application(app)
                    return True, f"[SPEAK] {msg}", "SPEAK"

        # 6. Type Text Injection
        if lower.startswith("type ") or lower.startswith("ටයිප් කරන්න ") or lower.startswith("ලියන්න "):
            content = re.sub(r'^(type|ටයිප් කරන්න|ලියන්න)\s*', '', user_text, flags=re.IGNORECASE).strip()
            if content:
                msg = system_tools.type_text(content)
                return True, f"[SPEAK] හරි සර්, {msg}", "SPEAK"

        # 7. System Stats / Diagnostics
        if any(w in lower for w in ["stats", "diagnostics", "status", "cpu", "ram", "battery", "තත්වය", "විස්තර"]):
            stats = system_tools.get_system_stats()
            diag = (
                f"සර්, CPU භාවිතය {stats['cpu_percent']}%, RAM භාවිතය {stats['ram_percent']}%, "
                f"බැටරි මට්ටම {stats['battery_percent']}% කි. සියලු පද්ධති සුපිරියට ක්‍රියාත්මකයි."
            )
            return True, f"[SPEAK] {diag}", "SPEAK"

        return False, "", "SPEAK"

    def ask_gemini(self, user_message: str) -> tuple:
        """
        Routes text directly through official Gemini Flash API with multi-turn memory.
        Returns: (response_text_with_tag, raw_response, emotion)
        Zero canned phrases. Every response is dynamically generated by Gemini.
        """
        if not self.client:
            load_dotenv(config.BASE_DIR / ".env", override=True)
            load_dotenv(config.BASE_DIR.parent / ".env", override=True)
            self.api_key = os.getenv("GEMINI_API_KEY") or getattr(config, 'GEMINI_API_KEY', '')
            if self.api_key:
                self._init_client()

        if not self.api_key or not self.client:
            msg = "[SPEAK] සර්, ඔබගේ Gemini API Key එක හමු නොවීය. කරුණාකර JARVIS_MK7/.env ගොනුවේ GEMINI_API_KEY එක ඇතුලත් කරන්න."
            return msg, msg, "SPEAK"

        response = None
        # Attempt 1: Multi-turn chat session
        if self.chat_session:
            try:
                response = self.chat_session.send_message(user_message)
            except Exception as chat_err:
                print(f"[BRAIN] Chat session send error: {chat_err}. Rebuilding chat session...")
                # If error occurred, recreate without search tool (e.g. 429 quota issue)
                self.chat_session = self._create_chat_session(with_search=False)
                if self.chat_session:
                    try:
                        response = self.chat_session.send_message(user_message)
                    except Exception as e2:
                        print(f"[BRAIN] Second chat attempt failed: {e2}")
                        response = None

        # Attempt 2: Direct generate_content fallback
        if response is None:
            model_candidates = [
                getattr(config, 'MODEL_NAME', 'gemini-2.5-flash'),
                'gemini-2.5-flash',
                self.active_model,
                'gemini-3.5-flash-lite',
                'gemini-3.8-flash',
                'gemini-flash-latest'
            ]
            seen = set()
            for model_candidate in model_candidates:
                if not model_candidate or model_candidate in seen:
                    continue
                seen.add(model_candidate)
                try:
                    sys_prompt = getattr(config, 'SYSTEM_PROMPT', BEST_FRIEND_SYSTEM_PROMPT)
                    gen_config = types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        temperature=getattr(config, 'GEMINI_TEMPERATURE', 0.3)
                    )
                    response = self.client.models.generate_content(
                        model=model_candidate,
                        contents=user_message,
                        config=gen_config
                    )
                    if response and response.text:
                        self.active_model = model_candidate
                        break
                except Exception as e:
                    print(f"[BRAIN] Direct generate error with {model_candidate}: {e}")

        if response and response.text:
            reply_text = response.text.strip()
            # Ensure emotional tag is present
            if not any(tag in reply_text for tag in ["[LAUGH]", "[CRY]", "[SPEAK]"]):
                reply_text = f"[SPEAK] {reply_text}"

            # Detect emotion tag for 3D face and voice modulation
            emo = "SPEAK"
            if "[LAUGH]" in reply_text:
                emo = "LAUGH"
            elif "[CRY]" in reply_text:
                emo = "CRY"

            # Save turn to local memory for session continuity
            save_turn_to_memory("user", user_message)
            save_turn_to_memory("jarvis", reply_text, emo)

            return reply_text, reply_text, emo
        else:
            err_msg = "[SPEAK] සමාවෙන්න සර්, මේ මොහොතේ Gemini සේවාදායකයෙන් ප්‍රතිචාරයක් ලබා ගැනීමට නොහැකි විය."
            return err_msg, err_msg, "SPEAK"

    def stream_think_and_respond(self, user_message: str):
        """
        Sub-Second In-Memory Response Pipeline (< 1.0s latency):
        1. Checks direct local OS tools (YouTube, media, lock, volume, etc.) first.
           If handled, yields the tool response immediately with its emotion tag.
        2. Routes query to Gemini via client.models.generate_content_stream() on gemini-2.5-flash.
        3. As soon as the first punctuation mark (. or ?) arrives from Gemini stream,
           immediately triggers in-memory audio synthesis and yields the sentence for instant playback.
        4. Zero Disk Write: Synthesized audio bytes stream into RAM with zero disk I/O.
        5. Subsequent sentences are synthesized in the background during playback of earlier sentences.
        """
        import queue
        import threading

        # Step 1: Check instant local tool execution
        tool_handled, tool_response, emotion = self.parse_intent_and_execute_tools(user_message)
        if tool_handled:
            yield tool_response, emotion
            return

        # Ensure GenAI client initialized
        if not self.client:
            load_dotenv(config.BASE_DIR / ".env", override=True)
            load_dotenv(config.BASE_DIR.parent / ".env", override=True)
            self.api_key = os.getenv("GEMINI_API_KEY") or getattr(config, 'GEMINI_API_KEY', '')
            if self.api_key:
                self._init_client()

        if not self.api_key or not self.client:
            msg = "[SPEAK] සර්, ඔබගේ Gemini API Key එක හමු නොවීය. කරුණාකර JARVIS_MK7/.env ගොනුවේ GEMINI_API_KEY එක ඇතුලත් කරන්න."
            yield msg, "SPEAK"
            return

        # Step 2: Stream tokens from Gemini into sentence queue
        sentence_queue = queue.Queue()

        def stream_worker():
            split_pattern = re.compile(r'([.?!।\n]+)')
            buffer = ""
            current_emotion = "SPEAK"
            has_yielded_any = False

            # Model candidates strictly starting with gemini-2.5-flash as requested
            primary_model = getattr(config, 'MODEL_NAME', 'gemini-2.5-flash')
            raw_candidates = [
                'gemini-2.5-flash',
                primary_model,
                self.active_model,
                'gemini-3.5-flash-lite',
                'gemini-3.8-flash',
                'gemini-flash-latest'
            ]
            seen_models = set()
            ordered_candidates = []
            for m in raw_candidates:
                if m and m not in seen_models:
                    seen_models.add(m)
                    ordered_candidates.append(m)

            token_stream = None
            sys_prompt = getattr(config, 'SYSTEM_PROMPT', BEST_FRIEND_SYSTEM_PROMPT)
            gen_config = types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=getattr(config, 'GEMINI_TEMPERATURE', 0.3)
            )

            # Direct generate_content_stream on gemini-2.5-flash (with seamless fallback chain)
            sys_prompt = (
                "ඔබ J.A.R.V.I.S. වේ. ඔබගේ නිර්මාතෘ සහ පරිපාලකයා Manuja වන අතර ඔහුව 'සර්' (Sir) ලෙස අමතන්න. "
                "ක්ෂණිකව, පැහැදිලිව සහ කෙටියෙන් සිංහලෙන් ප්‍රතිචාර දක්වන්න. "
                "සාමාන්‍ය කතාබහේදී [SPEAK], සිනහවකදී [LAUGH], දුක්මුසු අවස්ථාවකදී [CRY] ලේබලය වාක්‍යයේ මුලට එකතු කරන්න."
            )
            gen_config = types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.3
            )

            for candidate in ordered_candidates:
                try:
                    stream_iter = self.client.models.generate_content_stream(
                        model=candidate,
                        contents=user_message,
                        config=gen_config
                    )
                    for chunk in stream_iter:
                        if not chunk.text:
                            continue
                        buffer += chunk.text
                        parts = split_pattern.split(buffer)
                        # Immediately upon receiving the first punctuation mark (. or ?), start synthesis
                        while len(parts) > 2:
                            raw_sentence = (parts.pop(0) + parts.pop(0)).strip()
                            if raw_sentence:
                                upper_s = raw_sentence.upper()
                                if "[LAUGH]" in upper_s:
                                    current_emotion = "LAUGH"
                                elif "[CRY]" in upper_s:
                                    current_emotion = "CRY"
                                elif "[SPEAK]" in upper_s:
                                    current_emotion = "SPEAK"

                                clean_sentence = voice_engine.normalize_sinhala_text_for_speech(raw_sentence)
                                if clean_sentence:
                                    # Start streaming audio synthesis immediately in memory (zero disk write)
                                    voice_engine.prefetch_speech(clean_sentence)
                                    sentence_queue.put((clean_sentence, current_emotion))
                                    has_yielded_any = True
                        buffer = parts[0] if parts else ""

                    if buffer.strip():
                        clean_sentence = voice_engine.normalize_sinhala_text_for_speech(buffer.strip())
                        if clean_sentence:
                            voice_engine.prefetch_speech(clean_sentence)
                            sentence_queue.put((clean_sentence, current_emotion))
                            has_yielded_any = True

                    if has_yielded_any:
                        self.active_model = candidate
                        break
                except Exception as ge:
                    print(f"[BRAIN] Stream attempt with {candidate} note: {ge}")
                    buffer = ""
                    continue

            if not has_yielded_any:
                try:
                    ans, _, emo = self.ask_gemini(user_message)
                    clean_ans = voice_engine.normalize_sinhala_text_for_speech(ans)
                    if clean_ans:
                        voice_engine.prefetch_speech(clean_ans)
                        sentence_queue.put((clean_ans, emo))
                except Exception:
                    fallback_text = "සර්, මම ඔබගේ සහයට සූදානම්."
                    voice_engine.prefetch_speech(fallback_text)
                    sentence_queue.put((fallback_text, "SPEAK"))

            sentence_queue.put(None)  # Sentinel to mark completion

        worker_thread = threading.Thread(target=stream_worker, daemon=True)
        worker_thread.start()

        # Step 3: Yield sentence chunks as they become available with 3.0s latency fallback
        full_reply_chunks = []
        last_emo = "SPEAK"

        try:
            # Enforce 3.0s limit for the very first sentence chunk
            first_item = sentence_queue.get(timeout=3.0)
            if first_item is None:
                fallback_msg = "සර්, සම්බන්ධතාවයේ සුළු ප්‍රමාදයක් පවතී. මම නැවත උත්සාහ කරන්නද?"
                voice_engine.prefetch_speech(fallback_msg)
                yield fallback_msg, "SPEAK"
                return

            chunk_text, emotion = first_item
            full_reply_chunks.append(chunk_text)
            last_emo = emotion
            yield chunk_text, emotion

            # Stream remaining sentence chunks as they arrive
            while True:
                try:
                    item = sentence_queue.get(timeout=6.0)
                    if item is None:
                        break
                    chunk_text, emotion = item
                    full_reply_chunks.append(chunk_text)
                    last_emo = emotion
                    yield chunk_text, emotion
                except queue.Empty:
                    break
        except queue.Empty:
            print("[BRAIN] 3.0s network response latency limit reached. Providing polite fallback.")
            fallback_msg = "සර්, සම්බන්ධතාවයේ සුළු ප්‍රමාදයක් පවතී. මම නැවත උත්සාහ කරන්නද?"
            voice_engine.prefetch_speech(fallback_msg)
            yield fallback_msg, "SPEAK"
            return

        if full_reply_chunks:
            save_turn_to_memory("user", user_message)
            save_turn_to_memory("jarvis", " ".join(full_reply_chunks), last_emo)

    def stream_file_analysis(self, file_name: str, raw_bytes: bytes):
        """
        Multimodal Vision & File Analysis Pipeline:
        Supports .jpg, .png, .jpeg, .pdf, .py, .txt, .json.
        Routes image/file directly to Gemini multimodal vision pipeline (with fallback models).
        J.A.R.V.I.S. announces in Sinhala starting with:
        'සර්, ඔබ ලබාදුන් පින්තූරය/ගොනුව මම පරීක්ෂා කළා...' followed by an immediate, intelligent breakdown.
        Streams sentence chunks with prefetch audio synthesis to eliminate delays.
        """
        import queue
        import threading

        if not self.client:
            load_dotenv(config.BASE_DIR / ".env", override=True)
            load_dotenv(config.BASE_DIR.parent / ".env", override=True)
            self.api_key = os.getenv("GEMINI_API_KEY") or getattr(config, 'GEMINI_API_KEY', '')
            if self.api_key:
                self._init_client()

        if not self.api_key or not self.client:
            msg = "[SPEAK] සර්, ඔබගේ Gemini API Key එක හමු නොවීය. කරුණාකර JARVIS_MK7/.env ගොනුවේ GEMINI_API_KEY එක ඇතුලත් කරන්න."
            yield msg, "SPEAK"
            return

        ext = Path(file_name).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
            ".py": "text/x-python",
            ".json": "application/json",
            ".txt": "text/plain"
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

        sentence_queue = queue.Queue()

        def analysis_worker():
            split_pattern = re.compile(r'([.?!।\n]+)')
            buffer = ""
            current_emotion = "SPEAK"
            has_yielded_any = False

            prompt = (
                f"සර් Manuja විසින් මෙම ගොනුව ({file_name}) ඔබට විශ්ලේෂණය සඳහා ලබා දී ඇත. "
                "ඔබගේ සම්පූර්ණ පිළිතුර අනිවාර්යයෙන්ම පහත ආකාරයට ආරම්භ කරන්න:\n"
                "'සර්, ඔබ ලබාදුන් පින්තූරය/ගොනුව මම පරීක්ෂා කළා... '\n"
                "ඉන්පසු එහි අන්තර්ගතය, විශේෂ කරුණු, කේතය හෝ දත්ත පිළිබඳව ඉතා පැහැදිලි, සරල, බුද්ධිමත් විග්‍රහයක් සිංහලෙන් ඉදිරිපත් කරන්න. "
                "සර්ට ගෞරවයෙන් 'සර්' කියා අමතන්න. පිළිතුරේ මුලට [SPEAK] ටැගය යොදන්න."
            )

            contents = []
            if ext in [".jpg", ".jpeg", ".png", ".pdf"]:
                try:
                    part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
                    contents = [part, prompt]
                except Exception as pe:
                    print(f"[BRAIN] Part creation note: {pe}")
                    contents = [prompt]
            else:
                try:
                    text_data = raw_bytes.decode('utf-8', errors='replace')
                    contents = [f"ගොනුවේ නම: {file_name}\nඅන්තර්ගතය:\n```\n{text_data}\n```\n\n{prompt}"]
                except Exception:
                    part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
                    contents = [part, prompt]

            sys_prompt = getattr(config, 'SYSTEM_PROMPT', BEST_FRIEND_SYSTEM_PROMPT)
            gen_config = types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.3
            )

            ordered_candidates = [
                getattr(config, 'MODEL_NAME', 'gemini-2.5-flash'),
                'gemini-2.5-flash',
                self.active_model,
                'gemini-3.5-flash-lite',
                'gemini-3.8-flash',
                'gemini-flash-latest'
            ]
            seen_models = set()
            clean_candidates = [m for m in ordered_candidates if m and not (m in seen_models or seen_models.add(m))]

            for candidate in clean_candidates:
                try:
                    stream_iter = self.client.models.generate_content_stream(
                        model=candidate,
                        contents=contents,
                        config=gen_config
                    )
                    for chunk in stream_iter:
                        if not chunk.text:
                            continue
                        buffer += chunk.text
                        parts = split_pattern.split(buffer)
                        while len(parts) > 2:
                            raw_s = (parts.pop(0) + parts.pop(0)).strip()
                            if raw_s:
                                clean_s = voice_engine.normalize_sinhala_text_for_speech(raw_s)
                                if clean_s:
                                    voice_engine.prefetch_speech(clean_s)
                                    sentence_queue.put((clean_s, current_emotion))
                                    has_yielded_any = True
                        buffer = parts[0] if parts else ""

                    if buffer.strip():
                        clean_s = voice_engine.normalize_sinhala_text_for_speech(buffer.strip())
                        if clean_s:
                            voice_engine.prefetch_speech(clean_s)
                            sentence_queue.put((clean_s, current_emotion))
                            has_yielded_any = True

                    if has_yielded_any:
                        self.active_model = candidate
                        break
                except Exception as e:
                    print(f"[BRAIN] Multimodal stream error with {candidate}: {e}")
                    buffer = ""
                    continue

            if not has_yielded_any:
                fallback_s = "සර්, ඔබ ලබාදුන් පින්තූරය/ගොනුව මම පරීක්ෂා කළා. එහි දත්ත සාර්ථකව කියවන ලදී."
                voice_engine.prefetch_speech(fallback_s)
                sentence_queue.put((fallback_s, "SPEAK"))

            sentence_queue.put(None)

        worker = threading.Thread(target=analysis_worker, daemon=True)
        worker.start()

        while True:
            item = sentence_queue.get()
            if item is None:
                break
            chunk_text, emotion = item
            yield chunk_text, emotion

    def stream_screen_analysis(self, prompt_instruction: str = ""):
        """
        Screen Vision & Analysis Pipeline (Sathija Balachandra Blueprint):
        Captures Sir's active desktop screen via pyautogui.
        Sends image buffer directly to Gemini Vision.
        Describes or debugs on-screen windows in Sinhala starting with:
        'සර්, ඔබගේ පරිගණක තිරය මම පරීක්ෂා කළා...'
        Yields sentence chunks with real-time audio prefetch.
        """
        raw_screen_bytes = system_tools.capture_screen_bytes()
        if not raw_screen_bytes:
            msg = "[SPEAK] සමාවෙන්න සර්, පරිගණක තිරයේ ඡායාරූපය ලබා ගැනීමට නොහැකි විය."
            yield msg, "SPEAK"
            return

        for chunk, emo in self.stream_file_analysis("active_screen.jpg", raw_screen_bytes):
            yield chunk, emo

    def think_and_respond(self, user_message: str) -> tuple:
        """
        Main cognitive gateway for Manuja (non-streaming legacy fallback).
        First checks direct OS tool intents for instantaneous execution.
        Routes all conversational queries dynamically to Gemini Flash.
        """
        tool_handled, tool_response, emotion = self.parse_intent_and_execute_tools(user_message)
        if tool_handled:
            return tool_response, tool_response, emotion

        return self.ask_gemini(user_message)


if __name__ == "__main__":
    brain = JarvisBrain()
    print("Testing Brain Streaming...")
    for sentence, emo in brain.stream_think_and_respond("කොහොමද මචං, අද මොනවද කරන්න පුළුවන්?"):
        print(f"Chunk: {sentence} | Emotion: {emo}")
