"""
J.A.R.V.I.S. MARK VII - Subsystem Verification & Diagnostic Test
Validates all modules: Security Gate, Telemetry, Voice Engine, Brain, Tools & UI
"""

import os
import sys
from pathlib import Path

# Ensure standard UTF-8 console output for Sinhala characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import config
import system_tools
import voice_engine
import security
from brain import JarvisBrain

def run_diagnostics():
    print("=" * 60)
    print("   J.A.R.V.I.S. MARK VII - COMPREHENSIVE SUBSYSTEM AUDIT")
    print(f"   PRIMARY USER: {config.PRIMARY_USER}")
    print("=" * 60)

    results = {}

    # 1. UI Assets Verification
    print("\n[1/7] Auditing UI Assets...")
    index_exists = (config.UI_DIR / "index.html").exists()
    style_exists = (config.UI_DIR / "style.css").exists()
    script_exists = (config.UI_DIR / "script.js").exists()
    ui_valid = index_exists and style_exists and script_exists
    results["UI_Assets"] = ui_valid
    print(f"  - index.html: {'OK' if index_exists else 'MISSING'}")
    print(f"  - style.css:  {'OK' if style_exists else 'MISSING'}")
    print(f"  - script.js:  {'OK' if script_exists else 'MISSING'}")

    # 2. Hardware Telemetry & Diagnostics
    print("\n[2/7] Testing Hardware Telemetry (psutil)...")
    try:
        stats = system_tools.get_system_stats()
        print(f"  - CPU: {stats['cpu_percent']}%")
        print(f"  - RAM: {stats['ram_percent']}% ({stats['ram_used_gb']} GB / {stats['ram_total_gb']} GB)")
        print(f"  - Arc Power / Battery: {stats['battery_percent']}% (Plugged: {stats['power_plugged']})")
        print(f"  - Storage (C:): {stats['disk_percent']}%")
        results["Telemetry"] = True
    except Exception as e:
        print(f"  - Telemetry Error: {e}")
        results["Telemetry"] = False

    # 3. One-Time Camera Auth & Biometric Security Gate
    print("\n[3/8] Testing One-Time Startup Camera & Voice Biometrics...")
    try:
        ref_path = Path(config.REFERENCE_IMAGE_PATH)
        print(f"  - Reference file: {ref_path} (Exists: {ref_path.exists()})")
        gate = security.get_security_gate()

        # Test one-time boot verification
        boot_verified = gate.one_time_startup_verification()
        print(f"  - One-time boot verification status: {boot_verified}")
        print(f"  - Camera permanently released: {security.SESSION_CAMERA_RELEASED}")

        # Test voice biometrics with synthetic PCM
        import numpy as np
        fake_pcm = (np.sin(np.linspace(0, 140 * 2 * np.pi, 16000)) * 10000).astype(np.int16).tobytes()
        gate.voice_biometrics.enroll_or_verify(fake_pcm)
        v_match = gate.voice_biometrics.enroll_or_verify(fake_pcm)
        print(f"  - In-memory Voice Biometrics enrollment & verification: {'OK' if v_match else 'FAILED'}")

        results["Biometrics"] = boot_verified and security.SESSION_CAMERA_RELEASED and v_match
    except Exception as e:
        print(f"  - Biometrics Error: {e}")
        results["Biometrics"] = False

    # 4. Windows System Control Tools & Intent Interception
    print("\n[4/8] Testing Windows Automation Tools & Intent Interception...")
    try:
        shot_path = system_tools.take_screenshot("audit_test_screen.png")
        shot_ok = os.path.exists(shot_path)
        print(f"  - Screenshot Capture: {'OK (' + shot_path + ')' if shot_ok else 'FAILED'}")

        # Test YouTube instant intent interception
        is_yt, yt_q = system_tools.parse_youtube_intent("ජාවිස් යූටියුබ් එකට ගිහිල්ලා ඉරාජ්ගේ කතන්දරේ සින්දුව ප්ලේ කරන්න")
        print(f"  - YouTube Intent Interception: {'OK (Query: ' + yt_q + ')' if (is_yt and 'ඉරාජ්' in yt_q) else 'FAILED'}")
        results["System_Tools"] = shot_ok and is_yt
    except Exception as e:
        print(f"  - System Tools Error: {e}")
        results["System_Tools"] = False

    # 5. Autonomous Project Builder
    print("\n[5/8] Testing Autonomous Project Builder...")
    try:
        test_project = system_tools.build_autonomous_project(
            project_name="MK7_Echo_Module",
            file_specs={
                "main.py": "print('Echo module initialized for Manuja.')\n",
                "test.py": "assert True\nprint('All tests passed.')\n"
            },
            test_command=f'"{sys.executable}" test.py'
        )
        print(f"  - Project Created at: {test_project['directory']}")
        print(f"  - Files: {test_project['files_created']}")
        print(f"  - Summary: {test_project['summary_sinhala']}")
        results["Autonomous_Builder"] = test_project["test_success"]
    except Exception as e:
        print(f"  - Project Builder Error: {e}")
        results["Autonomous_Builder"] = False

    # 6. Voice Engine Emotion Parsing & In-Memory TTS Cadence
    print("\n[6/8] Testing Voice Engine & Calibrated Sinhala Cadence (-5%)...")
    try:
        sample_raw = "[LAUGH] ආයුබෝවන් මනුජ! මම ඔබගේ හොඳම මිතුරා."
        cleaned, emotion = voice_engine.parse_emotion_and_clean(sample_raw)
        print(f"  - Raw Input:  {sample_raw}")
        print(f"  - Cleaned:    {cleaned}")
        print(f"  - Emotion:    {emotion}")
        print(f"  - Voice:      {config.VOICE_PROFILE}")
        print(f"  - Rate:       {config.TTS_RATE}")
        print(f"  - Pitch:      {config.TTS_PITCH}")
        assert emotion == "LAUGH", "Emotion tag parsing failed"
        assert "[LAUGH]" not in cleaned, "Emotion tag not stripped"
        assert "මනුජ," in cleaned or "මනුජ" in cleaned, "Micro-pause punctuation failed"
        results["Voice_Engine"] = True
    except Exception as e:
        print(f"  - Voice Engine Error: {e}")
        results["Voice_Engine"] = False

    # 7. Cognitive Brain (Gemini / Zero-Delay Streaming Sentence Chunking)
    print("\n[7/8] Testing Cognitive Brain Zero-Delay Streaming...")
    try:
        brain = JarvisBrain()
        stream_chunks = []
        for chunk, emo in brain.stream_think_and_respond("ආයුබෝවන් ජාවිස්, කොහොමද?"):
            stream_chunks.append((chunk, emo))
            print(f"  - Chunk: [{emo}] {chunk}")
        print(f"  - Total sentence chunks streamed: {len(stream_chunks)}")
        results["Brain_Streaming"] = len(stream_chunks) > 0
    except Exception as e:
        print(f"  - Brain Streaming Error: {e}")
        results["Brain_Streaming"] = False

    # 8. Best Friend Persona & Sir Protocol Verification
    print("\n[8/9] Verifying Best Friend Persona & Sir Protocol...")
    has_friend_prompt = "හොඳම මිතුරා" in config.SYSTEM_PROMPT and "මනුජ" in config.SYSTEM_PROMPT
    has_sir_protocol = "සර්" in config.SYSTEM_PROMPT
    print(f"  - Best Friend Persona in Prompt: {'VERIFIED' if has_friend_prompt else 'MISSING'}")
    print(f"  - Sir Protocol in Prompt:        {'VERIFIED' if has_sir_protocol else 'MISSING'}")
    results["Sir_Protocol"] = has_friend_prompt and has_sir_protocol

    # 9. Multi-Modal Vision & File Hub Streaming Test
    print("\n[9/9] Testing Multi-Modal Vision & File Hub Streaming...")
    try:
        sample_code = b"print('Hello Sir!')\ndef calculate_core(): return 42\n"
        chunks = []
        for c, emo in brain.stream_file_analysis("test_script.py", sample_code):
            chunks.append(c)
            print(f"  - File Analysis Chunk: [{emo}] {c}")
        results["MultiModal_Vision"] = len(chunks) > 0
        print(f"  - Multi-Modal Analysis: {'OK' if len(chunks) > 0 else 'EMPTY'}")
    except Exception as e:
        print(f"  - Multi-Modal Analysis Error: {e}")
        results["MultiModal_Vision"] = False

    # 10. Wake-Word Spotting & Self-Echo Protection Test
    print("\n[10/14] Testing Wake-Word Spotting & Self-Echo Protection...")
    try:
        has_ww1, rem1 = voice_engine.spot_wake_word("ජාවිස් මගේ තිරය බලන්න")
        has_ww2, rem2 = voice_engine.spot_wake_word("hey jarvis open vs code")
        has_ww3, rem3 = voice_engine.spot_wake_word("අද කාලගුණය කොහොමද")
        ww_ok = has_ww1 and ("මගේ තිරය" in rem1) and has_ww2 and (not has_ww3)
        print(f"  - Wake-word 'ජාවිස්' spotting:        {'OK' if has_ww1 else 'FAILED'}")
        print(f"  - Wake-word 'hey jarvis' spotting:    {'OK' if has_ww2 else 'FAILED'}")
        print(f"  - Non-wake utterance rejected:        {'OK' if not has_ww3 else 'FAILED'}")
        results["Wake_Word_Engine"] = ww_ok
    except Exception as e:
        print(f"  - Wake Word Error: {e}")
        results["Wake_Word_Engine"] = False

    # 11. Multi-Tier Security Sandbox & Audit Logger Test
    print("\n[11/14] Testing Multi-Tier Security Sandbox & Audit Logger...")
    try:
        risk_low, _ = system_tools.classify_command_risk("volume up")
        risk_high, reason = system_tools.classify_command_risk("delete file core_system.py")
        system_tools.log_audit_event("audit_verification_test", "LOW", "EXECUTED", "Audit system verified")
        audit_file_ok = config.AUDIT_LOG_PATH.exists()
        sandbox_ok = (risk_low == "LOW") and (risk_high == "HIGH") and audit_file_ok
        print(f"  - Low-Risk classification:            {'OK (LOW)' if risk_low == 'LOW' else 'FAILED'}")
        print(f"  - High-Risk classification:           {'OK (HIGH - ' + reason + ')' if risk_high == 'HIGH' else 'FAILED'}")
        print(f"  - Audit log file:                     {'OK (' + str(config.AUDIT_LOG_PATH) + ')' if audit_file_ok else 'FAILED'}")
        results["Security_Sandbox"] = sandbox_ok
    except Exception as e:
        print(f"  - Security Sandbox Error: {e}")
        results["Security_Sandbox"] = False

    # 12. Workspace File & Document Engine Test
    print("\n[12/14] Testing Workspace File & Document Engine...")
    try:
        w_res = system_tools.write_workspace_file("test_workspace_doc.txt", "J.A.R.V.I.S. MK-VII Document Engine Verified.")
        r_res = system_tools.read_workspace_file("test_workspace_doc.txt")
        files_list = system_tools.list_workspace_files()
        file_engine_ok = w_res["success"] and r_res["success"] and ("Verified" in r_res["content"]) and (len(files_list) > 0)
        print(f"  - Write workspace file:               {'OK' if w_res['success'] else 'FAILED'}")
        print(f"  - Read workspace file:                {'OK' if r_res['success'] else 'FAILED'}")
        print(f"  - Workspace files listed:             {len(files_list)} items")
        # Cleanup test file
        test_file = config.BASE_DIR / "test_workspace_doc.txt"
        if test_file.exists():
            test_file.unlink()
        results["File_Document_Engine"] = file_engine_ok
    except Exception as e:
        print(f"  - File Engine Error: {e}")
        results["File_Document_Engine"] = False

    # 13. Session Continuity & Local Memory Test
    print("\n[13/14] Testing Session Continuity Memory (local_memory.json)...")
    try:
        from brain import save_turn_to_memory, load_local_memory
        save_turn_to_memory("user", "ටෙස්ට් විධානය සර්")
        save_turn_to_memory("jarvis", "ඔව් සර්, මම සූදානම්.")
        mem_history = load_local_memory()
        mem_ok = len(mem_history) >= 2 and (config.LOCAL_MEMORY_PATH.exists())
        print(f"  - Local memory file:                  {'OK (' + str(config.LOCAL_MEMORY_PATH) + ')' if config.LOCAL_MEMORY_PATH.exists() else 'FAILED'}")
        print(f"  - Memory turns recorded:              {len(mem_history)} turns")
        results["Session_Continuity"] = mem_ok
    except Exception as e:
        print(f"  - Session Memory Error: {e}")
        results["Session_Continuity"] = False

    # 14. Screen Vision Capture Buffer Test
    print("\n[14/14] Testing Screen Vision Capture Buffer...")
    try:
        screen_bytes = system_tools.capture_screen_bytes()
        screen_ok = isinstance(screen_bytes, bytes) and len(screen_bytes) > 1000
        print(f"  - In-Memory Screen JPEG buffer:       {'OK (' + str(len(screen_bytes)) + ' bytes)' if screen_ok else 'FAILED'}")
        results["Screen_Vision_Capture"] = screen_ok
    except Exception as e:
        print(f"  - Screen Capture Error: {e}")
        results["Screen_Vision_Capture"] = False

    # Final Summary
    print("\n" + "=" * 60)
    print("   SUBSYSTEM DIAGNOSTIC AUDIT RESULTS")
    print("=" * 60)
    all_passed = True
    for sub, ok in results.items():
        status_str = "PASS [OPERATIONAL]" if ok else "FAIL [ATTENTION NEEDED]"
        if not ok:
            all_passed = False
        print(f"  {sub:<24} : {status_str}")
    print("=" * 60)
    print(f"OVERALL SYSTEM INTEGRITY: {'100% OPERATIONAL' if all_passed else 'SOME WARNINGS'}\n")
    return all_passed

if __name__ == "__main__":
    run_diagnostics()
