
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import wave
import json
import torch
from vosk import Model, KaldiRecognizer
from transformers import MarianMTModel, MarianTokenizer
from TTS.api import TTS

app = Flask(__name__)
CORS(app)

# Paths
VOSK_MODELS = {
    "en": "backend/models/vosk-model-en-us-0.22/vosk-model-en-us-0.22",
    "hi": "backend/models/vosk-model-hi-0.22/vosk-model-hi-0.22",
    "te": "backend/models/vosk-model-small-te-0.42/vosk-model-small-te-0.42"
}
TEMP_AUDIO_PATH = "backend/temp/input_audio.wav"
TTS_OUTPUT_PATH = "backend/static/translated_speech.wav"

# Load ASR Models
asr_models = {lang: Model(path) for lang, path in VOSK_MODELS.items()}

# Load Translation Models (Offline Paths)
LOCAL_TRANSLATION_MODELS = {
    "en-hi": "backend/models/opus-mt-en-hi",
    "hi-en": "backend/models/opus-mt-hi-en",
    "en-te": "backend/models/opus-mt-en-tl",
    "te-en": "backend/models/opus-mt-tl-en"
}

translator = {pair: MarianMTModel.from_pretrained(path) for pair, path in LOCAL_TRANSLATION_MODELS.items()}
tokenizer = {pair: MarianTokenizer.from_pretrained(path) for pair, path in LOCAL_TRANSLATION_MODELS.items()}

# Placeholder for Fine-Tuned Hindi-Telugu Model
def translate_hi_te_te_hi(text, lang_pair):
    """Temporary placeholder for direct Hindi-Telugu translation until fine-tuned model is ready."""
    return "Translation not available"

# Load TTS Model
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC").to("cpu")

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech to text using Vosk ASR."""
    if 'audio' not in request.files or 'language' not in request.form:
        return jsonify({"error": "Missing audio file or language parameter"}), 400
    
    audio_file = request.files['audio']
    lang = request.form['language']
    if lang not in asr_models:
        return jsonify({"error": "Unsupported language"}), 400
    
    audio_file.save(TEMP_AUDIO_PATH)
    wf = wave.open(TEMP_AUDIO_PATH, "rb")
    rec = KaldiRecognizer(asr_models[lang], wf.getframerate())
    rec.SetWords(True)
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    
    result = json.loads(rec.Result())["text"]
    return jsonify({"text": result})

@app.route('/translate', methods=['POST'])
def translate_text():
    """Translate text dynamically based on language pair."""
    data = request.json
    input_text = data.get("text", "")
    lang_pair = data.get("lang_pair", "")

    # Handle Hindi-Telugu cases separately (Placeholder)
    if lang_pair in ["hi-te", "te-hi"]:
        translated_text = translate_hi_te_te_hi(input_text, lang_pair)
    elif lang_pair in LOCAL_TRANSLATION_MODELS:
        inputs = tokenizer[lang_pair](input_text, return_tensors="pt", padding=True, truncation=True)
        translated_ids = translator[lang_pair].generate(**inputs)
        translated_text = tokenizer[lang_pair].batch_decode(translated_ids, skip_special_tokens=True)[0]
    else:
        return jsonify({"error": "Unsupported language pair"}), 400

    return jsonify({"translated_text": translated_text})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert translated text to speech."""
    data = request.json
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    tts.tts_to_file(text=text, file_path=TTS_OUTPUT_PATH)
    return send_file(TTS_OUTPUT_PATH, as_attachment=True, mimetype='audio/wav')

@app.route('/real-time-translate', methods=['POST'])
def real_time_translate():
    """Real-time speech-to-text, translation, and text-to-speech."""
    if 'audio' not in request.files or 'source_lang' not in request.form or 'target_lang' not in request.form:
        return jsonify({"error": "Missing audio file or language parameters"}), 400
    
    audio_file = request.files['audio']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    lang_pair = f"{source_lang}-{target_lang}"

    if source_lang not in asr_models:
        return jsonify({"error": "Unsupported source language"}), 400

    audio_file.save(TEMP_AUDIO_PATH)
    wf = wave.open(TEMP_AUDIO_PATH, "rb")
    rec = KaldiRecognizer(asr_models[source_lang], wf.getframerate())
    rec.SetWords(True)
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    
    text_result = json.loads(rec.Result())["text"]

    # Handle Hindi-Telugu cases separately (Placeholder)
    if lang_pair in ["hi-te", "te-hi"]:
        translated_text = translate_hi_te_te_hi(text_result, lang_pair)
    elif lang_pair in LOCAL_TRANSLATION_MODELS:
        inputs = tokenizer[lang_pair](text_result, return_tensors="pt", padding=True, truncation=True)
        translated_ids = translator[lang_pair].generate(**inputs)
        translated_text = tokenizer[lang_pair].batch_decode(translated_ids, skip_special_tokens=True)[0]
    else:
        return jsonify({"error": "Unsupported translation pair"}), 400

    tts.tts_to_file(text=translated_text, file_path=TTS_OUTPUT_PATH)

    return jsonify({
        "original_text": text_result,
        "translated_text": translated_text,
        "audio_url": TTS_OUTPUT_PATH
    })

if __name__ == "__main__":
    app.run(debug=True)


