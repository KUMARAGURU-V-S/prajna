import os
import sys
import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model

RATE = 16000
CHUNK_SIZE = 1280  # Ideal chunk size for openwakeword

def main():
    print("=== Sound Device Information ===")
    print(sd.query_devices())
    print(f"Default input device: {sd.default.device[0]}\n")
    
    print("Loading 'hey_jarvis' wake word model...")
    model_paths = [m for m in openwakeword.get_pretrained_model_paths() if "hey_jarvis" in m]
    oww_model = Model(wakeword_model_paths=model_paths)
    
    print("\n✅ Setup complete! Microphone is open.")
    print("🎙️ Please say 'Hey Jarvis'.")
    print("(Press Ctrl+C to stop)\n")

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
            
        audio_data = indata.flatten()
        prediction = oww_model.predict(audio_data)
        
        # Check scores
        for md, score in prediction.items():
            if score > 0.5:
                print(f"\n🚀 WAKE WORD DETECTED! (Score: {score:.3f})")
            elif score > 0.05:
                # To show it's somewhat hearing something resembling the word
                print(f"  [Hearing something... score: {score:.3f}]")

    # Start the continuous microphone stream
    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype='int16', 
                           blocksize=CHUNK_SIZE, callback=audio_callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nTest stopped by user.")

if __name__ == "__main__":
    main()
