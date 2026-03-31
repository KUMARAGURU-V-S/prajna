import os
import wave
import time
import numpy as np
import sounddevice as sd
import webrtcvad
from openwakeword.model import Model

# Audio parameters (16kHz, 1-channel, 16-bit)
RATE = 16000
CHANNELS = 1
CHUNK_DURATION_MS = 30  # WebRTC VAD requires 10, 20, or 30ms
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
WAKE_WORD_THRESHOLD = 0.5
SILENCE_DURATION = 1.5  # Seconds of silence before stopping VAD
MAX_RECORDING_DURATION = 10  # Maximum length of a command in seconds

VAD_MODE = 3  # 0 to 3 (most aggressive)
TMP_WAV_PATH = "/tmp/prajna_input.wav"

def save_wav(audio_data, path):
    """Save raw audio chunks to a WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(b"".join(audio_data))

def listen():
    print("Loading wake word model...")
    # Using 'hey_jarvis' as the default proxy for Prajna for now
    import openwakeword
    model_paths = [m for m in openwakeword.get_pretrained_model_paths() if "hey_jarvis" in m]
    oww_model = Model(wakeword_model_paths=model_paths)
    vad = webrtcvad.Vad(VAD_MODE)
    
    print("प्रज्ञा (Prajñā) is listening...")
    
    stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16', blocksize=CHUNK_SIZE)
    stream.start()
    
    listening_for_wake_word = True
    vad_buffer = []
    silence_frames = 0
    max_silence_frames = int((SILENCE_DURATION * 1000) / CHUNK_DURATION_MS)
    max_recording_frames = int((MAX_RECORDING_DURATION * 1000) / CHUNK_DURATION_MS)
    
    try:
        while True:
            chunk, _ = stream.read(CHUNK_SIZE)
            # audio_data = np.frombuffer(chunk, dtype=np.int16)
            audio_data = chunk.flatten() # sounddevice already gives you a numpy array
            
            if listening_for_wake_word:
                # OpenWakeWord expects 1280 samples (80ms), but we're feeding 30ms.
                # OWW buffers internally if fed smaller chunks, so this is fine.
                prediction = oww_model.predict(audio_data)
                
                # Check for detection
                for md, score in prediction.items():
                    if score > WAKE_WORD_THRESHOLD:
                        print(f"\n[SENTRY] Wake word detected! (score: {score:.2f})")
                        listening_for_wake_word = False
                        vad_buffer = []  # Start fresh for command
                        silence_frames = 0
                        recording_frames = 0
                        print("[SENTRY] Recording command...")
                        break
                        
            else:
                # VAD Phase: Record until silence
                vad_buffer.append(chunk)
                raw_bytes = audio_data.tobytes()
                recording_frames += 1
                
                is_speech = vad.is_speech(raw_bytes, RATE)
                
                # Simple static gate: ignore noise if RMS energy is very low
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                if rms < 250:
                    is_speech = False
                
                if not is_speech:
                    silence_frames += 1
                else:
                    silence_frames = 0
                    
                if silence_frames > max_silence_frames or recording_frames > max_recording_frames:
                    if silence_frames > max_silence_frames:
                        print("[SENTRY] Silence detected. Stopping recording.")
                    else:
                        print(f"[SENTRY] Max recording duration ({MAX_RECORDING_DURATION}s) reached. Stopping recording.")
                    stream.stop()
                    
                    # Save the buffer
                    save_wav(vad_buffer, TMP_WAV_PATH)
                    print(f"[SENTRY] Command saved to {TMP_WAV_PATH}")
                    
                    # ---- Pass to Intellect ----
                    import intellect
                    import action
                    
                    print("[SENTRY] Handing off to Intellect (Whisper)...")
                    transcript = intellect.transcribe(TMP_WAV_PATH)
                    
                    if transcript:
                        print(f"[INTELLECT] Transcript: '{transcript}'")
                        print("[SENTRY] Handing off to Action parser...")
                        response = action.dispatch(transcript)
                        print(f"[ACTION] {response}")
                    else:
                        print("[INTELLECT] No transcription received.")
                    
                    # Reset state
                    print("\nप्रज्ञा (Prajñā) is listening...")
                    listening_for_wake_word = True
                    stream.start()

    except KeyboardInterrupt:
        print("\nStopping Sentry.")
    finally:
        stream.stop()
        stream.close()

if __name__ == "__main__":
    listen()
