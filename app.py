from flask import Flask, jsonify
import pvlib
import pandas as pd

app = Flask(__name__)

# --------- DATOS INSTALACION ---------
LATITUD = 37.78926189842914
LONGITUD = -5.037213738717979

AXIS_AZIMUTH = 6      # eje del tracker (6º Oeste)
AXIS_TILT = 0         # inclinación del eje

# LIMITES MECANICOS
ANGULO_MIN = -55
ANGULO_MAX = 55

# POSICION DEFENSA (NOCHE)
ANGULO_DEFENSA = 92


@app.route("/")
def obtener_angulo():

    tiempo = pd.DatetimeIndex([pd.Timestamp.utcnow()])

    # Posicion solar
    sol = pvlib.solarposition.get_solarposition(
        time=tiempo,
        latitude=LATITUD,
        longitude=LONGITUD
    )

    zenith = float(sol["apparent_zenith"].iloc[0])

    # -------- NOCHE --------
    if zenith >= 90:
        angulo = ANGULO_DEFENSA

    else:
        # Calculo tracking normal
        tracking = pvlib.tracking.singleaxis(
            apparent_zenith=sol["apparent_zenith"],
            apparent_azimuth=sol["azimuth"],
            axis_tilt=AXIS_TILT,
            axis_azimuth=AXIS_AZIMUTH,
            max_angle=90,
            backtrack=False
        )

        angulo = float(tracking["tracker_theta"].iloc[0])

        # Limites mecanicos
        if angulo > ANGULO_MAX:
            angulo = ANGULO_MAX
        elif angulo < ANGULO_MIN:
            angulo = ANGULO_MIN

    return jsonify({
        "angulo": angulo
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
