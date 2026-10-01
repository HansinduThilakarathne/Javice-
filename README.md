# J.A.R.V.I.S. MK-VII - Autonomous Desktop AI Companion

An advanced, real-time autonomous personal AI companion inspired by Iron Man, engineered exclusively for **Sir (Manuja)** on Windows.

Powered by Google Gemini 2.5 Flash, Microsoft Edge TTS (Sinhala), OpenCV facial biometrics, Windows OS automation, and a Three.js-based 3D Holographic HUD.

---

## 🌟 Key Features

- **Cognitive Intelligence & Real-Time Voice**
  - Google Gemini 2.5 Flash
  - Multi-turn conversational reasoning
  - Google Search Grounding for current information, weather, and research

- **Natural Sinhala Voice Engine**
  - Microsoft Edge TTS
  - `si-LK-SameeraNeural`
  - `edge-tts`
  - `pygame.mixer`
  - Dynamic lip-sync articulation

- **Complete Sentence Capture & Self-Echo Protection**
  - Hands-free voice interaction
  - Dynamic noise calibration
  - `1.5s` silence threshold
  - Automatic microphone muting during voice playback

- **3D Cybernetic Iron Man HUD**
  - Three.js wireframe Iron Man Helmet
  - Real-time jaw articulation
  - Eye-pulse effects
  - Floating desktop widget
  - Fullscreen HUD
  - `F11` fullscreen toggle

- **Deep Windows OS Automation**
  - Application control
  - Active-window typing
  - Keyboard automation
  - Unicode typing
  - Software installation using `winget`
  - Direct YouTube playback

- **Multi-Modal Inspection Hub**
  - Drag-and-drop workspace
  - Image analysis using Gemini Vision
  - Desktop screenshot diagnostics

- **Biometric Identity Security**
  - Startup facial authentication
  - OpenCV / DeepFace
  - Facenet512 / ArcFace
  - Uses `manuja.jpg` as the reference image
  - Webcam is released after boot verification

---

## 🛠️ System Architecture & Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Cognitive Brain | Google Gemini 2.5 Flash, `google-genai` | AI reasoning, conversation memory, tool calling and web grounding |
| Speech-to-Text | `SpeechRecognition` | Continuous microphone input |
| Text-to-Speech | Microsoft Edge TTS, `pygame.mixer` | Sinhala voice generation |
| Computer Vision | OpenCV, DeepFace | Facial verification and vision diagnostics |
| Face Recognition | Facenet512 / ArcFace | Biometric authentication |
| OS Automation | `pyautogui`, `pyperclip`, `subprocess`, `winget` | Windows automation and package installation |
| Desktop UI | Three.js, HTML5, CSS3, `pywebview` | Holographic HUD and desktop widget |

---

## 👥 Project Team & Work Division

The project is divided between two core engineers.

```text
┌────────────────────────────────────────────────────────┐
│                   J.A.R.V.I.S. MK-VII                 │
├───────────────────────────┬────────────────────────────┤
│   MEMBER 1: Manuja        │   MEMBER 2: Lishani    │
│   Core AI, Audio & Sec    │   UI, HUD & OS Engine      │
├───────────────────────────┼────────────────────────────┤
│ • brain.py                │ • ui/index.html            │
│ • voice_engine.py         │ • ui/script.js             │
│ • security.py             │ • ui/style.css             │
│ • config.py               │ • system_tools.py          │
│ • requirements.txt        │ • app.py                   │
└───────────────────────────┴────────────────────────────┘
```

---

## 👨‍💻 Member 1: Lead AI & Systems Architect

### Primary Domain

Cognitive Core, Audio Pipelines, Biometrics, and System Configuration.

### Responsibilities

#### Cognitive Engine - `brain.py`

- Set up Google Gemini 2.5 Flash using the `google-genai` SDK.
- Implement multi-turn conversational session context.
- Maintain continuous conversation memory.
- Integrate Google Search Grounding.
- Configure the J.A.R.V.I.S. persona.
- Address the administrator as **"Sir" / "සර්"**.

#### Voice & Listening Pipeline - `voice_engine.py`

- Configure `SpeechRecognition`.
- Implement dynamic noise gating.
- Use a `1.5s` silence threshold.
- Capture complete sentences.
- Integrate `edge-tts`.
- Use `si-LK-SameeraNeural`.
- Route audio through `pygame.mixer`.
- Implement self-echo protection.

#### Biometrics & Security - `security.py`, `config.py`

- Implement startup facial verification.
- Compare the user's face against `manuja.jpg`.
- Release webcam hardware after verification.
- Implement acoustic voice profiling.

---

## 👨‍💻 Member 2: Frontend & Automation Specialist

### Primary Domain

Three.js Holographic Visuals, Multi-Modal Hub, and Windows OS Automation.

### Responsibilities

#### 3D Holographic HUD

Files:

- `ui/index.html`
- `ui/style.css`
- `ui/script.js`

Responsibilities:

- Build the 3D wireframe Iron Man Helmet.
- Implement Three.js rendering.
- Implement dynamic eye glow.
- Implement jaw movement.
- Synchronize jaw movement with TTS audio.
- Create responsive HUD layouts.
- Implement fullscreen mode using `F11`.

#### Desktop Application & IPC Bridge - `app.py`

- Configure `pywebview`.
- Create frameless and semi-transparent windows.
- Position the assistant as a floating desktop widget.
- Dock the widget in the bottom-right corner.
- Implement JavaScript ↔ Python communication.
- Send transcripts and face states to the HUD.

#### Deep OS Automation - `system_tools.py`

- Implement direct YouTube launching.
- Implement software installation using `winget`.
- Implement dependency installation using `pip`.
- Implement keyboard automation.
- Implement Unicode typing.
- Use `pyautogui` and `pyperclip`.

#### Multi-Modal Inspection Hub

- Create drag-and-drop support.
- Support images, files, and scripts.
- Capture desktop screenshots using `pyautogui.screenshot()`.
- Send screenshots for Gemini Vision diagnostics.

---

## 📁 Project Directory Structure

```text
JARVIS_MK7/
│
├── ui/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── autonomous_projects/
│   └── Output workspace for code generated by J.A.R.V.I.S.
│
├── screenshots/
│   └── Stored screenshots for vision analysis
│
├── logs/
│   └── Audit logs and security events
│
├── app.py
├── brain.py
├── config.py
├── security.py
├── system_tools.py
├── voice_engine.py
├── verify_system.py
│
├── manuja.jpg
├── requirements.txt
├── run_jarvis.bat
└── .env
```

---

## 🚀 Installation & Setup

### 1. Prerequisites

- Windows 10 or Windows 11 64-bit
- Python 3.11
- Functional microphone
- Functional webcam
- Active internet connection

During Python installation, make sure:

```text
Add python.exe to PATH
```

is enabled.

---

### 2. Open the Project

Open Command Prompt or PowerShell inside the project directory.

```bash
cd JARVIS_MK7
```

---

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment:

```bash
.venv\Scripts\activate
```

---

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Configure Gemini API Key

Create a `.env` file in the project root.

Add:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

> **Important:** Never upload your real API key to GitHub.

Add the following to `.gitignore`:

```text
.env
.venv/
__pycache__/
logs/
screenshots/
```

---

### 6. Biometric Enrollment

Place a clear, front-facing, well-lit reference photograph in the project root.

The expected filename is:

```text
manuja.jpg
```

This image is used for startup facial verification.

---

### 7. Launch J.A.R.V.I.S.

Run:

```bash
python app.py
```

Or use:

```text
run_jarvis.bat
```

---

## 🛡️ Operational Protocols

### "Sir" Protocol

J.A.R.V.I.S. is configured to recognize the administrator as its commander and address him as:

**Sir / සර්**

### Boot-Time Biometric Gate

During startup:

1. The webcam is activated.
2. The user's face is captured.
3. The face is compared with `manuja.jpg`.
4. Identity is verified.
5. The webcam is released after verification.

### Voice Biometrics

Runtime acoustic voice profiling helps filter background third-party speech without continuously using the camera.

### Safety Sandbox

High-risk operations require explicit confirmation.

Examples include:

- File deletion
- Registry modifications
- Potentially destructive system commands

System actions are recorded in:

```text
logs/audit_log.jsonl
```

### Display Controls

Press:

```text
F11
```

to switch between:

**Floating Desktop Widget ↔ Fullscreen Tactical HUD**

---

## ⚙️ Main Components

| File | Description |
|---|---|
| `app.py` | Main application entry point, window manager and IPC bridge |
| `brain.py` | Gemini AI client, persona and tool declarations |
| `voice_engine.py` | Speech recognition and Sinhala TTS |
| `security.py` | Facial verification and voice biometric security |
| `config.py` | Application configuration and identity settings |
| `system_tools.py` | Windows automation and system tools |
| `verify_system.py` | Environment and dependency checker |
| `ui/index.html` | Main HUD interface |
| `ui/style.css` | HUD styling |
| `ui/script.js` | Three.js 3D helmet and visual effects |
| `requirements.txt` | Python dependencies |
| `run_jarvis.bat` | Windows quick-launch script |
| `manuja.jpg` | Biometric reference image |
| `.env` | API keys and environment configuration |

---

## 🔄 Application Flow

```text
              ┌───────────────────┐
              │  Start J.A.R.V.I.S │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Biometric Face    │
              │ Authentication    │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Initialize Gemini │
              │ 2.5 Flash         │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Start Voice       │
              │ Recognition       │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ User Voice Input  │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Speech-to-Text    │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Gemini AI Brain   │
              │ + Tool Calling    │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Execute Action /  │
              │ Generate Response │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Sinhala TTS       │
              │ Voice Response    │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Three.js HUD      │
              │ Lip Sync / Effects│
              └───────────────────┘
```

---

## 🎯 Project Goals

J.A.R.V.I.S. MK-VII aims to provide:

- Intelligent conversational assistance
- Natural Sinhala voice interaction
- Hands-free computer control
- Secure biometric authentication
- Real-time information retrieval
- Windows OS automation
- Visual 3D interaction
- Image and screenshot analysis
- Multi-modal desktop interaction

---

## 🔒 Security Considerations

For security reasons:

- Never commit `.env` files.
- Never expose Gemini API keys publicly.
- Keep biometric images private.
- Review automated system commands before execution.
- Keep audit logs protected.
- Do not run destructive commands without confirmation.

---

## 🧪 System Verification

Before launching the application, run:

```bash
python verify_system.py
```

This checks the environment and required dependencies.

---

## ▶️ Quick Start

```bash
cd JARVIS_MK7
.venv\Scripts\activate
python app.py
```

Or simply run:

```text
run_jarvis.bat
```

---

## 👤 Project Team

### Member 1 - Manuja

**Lead AI & Systems Architect**

Responsibilities:

- AI Brain
- Voice Engine
- Biometrics
- Security
- Configuration

### Member 2 - Co-Engineer

**Frontend & Automation Specialist**

Responsibilities:

- Three.js HUD
- Frontend
- Desktop UI
- IPC Bridge
- Windows Automation
- Multi-Modal Inspection Hub

---

## 🎖️ J.A.R.V.I.S. MK-VII

```text
J.A.R.V.I.S. MK-VII
Autonomous Desktop AI Companion

Cognitive Intelligence
+ Sinhala Voice
+ Facial Biometrics
+ Windows Automation
+ 3D Holographic HUD
+ Multi-Modal Vision
```

---

## 📄 License

This project is developed as a personal/academic software project.

Refer to the project repository for licensing and usage conditions.
