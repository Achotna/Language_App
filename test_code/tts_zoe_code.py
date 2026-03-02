import os
import pandas as pd
from sqlalchemy import create_engine
from google.cloud import texttospeech
from pydub import AudioSegment
import sqlite3
import main
from pydub.generators import Sine


# ============================
# Google Text-to-Speech Setup
# ============================

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "D:\\Projects\\Language app\\tts_service_account.json"
)

client = texttospeech.TextToSpeechClient()


# ============================
# Dossiers pour stockage audio
# ============================

BASE_DIR = "audio"
WORDS_DIR = f"{BASE_DIR}/words"
TRANS_DIR = f"{BASE_DIR}/translations"
SILENCE_DIR = f"{BASE_DIR}/silence"
FINAL_DIR = f"{BASE_DIR}/final"

for d in [WORDS_DIR, TRANS_DIR, SILENCE_DIR, FINAL_DIR]:
    os.makedirs(d, exist_ok=True)


# ======================================
# Fonction générique Text-to-Speech
# ======================================

def text_to_speech(
    text: str,
    output_file: str,
    language_code: str,
    voice_name: str
):
    if not text.strip():
        raise ValueError("Input text is empty.")

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(output_file, "wb") as out:
        out.write(response.audio_content)


# ============================
# Dictionnaire des voix
# ============================

VOICES = {
    "cmn-CN": {
        "female": "cmn-TW-Standard-A",
        "male": "cmn-CN-Wavenet-B"
    },
    "en-GB": {
        "female": "en-GB-Chirp3-HD-Leda",
        "male": "en-GB-Chirp3-HD-Alnilam"
    },
    "fr-FR": {
        "female": "fr-FR-Chirp-HD-O",
        "male": "fr-FR-Chirp3-HD-Algenib"
    },
    "es-ES": {
        "female": "es-ES-Chirp-HD-F",
        "male": "es-ES-Chirp-HD-D"
    }
}


# ============================
# Génération du silence
# ============================

def generate_silence(duration_seconds: float) -> str:
    filename = f"{SILENCE_DIR}/{duration_seconds:.1f}s.wav"

    if os.path.exists(filename):
        return filename

    silence = AudioSegment.silent(
        duration=int(duration_seconds * 1000)
    )

    silence.export(filename, format="wav")
    return filename


# ============================
# Assemblage des audios
# ============================

def concatenate_audios(audio_files, output_file):
    final_audio = AudioSegment.empty()

    for file in audio_files:
        final_audio += AudioSegment.from_wav(file)

    final_audio.export(output_file, format="wav")


# ============================
# Génération audio pour une entrée
# ============================

def generate_audio_for_entry(
    entry,
    delay_seconds,
    target_lang,
    translation_lang,
    target_gender,
    translation_gender,
    index
):
    word = entry["word"]
    translation = entry["translation"]

    target_voice_name = VOICES[target_lang][target_gender]
    translation_voice_name = VOICES[translation_lang][translation_gender]

    target_file = (
        f"{WORDS_DIR}/{index}_{target_lang}_{target_gender}.wav"
    )

    translation_file = (
        f"{TRANS_DIR}/{index}_{translation_lang}_{translation_gender}.wav"
    )

    final_file = (
        f"{FINAL_DIR}/"
        f"{index}_"
        f"{target_lang}_{target_gender}_"
        f"{translation_lang}_{translation_gender}_"
        f"{delay_seconds}.wav"
    )

    if os.path.exists(final_file):
        return final_file

    if not os.path.exists(target_file):
        text_to_speech(
            word,
            target_file,
            target_lang,
            target_voice_name
        )

    if not os.path.exists(translation_file):
        text_to_speech(
            translation,
            translation_file,
            translation_lang,
            translation_voice_name
        )

    silence_file = generate_silence(delay_seconds)

    concatenate_audios(
        [target_file, silence_file, translation_file],
        final_file
    )

    return final_file


# ============================
# Configuration utilisateur
# ============================

USER_CONFIG = {
    "target_lang": "cmn-CN",
    "translation_lang": "en-GB",
    "target_gender": "female",
    "translation_gender": "male",
    "delay_seconds": 2.0
}


# ============================
# Récupération des données BDD
# ============================

df = pd.read_sql(
    "SELECT english AS word, french AS translation "
    "FROM vocab WHERE status=1",
    main.engine
)


# ============================
# Génération audio complet
# ============================

final_audio_all = AudioSegment.empty()
bip = Sine(1000).to_audio_segment(duration=300)

for i, (index, row) in enumerate(df.iterrows()):
    word = row["word"]
    translation = row["translation"]

    final_audio_path = generate_audio_for_entry(
        entry={
            "word": word,
            "translation": translation
        },
        delay_seconds=USER_CONFIG["delay_seconds"],
        target_lang=USER_CONFIG["target_lang"],
        translation_lang=USER_CONFIG["translation_lang"],
        target_gender=USER_CONFIG["target_gender"],
        translation_gender=USER_CONFIG["translation_gender"],
        index=index + 1
    )

    final_audio_all += AudioSegment.from_wav(final_audio_path)

    if i < len(df) - 1:
        final_audio_all += bip


final_audio_all.export(
    f"{FINAL_DIR}/final_output.mp3",
    format="mp3"
)


