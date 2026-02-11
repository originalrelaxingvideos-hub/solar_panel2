from flask import Flask, jsonify
import pandas as pd
import pvlib
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# Ubicación
LAT = 37.78926189842914
LON = -5.037213738717979

# Zona horaria Madrid
TZ = "Europe/Madrid"

@app.route("/")
def simular_dia():

    tz = pytz.timezone(TZ)

    ahora = datetime.now(tz)
    hoy = ahora.date()
    manana = hoy + timedelta(days=1)

    # desde 06:00 hoy hasta 06:00 mañana
    tiempos = pd.date_range(
        start=f"{hoy} 06:00",
        end=f"{manana} 06:00",
        freq="30min",
        tz=TZ
    )

    # posición solar
    solpos = pvlib.solarposition.get_solarposition(
        tiempos,
        LAT,
        LON
    )

    # tracking eje único
    tracking = pvlib.tracking.singleaxis(
        apparent_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        axis_tilt=0,
        axis_azimuth=6,
        backtrack=False
    )

    resultado = []

    for t, ang in zip(tiempos, tracking["tracker_theta"]):

        if pd.isna(ang):
            ang = 92.0   # posición defensa noche

        resultado.append({
            "hora": t.strftime("%H:%M"),
            "angulo": float(ang)
        })

    return jsonify(resultado)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
