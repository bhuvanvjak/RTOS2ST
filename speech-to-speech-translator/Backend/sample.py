import numpy as np
import scipy.io.wavfile as wav

# Parameters
sample_rate = 44100  # Samples per second
duration = 2  # seconds
frequency = 440.0  # Frequency of the sine wave (Hz)

# Generate time values
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Generate sine wave
audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

# Save as .wav file
wav.write("hello-46355.wav", sample_rate, audio_data)

print("sample.wav file generated successfully!")
