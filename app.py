from flask import Flask, jsonify, request
import pvlib
import pandas as pd
import pytz
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# -----------------------------
# DATOS INSTALACION
# -----------------------------
LATITUD = 37.78926189842914
LONGITUD = -5.037213738717979
TIMEZONE = "Europe/Madrid"

ANGULO_MAX = 55
ANGULO_MIN = -55
POSICION_DEFENSA = 1.0


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

    # Noche -> defensa
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
# ANGULO ACTUAL (ESP)
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

    # ✅ SI SE PASA FECHA -> usarla
    if fecha_param:
        fecha_base = datetime.strptime(fecha_param, "%Y-%m-%d")
        fecha_base = tz.localize(fecha_base)
    else:
        fecha_base = datetime.now(tz)

    # Inicio 06:00 del día indicado
    inicio = fecha_base.replace(hour=6, minute=0, second=0, microsecond=0)

    # Fin 06:00 del día siguiente
    fin = inicio + timedelta(days=1)

    tiempos = pd.date_range(
        start=inicio,
        end=fin,
        freq="30min",
        tz=TIMEZONE
    )

    resultados = []

    for t in tiempos:
        tiempo = pd.DatetimeIndex([t])
        angulo = calcular_angulo(tiempo)

        resultados.append({
            "hora": t.strftime("%H:%M"),
            "angulo": angulo
        })

    return jsonify(resultados)

# -----------------------------
# ANGULO POR HORA MANUAL (ESP)
# -----------------------------
@app.route("/test")
def angulo_por_hora():

    tz = pytz.timezone(TIMEZONE)

    hora_param = request.args.get("hora")

    # Si no se pasa hora -> defensa
    if not hora_param:
        return str(POSICION_DEFENSA)

    try:
        # Separar HH:MM
        hora, minuto = map(int, hora_param.split(":"))

        # Fecha de hoy
        ahora = datetime.now(tz)
        fecha_manual = ahora.replace(
            hour=hora,
            minute=minuto,
            second=0,
            microsecond=0
        )

        tiempo = pd.DatetimeIndex([fecha_manual])

        angulo = calcular_angulo(tiempo)

        return str(angulo)

    except:
        return str(POSICION_DEFENSA)

# -----------------------------
# ARRANQUE RENDER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
