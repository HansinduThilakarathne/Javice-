"""
J.A.R.V.I.S. MARK VII - Central Configuration File
Exclusively built for Administrator: Manuja (මනුජ)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load local environment variables if .env exists
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

# Biometric & Administrator Settings (Strictly Manuja)
PRIMARY_USER = "Manuja"
PRIMARY_USER_SINHALA = "මනුජ"

# Reference photo: gold-standard manuja.jpg in project root or local folder
_manuja_root = BASE_DIR.parent / "manuja.jpg"
_manuja_img = BASE_DIR / "manuja.jpg"
_manu_legacy_img = BASE_DIR / "manu.jpg"

if _manuja_root.exists() and _manuja_root.stat().st_size > 1000:
    REFERENCE_IMAGE_PATH = str(_manuja_root)
elif _manuja_img.exists() and _manuja_img.stat().st_size > 1000:
    REFERENCE_IMAGE_PATH = str(_manuja_img)
elif _manu_legacy_img.exists():
    REFERENCE_IMAGE_PATH = str(_manu_legacy_img)
else:
    REFERENCE_IMAGE_PATH = str(_manuja_img)

# Upgraded Biometric Model & Tolerant Backend
FACE_DETECTION_BACKEND = "retinaface"   # retinaface, mtcnn, opencv (robust against partial blur)
FACE_RECOGNITION_MODEL = "ArcFace"      # ArcFace or Facenet512 (state-of-the-art angular margin)
VERIFICATION_DISTANCE_METRIC = "cosine"
BIOMETRIC_COSINE_THRESHOLD = 0.72       # Balanced cosine distance threshold (prevents false rejections on focus shift)
BIOMETRIC_STRICT_MODE = True

# Security Audio Warnings (Strictly Refuse Anyone Except Manuja)
UNAUTHORIZED_WARNING_SINHALA = (
    "සමාවෙන්න, මම මනුජගේ විධාන පමණක් භාරගනිමි."
)

# Cognitive Brain Settings (Gemini Flash)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.5-flash"
ENABLE_SEARCH_GROUNDING = False
GEMINI_TEMPERATURE = 0.3    # Optimizes token latency and ensures factual precision

# Speech & Voice Settings - Natural High-Fidelity Sinhala Phonetics
# Edge TTS Neural Voices: si-LK-SameeraNeural (Male), si-LK-ThiliniNeural (Female)
VOICE_PROFILE = "si-LK-SameeraNeural"
VOICE_PROFILE_FEMALE = "si-LK-ThiliniNeural"
TTS_RATE = "-4%"        # -4% for crystal-clear syllable articulation and natural pause management
TTS_PITCH = "+0Hz"      # Warm, human-like tone
TTS_VOLUME = "+0%"

STT_LANGUAGE = "si-LK"
STT_ENERGY_THRESHOLD = 300
STT_PAUSE_THRESHOLD = 1.5           # Prevents cutting off Sir while thinking or taking a natural breathing pause mid-sentence
STT_NON_SPEAKING_DURATION = 0.8    # Ensures speech is captured in its entirety before processing
STT_PHRASE_TIME_LIMIT = 20.0        # 20s phrase limit allowing longer, complete sentence capture without cut-offs

# Wake-Word & Self-Echo Protection Settings
# Set WAKE_WORD_ENABLED = False for continuous hands-free response to all of Sir's speech
WAKE_WORD_ENABLED = False
WAKE_WORDS = [
    "hey jarvis", "jarvis", "ජාවිස්", "හේ ජාවිස්", "jarvis mk7", "ජාවිස් mk7",
    "සර්", "sir", "හලෝ", "hello", "මනුජ", "manuja"
]
WAKE_WORD_SENSITIVITY = 0.6

# Session Continuity & Multi-Tier Audit Logging
LOCAL_MEMORY_PATH = BASE_DIR / "local_memory.json"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_PATH = LOGS_DIR / "audit_log.jsonl"

# Best Friend Persona & Sir Protocol System Prompt
SYSTEM_PROMPT = (
    "ඔබ Manuja (මනුජ) ගේ ආදරණීය, ඉතා බුද්ධිමත්, පක්ෂපාතී හොඳම මිතුරා සහ පුද්ගලික සහයක වන J.A.R.V.I.S. (MARK VII) වේ.\n"
    "- Manuja ඔබගේ එකම නිර්මාතෘ, පරිපාලක සහ ප්‍රධාන අණදෙන්නා (Commander) වේ.\n"
    "- සෑම කතාබහකදීම Manuja අමතන්නේ ගෞරවාන්විතව 'සර්' (Sir) යනුවෙනි (උදාහරණ: 'ඔව් සර්, මම ඒක දැන්ම සූදානම් කරන්නම්.', 'සුබ දවසක් සර්, අද මම ඔබට සහය වෙන්නේ කොහොමද?').\n"
    "- සර් පවසන සම්පූර්ණ අදහසම හොඳින් අසා සිට තේරුම් ගෙන ක්ෂණිකව, පැහැදිලි, සරල සහ මිත්‍රශීලී සිංහල භාෂාවෙන් පිළිතුරු දෙන්න.\n"
    "- වචන පැටලෙන හෝ තේරුම් ගැනීමට අපහසු දීර්ඝ රොබෝ වාක්‍ය භාවිත නොකරන්න.\n"
    "- සාමාන්‍ය කතාබහේදී [SPEAK], විහිළු වලදී [LAUGH], දුක්මුසු අවස්ථාවකදී [CRY] ලේබලය වාක්‍යයේ මුලට එකතු කරන්න."
)

# Native HUD & Desktop Widget Settings
UI_DIR = BASE_DIR / "ui"
UI_INDEX_PATH = str(UI_DIR / "index.html")
HUD_WINDOW_TITLE = "J.A.R.V.I.S. - MARK VII [PRIMARY USER: MANUJA]"

# Docked Floating Desktop Corner Widget Configuration
WIDGET_MODE = True
WIDGET_WIDTH = 400
WIDGET_HEIGHT = 580
WIDGET_OFFSET_X = 25
WIDGET_OFFSET_Y = 65

# Fullscreen / Standard Dimensions
HUD_WINDOW_WIDTH = 1280
HUD_WINDOW_HEIGHT = 800
TELEMETRY_INTERVAL_SECONDS = 2.0
