# 🤖 Nova Assistant

> **Nova Assistant** is an AI-powered desktop assistant built with **Flask**, **OpenCV**, **MediaPipe**, and **Speech Recognition**. It combines computer vision, voice commands, and gesture recognition to provide a natural, hands-free interaction experience.

---

# ✨ Features

- 🎙️ Voice Command Recognition
- ✋ Real-time Hand Gesture Recognition
- 👤 Face Detection
- 📷 Live Camera Streaming
- 🧠 Multi-Profile Gesture Mapping
- 🌐 Launch Websites via Gestures
- 💻 Execute Custom Terminal Commands
- ⚙️ Camera & Face Detection Toggle
- 🔊 Text-to-Speech Assistant
- 📊 Live FPS Monitoring
- 📝 Activity & System Logs

---

# 🛠️ Technologies Used

| Technology | Description |
|------------|-------------|
| Python 3.10 | Programming Language |
| Flask | Web Framework |
| OpenCV | Computer Vision |
| MediaPipe | Hand & Face Detection |
| SpeechRecognition | Voice Recognition |
| PyAudio | Microphone Input |
| NumPy | Image Processing |
| HTML5 | Frontend |
| CSS3 | Styling |
| JavaScript | Client Interaction |

---

# 🚀 Getting Started

## 1️⃣ Prerequisites

Make sure you have installed:

- **Python 3.10.x**

Check your version:

```bash
python --version
```

Expected output:

```text
Python 3.10.x
```

---

## 2️⃣ Clone Repository

```bash
git clone https://github.com/Mimi83982/Nova_Assistant.git

cd Nova_Assistant
```

---

## 3️⃣ Create Virtual Environment

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
.\venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

If the `requirements.txt` file is missing, generate it using:

```bash
pip freeze > requirements.txt
```

---

## 5️⃣ Run the Application

Start Nova Assistant:

```bash
python app.py
```

The application will be available at:

```
http://127.0.0.1:5000
```

---

# 📂 Project Structure

```text
Nova-Assistant/
│
├── app.py
├── engine.py
├── requirements.txt
├── profiles.json
└── README.md
```

---

# 🎙️ Voice Commands

| Command | Action |
|----------|--------|
| Nova Awake | Wake Assistant |
| Nova Sleep | Put Assistant to Sleep |
| Face On | Enable Face Detection |
| Face Off | Disable Face Detection |
| Camera On | Enable Camera |
| Camera Off | Disable Camera |

---

# ✋ Default Gesture Mapping

| Gesture | Pattern | Action |
|----------|----------|--------|
| ☝️ Index | `01000` | Open Safari |
| ✌️ Peace | `01100` | Open WhatsApp Web |
| 👌 Three | `01110` | Open Microsoft Excel |
| ✋ Four | `01111` | Open Photo Booth |
| 🖐️ Palm | `11111` | Open Voice Memos |
| 👍 Thumbs Up | `10000` | Customizable |
| 🤙 Shaka | `10001` | Customizable |
| 🤘 Rock On | `01001` | Customizable |
| ✊ Fist | `00000` | Customizable |

---

# 👤 Multi-Profile Support

Nova Assistant supports multiple user profiles.

Each profile stores:

- User Name
- Gesture Mapping
- Custom Commands
- Custom URLs
- Terminal Commands

Configuration is automatically saved in:

```text
profiles.json
```

---

# 🌐 Supported Built-in Commands

- Open Safari
- Open Chrome
- Open YouTube
- Open WhatsApp Web
- Open Microsoft Excel
- Open Notes
- Open Settings
- Open Photo Booth
- Open Voice Memos
- Camera Control
- Face Detection Control

---

# 📸 Computer Vision Features

- Real-time Hand Tracking
- Finger State Recognition
- Gesture Recognition
- Face Detection
- FPS Counter
- Live Camera Feed
- Gesture Overlay
- Active Command Display

---

# 🎯 System Requirements

- Python 3.10.x
- Webcam
- Microphone
- macOS (Optimized)

Required Python packages include:

- Flask
- OpenCV
- MediaPipe
- NumPy
- SpeechRecognition
- PyAudio

Install them via:

```bash
pip install -r requirements.txt
```

---

# 📝 Notes

- Always activate the virtual environment before running the application.
- Make sure your webcam and microphone are connected.
- Grant camera and microphone permissions to your operating system if prompted.
- Some built-in commands (such as Safari, Photo Booth, Voice Memos, and System Preferences) are specifically designed for **macOS**.

---

# 👨‍💻 Author

Developed as an intelligent desktop assistant integrating **Computer Vision**, **Speech Recognition**, and **Gesture-Based Human-Computer Interaction** using Python and Flask.

---

# 📄 License

This project is intended for educational, research, and personal development purposes.
