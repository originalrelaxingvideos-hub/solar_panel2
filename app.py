from flask import Flask
import pandas as pd
import pvlib

app = Flask(__name__)

# -----------------------------
# UBICACION
# -----------------------------
LATITUD = 37.78926189842914
LONGITUD = -5.037213738717979
TIMEZONE = "Europe/Madrid"

ANGULO_DEFENSA = 92   # posicion noche


@app.route("/")
def angulo_solar():

    # Hora actual en Madrid
    fecha = pd.Timestamp.now(tz=TIMEZONE)

    # Localizacion
    location = pvlib.location.Location(
        LATITUD,
        LONGITUD,
        tz=TIMEZONE
    )

    # Posicion solar
    solpos = location.get_solarposition(fecha)

    elevacion = solpos["apparent_elevation"].values[0]

    # -----------------------------
    # NOCHE → posicion defensa
    # -----------------------------
    if elevacion <= 0:
        return str(float(ANGULO_DEFENSA))

    # -----------------------------
    # SEGUIDOR 1 EJE
    # -----------------------------
    tracking = pvlib.tracking.singleaxis(
        apparent_zenith=solpos["apparent_zenith"],
        apparent_azimuth=solpos["azimuth"],
        axis_tilt=0,
        axis_azimuth=6,
        backtrack=False
    )

    angulo = float(tracking["tracker_theta"].values[0])

    return str(angulo)


if __name__ == "__main__":
    app.run()
