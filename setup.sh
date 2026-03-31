#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "    Prajna (प्रज्ञा) Voice Assistant Setup   "
echo "=========================================="

echo " [1/5] Installing OS-level Dependencies..."
# Install packages via pacman. Requires sudo.
sudo pacman -S --needed --noconfirm alsa-utils portaudio onnxruntime make gcc git

echo " [2/5] Setting up Python Virtual Environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo " [3/5] Compiling Whisper.cpp Transcription Engine (Locally)..."
if [ ! -d "whisper.cpp" ]; then
    git clone https://github.com/ggerganov/whisper.cpp.git
fi
cd whisper.cpp
make -j$(nproc)

echo " [4/5] Downloading Whisper language model (base.en)..."
bash ./models/download-ggml-model.sh base.en
cd ..

echo " [5/5] Configuring Systemd Background Service..."
mkdir -p ~/.config/systemd/user
# Ensure absolute paths in the actual run directory
sed "s|/mnt/linux_d_drive/prajna|$(pwd)|g" prajna.service > ~/.config/systemd/user/prajna.service
systemctl --user daemon-reload
systemctl --user enable prajna.service
systemctl --user restart prajna.service

echo "=========================================="
echo " ✅ Setup Complete! Prajna is now running."
echo " To monitor logs: journalctl --user -u prajna.service -f"
echo "=========================================="
