import os
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer

# Path to your Vosk model (change the path accordingly)
model_path = "models/vosk-model-en-us-0.22/vosk-model-en-us-0.22"

# Load model
if not os.path.exists(model_path):
    print("Model not found! Check the path.")
    exit(1)

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)
audio_queue = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    audio_queue.put(bytes(indata))

# Start Recording
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                        channels=1, callback=callback):
    print("🎤 Speak now...")
    while True:
        data = audio_queue.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            print("Recognized:", result["text"])

