
import os
import pandas as pd
from sqlalchemy import create_engine
from google.cloud import texttospeech
from pydub import AudioSegment


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


text_block= '''世界再见'''

synthesis_input = texttospeech.SynthesisInput(text=text_block)

voice = texttospeech.VoiceSelectionParams(
    language_code="zh-CN",
    name='cmn-TW-Standard-A'
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    effects_profile_id=['small-bluetooth-speaker-class-device'],
    speaking_rate=1, 
    pitch=1
)
    
response = client.synthesize_speech(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config
)

with open("output.mp3", "wb") as output:
    output.write(response.audio_content)
    print('Audio content written to file "output.mp3"')  
