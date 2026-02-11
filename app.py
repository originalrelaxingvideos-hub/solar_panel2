from flask import Flask
import pvlib
import pandas as pd
import pytz
from datetime import datetime
import os

app = Flask(__name__)

# -----------------------------
# DATOS INSTALACION
# -----------------------------
LATITUD = 37.78926189842914
LONGITUD = -5.037213738717979
TIMEZONE = "Europe/Madrid"

# -----------------------------
# FUNCION CALCULO ANGULO
# -----------------------------
def calcular_angulo():

    tz = pytz.timezone(TIMEZONE)
    ahora = datetime.now(tz)

    tiempo = pd.DatetimeIndex([ahora])

    # Posicion solar
    solpos = pvlib.solarposition.get_solarposition(
        tiempo,
        LATITUD,
        LONGITUD
    )

    elevacion = solpos["apparent_elevation"].values[0]

    # Si es de noche → posicion defensa
    if elevacion <= 0:
        return 92.0

    # Tracker eje único
    tracking = pvlib.tracking.singleaxis(
        apparent_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        axis_tilt=0,
        axis_azimuth=6,   # tu orientación
        max_angle=90,
        backtrack=False
    )

    angulo = tracking["tracker_theta"].values[0]

    return float(angulo)


# -----------------------------
# RUTA WEB
# -----------------------------
@app.route("/")
def home():
    angulo = calcular_angulo()
    return str(angulo)


# -----------------------------
# ARRANQUE RENDER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
