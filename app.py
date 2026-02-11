from flask import Flask, jsonify
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

ANGULO_MAX = 55.0
ANGULO_MIN = -55.0
POSICION_DEFENSA = 1.0   # <-- cambiado


# -----------------------------
# LIMITADOR MECANICO
# -----------------------------
def limitar_angulo(angulo):
    if angulo > ANGULO_MAX:
        return ANGULO_MAX
    if angulo < ANGULO_MIN:
        return ANGULO_MIN
    return angulo


# -----------------------------
# CALCULO ANGULO SOLAR
# -----------------------------
def calcular_angulo_en_tiempo(fecha_hora):

    tiempo = pd.DatetimeIndex([fecha_hora])

    solpos = pvlib.solarposition.get_solarposition(
        tiempo,
        LATITUD,
        LONGITUD
    )

    elevacion = solpos["apparent_elevation"].values[0]

    # Noche → posicion defensa
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

    angulo = float(tracking["tracker_theta"].values[0])

    # limitar al rango mecánico
    angulo = limitar_angulo(angulo)

    return angulo


# -----------------------------
# ANGULO ACTUAL
# -----------------------------
def calcular_angulo_actual():
    tz = pytz.timezone(TIMEZONE)
    ahora = datetime.now(tz)
    return calcular_angulo_en_tiempo(ahora)


# -----------------------------
# SIMULACION 24H (6AM → 6AM)
# -----------------------------
def simulacion_dia():

    tz = pytz.timezone(TIMEZONE)
    hoy = datetime.now(tz).date()

    inicio = tz.localize(datetime.combine(hoy, datetime.min.time())) + timedelta(hours=6)
    fin = inicio + timedelta(days=1)

    tiempos = pd.date_range(
        start=inicio,
        end=fin,
        freq="30min"
    )

    resultado = []

    for t in tiempos:
        angulo = calcular_angulo_en_tiempo(t)

        resultado.append({
            "hora": t.strftime("%H:%M"),
            "angulo": round(angulo, 2)
        })

    return resultado


# -----------------------------
# RUTAS WEB
# -----------------------------
@app.route("/")
def home():
    return str(calcular_angulo_actual())


@app.route("/simulacion")
def simulacion():
    return jsonify(simulacion_dia())


# -----------------------------
# ARRANQUE RENDER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

