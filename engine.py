# engine.py
import cv2
import mediapipe as mp
import speech_recognition as sr
import threading
import time
import subprocess
import platform
import os
import json
import webbrowser

# ==================================================
# MEDIAPIPE SETUP
# ==================================================
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

face_detection = mp_face.FaceDetection(
    min_detection_confidence=0.7
)

# ==================================================
# PERSISTENT PROFILE CONTROLLER WITH CUSTOM MAPS
# ==================================================
PROFILE_FILE = "profiles.json"

# Clean translation layer for rendering dynamic strings visually
FINGER_LABELS = {
    "01000": "1 (Index) ☝️",
    "01100": "2 (Peace) ✌️",
    "01110": "3 (Three) 👌",
    "01111": "4 (Four) ✋",
    "11111": "5 (Palm) 🖐️",
    "10001": "Shaka (Thumb+Pinky) 🤙",
    "01001": "Rock-On (Index+Pinky) 🤘",
    "10000": "Thumbs-Up 👍",
    "00000": "Fist ✊"
}

# Concrete default actions assigned across patterns layout mapped out below
DEFAULT_PROFILES = {
    "Profile 1": {
        "name": "Yohan",
        "gestures": {
            "01000": "open_safari",
            "01100": "open_whatsapp_web",
            "01110": "open_excel",
            "01111": "open_photobooth",
            "11111": "open_voicememos"
        },
        "custom_commands": {}
    },
    "Profile 2": {
        "name": "Profile 2",
        "gestures": {
            "01000": "open_safari",
            "01100": "open_whatsapp_web",
            "01110": "open_excel",
            "01111": "open_photobooth",
            "11111": "open_voicememos"
        },
        "custom_commands": {}
    },
    "Profile 3": {
        "name": "Profile 3",
        "gestures": {
            "01000": "open_safari",
            "01100": "open_whatsapp_web",
            "01110": "open_excel",
            "01111": "open_photobooth",
            "11111": "open_voicememos"
        },
        "custom_commands": {}
    }
}


def load_profiles():
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_PROFILES
    return DEFAULT_PROFILES


def save_profiles():
    with open(PROFILE_FILE, "w") as f:
        json.dump(PROFILES, f, indent=4)


PROFILES = load_profiles()

# ==================================================
# SHARED GLOBAL STATE
# ==================================================
STATE = {
    "assistant_awake": False,  # Boot default changed to sleep
    "assistant_status": "Sleeping", # Boot status set to sleeping
    "hover_state": None,
    "active_profile_key": "Profile 1",
    "current_user": PROFILES["Profile 1"]["name"],
    "face_recognition_enabled": True,
    "camera_enabled": True # Tracks if video capturing stream processing layer is active
}

SYSTEM_LOGS = []


def log_message(text):
    timestamp = time.strftime("%H:%M:%S")
    formatted_log = f"[{timestamp}] {text}"
    print(text)
    SYSTEM_LOGS.append(formatted_log)
    if len(SYSTEM_LOGS) > 50:
        SYSTEM_LOGS.pop(0)


# ==================================================
# DEBOUNCE STATE
# ==================================================
last_gesture = None
last_time = 0
GESTURE_COOLDOWN = 2


# ==================================================
# VOICE (MAC SAMANTHA)
# ==================================================
def speak(text):
    subprocess.Popen(["say", "-v", "Samantha", text])


# ==================================================
# CORE COMMAND EXECUTION SYSTEM
# ==================================================
commands = {}


def register_command(name):
    def wrapper(func):
        commands[name] = func
        return func

    return wrapper


def execute_command(name):
    name = name.lower()

    # 1. Check if it's a built-in static native feature
    func = commands.get(name)
    if func:
        func()
        return

    # 2. Check if it's a dynamic user custom defined binding
    active_profile = PROFILES.get(STATE["active_profile_key"])
    if active_profile and "custom_commands" in active_profile:
        custom_action = active_profile["custom_commands"].get(name)
        if custom_action:
            action_type = custom_action.get("type")
            target = custom_action.get("target")

            if action_type == "url":
                log_message(f"🌐 Launching Custom Web Target: {target}")
                webbrowser.open(target)
                return
            elif action_type == "terminal":
                log_message(f"💻 Running Custom Shell Script: {target}")
                try:
                    subprocess.Popen(target, shell=True)
                except Exception as e:
                    log_message(f"❌ Execution Failure: {str(e)}")
                return

    log_message(f"⚠️ Unknown action string pointer: {name}")


# All active command hooks mapped out safely for the UI setup configuration context
AVAILABLE_COMMAND_HOOKS = [
    "open_chrome",
    "open_youtube",
    "open_notepad",
    "open_settings",
    "open_safari",
    "open_whatsapp_web",
    "open_excel",
    "open_photobooth",
    "open_voicememos",
    "face_on",
    "face_off",
    "camera_on",
    "camera_off"
]


@register_command("wake")
def cmd_wake():
    STATE["assistant_awake"] = True
    STATE["assistant_status"] = "Listening" # Updated visual status
    msg = "Awake and ready, I understand my purpose."
    log_message(f"🟢 {msg}")
    speak(msg)


@register_command("sleep")
def cmd_sleep():
    STATE["assistant_awake"] = False
    STATE["assistant_status"] = "Sleeping"
    log_message("😴 Nova Sleeping")
    speak("Going to sleep.")


@register_command("face_off")
def cmd_face_off():
    STATE["face_recognition_enabled"] = False
    log_message("👤 Face Detection: DISABLED")
    speak("Face tracking disabled.")


@register_command("face_on")
def cmd_face_on():
    STATE["face_recognition_enabled"] = True
    log_message("👤 Face Detection: ENABLED")
    speak("Face tracking enabled.")


@register_command("camera_off")
def cmd_camera_off():
    STATE["camera_enabled"] = False
    log_message("📷 Camera Engine: DISABLED")
    speak("Camera disabled.")


@register_command("camera_on")
def cmd_camera_on():
    STATE["camera_enabled"] = True
    log_message("📷 Camera Engine: ENABLED")
    speak("Camera enabled.")


@register_command("open_chrome")
def open_chrome():
    log_message("🌐 Opening Chrome")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Google Chrome"])


@register_command("open_notepad")
def open_notepad():
    log_message("📝 Opening Notes")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Notes"])


@register_command("open_settings")
def open_settings():
    log_message("⚙️ Opening Settings")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "System Preferences"])


@register_command("open_youtube")
def open_youtube():
    log_message("▶️ Opening YouTube in Chrome")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Google Chrome", "https://www.youtube.com"])


@register_command("open_safari")
def open_safari():
    log_message("🌐 Opening Safari browser app")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Safari"])


@register_command("open_whatsapp_web")
def open_whatsapp_web():
    log_message("💬 Opening WhatsApp Web")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Safari", "https://web.whatsapp.com"])


@register_command("open_excel")
def open_excel():
    log_message("📊 Opening Microsoft Excel")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Microsoft Excel"])


@register_command("open_photobooth")
def open_photobooth():
    log_message("📸 Opening Photo Booth")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Photo Booth"])


@register_command("open_voicememos")
def open_voicememos():
    log_message("🎙️ Opening Voice Memos")
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-a", "Voice Memos"])


# ==================================================
# UNLOCKED DYNAMIC GESTURE HANDLING FOR PROFILES
# ==================================================
def handle_gesture(gesture_id):
    global last_gesture, last_time

    # Completely blocks gesture action unless awake
    if not STATE["assistant_awake"] or gesture_id is None:
        return

    now = time.time()

    # LATCHING LOGIC: Only fire if:
    # 1. The gesture has changed
    # 2. OR the cooldown period has expired
    if gesture_id == last_gesture and (now - last_time) < GESTURE_COOLDOWN:
        return

    last_gesture = gesture_id
    last_time = now

    active_profile = PROFILES.get(STATE["active_profile_key"], DEFAULT_PROFILES["Profile 1"])
    command = active_profile["gestures"].get(gesture_id)

    # Convert pattern id to human string & strip emojis for OpenCV safety
    raw_pattern = FINGER_LABELS.get(gesture_id, gesture_id)
    clean_pattern_name = "".join(c for c in raw_pattern if ord(c) < 128).strip()

    if command:
        STATE["hover_state"] = f"{clean_pattern_name} -> {command}"
        log_message(f"🟡 HOVER: {STATE['hover_state']}")
        execute_command(command)
    else:
        # Only log 'unassigned' if it's a new state to avoid flooding the log
        if STATE["hover_state"] != f"{clean_pattern_name} -> unassigned":
            STATE["hover_state"] = f"{clean_pattern_name} -> unassigned"
            log_message(f"⚪ {STATE['hover_state']}")


# ==================================================
# GESTURE RECOGNITION (RAW PATTERN PIPELINE EXPOSED)
# ==================================================
def recognize_gesture(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb processing context
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Standard fingers loop tracking parameters
    for i in range(1, 5):
        if hand_landmarks.landmark[tips[i]].y < hand_landmarks.landmark[tips[i] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    # Returns raw string structure layout context, e.g. "01000" or "10001"
    return ''.join(map(str, fingers))


# ==================================================
# VOICE THREAD INTERFACE CONTROL
# ==================================================
def listen_to_voice():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    log_message("🎤 Voice Engine Started")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                text = recognizer.recognize_google(audio)
                lower = text.lower()
                log_message(f"🎤 Voice Heard: '{text}'")

                # Requires both words to activate
                if "nova" in lower and "awake" in lower:
                    execute_command("wake")
                    continue
                elif "go to sleep" in lower or "nova sleep" in lower:
                    execute_command("sleep")
                    continue

                if "face off" in lower or "turn off face" in lower:
                    execute_command("face_off")
                    continue
                elif "face on" in lower or "turn on face" in lower:
                    execute_command("face_on")
                    continue

                # Camera Control Triggers
                if "camera off" in lower or "turn off camera" in lower or "came off" in lower:
                    execute_command("camera_off")
                    continue
                elif "camera on" in lower or "turn on camera" in lower or "came on" in lower:
                    execute_command("camera_on")
                    continue
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception:
                pass


threading.Thread(target=listen_to_voice, daemon=True).start()


# ==================================================
# HELP PANEL (DYNAMICALLY RENDERS CUSTOM TARGETS)
# ==================================================
def draw_help_panel(frame):
    active_p = PROFILES.get(STATE["active_profile_key"], DEFAULT_PROFILES["Profile 1"])
    g_map = active_p["gestures"]

    panel = ["ACTIVE MAPS:"]
    # Look through all defined finger labels in our system config
    for pattern, label in FINGER_LABELS.items():
        cmd = g_map.get(pattern)
        if cmd: # Ensures it skips empty bindings, no floating arrows
            # Shorten name and strip emojis completely
            clean_lbl = label.split(" ")[0]
            clean_lbl = "".join(c for c in clean_lbl if ord(c) < 128).strip()
            panel.append(f"{clean_lbl} -> {cmd}")

    x, y = 15, 170
    for i, line in enumerate(panel[:8]):  # Limit overlay rows to prevent layout bleeding
        cv2.putText(frame, line, (x, y + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)


# ==================================================
# FRAME GENERATOR WITH REGULATOR THROTTLE
# ==================================================
def generate_frames():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    prev_time = time.time()
    log_message("📷 Nova AI Frame Generator Engine Active")

    while True:
        # Check if the camera should output placeholder blank frames instead
        if not STATE.get("camera_enabled", True):
            import numpy as np
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(frame, "CAMERA FEED DISABLED", (440, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        else:
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            hand_results = hands.process(rgb)
            if hand_results.multi_hand_landmarks:
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    gesture_pattern = recognize_gesture(hand_landmarks)
                    handle_gesture(gesture_pattern)

                    h, w, _ = frame.shape
                    x = int(hand_landmarks.landmark[0].x * w)
                    y = int(hand_landmarks.landmark[0].y * h)

                    # Strip emojis so OpenCV text rendering doesn't print "???"
                    readable_label = FINGER_LABELS.get(gesture_pattern, "Unrecognized")
                    clean_readable_label = "".join(c for c in readable_label if ord(c) < 128).strip()
                    cv2.putText(frame, clean_readable_label, (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if STATE["face_recognition_enabled"]:
                face_results = face_detection.process(rgb)
                if face_results.detections:
                    for detection in face_results.detections:
                        mp_draw.draw_detection(frame, detection)
                        bboxC = detection.location_data.relative_bounding_box
                        ih, iw, _ = frame.shape
                        x_face = int(bboxC.xmin * iw)
                        y_face = int(bboxC.ymin * ih)
                        cv2.putText(frame, f"User: {STATE['current_user']}", (x_face, y_face - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        current_time = time.time()
        fps = int(1 / (current_time - prev_time))
        prev_time = current_time

        cv2.putText(frame, f"FPS: {fps}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Status: {STATE['assistant_status']}", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0),
                    2)

        hover_display = STATE["hover_state"] if STATE["hover_state"] else "None"
        cv2.putText(frame, f"HOVER: {hover_display}", (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)

        face_status_text = "Active" if STATE["face_recognition_enabled"] else "Disabled"
        cv2.putText(frame, f"Face Engine: {face_status_text}", (15, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2)
        cv2.putText(frame, f"Active Profile: {STATE['current_user']}", (15, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255), 2)

        draw_help_panel(frame)
        time.sleep(0.01)  # Regulator throttle
        yield frame

    cap.release()