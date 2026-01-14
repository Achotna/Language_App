from flask import Flask, render_template, request, url_for, redirect
from flask_dropzone import Dropzone
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
import tts_zoe_code


#SETUP
app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER="uploads/",
    #only excel files DROPZONE_ALLOWED_FILE_TYPE="xls,xlsx", 
    DROPZONE_MAX_FILE_SIZE=1024,  # MB
)
dropzone = Dropzone(app)

###################################################################################################
#ZOE

import os
import pandas as pd
from sqlalchemy import create_engine
from google.cloud import texttospeech
from pydub import AudioSegment
import sqlite3

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


##############################################################################################################"



engine = create_engine("sqlite:///./vocab.db")

@app.route("/",methods=["GET", "POST"])
def home():

    rows=None

    #initialize database
    conn = sqlite3.connect("vocab.db")
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocab (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english TEXT NOT NULL,
                french TEXT NOT NULL,
                status INTEGER
            )
            """)
    conn.commit()

   

    #insert data into database
    if request.method == "POST":
        f = request.files.get("file")
        if f:
            file_name=f"{app.config['UPLOAD_FOLDER']}/{f.filename}"
            f.save(file_name)


            data = pd.read_excel(file_name)
            data.columns = ["english", "french"]
            data["status"] = 1
            print(data.head())

            #initialize database
            data.to_sql('vocab', con=engine, if_exists='append', index=False)

        #add new word
        word = request.form.get("word")
        translation= request.form.get("translation")
        if word and translation:
            print("New word", word)
            print("New translation", translation)  
            #new entry
            new = {"english": word, "french": translation, "status": 1}
            new_data = pd.DataFrame([new])
            #check for duplicates
            existing_data = pd.read_sql("SELECT * FROM vocab", engine)
            new_data_to_insert = new_data[~new_data['english'].isin(existing_data['english'])]
            #insert 
            new_data_to_insert.to_sql("vocab", con=engine, if_exists="append", index=False)

        #resultat verif##########################################
        cursor.execute("SELECT * FROM vocab")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        conn.commit()
        ####################################################

        clear= request.form.get("clear")
        if clear:
            cursor.execute("DELETE FROM vocab")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='vocab'")
            print('database cleared')
            conn.commit()

        update = request.form.get("update")

        if update:
            status_list = []
            for i in range(1, len(rows)+1):
                check = request.form.get(f"check_{i}")
                word_id = request.form.get(f"word_id_{i}")
                status_list.append(1 if check else 0)
                new_status = 1 if check else 0
                cursor.execute("UPDATE vocab SET status = ? WHERE id = ?", (new_status, word_id))
            conn.commit()
            print(status_list)


#pause duration setting
        pause_duration = request.form.get("pause_duration")
        if pause_duration:
            pause_duration = float(pause_duration)
            print(f"Pause duration set to {pause_duration} s")


#gender_voice setting
        gender_voice = request.form.get("gender_voice") 
        if gender_voice:
            gender_voice = str(gender_voice)
            print(f"Gender voice: {gender_voice}")

#num_loops setting
        num_loops = request.form.get("num_loops")
        if num_loops:  
            num_loops = int(num_loops)
            print(f"Number of loops set to: {num_loops}")

#Language switch setting



################################################################################################################################################################""
        
        

        audio_generate = request.form.get("audio_generate")
        if audio_generate:
            USER_DELAY = pause_duration 
            USER_ZH_GENDER = "female" #ou "male"
            USER_EN_GENDER = "male"

            #Récupération des données depuis la BDD

            df = pd.read_sql("SELECT english AS word, french AS translation FROM vocab WHERE status=1", engine)

            #Génération audios complets pour chaque entrée => à adapter pour la BDD
            final_audio_all = AudioSegment.empty()

            for index, row in df.iterrows():
                chinese_word = row["word"]  
                english_word = row["translation"]  

                #Audio pour une ligne
                final_audio_path = tts_zoe_code.generate_audio_for_entry(
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
                f"{FINAL_DIR}/final_output.mp3", 
                format="mp3"
            )
                        
            


        cursor.execute("SELECT * FROM vocab")
        rows = cursor.fetchall()
        conn.close()

    


    return render_template('index.html', rows=rows)

#################################################################################################


if __name__ == "__main__":
    app.run(debug=True)


#$env:FLASK_APP = "main.py"
#$env:FLASK_DEBUG = "1"
#python -m flask run