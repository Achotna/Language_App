from flask import Flask, render_template, request
from flask_dropzone import Dropzone
import pandas as pd
from sqlalchemy import create_engine
import sqlite3

app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER="uploads/",
    #only excel files DROPZONE_ALLOWED_FILE_TYPE="xls,xlsx", 
    DROPZONE_MAX_FILE_SIZE=1024,  # MB
)

dropzone = Dropzone(app)

@app.route("/",methods=["GET", "POST"])
def home():
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
    engine = create_engine("sqlite:///./vocab.db")


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

        #resultat verif
        
        cursor.execute("SELECT * FROM vocab")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        conn.commit()

        clear= request.form.get("clear")
        if clear:
            cursor.execute("DROP TABLE IF EXISTS vocab")
            print('database cleared')
            conn.commit()


        conn.close()






    return render_template('index.html')




if __name__ == "__main__":
    app.run(debug=True)


#$env:FLASK_APP = "main.py"
#$env:FLASK_DEBUG = "1"
#python -m flask run