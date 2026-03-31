import os
import subprocess
import tempfile
from pathlib import Path

# Paths depending on how whisper.cpp is installed (yay package or built locally)
# The yay package uses "whisper-cli" or "whisper". We try both.
POSSIBLE_BINARIES = ["whisper-cli", "whisper", "./whisper.cpp/main", "./whisper.cpp/build/bin/whisper-cli"]

# Model paths
# The AUR package installs to /usr/share/whisper-cpp/models/
POSSIBLE_MODELS = [
    "/usr/share/whisper-cpp/models/ggml-base.en.bin",
    "ggml-base.en.bin",
    "./whisper.cpp/models/ggml-base.en.bin"
]

def find_binary():
    import shutil
    for config in POSSIBLE_BINARIES:
        if config.startswith("./"):
            if os.path.exists(config):
                return config
        else:
            path = shutil.which(config)
            if path:
                return path
    return None

def find_model():
    for m in POSSIBLE_MODELS:
        if os.path.exists(m):
            return m
    return None

def transcribe(wav_path: str) -> str:
    """Takes a 16kHz WAV file and returns transcribed text via Whisper."""
    whisper_bin = find_binary()
    model_path = find_model()

    if not whisper_bin:
        print("[INTELLECT] Error: Whisper binary not found.")
        return ""
    if not model_path:
        print("[INTELLECT] Error: Whisper model not found. (Download it first)")
        return ""

    # Run whisper-cpp
    # -nt: no timestamps
    # -f: audio file
    # -m: model
    # -f <file> will write to <file>.txt if --output-txt is passed, but whisper-cli 
    # typically outputs to stdout by default, so we capture stdout.
    cmd = [
        whisper_bin,
        "-m", model_path,
        "-f", wav_path,
        "-nt"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse output for actual text (whisper prints some debug to stderr, but wait: 
        # normally main prints debug to stderr and transcript to stdout)
        stdout = result.stdout.strip()
        # Some whisper builds put transcripts inside brackets like [00:00:00.000 -> 00:00:02.000] Hello.
        # But with -nt, it just prints the text.
        return stdout
    except subprocess.CalledProcessError as e:
        print(f"[INTELLECT] Whisper failed with error: {e.stderr}")
        return ""
