# Prajna Voice Assistant (प्रज्ञा)

Prajna (प्रज्ञा) is a lightweight, privacy-focused, and fully offline voice assistant designed for Linux environments. It runs persistently as a systemd background service, listens for a customizable wake word, transcribes audio locally using Whisper.cpp, and executes system commands seamlessly.

## 🌟 Key Features

* **100% Offline & Private:** Wake word detection and speech-to-text processing happen entirely on-device. No audio is ever sent to the cloud.
* **Low Resource Footprint:** Designed to run efficiently in the background, capable of being pinned to specific E-cores using Systemd to save battery on modern processors.
* **Robust Wake Word Detection:** Powered by `OpenWakeWord` and optimized with `ONNXRuntime`.
* **Smart Voice Activity Detection (VAD):** Employs `webrtcvad` intertwined with local RMS noise gating and safe-duration fallbacks to cleanly capture speech even in noisy ambient environments.
* **Extensible Action Engine:** Easily map natural language commands to scripts, system UI notifications (`notify-send`), and application launches.

## 🏗️ System Architecture

Prajna is structured sequentially over a robust pipeline of decoupled modules:

### 1. `prajna_assistant.py` (The Daemon)
The core entry point that binds the modules together. It is built to be run as a standard systemd user service (`prajna.service`), ensuring it survives terminal closures, hooks into exactly the right PulseAudio/PipeWire sockets (`DISPLAY=:0`, `DBUS_SESSION_BUS_ADDRESS`), and starts silently on boot.

### 2. `sentry.py` (The Ears)
Handles the continuous 16kHz audio stream from the microphone using `sounddevice`.
* Uses `OpenWakeWord` configured for raw `.onnx` model inference to detect the wake keyword (default: *"Hey Jarvis"*).
* Once triggered, it activates a high-aggressiveness WebRTC VAD to isolate human speech from room noise, safely buffering the command to `/tmp/prajna_input.wav`.
* Includes anti-lockout mechanisms (10s max duration limit) to prevent the microphone from being infinitely held open by ambient hums.

### 3. `intellect.py` (The Brain)
Responsible for transcription. Intellect interfaces dynamically with a locally compiled `whisper.cpp` engine. It processes the buffered `.wav` file through the `ggml-base.en.bin` model, rapidly extracting textual commands.

### 4. `action.py` (The Hands)
Acts as the command router. It parses the final string transcript using Regex and maps intents to python behaviors.
* **Reminders:** Launches detached `nohup` bash scripts that trigger delayed `notify-send` desktop popups.
* **Time Inquiries:** Uses the native `datetime` module to fetch and broadcast the current time.
* **Application Launching:** Gracefully handles `subprocess.Popen` to open desktop apps like Firefox, wrapped in robust fallbacks to prevent crashes on mistranscriptions.

## 🚀 Setup & Installation

### Quick Automated Installation
The easiest way to initialize Prajna on an Arch Linux environment is by running the packaged setup script. It automatically triggers `pacman` for native dependencies, builds the isolated Python environment using `requirements.txt`, gracefully compiles `whisper.cpp` locally, and sets up your systemd service.

```bash
chmod +x setup.sh
./setup.sh
```

---

### Alternative (Manual) Installation

#### 1. System Dependencies
You'll need `alsa-utils`, `portaudio`, and `onnxruntime` installed on your system.
```bash
sudo pacman -S alsa-utils portaudio onnxruntime make gcc git
```

#### 2. Python Virtual Environment
Prajna uses an isolated Python environment to prevent conflicts, bypassing the system's broken tensorflow-lite packages by strictly calling ONNX models for wake word support.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Whisper.cpp Setup
The STT engine is built directly inside the project directory to map strictly to your local CPU architecture for maximum processing speed:
```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make -j$(nproc)
bash ./models/download-ggml-model.sh base.en
```

#### 4. Systemd Service
To ensure Prajna runs entirely in the background, a `prajna.service` unit is placed in `~/.config/systemd/user/`.

Enable and start the daemon:
```bash
systemctl --user daemon-reload
systemctl --user enable prajna.service
systemctl --user start prajna.service
```

*(Note: Adding `Environment=PYTHONUNBUFFERED=1` inside the systemd service ensures you can view logs in real time).*

## 🛠️ Usage & Debugging

Prajna runs invisibly. To trigger it, simply say **"Hey Jarvis"** followed by a command like `"What time is it?"` or `"Launch Firefox."`

If you are expanding action capabilities or troubleshooting, monitor the assistant's live thought process and transcription logs via:
```bash
journalctl --user -u prajna.service -f
```

## 🔮 Future Roadmap 

* **Generative AI Pass-through:** Forward fallback commands (where an explicit regex match isn't found) to a local LLM infrastructure (like Ollama, Llama.cpp) to enable conversational chat responses.
* **Text-To-Speech (TTS):** Integrate a lightweight local text-to-speech engine (e.g. `piper-tts` or `espeak`) to allow Prajna to speak back out loud rather than relying solely on desktop notifications.
* **Dynamic Wake Words:** Switch the model configuration dynamically to support multiple users or personalized wake words without manually patching standard `.onnx` files.
