from flask import Flask, jsonify
import pandas as pd
import pvlib
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# -------------------------------
# CONFIGURACION
# -------------------------------
LATITUD = 37.78926189842914
LONGITUD = -5.037213738717979
TIMEZONE = "Europe/Madrid"

# -------------------------------
# FUNCION CALCULO ANGULO
# -------------------------------
def calcular_dia_verano():

    tz = pytz.timezone(TIMEZONE)

    # Día fijo de verano (21 junio)
    fecha_base = datetime.now(tz).replace(
        month=6, day=21,
        hour=6, minute=0, second=0, microsecond=0
    )

    tiempos = []
    angulos = []

    for i in range(48):
        momento = fecha_base + timedelta(minutes=30 * i)

        # cálculo solar
        sol = pvlib.solarposition.get_solarposition(
            momento,
            LATITUD,
            LONGITUD
        )

        zenith = sol["apparent_zenith"].iloc[0]
        azimuth = sol["azimuth"].iloc[0]

        # Si no hay sol → posición defensa
        if zenith > 90:
            angulo = 92.0
        else:
            tracking = pvlib.tracking.singleaxis(
                apparent_zenith=zenith,
                solar_azimuth=azimuth,
                axis_tilt=0,
                axis_azimuth=180,
                max_angle=90,
                backtrack=False
            )

            angulo = float(tracking["tracker_theta"])

        tiempos.append(momento.strftime("%H:%M"))
        angulos.append(angulo)

    resultado = [
        {"hora": h, "angulo": a}
        for h, a in zip(tiempos, angulos)
    ]

    return resultado


# -------------------------------
# API
# -------------------------------
@app.route("/")
def index():
    datos = calcular_dia_verano()
    return jsonify(datos)


# -------------------------------
# SERVIDOR (IMPORTANTE PARA RENDER)
# -------------------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
