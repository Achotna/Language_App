import os
import pandas as pd
from sqlalchemy import create_engine
from google.cloud import texttospeech
from pydub import AudioSegment
import sqlite3
import main

#Google Text to Speech API setup

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:\\Projects\\Language app\\tts_service_account.json"
client = texttospeech.TextToSpeechClient()

#Files for audio storage

BASE_DIR = "audio" 
WORDS_DIR = f"{BASE_DIR}/words"
TRANS_DIR = f"{BASE_DIR}/translations"
SILENCE_DIR = f"{BASE_DIR}/silence" #delay between words, dépend du choix de l'utilisateur
FINAL_DIR = f"{BASE_DIR}/final" #audios complets, fournis à l'utilisateur

for d in [WORDS_DIR, TRANS_DIR, SILENCE_DIR, FINAL_DIR]:
    os.makedirs(d, exist_ok=True) #pour ne pas avoir d'erreur si le dossier existe déjà 


#-------------Fonction générique !!! (╹ڡ╹ )-------------

def text_to_speech(
    text: str,
    output_file: str,
    language_code: str,
    voice_name: str
): 
    if not text.strip():
        raise ValueError("Input text is empty.") #Vérifie que le texte ne soit pas vide, strip machin enlève les espaces /!\ même les espaces comptent comme des caractères dans le quota de l'API /!\
    
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16 #format WAV pour pouvoir utiliser pydub 
    )
    
    #Appel à l'API Google TTS 
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    #Sauvegarde du fichier audio
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        #print(f'Audio content written to file "{output_file}"')
    
#-------------Choix des voix !! (Anglais et Chinois, voix F/M pour chaque)-------------
#J'ai mis British Eng mais on peut changer => Documentation : https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types?hl=fr#standard_voices

VOICES = {
    "en": {
        "female": {
            "lang": "en-GB",
            "name": "en-GB-Chirp3-HD-Leda" 
        }, 
        "male": {
            "lang": "en-GB",
            "name": "en-GB-Chirp3-HD-Alnilam"
        }
    },
        
    "zh": {
        "female": {
            "lang": "cmn-CN",
            "name": "cmn-TW-Standard-A"
        },
        "male": {
            "lang": "cmn-CN",
            "name": "cmn-CN-Wavenet-B"
        }
    }
}

#-------------Génération temps d'attente entre mot/traduction-------------

def generate_silence(duration_seconds: float) -> str: 

    filename = f"{SILENCE_DIR}/{duration_seconds:.1f}s.wav"

    if os.path.exists(filename):
        return filename  # Si le fichier avec le silence de cette durée existe déjà, le réutilise

    silence = AudioSegment.silent(
        duration=int(duration_seconds * 1000) #Parce que pydub utilise des millisecondes
    )  

    silence.export(filename, format="wav")

    return filename

#-------------Assemblage du mot -> temps d'attente -> traduction-------------

def concatenate_audios(audio_files, output_file):
    final_audio = AudioSegment.empty()

    for file in audio_files:
        final_audio += AudioSegment.from_wav(file)

    final_audio.export(output_file, format="wav")  #Peut-être changer en mp3 si besoin

#-------------Pour un seul mot !-------------
#/!\ Sûrement à modifier pour l'adapter à la base de données (￣┰￣*) /!\
#Exemple entry : 
"""
entry = {
    "chinese": "世界再见",
    "translation": "hao ref"
}
"""

def generate_audio_for_entry(entry, delay_seconds, zh_gender, en_gender, index): 

    word = entry["chinese"]
    translation = entry["translation"]

    zh_voice = VOICES["zh"][zh_gender]
    en_voice = VOICES["en"][en_gender]

    zh_file = f"{WORDS_DIR}/{index}_zh.wav"
    en_file = f"{TRANS_DIR}/{index}_en.wav"
    final_file = f"{FINAL_DIR}/{index}.wav"

    #Chinese
    if not os.path.exists(zh_file):
        text_to_speech(
            word, 
            zh_file,
            zh_voice["lang"],
            zh_voice["name"]
        )

    #English
    if not os.path.exists(en_file):
        text_to_speech(
            translation, 
            en_file,
            en_voice["lang"],
            en_voice["name"]
        )

    #Silence
    silence_file = generate_silence(delay_seconds)

    concatenate_audios(
        [zh_file, silence_file, en_file],
        final_file  
    )

    return final_file

#-------------Génération de l'audio pour toute la BDD-------------
#Partie non terminée ! (* ￣︿￣)

#Paramètres utilisateur (à récupérer via l'interface web plus tard)
USER_DELAY = 2.0 #secondes de pause entre mot et traduction, faire en sorte que l'utilisateur puisse choisir -> Eventuellement avec un slider
USER_ZH_GENDER = "female" #ou "male"
USER_EN_GENDER = "male"

#Récupération des données depuis la BDD
df = pd.read_sql("SELECT english AS word, french AS translation FROM vocab", main.engine)

#Génération audios complets pour chaque entrée => à adapter pour la BDD
final_audio_all = AudioSegment.empty()

for index, row in df.iterrows():
    chinese_word = row["word"]  
    english_word = row["translation"]  

    #Audio pour une ligne
    final_audio_path = generate_audio_for_entry(
        entry={
            "chinese": chinese_word,
            "translation": english_word
        }, 
        delay_seconds=USER_DELAY,
        zh_gender=USER_ZH_GENDER,
        en_gender=USER_EN_GENDER,
        index=index + 1
    )

    #Ajout du segment mot à l'audio final
    final_audio_all += AudioSegment.from_wav(final_audio_path)

#Export de l'audio final complet
final_audio_all.export(
    f"{FINAL_DIR}/final_output.wav", 
    format="wav"
)