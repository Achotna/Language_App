from flask import Flask, render_template, request
from flask_dropzone import Dropzone

app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER="uploads/",
    #only excel files DROPZONE_ALLOWED_FILE_TYPE="xls,xlsx", 
    DROPZONE_MAX_FILE_SIZE=1024,  # MB
)

dropzone = Dropzone(app)

@app.route("/",methods=["GET", "POST"])
def home():
    if request.method == "POST":
        f = request.files.get("file")
        f.save(f"{app.config['UPLOAD_FOLDER']}/{f.filename}")


    return render_template('index.html')




if __name__ == "__main__":
    app.run(debug=True)


#$env:FLASK_APP = "main.py"
#$env:FLASK_DEBUG = "1"
#python -m flask run