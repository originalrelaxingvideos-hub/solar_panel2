from flask import Flask, request, jsonify
import math

app = Flask(__name__)

@app.route("/angulo")
def angulo():

    lat = float(request.args.get("lat", 40.0))
    lon = float(request.args.get("lon", -3.0))

    # EJEMPLO SIMPLE (luego puedes poner pvlib)
    angulo = 30.0

    return jsonify({"angulo": angulo})

app.run(host="0.0.0.0", port=10000)
