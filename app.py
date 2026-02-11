from flask import Flask, jsonify
import pvlib
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# -----------------------------
# CONFIGURACION
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

    # Posición solar
    sol = pvlib.solarposition.get_solarposition(
        ahora,
        LATITUD,
        LONGITUD
    )

    zenith = sol["apparent_zenith"].iloc[0]
    azimuth = sol["azimuth"].iloc[0]
    elevation = sol["apparent_elevation"].iloc[0]

    # -----------------------------
    # NOCHE → POSICION DEFENSA
    # -----------------------------
    if elevation <= 0:
        return 90.0

    # -----------------------------
    # TRACKER SOLAR
    # -----------------------------
    tracking = pvlib.tracking.singleaxis(
        apparent_zenith=zenith,
        solar_azimuth=azimuth,
        axis_tilt=0,
        axis_azimuth=180,
        max_angle=90,
        backtrack=False
    )

    tracker_angle = float(tracking["tracker_theta"])

    # -----------------------------
    # LIMITE MECANICO ±55°
    # -----------------------------
    if tracker_angle > 55:
        tracker_angle = 55.0
    elif tracker_angle < -55:
        tracker_angle = -55.0

    # -----------------------------
    # CONVERSION A TU SISTEMA
    # 90° = horizontal
    # -----------------------------
    angulo_motor = tracker_angle + 90.0

    return angulo_motor


# -----------------------------
# API
# -----------------------------
@app.route("/")
def index():
    angulo = calcular_angulo()
    return jsonify({"angulo": angulo})


# -----------------------------
# SERVIDOR RENDER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
