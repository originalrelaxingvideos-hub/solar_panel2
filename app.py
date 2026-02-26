from flask import Flask, jsonify, request
from flask_cors import CORS
import pvlib
import pandas as pd
import pytz
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
CORS(app, origins="*")

# -----------------------------
# DATOS INSTALACION
# -----------------------------
LATITUD = 37.78926189842914
LONGITUD = -5.037213738717979
TIMEZONE = "Europe/Madrid"
ANGULO_MAX = 55
ANGULO_MIN = -55
POSICION_DEFENSA = 1.0
CALIBRACION_FILE = "calibracion.json"

# -----------------------------
# MODO ESP32 (en memoria)
# -----------------------------
modo_actual = {"modo": "STOP"}

# -----------------------------
# CARGAR / GUARDAR CALIBRACION
# -----------------------------
def cargar_calibracion():
    if os.path.exists(CALIBRACION_FILE):
        with open(CALIBRACION_FILE, "r") as f:
            return json.load(f)
    return {"Vmin": None, "Vmax": None}

def guardar_calibracion_archivo(Vmin, Vmax):
    with open(CALIBRACION_FILE, "w") as f:
        json.dump({"Vmin": Vmin, "Vmax": Vmax}, f)

# -----------------------------
# LIMITAR ANGULO
# -----------------------------
def limitar_angulo(angulo):
    return max(ANGULO_MIN, min(ANGULO_MAX, angulo))

# -----------------------------
# CALCULO ANGULO SOLAR
# -----------------------------
def calcular_angulo(fecha_hora):
    solpos = pvlib.solarposition.get_solarposition(
        fecha_hora,
        LATITUD,
        LONGITUD
    )
    elevacion = solpos["apparent_elevation"].values[0]
    if elevacion <= 0:
        return POSICION_DEFENSA
    tracking = pvlib.tracking.singleaxis(
        apparent_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        axis_tilt=0,
        axis_azimuth=6,
        max_angle=90,
        backtrack=False
    )
    angulo = tracking["tracker_theta"].values[0]
    angulo = limitar_angulo(angulo)
    return round(float(angulo), 2)

# -----------------------------
# ANGULO ACTUAL
# -----------------------------
@app.route("/")
def home():
    tz = pytz.timezone(TIMEZONE)
    ahora = datetime.now(tz)
    tiempo = pd.DatetimeIndex([ahora])
    angulo = calcular_angulo(tiempo)
    return str(angulo)

# -----------------------------
# SIMULACION DIA COMPLETO
# -----------------------------
@app.route("/simulacion")
def simulacion():
    tz = pytz.timezone(TIMEZONE)
    fecha_param = request.args.get("fecha")
    if fecha_param:
        fecha_base = datetime.strptime(fecha_param, "%Y-%m-%d")
        fecha_base = tz.localize(fecha_base)
    else:
        fecha_base = datetime.now(tz)
    inicio = fecha_base.replace(hour=6, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(days=1)
    tiempos = pd.date_range(start=inicio, end=fin, freq="30min", tz=TIMEZONE)
    resultados = []
    for t in tiempos:
        tiempo = pd.DatetimeIndex([t])
        angulo = calcular_angulo(tiempo)
        resultados.append({"hora": t.strftime("%H:%M"), "angulo": angulo})
    return jsonify(resultados)

# -----------------------------
# ANGULO POR HORA MANUAL
# -----------------------------
@app.route("/test")
def angulo_por_hora():
    tz = pytz.timezone(TIMEZONE)
    hora_param = request.args.get("hora")
    if not hora_param:
        return str(POSICION_DEFENSA)
    try:
        hora, minuto = map(int, hora_param.split(":"))
        ahora = datetime.now(tz)
        fecha_manual = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        tiempo = pd.DatetimeIndex([fecha_manual])
        angulo = calcular_angulo(tiempo)
        return str(angulo)
    except:
        return str(POSICION_DEFENSA)

# -----------------------------
# CALIBRACION
# -----------------------------
@app.route("/calibracion", methods=["GET"])
def leer_calibracion():
    datos = cargar_calibracion()
    if datos["Vmin"] is None or datos["Vmax"] is None:
        return jsonify({"status": "SIN_CALIBRAR"})
    return jsonify({"status": "OK", "Vmin": datos["Vmin"], "Vmax": datos["Vmax"]})

@app.route("/calibracion", methods=["POST"])
def guardar_calibracion():
    try:
        data = request.get_json()
        Vmin = data["Vmin"]
        Vmax = data["Vmax"]
        guardar_calibracion_archivo(Vmin, Vmax)
        return jsonify({"status": "OK", "Vmin": Vmin, "Vmax": Vmax})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

# -----------------------------
# MODO ESP32
# -----------------------------
@app.route("/modo", methods=["GET"])
def get_modo():
    return jsonify(modo_actual)

@app.route("/modo", methods=["POST"])
def set_modo():
    try:
        data = request.get_json()
        modo_actual["modo"] = data["modo"]
        return jsonify({"status": "OK", "modo": modo_actual["modo"]})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)})

# -----------------------------
# ARRANQUE
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
