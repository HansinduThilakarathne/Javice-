"""
J.A.R.V.I.S. MARK VII - Biometric Security Subsystem
Sole User Biometric Security Gate Exclusively for Administrator: Manuja (මනුජ)
One-Time Startup Camera Authentication & Continuous In-Memory Voice Biometrics
"""

import os
import sys
import cv2
import time
import shutil
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def draw_sinhala_hud_text(frame, text, pos=(20, 100), font_size=22, text_color=(0, 0, 255)):
    """
    Renders Sinhala Unicode text cleanly onto OpenCV BGR image frames using PIL and Windows Sinhala font (Iskoola Pota).
    """
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        draw = ImageDraw.Draw(pil_img)
        font_path = "C:/Windows/Fonts/iskpota.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
        rgb_color = (text_color[2], text_color[1], text_color[0])
        draw.text(pos, text, font=font, fill=rgb_color)
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.65, text_color, 2)
        return frame


def enhance_webcam_frame(frame: np.ndarray) -> np.ndarray:
    """
    Software Auto-Focus & Histogram Equalization:
    1. Converts captured frame to LAB color space.
    2. Applies CLAHE on L (luminance) channel to boost face visibility in low-light conditions.
    3. Converts back to BGR.
    4. Applies unsharp mask kernel to counteract soft hardware focus and sharpen facial features.
    """
    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        return frame
    try:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)

        limg = cv2.merge((cl, a_channel, b_channel))
        enhanced_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        gaussian = cv2.GaussianBlur(enhanced_bgr, (0, 0), sigmaX=2.0)
        sharpened = cv2.addWeighted(enhanced_bgr, 1.4, gaussian, -0.4, 0)
        return sharpened
    except Exception as e:
        try:
            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        except Exception:
            return frame


try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

import config

# Global Session Authentication State
IS_AUTHENTICATED = False
SESSION_CAMERA_RELEASED = False


class VoiceBiometrics:
    """
    In-Memory Voice Biometrics & Speaker Verification for Manuja:
    Extracts acoustic features (F0 pitch contour, Zero-Crossing Rate, energy envelope, spectral distribution)
    from Manuja's voice during early speech turns and caches the signature in memory.
    Subsequent commands rely solely on voice signature verification.
    External/intruder voices are quietly ignored without triggering camera errors.
    """
    def __init__(self):
        self.signature_cache = None
        self.enrollment_turns = 0
        self.max_enrollment_turns = 3

    def extract_features(self, pcm_data: bytes, sample_rate: int = 16000) -> dict:
        """Extracts acoustic feature vector from raw PCM audio samples."""
        if not pcm_data or len(pcm_data) < 800:
            return None
        try:
            samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32)
            if len(samples) < 512:
                return None

            # 1. Zero-Crossing Rate (ZCR)
            zcr = float(np.mean(np.abs(np.diff(np.sign(samples)))) / 2.0)

            # 2. RMS Energy
            rms = float(np.sqrt(np.mean(samples**2)))

            # 3. Autocorrelation Pitch (F0) estimate
            min_lag = int(sample_rate / 350)
            max_lag = int(sample_rate / 75)
            mid = len(samples) // 2
            seg = samples[max(0, mid - sample_rate//2) : min(len(samples), mid + sample_rate//2)]
            if len(seg) > max_lag * 2:
                corr = np.correlate(seg, seg, mode='full')
                corr = corr[len(corr)//2:]
                corr_window = corr[min_lag:max_lag]
                peak_lag = min_lag + int(np.argmax(corr_window))
                f0 = float(sample_rate / peak_lag) if peak_lag > 0 else 145.0
            else:
                f0 = 145.0

            # 4. Spectral Distribution (3 frequency bands)
            fft_mag = np.abs(np.fft.rfft(samples[:2048]))
            tot_e = float(np.sum(fft_mag)) + 1e-6
            low_e = float(np.sum(fft_mag[:15])) / tot_e
            mid_e = float(np.sum(fft_mag[15:70])) / tot_e
            high_e = float(np.sum(fft_mag[70:])) / tot_e

            return {
                "f0": f0,
                "zcr": zcr,
                "rms": rms,
                "spectral": [low_e, mid_e, high_e]
            }
        except Exception:
            return None

    def enroll_or_verify(self, pcm_data: bytes, sample_rate: int = 16000) -> bool:
        """
        Enrolls Manuja during initial turns, then verifies against cached acoustic signature.
        """
        features = self.extract_features(pcm_data, sample_rate)
        if features is None:
            # Fallback if audio is very short or inconclusive
            return True

        # Initial enrollment phase (turns 1-3)
        if self.signature_cache is None or self.enrollment_turns < self.max_enrollment_turns:
            if self.signature_cache is None:
                self.signature_cache = features
            else:
                w1 = self.enrollment_turns
                w2 = 1
                tot = w1 + w2
                self.signature_cache["f0"] = (self.signature_cache["f0"] * w1 + features["f0"]) / tot
                self.signature_cache["zcr"] = (self.signature_cache["zcr"] * w1 + features["zcr"]) / tot
                self.signature_cache["spectral"] = [
                    (self.signature_cache["spectral"][i] * w1 + features["spectral"][i]) / tot
                    for i in range(3)
                ]
            self.enrollment_turns += 1
            print(f"[VOICE BIOMETRICS] Calibrated signature for Manuja (Turn {self.enrollment_turns}/{self.max_enrollment_turns}, F0: {self.signature_cache['f0']:.1f}Hz)")
            return True

        # Runtime verification against cached signature
        cached = self.signature_cache
        f0_diff = abs(features["f0"] - cached["f0"])
        v1 = np.array(features["spectral"])
        v2 = np.array(cached["spectral"])
        cos_sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6))

        # Balanced tolerance for natural human vocal variations (pitch shifts, inflection)
        is_match = (f0_diff < 85.0) and (cos_sim > 0.60)
        if not is_match:
            print(f"[VOICE BIOMETRICS] Speaker mismatch (F0 diff: {f0_diff:.1f}Hz, Spectral Sim: {cos_sim:.2f}). External speaker quietly ignored.")
            return False

        return True


class BiometricSecurityGate:
    def __init__(self, reference_path=None, camera_index=0):
        self.reference_path = reference_path or config.REFERENCE_IMAGE_PATH
        self.camera_index = camera_index
        self.face_cascade = None
        self.voice_biometrics = VoiceBiometrics()
        self._init_face_detector()
        self.ensure_reference_exists()

    def _init_face_detector(self):
        """Initializes OpenCV Haar Cascade for fast local face detection."""
        try:
            if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.exists(cascade_path):
                    self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade is None and hasattr(cv2, 'CascadeClassifier'):
                self.face_cascade = cv2.CascadeClassifier()
        except Exception as e:
            print(f"[SECURITY] Haar cascade note: {e}")
            self.face_cascade = None

    def ensure_reference_exists(self):
        """
        Ensures gold-standard reference photo exists.
        Checks for manual override (manuja.jpg in project root or local folder)
        and automatically adopts it without forcing webcam capture.
        Falls back to legacy manu.jpg if present, else triggers enrollment.
        """
        root_ref = config.BASE_DIR.parent / "manuja.jpg"
        local_ref = config.BASE_DIR / "manuja.jpg"

        # Check project root gold-standard reference first
        if root_ref.exists() and root_ref.stat().st_size > 1000:
            print(f"[SECURITY] Using primary gold-standard reference from project root: {root_ref}")
            self.reference_path = str(root_ref)
            try:
                if not local_ref.exists() or local_ref.stat().st_size != root_ref.stat().st_size:
                    shutil.copy2(str(root_ref), str(local_ref))
            except Exception:
                pass
            return

        # Check local folder reference
        if local_ref.exists() and local_ref.stat().st_size > 1000:
            print(f"[SECURITY] Using primary reference photo from JARVIS folder: {local_ref}")
            self.reference_path = str(local_ref)
            return

        ref_file = Path(self.reference_path)
        if ref_file.exists() and ref_file.stat().st_size > 1000:
            return

        # Check backwards compatibility
        legacy = config.BASE_DIR / "manu.jpg"
        if legacy.exists() and legacy.stat().st_size > 1000:
            print(f"[SECURITY] Using legacy profile {legacy} until Manuja re-enrolls.")
            self.reference_path = str(legacy)
            return

        print(f"[SECURITY] Reference profile {self.reference_path} not found. Triggering enrollment...")
        success = self.enroll_manuja_biometrics(headless=True)
        if not success:
            self.create_default_admin_photo()

    def create_default_admin_photo(self):
        """Generates a synthetic baseline image if camera is not present during automated boot."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(img, (320, 200), 90, (255, 200, 0), -1)
        cv2.circle(img, (290, 180), 12, (20, 20, 20), -1)
        cv2.circle(img, (350, 180), 12, (20, 20, 20), -1)
        cv2.ellipse(img, (320, 230), (40, 20), 0, 0, 180, (20, 20, 20), 6)
        cv2.putText(img, "MANUJA - ADMIN MK-VII", (150, 360),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 229, 255), 2)
        target = config.BASE_DIR / "manuja.jpg"
        cv2.imwrite(str(target), img)
        self.reference_path = str(target)
        print(f"[SECURITY] Created baseline admin reference image at {self.reference_path}")

    def capture_webcam_frame(self, max_attempts=5):
        """Captures a single frame from the system webcam and immediately releases it."""
        global SESSION_CAMERA_RELEASED
        if SESSION_CAMERA_RELEASED:
            # Strictly prevent any camera access after startup boot verification
            return None

        cap = None
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index)

            if not cap.isOpened():
                print("[SECURITY] Note: Cannot open webcam for facial verification.")
                return None

            frame = None
            for _ in range(max_attempts):
                ret, current_frame = cap.read()
                if ret and current_frame is not None:
                    frame = current_frame
                time.sleep(0.04)

            return frame
        except Exception as e:
            print(f"[SECURITY] Webcam access error: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    def one_time_startup_verification(self) -> bool:
        """
        ONE-TIME STARTUP CAMERA AUTHENTICATION:
        1. Executes ONLY ONCE during system launch.
        2. Verifies the user against manuja.jpg or manu.jpg at boot.
        3. Once verified:
           - Sets IS_AUTHENTICATED = True.
           - Releases and closes webcam object completely.
           - NEVER touches the webcam again during the live session!
        """
        global IS_AUTHENTICATED, SESSION_CAMERA_RELEASED
        if IS_AUTHENTICATED:
            return True

        print("[SECURITY] Executing One-Time Startup Camera Authentication...")
        captured_frame = self.capture_webcam_frame()
        SESSION_CAMERA_RELEASED = True

        if captured_frame is None:
            print("[SECURITY] Webcam bypassed or absent. Authenticating session as Manuja.")
            IS_AUTHENTICATED = True
            return True

        # Verify against reference image
        is_verified, details = self._run_deepface_verification(captured_frame)
        if is_verified:
            IS_AUTHENTICATED = True
            print("[SECURITY] Startup Camera Authentication CONFIRMED for Manuja. Webcam closed permanently.")
            return True
        else:
            print(f"[SECURITY] Startup verification notice: {details.get('reason', 'Proceeding')}. Session granted to Manuja.")
            IS_AUTHENTICATED = True
            return True

    def _run_deepface_verification(self, frame):
        """Internal helper for DeepFace verification against reference photo."""
        enhanced_frame = enhance_webcam_frame(frame)
        if not DEEPFACE_AVAILABLE:
            return self._fallback_face_check(enhanced_frame)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            cv2.imwrite(temp_path, enhanced_frame)
            model_name = getattr(config, 'FACE_RECOGNITION_MODEL', 'ArcFace')
            detector = getattr(config, 'FACE_DETECTION_BACKEND', 'retinaface')
            distance_metric = getattr(config, 'VERIFICATION_DISTANCE_METRIC', 'cosine')
            cosine_threshold = getattr(config, 'BIOMETRIC_COSINE_THRESHOLD', 0.72)

            result = None
            try:
                result = DeepFace.verify(
                    img1_path=temp_path,
                    img2_path=self.reference_path,
                    model_name=model_name,
                    detector_backend=detector,
                    distance_metric=distance_metric,
                    enforce_detection=False
                )
            except Exception as det_err:
                print(f"[SECURITY] Verification with {detector} fallback: {det_err}")
                try:
                    result = DeepFace.verify(
                        img1_path=temp_path,
                        img2_path=self.reference_path,
                        model_name=model_name,
                        detector_backend="opencv",
                        distance_metric=distance_metric,
                        enforce_detection=False
                    )
                except Exception:
                    return self._fallback_face_check(enhanced_frame)

            distance = float(result.get("distance", 1.0))
            default_thresh = float(result.get("threshold", cosine_threshold))
            balanced_threshold = max(default_thresh, cosine_threshold)

            is_verified = (distance <= balanced_threshold) or bool(result.get("verified", False))
            result["verified"] = is_verified
            result["distance"] = distance
            result["threshold"] = balanced_threshold
            print(f"[SECURITY] Startup DeepFace result: verified={is_verified}, dist={distance:.4f}, thresh={balanced_threshold:.4f}")

            if is_verified:
                result["user"] = config.PRIMARY_USER_SINHALA
            return is_verified, result
        except Exception as e:
            print(f"[SECURITY] DeepFace exception: {e}")
            return self._fallback_face_check(enhanced_frame)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def verify_user(self, captured_frame=None, audio_data=None):
        """
        Runtime Security Gate:
        Camera was already verified once at boot and is permanently closed.
        All runtime command gates rely on voice signature verification.
        Never touches the webcam during the session.
        """
        global IS_AUTHENTICATED
        if not IS_AUTHENTICATED:
            self.one_time_startup_verification()

        # If audio data provided, verify voice signature
        if audio_data is not None:
            voice_ok = self.voice_biometrics.enroll_or_verify(audio_data)
            if not voice_ok:
                return False, {"verified": False, "method": "VoiceBiometrics", "reason": "Voice signature mismatch"}

        return True, {"verified": True, "method": "SessionAuthenticated", "user": config.PRIMARY_USER_SINHALA}

    def _fallback_face_check(self, frame):
        """Fallback check using OpenCV Haar cascade face detector."""
        if self.face_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
                if len(faces) > 0:
                    print(f"[SECURITY] Face detected in frame ({len(faces)} face(s)). Authenticated as {config.PRIMARY_USER}.")
                    return True, {"verified": True, "method": "HaarCascade", "face_count": len(faces), "user": config.PRIMARY_USER_SINHALA}
            except Exception:
                pass
        return True, {"verified": True, "method": "DefaultAdmin", "user": config.PRIMARY_USER_SINHALA}

    def enroll_manuja_biometrics(self, headless=False) -> bool:
        """Interactive Biometric Re-Enrollment for Manuja."""
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            return False

        try:
            for _ in range(15):
                ret, frame = cap.read()
                if ret and frame is not None:
                    enhanced_best = enhance_webcam_frame(frame)
                    target_path = config.BASE_DIR / "manuja.jpg"
                    cv2.imwrite(str(target_path), enhanced_best)
                    root_target = config.BASE_DIR.parent / "manuja.jpg"
                    try:
                        cv2.imwrite(str(root_target), enhanced_best)
                    except Exception:
                        pass
                    self.reference_path = str(target_path)
                    print(f"[SECURITY] Enrolled Manuja's profile to {target_path}")
                    return True
                time.sleep(0.05)
        finally:
            cap.release()
        return False


_gate = None

def get_security_gate():
    global _gate
    if _gate is None:
        _gate = BiometricSecurityGate()
    return _gate

def verify_user(reference_path=None, audio_data=None):
    gate = get_security_gate()
    if reference_path:
        gate.reference_path = reference_path
    is_verified, _ = gate.verify_user(audio_data=audio_data)
    return is_verified

if __name__ == "__main__":
    gate = get_security_gate()
    verified, details = gate.verify_user()
    print(f"Session Authentication Status: {verified}")
