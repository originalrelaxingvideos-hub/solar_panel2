from flask import Flask, jsonify
import pvlib
import pandas as pd
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# ---- CONFIGURACION ----
LATITUD = 40.4168      # Madrid
LONGITUD = -3.7038
TIMEZONE = "Europe/Madrid"

MAX_ANGULO = 55
MIN_ANGULO = -55
ANGULO_DEFENSA = 1     # noche

# -----------------------

@app.route("/")
def simulacion_dia():

    tz = pytz.timezone(TIMEZONE)

    # Hoy a las 06:00
    ahora = datetime.now(tz)
    inicio = ahora.replace(hour=6, minute=0, second=0, microsecond=0)

    # Mañana a las 06:00
    fin = inicio + timedelta(days=1)

    # Cada 30 minutos
    tiempos = pd.date_range(
        start=inicio,
        end=fin,
        freq="30min",
        tz=TIMEZONE,
        inclusive="left"
    )

    # Posición solar
    solar_position = pvlib.solarposition.get_solarposition(
        tiempos,
        LATITUD,
        LONGITUD
    )

    resultados = []

    for t in tiempos:

        elevacion = solar_position.loc[t, "apparent_elevation"]

        # Noche
        if elevacion <= 0:
            angulo = ANGULO_DEFENSA
        else:
            # Convertimos elevación solar a rango -55 a 55
            angulo = (elevacion / 90.0) * MAX_ANGULO

            if angulo > MAX_ANGULO:
                angulo = MAX_ANGULO
            if angulo < MIN_ANGULO:
                angulo = MIN_ANGULO

        resultados.append({
            "hora": t.strftime("%H:%M"),
            "angulo": float(f"{angulo:.2f}")
        })

    return jsonify(resultados)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
