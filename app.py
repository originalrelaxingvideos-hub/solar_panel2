from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor OK"

@app.route("/angulo")
def angulo():
    return {"angulo": 25}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
