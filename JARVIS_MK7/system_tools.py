"""
J.A.R.V.I.S. MARK VII - Windows System Automation & Tools
Full Windows OS Control, Hardware Telemetry, Application Launcher & Project Builder
"""

import os
import sys
import ctypes
from ctypes import wintypes
import psutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from PIL import Image
import pyautogui

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config

# Create screenshots & projects directory
SCREENSHOTS_DIR = config.BASE_DIR / "screenshots"
PROJECTS_DIR = config.BASE_DIR / "autonomous_projects"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

import json
import io

def log_audit_event(command: str, risk_level: str = "LOW", status: str = "EXECUTED", details: str = ""):
    """
    Appends system automation event to audit log (logs/audit_log.jsonl).
    Tracks all low and high-risk system commands for administrative review.
    """
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": getattr(config, 'PRIMARY_USER', 'Manuja'),
            "command": command,
            "risk_level": risk_level,
            "status": status,
            "details": details
        }
        with open(config.AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[AUDIT] Failed to write audit log: {e}")

def classify_command_risk(command_text: str) -> tuple:
    """
    Multi-Tier Security Sandbox:
    Classifies system commands into 'LOW' or 'HIGH' risk.
    High-risk actions require explicit voice confirmation:
    'සර්, මෙම ක්‍රියාව අනතුරුදායක විය හැක. ඉදිරියට යන්නද?'
    Returns (risk_level: str, reason_sinhala: str)
    """
    lower = command_text.lower().strip()

    # 1. File or Directory Deletion
    if any(k in lower for k in ["delete file", "remove file", "del ", "rm ", "erase", "ගොනුව මකන්න", "මකා දමන්න", "මකන්න"]):
        return "HIGH", "ගොනු මකා දැමීම (File Deletion)"

    # 2. Drive Formatting / Disk Partitioning
    if any(k in lower for k in ["format ", "diskpart", "fdisk", "පාටිෂන්", "ෆෝමැට්"]):
        return "HIGH", "ධාවකය හැඩතල ගැන්වීම (Drive Formatting)"

    # 3. Recursive directory purging or force kill system components
    if any(k in lower for k in ["rmdir /s", "rd /s", "taskkill /f /im svchost", "taskkill /f /im explorer"]):
        return "HIGH", "පද්ධතිමය ගොනු හෝ ක්‍රියාවලි අවසන් කිරීම (System Critical Termination)"

    # 4. Windows Registry Modifying Commands
    if "reg " in lower and any(k in lower for k in ["add", "delete", "import"]):
        return "HIGH", "Windows රෙජිස්ට්‍රිය වෙනස් කිරීම (Registry Modification)"

    return "LOW", ""

# ---------------- WORKSPACE FILE & DOCUMENT ENGINE ---------------- #

def read_workspace_file(rel_path: str) -> dict:
    """
    Reads a file inside the workspace safely.
    Returns: {"success": bool, "content": str, "error": str}
    """
    try:
        target = (config.BASE_DIR / rel_path).resolve()
        if not str(target).startswith(str(config.BASE_DIR.parent)):
            log_audit_event(f"read_file: {rel_path}", "HIGH", "BLOCKED", "Path traversal outside workspace")
            return {"success": False, "content": "", "error": "සර්, මෙම ගොනුව ව්‍යාපෘති සීමාවෙන් පිටත පිහිටා ඇත."}

        if not target.exists():
            return {"success": False, "content": "", "error": f"සර්, '{rel_path}' ගොනුව හමු නොවීය."}

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        log_audit_event(f"read_file: {rel_path}", "LOW", "EXECUTED", f"Read {len(content)} chars")
        return {"success": True, "content": content, "error": ""}
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}

def write_workspace_file(rel_path: str, content: str) -> dict:
    """
    Writes or creates a file inside the workspace safely.
    """
    try:
        target = (config.BASE_DIR / rel_path).resolve()
        if not str(target).startswith(str(config.BASE_DIR.parent)):
            log_audit_event(f"write_file: {rel_path}", "HIGH", "BLOCKED", "Path traversal outside workspace")
            return {"success": False, "message": "සර්, ව්‍යාපෘති සීමාවෙන් පිටත ගොනු ලිවීම අවහිර කර ඇත."}

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

        log_audit_event(f"write_file: {rel_path}", "LOW", "EXECUTED", f"Wrote {len(content)} chars")
        return {"success": True, "message": f"සර්, '{rel_path}' ගොනුව සාර්ථකව සුරකින ලදී."}
    except Exception as e:
        return {"success": False, "message": f"ගොනුව සුරැකීමේ දෝෂයකි: {e}"}

def list_workspace_files(subdir: str = "") -> list:
    """
    Lists files and directories in workspace.
    """
    try:
        target_dir = (config.BASE_DIR / subdir).resolve()
        if not target_dir.exists():
            return []
        items = []
        for p in target_dir.iterdir():
            if p.name.startswith(".") or p.name in ["__pycache__", "venv"]:
                continue
            items.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size_kb": round(p.stat().st_size / 1024, 1) if p.is_file() else 0
            })
        return items
    except Exception:
        return []

def search_workspace_files(keyword: str) -> list:
    """
    Searches workspace files containing keyword.
    """
    results = []
    kw_lower = keyword.lower()
    try:
        for root, dirs, files in os.walk(config.BASE_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "venv"]]
            for file in files:
                if kw_lower in file.lower():
                    rel = os.path.relpath(os.path.join(root, file), config.BASE_DIR)
                    results.append(rel)
    except Exception:
        pass
    return results

def get_system_stats():
    """
    Returns real-time hardware diagnostics:
    - CPU Usage % and frequency
    - RAM Usage %, used GB, total GB
    - Battery percentage, plugged state
    - Disk usage %
    - Network I/O
    """
    try:
        cpu_pct = psutil.cpu_percent(interval=0.05)
    except Exception:
        cpu_pct = 0.0

    try:
        ram = psutil.virtual_memory()
        ram_pct = ram.percent
        ram_used_gb = round(ram.used / (1024**3), 2)
        ram_total_gb = round(ram.total / (1024**3), 2)
    except Exception:
        ram_pct, ram_used_gb, ram_total_gb = 0.0, 0.0, 0.0

    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_pct = battery.percent
            power_plugged = battery.power_plugged
        else:
            battery_pct = 100
            power_plugged = True
    except Exception:
        battery_pct = 100
        power_plugged = True

    try:
        disk = psutil.disk_usage('C:\\')
        disk_pct = disk.percent
    except Exception:
        disk_pct = 0.0

    try:
        net = psutil.net_io_counters()
        net_sent_mb = round(net.bytes_sent / (1024**2), 1)
        net_recv_mb = round(net.bytes_recv / (1024**2), 1)
    except Exception:
        net_sent_mb, net_recv_mb = 0.0, 0.0

    return {
        "cpu_percent": cpu_pct,
        "ram_percent": ram_pct,
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "battery_percent": battery_pct,
        "power_plugged": power_plugged,
        "disk_percent": disk_pct,
        "net_sent_mb": net_sent_mb,
        "net_recv_mb": net_recv_mb,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

def set_volume(level):
    """
    Adjusts system master volume:
    - 'up' -> increases volume
    - 'down' -> decreases volume
    - 'mute' -> toggles mute
    - integer 0-100 -> sets approximate volume level
    """
    try:
        if isinstance(level, str):
            lower = level.strip().lower()
            if "up" in lower:
                for _ in range(5):
                    pyautogui.press('volumeup')
                return "ශබ්දය වැඩි කරන ලදී (Volume increased)."
            elif "down" in lower:
                for _ in range(5):
                    pyautogui.press('volumedown')
                return "ශබ්දය අඩු කරන ලදී (Volume decreased)."
            elif "mute" in lower:
                pyautogui.press('volumemute')
                return "ශබ්දය නිහඬ කරන ලදී (Mute toggled)."
            else:
                level_val = int(''.join(filter(str.isdigit, level)) or 50)
        else:
            level_val = int(level)

        # Set specific volume steps
        steps = int(max(0, min(100, level_val)) / 2)
        for _ in range(50):
            pyautogui.press('volumedown')
        for _ in range(steps):
            pyautogui.press('volumeup')
        return f"ශබ්දය {level_val}% මට්ටමට සකසන ලදී."
    except Exception as e:
        return f"ශබ්දය වෙනස් කිරීම අසාර්ථකයි: {e}"

def set_brightness(level: int):
    """Adjusts display brightness (0-100%) via Windows WMI."""
    try:
        level = max(0, min(100, int(level)))
        cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=False)
        return f"තිරයේ දීප්තිය {level}% මට්ටමට සකස් කරන ලදී."
    except Exception as e:
        return f"දීප්තිය සකස් කිරීමේ දෝෂයකි: {e}"

def _native_gdi_screenshot():
    """Captures desktop using native Windows GDI BitBlt API."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)

    hdc_screen = user32.GetDC(None)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)

    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(None, hdc_screen)

    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    return im.convert('RGB')

def take_screenshot(filename: str = None) -> str:
    """Takes a full screen screenshot and saves it with multi-tier fallback."""
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jarvis_screenshot_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename

        # Primary: Native GDI BitBlt
        try:
            img = _native_gdi_screenshot()
            img.save(filepath)
            return str(filepath)
        except Exception:
            pass

        # Secondary: PyAutoGUI / PIL
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return str(filepath)
        except Exception:
            pass

        # Fallback: Blank diagnostic canvas
        blank = Image.new("RGB", (1280, 720), color=(4, 9, 13))
        blank.save(filepath)
        return str(filepath)
    except Exception as e:
        print(f"[SYSTEM] Screenshot error: {e}")
        return ""

def capture_screen_bytes() -> bytes:
    """
    Captures an instant screenshot of Sir's active desktop and returns in-memory JPEG bytes.
    Zero disk write latency. Direct RAM buffer for Gemini Vision.
    Multi-tier capture: Native GDI -> PyAutoGUI -> Diagnostic Canvas.
    """
    img = None
    # Tier 1: Native GDI BitBlt
    try:
        img = _native_gdi_screenshot()
    except Exception:
        img = None

    # Tier 2: PyAutoGUI / PIL
    if img is None:
        try:
            img = pyautogui.screenshot()
        except Exception:
            img = None

    # Tier 3: Diagnostic Canvas
    if img is None:
        img = Image.new("RGB", (1280, 720), color=(10, 15, 30))

    try:
        if img.mode != "RGB":
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
    except Exception as e:
        print(f"[SYSTEM] Screenshot capture for vision error: {e}")
        return b""

def lock_pc():
    """Locks the Windows workstation instantly."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "පරිගණකය අගුලු දමන ලදී (Workstation Locked)."
    except Exception:
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
            return "පරිගණකය අගුලු දමන ලදී."
        except Exception as e:
            return f"අගුලු දැමීමේ දෝෂයකි: {e}"

def open_application(app_name: str) -> str:
    """
    Launches standard Windows applications:
    Edge, Chrome, VS Code, Notepad, Calculator, File Explorer, etc.
    """
    app_lower = app_name.strip().lower()
    try:
        if "edge" in app_lower:
            subprocess.Popen(["cmd", "/c", "start", "msedge"], shell=True)
            return "Microsoft Edge විවෘත කරන ලදී."
        elif "chrome" in app_lower:
            subprocess.Popen(["cmd", "/c", "start", "chrome"], shell=True)
            return "Google Chrome විවෘත කරන ලදී."
        elif "code" in app_lower or "vs" in app_lower:
            subprocess.Popen(["cmd", "/c", "code"], shell=True)
            return "Visual Studio Code විවෘත කරන ලදී."
        elif "notepad" in app_lower or "සටහන්" in app_lower:
            subprocess.Popen(["notepad.exe"])
            return "Notepad විවෘත කරන ලදී."
        elif "calc" in app_lower or "ගණක" in app_lower:
            subprocess.Popen(["calc.exe"])
            return "Calculator විවෘත කරන ලදී."
        elif "explorer" in app_lower or "file" in app_lower or "ගොනු" in app_lower:
            subprocess.Popen(["explorer.exe"])
            return "File Explorer විවෘත කරන ලදී."
        elif "terminal" in app_lower or "cmd" in app_lower:
            subprocess.Popen(["cmd.exe", "/c", "start", "powershell"], shell=True)
            return "PowerShell Terminal විවෘත කරන ලදී."
        elif app_name.startswith("http://") or app_name.startswith("https://"):
            webbrowser.open(app_name)
            return f"{app_name} වෙබ් අඩවිය විවෘත කරන ලදී."
        else:
            subprocess.Popen(["cmd", "/c", "start", app_name], shell=True)
            return f"{app_name} යෙදුම විවෘත කිරීමට උත්සාහ කරන ලදී."
    except Exception as e:
        return f"{app_name} විවෘත කිරීම අසාර්ථකයි: {e}"

def parse_youtube_intent(user_text: str) -> tuple:
    """
    Parses natural language requests to play songs/videos on YouTube:
    Example inputs from Manuja:
    - "ජාවිස් යූටියුබ් එකට ගිහිල්ලා ඉරාජ්ගේ කතන්දරේ සින්දුව ප්ලේ කරන්න"
    - "youtube එකේ Iraj කතන්දරේ song play කරන්න"
    - "යූටියුබ් එකේ සින්දුවක් දාන්න"
    Returns: (is_match: bool, search_query: str)
    """
    if not user_text:
        return False, ""

    text = user_text.strip()
    lower = text.lower()

    # Check for youtube or song intent triggers
    has_youtube = any(w in lower for w in ["youtube", "යූටියුබ්", "yt"])
    has_play_action = any(w in lower for w in ["play", "ප්ලේ", "දාන්න", "අහන්න", "ගහන්න", "වාදනය", "සින්දු", "සින්දුව"])

    if not (has_youtube and has_play_action):
        # Also check for direct "play ... song" command even if youtube isn't explicitly mentioned
        if ("play " in lower or "ප්ලේ කරන්න" in lower or "සින්දුව දාන්න" in lower) and any(w in lower for w in ["song", "සින්දුව", "සින්දු", "music", "ගීතය"]):
            pass
        else:
            return False, ""

    # Clean query by removing boilerplate speech tokens
    import re
    query = text
    # Remove jarvis invocation
    query = re.sub(r'^(ජාවිස්|jarvis)[,\s]*', '', query, flags=re.IGNORECASE)
    # Remove youtube references
    query = re.sub(r'(යූටියුබ්\s*එකට\s*ගිහිල්ලා|යූටියුබ්\s*එකට\s*ගිහින්|යූටියුබ්\s*එකෙන්|යූටියුබ්\s*එකේ|යූටියුබ්|youtube|yt)\s*', '', query, flags=re.IGNORECASE)
    # Remove action verbs
    query = re.sub(r'(ප්ලේ\s*කරන්න|play\s*කරන්න|play|දාන්න|අහන්න|ගහන්න|වාදනය\s*කරන්න|කරන්න)\s*$', '', query, flags=re.IGNORECASE)
    query = re.sub(r'^(ප්ලේ\s*කරන්න|play\s*කරන්න|play|දාන්න|අහන්න|ගහන්න|වාදනය\s*කරන්න)\s*', '', query, flags=re.IGNORECASE)
    # Remove "song", "සින්දුව", "music"
    query = re.sub(r'(සින්දුවක්|සින්දුව|ගීතය|song|music|video)\s*', '', query, flags=re.IGNORECASE)
    # Clean whitespace and punctuation
    query = query.strip(' ,.?!')

    if not query:
        query = "trending sinhala songs"

    return True, query

def play_youtube(query: str) -> str:
    """
    Direct ultra-fast YouTube playback for Manuja.
    1. Attempts direct playback via pywhatkit.playonyt.
    2. Fallback: Directly launches default browser with targeted YouTube query and triggers Enter.
    """
    query = query.strip()
    if not query:
        query = "trending sinhala songs"

    print(f"[SYSTEM] Instant YouTube playback triggered for query: '{query}'")

    def _execute_play():
        try:
            import pywhatkit
            pywhatkit.playonyt(query)
            return
        except Exception as e:
            print(f"[SYSTEM] pywhatkit playback notice: {e}, using browser fallback...")

        try:
            import urllib.parse
            encoded = urllib.parse.quote(query)
            target_url = f"https://www.youtube.com/results?search_query={encoded}"
            webbrowser.open(target_url)
            time.sleep(2.0)
            try:
                pyautogui.press('enter')
            except Exception:
                pass
        except Exception as e2:
            print(f"[SYSTEM] Direct browser launch error: {e2}")

    # Launch non-blocking so speech response happens instantaneously
    import threading
    threading.Thread(target=_execute_play, daemon=True).start()
    return "ක්ෂණිකව ප්ලේ කරනවා සර්."

def install_package(package_name: str) -> str:
    """
    Autonomous package self-installation using Windows winget.
    Command: winget install <tool_name> --accept-source-agreements --silent
    """
    pkg = package_name.strip()
    if not pkg:
        return "සර්, ස්ථාපනය කිරීමට පැකේජයේ නම සඳහන් කරන්න."

    try:
        cmd = f'winget install {pkg} --accept-source-agreements --silent'
        ret, stdout, stderr = execute_shell_command(cmd)
        if ret == 0:
            return f"සර්, '{pkg}' සාර්ථකව පරිගණකයේ ස්ථාපනය කරන ලදී."
        else:
            # Fallback to search install with agreements
            cmd_fallback = f'winget install --id "{pkg}" --accept-source-agreements --silent'
            ret2, out2, err2 = execute_shell_command(cmd_fallback)
            if ret2 == 0:
                return f"සර්, '{pkg}' සාර්ථකව ස්ථාපනය කරන ලදී."
            return f"සර්, '{pkg}' ස්ථාපනය කිරීමේදී දෝෂයක් මතු විය: {stderr or err2}"
    except Exception as e:
        return f"පැකේජ ස්ථාපන දෝෂයකි: {e}"

def control_media(action: str) -> str:
    """Controls background media playback (play, pause, next, previous)."""
    act = action.lower().strip()
    try:
        if any(w in act for w in ["play", "pause", "නවත්තන්න", "නවත්වන්න", "නවතන්න"]):
            pyautogui.press('playpause')
            return "මාධ්‍ය ධාවනය පාලනය කරන ලදී."
        elif any(w in act for w in ["next", "ඊළඟ"]):
            pyautogui.press('nexttrack')
            return "ඊළඟ ගීතය වෙත මාරු කරන ලදී."
        elif any(w in act for w in ["prev", "previous", "කලින්"]):
            pyautogui.press('prevtrack')
            return "පෙර ගීතය වෙත මාරු කරන ලදී."
        return "මාධ්‍ය විධානයක් ලබා නොදුනි."
    except Exception as e:
        return f"මාධ්‍ය පාලන දෝෂයකි: {e}"


def close_application(app_name: str) -> str:
    """
    Terminates running applications cleanly for Manuja.
    """
    app_lower = app_name.strip().lower()
    try:
        proc_names = []
        if "edge" in app_lower:
            proc_names = ["msedge.exe"]
            display = "Microsoft Edge"
        elif "chrome" in app_lower:
            proc_names = ["chrome.exe"]
            display = "Google Chrome"
        elif "code" in app_lower or "vs" in app_lower:
            proc_names = ["Code.exe"]
            display = "Visual Studio Code"
        elif "notepad" in app_lower or "සටහන්" in app_lower:
            proc_names = ["notepad.exe"]
            display = "Notepad"
        elif "calc" in app_lower or "ගණක" in app_lower:
            proc_names = ["CalculatorApp.exe", "calc.exe"]
            display = "Calculator"
        else:
            proc_names = [f"{app_lower}.exe"]
            display = app_name

        for proc in proc_names:
            subprocess.run(["taskkill", "/F", "/IM", proc], capture_output=True, check=False)
        return f"{display} යෙදුම සාර්ථකව වසා දමන ලදී."
    except Exception as e:
        return f"{app_name} වැසීම අසාර්ථකයි: {e}"

def type_text(text: str) -> str:
    """
    Types text into the active focused window using clipboard injection.
    Supports full Sinhala Unicode and English text.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        return "පෙළ සාර්ථකව සටහන් කරන ලදී (Text Typed)."
    except Exception as e:
        # Fallback to direct write
        try:
            pyautogui.write(text, interval=0.03)
            return "පෙළ සටහන් කරන ලදී."
        except Exception as e2:
            return f"ටයිප් කිරීමේ දෝෂයකි: {e2}"

def press_key(key: str) -> str:
    """Presses hotkeys or navigation keys."""
    try:
        pyautogui.press(key.lower().strip())
        return f"{key} යතුර ඔබන ලදී."
    except Exception as e:
        return f"යතුරු දෝෂයකි: {e}"

def execute_shell_command(command: str, cwd: str = None) -> tuple:
    """
    Executes a shell command on Windows and returns (returncode, stdout, stderr).
    """
    working_dir = cwd or str(config.BASE_DIR)
    try:
        proc = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            timeout=120
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "විධානය ක්‍රියාත්මක වීමේ කාලය ඉක්මවා ගියේය (Command Timed Out)."
    except Exception as e:
        return -1, "", str(e)

def build_autonomous_project(project_name: str, file_specs: dict, test_command: str = None) -> dict:
    """
    Autonomous Project Builder:
    Takes project_name and a dictionary of { relative_filepath: file_content }.
    Creates files, executes tests/build commands, and returns summary in Sinhala.
    """
    target_dir = PROJECTS_DIR / project_name
    target_dir.mkdir(parents=True, exist_ok=True)

    created_files = []
    for rel_path, content in file_specs.items():
        file_path = target_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        created_files.append(rel_path)

    test_output = ""
    test_success = True
    if test_command:
        ret, stdout, stderr = execute_shell_command(test_command, cwd=str(target_dir))
        test_output = stdout if ret == 0 else f"{stdout}\nErrors:\n{stderr}"
        test_success = (ret == 0)

    summary_sinhala = (
        f"සර්, '{project_name}' ව්‍යාපෘතිය සාර්ථකව ගොඩනැගුවෙමි. "
        f"ගොනු {len(created_files)} ක් සාදන ලදී: {', '.join(created_files)}. "
        + ("පරීක්ෂණ සාර්ථකයි!" if test_success else "පරීක්ෂණ වලදී ගැටළු මතු විය.")
    )

    return {
        "project_name": project_name,
        "directory": str(target_dir),
        "files_created": created_files,
        "test_success": test_success,
        "test_output": test_output,
        "summary_sinhala": summary_sinhala
    }

def get_windows_startup_dir() -> Path:
    """Returns the Windows User Startup directory, creating it if needed."""
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        p = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    else:
        p = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    p.mkdir(parents=True, exist_ok=True)
    return p

def enable_windows_startup() -> dict:
    """
    Windows Auto-Startup Integration for Manuja:
    1. Locates %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup.
    2. Generates silent non-blocking VBScript (JARVIS_MK7_Startup.vbs) invoking pythonw.exe.
    3. Registers background runner into HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.
    Ensures J.A.R.V.I.S. loads docked at desktop corner without black console window flashing.
    """
    try:
        app_path = (config.BASE_DIR / "app.py").resolve()
        python_exe = sys.executable
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe

        # 1. Generate silent VBScript in Windows Startup directory
        startup_dir = get_windows_startup_dir()
        vbs_startup_file = startup_dir / "JARVIS_MK7_Startup.vbs"

        # Also write a local silent runner in root directory
        local_vbs_file = config.BASE_DIR.parent / "run_jarvis_silent.vbs"

        vbs_content = (
            'Set WshShell = CreateObject("WScript.Shell")\r\n'
            f'WshShell.CurrentDirectory = "{config.BASE_DIR}"\r\n'
            f'WshShell.Run """{pythonw_exe}"" ""{app_path}""", 0, False\r\n'
        )

        with open(vbs_startup_file, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        with open(local_vbs_file, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        # 2. Add entry to Windows Registry (HKCU Run) for double-redundant boot
        reg_ok = False
        try:
            import winreg
            run_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            reg_cmd = f'wscript.exe "{vbs_startup_file}"'
            winreg.SetValueEx(run_key, "JARVIS_MARK_VII", 0, winreg.REG_SZ, reg_cmd)
            winreg.CloseKey(run_key)
            reg_ok = True
        except Exception as reg_err:
            print(f"[STARTUP] Registry note: {reg_err}")

        print(f"[STARTUP] Windows auto-startup configured: {vbs_startup_file}")
        return {
            "success": True,
            "vbs_path": str(vbs_startup_file),
            "local_vbs": str(local_vbs_file),
            "registry_registered": reg_ok,
            "message": "J.A.R.V.I.S. auto-startup configured successfully for Manuja."
        }
    except Exception as e:
        print(f"[STARTUP] Failed to configure auto-startup: {e}")
        return {"success": False, "error": str(e)}

def disable_windows_startup() -> dict:
    """Removes J.A.R.V.I.S. from Windows Startup folder and Registry."""
    try:
        startup_dir = get_windows_startup_dir()
        vbs_file = startup_dir / "JARVIS_MK7_Startup.vbs"
        if vbs_file.exists():
            vbs_file.unlink()

        try:
            import winreg
            run_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(run_key, "JARVIS_MARK_VII")
            winreg.CloseKey(run_key)
        except Exception:
            pass

        return {"success": True, "message": "Windows auto-startup disabled."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def is_windows_startup_enabled() -> bool:
    """Checks if J.A.R.V.I.S. is registered in Windows Startup folder or Registry."""
    try:
        startup_dir = get_windows_startup_dir()
        vbs_file = startup_dir / "JARVIS_MK7_Startup.vbs"
        if vbs_file.exists():
            return True
        import winreg
        run_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        try:
            val, _ = winreg.QueryValueEx(run_key, "JARVIS_MARK_VII")
            winreg.CloseKey(run_key)
            return bool(val)
        except FileNotFoundError:
            winreg.CloseKey(run_key)
            return False
    except Exception:
        return False

if __name__ == "__main__":
    print("Telemetry check:", get_system_stats())
    print("Configuring auto-startup:", enable_windows_startup())

