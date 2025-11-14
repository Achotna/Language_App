from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<p>This is a Language App</p>"


#$env:FLASK_APP = "main.py"
#$env:FLASK_DEBUG = "1"
#python -m flask run