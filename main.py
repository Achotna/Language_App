from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<p>This is a Language App</p>"