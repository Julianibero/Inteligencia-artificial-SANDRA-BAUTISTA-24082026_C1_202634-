"""
Generador del dataset de muestra: afluencia horaria por estación
del Metro de Medellín (líneas A y B).

Por qué existe este archivo
---------------------------
El Metro publica la afluencia agregada por LÍNEA, día y hora, pero no por
ESTACIÓN, que es el nivel que necesita nuestro modelo. Siguiendo el punto 2
de la actividad ("en caso de no existir dichas fuentes de datos, desarrolle
un dataset con una muestra de dichos datos") construimos una muestra
SIMULADA con la misma estructura que tendría el dato real.

Lo que es real:   nombres y orden de las estaciones, líneas, calendario y
                  festivos de Colombia, horario aproximado de operación.
Lo que es simulado: el número de pasajeros, el clima, los eventos y, por
                  tanto, el nivel de congestión.

Uso:
    python data/generar_dataset.py
Genera:
    data/estaciones.csv
    data/afluencia_metro_medellin.csv
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 42
CARPETA = Path(__file__).resolve().parent

# Periodo de la muestra: 8 semanas completas (lunes a domingo).
FECHA_INICIO = date(2026, 3, 2)
FECHA_FIN = date(2026, 4, 26)

# Festivos de Colombia que caen dentro del periodo.
FESTIVOS = {
    date(2026, 3, 23): "Día de San José (trasladado)",
    date(2026, 4, 2): "Jueves Santo",
    date(2026, 4, 3): "Viernes Santo",
}

# Umbrales del índice de ocupación que definen la etiqueta.
UMBRAL_MEDIO = 0.45
UMBRAL_ALTO = 0.80

# Usos de un día laboral típico en líneas A y B, usado solo para que los
# volúmenes tengan un orden de magnitud creíble (~713 mil, dato de 2016
# reportado por el Metro de Medellín a ALAMYS).
USOS_DIA_LABORAL_REFERENCIA = 713_000

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# (estación, línea, orden en la línea, tipo de zona, transferencia, peso de demanda)
# - tipo_zona y peso_demanda son una clasificación PROPIA del equipo.
# - es_transferencia = 1 si conecta con otra línea férrea o de cable.
ESTACIONES = [
    ("Niquía", "A", 1, "Residencial", 0, 1.25),
    ("Bello", "A", 2, "Residencial", 0, 0.95),
    ("Madera", "A", 3, "Residencial", 0, 0.60),
    ("Acevedo", "A", 4, "Residencial", 1, 1.10),
    ("Tricentenario", "A", 5, "Residencial", 0, 0.55),
    ("Caribe", "A", 6, "Mixta", 0, 0.85),
    ("Universidad", "A", 7, "Mixta", 0, 0.90),
    ("Hospital", "A", 8, "Centro_Empleo", 0, 1.00),
    ("Prado", "A", 9, "Centro_Empleo", 0, 0.85),
    ("Parque Berrío", "A", 10, "Centro_Empleo", 0, 1.30),
    ("San Antonio", "A", 11, "Centro_Empleo", 1, 1.60),
    ("Alpujarra", "A", 12, "Centro_Empleo", 0, 0.90),
    ("Exposiciones", "A", 13, "Centro_Empleo", 0, 0.85),
    ("Industriales", "A", 14, "Centro_Empleo", 0, 1.05),
    ("Poblado", "A", 15, "Centro_Empleo", 0, 1.25),
    ("Aguacatala", "A", 16, "Mixta", 0, 0.80),
    ("Ayurá", "A", 17, "Mixta", 0, 0.75),
    ("Envigado", "A", 18, "Residencial", 0, 0.95),
    ("Itagüí", "A", 19, "Residencial", 0, 1.10),
    ("Sabaneta", "A", 20, "Residencial", 0, 0.80),
    ("La Estrella", "A", 21, "Residencial", 0, 0.90),
    ("San Antonio", "B", 1, "Centro_Empleo", 1, 1.20),
    ("Cisneros", "B", 2, "Centro_Empleo", 0, 0.70),
    ("Suramericana", "B", 3, "Mixta", 0, 0.65),
    ("Estadio", "B", 4, "Mixta", 0, 0.80),
    ("Floresta", "B", 5, "Residencial", 0, 0.75),
    ("Santa Lucía", "B", 6, "Residencial", 0, 0.70),
    ("San Javier", "B", 7, "Residencial", 1, 1.15),
]

# Perfil horario de INGRESOS en día laboral según el tipo de zona.
# Zonas residenciales cargan en la mañana (la gente sale a trabajar);
# zonas de empleo cargan en la tarde (la gente regresa).
PERFIL_LABORAL = {
    "Residencial": {4: 0.35, 5: 0.85, 6: 1.25, 7: 1.15, 8: 0.80, 9: 0.55, 10: 0.45,
                    11: 0.45, 12: 0.50, 13: 0.50, 14: 0.45, 15: 0.45, 16: 0.50,
                    17: 0.55, 18: 0.50, 19: 0.40, 20: 0.30, 21: 0.22, 22: 0.12},
    "Centro_Empleo": {4: 0.08, 5: 0.20, 6: 0.40, 7: 0.55, 8: 0.55, 9: 0.50, 10: 0.50,
                      11: 0.55, 12: 0.70, 13: 0.65, 14: 0.60, 15: 0.70, 16: 0.95,
                      17: 1.30, 18: 1.25, 19: 0.90, 20: 0.60, 21: 0.40, 22: 0.20},
    "Mixta": {4: 0.20, 5: 0.50, 6: 0.85, 7: 0.90, 8: 0.70, 9: 0.50, 10: 0.48,
              11: 0.50, 12: 0.60, 13: 0.58, 14: 0.52, 15: 0.58, 16: 0.75,
              17: 0.95, 18: 0.90, 19: 0.65, 20: 0.45, 21: 0.30, 22: 0.16},
}

# Sábados y domingos/festivos: sin picos marcados, demanda repartida en el día.
PERFIL_SABADO = {4: 0.15, 5: 0.30, 6: 0.45, 7: 0.55, 8: 0.60, 9: 0.62, 10: 0.65,
                 11: 0.68, 12: 0.72, 13: 0.70, 14: 0.66, 15: 0.66, 16: 0.68,
                 17: 0.70, 18: 0.66, 19: 0.55, 20: 0.42, 21: 0.30, 22: 0.18}
PERFIL_DOMINGO = {5: 0.12, 6: 0.20, 7: 0.28, 8: 0.34, 9: 0.40, 10: 0.44,
                  11: 0.46, 12: 0.46, 13: 0.44, 14: 0.44, 15: 0.46, 16: 0.48,
                  17: 0.48, 18: 0.42, 19: 0.34, 20: 0.26, 21: 0.16}

# Pequeño ajuste por día de la semana (los viernes se mueve más gente).
FACTOR_DIA = {"Lunes": 1.03, "Martes": 1.00, "Miércoles": 1.00, "Jueves": 1.00,
              "Viernes": 1.06, "Sábado": 1.00, "Domingo": 1.00}

# Partidos en el estadio Atanasio Girardot (fechas inventadas para la muestra;
# con dos equipos locales es normal tener uno o dos partidos por semana).
# Cargan las estaciones Estadio y Suramericana entre las 17:00 y las 21:59.
FECHAS_PARTIDO = [date(2026, 3, 4), date(2026, 3, 7), date(2026, 3, 11),
                  date(2026, 3, 15), date(2026, 3, 18), date(2026, 3, 21),
                  date(2026, 3, 25), date(2026, 3, 28), date(2026, 4, 1),
                  date(2026, 4, 8), date(2026, 4, 12), date(2026, 4, 15),
                  date(2026, 4, 18), date(2026, 4, 22), date(2026, 4, 25)]
ESTACIONES_EVENTO = {"Estadio", "Suramericana"}
HORAS_EVENTO = range(17, 22)

EFECTO_LLUVIA = 1.12   # con lluvia entra más gente al metro (supuesto)
EFECTO_EVENTO = 1.90   # un partido casi duplica los ingresos (supuesto)
RUIDO_SIGMA = 0.15     # variación aleatoria propia de cada hora


def tipo_de_dia(fecha: date) -> str:
    """Laboral, Sábado o Domingo_Festivo (los festivos operan como domingo)."""
    if fecha in FESTIVOS or fecha.weekday() == 6:
        return "Domingo_Festivo"
    if fecha.weekday() == 5:
        return "Sábado"
    return "Laboral"


def probabilidad_lluvia(hora: int) -> float:
    """En Medellín llueve más en la tarde; marzo-abril es temporada de lluvias."""
    if 13 <= hora <= 18:
        return 0.38
    if hora >= 19:
        return 0.25
    return 0.14


def clasificar(indice: float) -> str:
    """Convierte el índice de ocupación en la etiqueta que predice el modelo."""
    if indice < UMBRAL_MEDIO:
        return "Bajo"
    if indice < UMBRAL_ALTO:
        return "Medio"
    return "Alto"


def catalogo_estaciones() -> pd.DataFrame:
    columnas = ["estacion", "linea", "orden_en_linea", "tipo_zona",
                "es_transferencia", "peso_demanda"]
    return pd.DataFrame(ESTACIONES, columns=columnas)


def generar() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEMILLA)
    estaciones = catalogo_estaciones()

    filas = []
    fecha = FECHA_INICIO
    while fecha <= FECHA_FIN:
        tipo = tipo_de_dia(fecha)
        dia = DIAS[fecha.weekday()]
        if tipo == "Laboral":
            horas = range(4, 23)
        elif tipo == "Sábado":
            horas = PERFIL_SABADO.keys()
        else:
            horas = PERFIL_DOMINGO.keys()

        for hora in horas:
            # El clima es el mismo para todo el sistema en una hora dada.
            llueve = rng.random() < probabilidad_lluvia(hora)
            for est in estaciones.itertuples(index=False):
                if tipo == "Laboral":
                    perfil = PERFIL_LABORAL[est.tipo_zona][hora]
                elif tipo == "Sábado":
                    perfil = PERFIL_SABADO[hora]
                else:
                    perfil = PERFIL_DOMINGO[hora]

                evento = int(fecha in FECHAS_PARTIDO
                             and est.estacion in ESTACIONES_EVENTO
                             and hora in HORAS_EVENTO)

                indice = est.peso_demanda * perfil * FACTOR_DIA[dia]
                if llueve:
                    indice *= EFECTO_LLUVIA
                if evento:
                    indice *= EFECTO_EVENTO
                indice *= rng.lognormal(mean=0.0, sigma=RUIDO_SIGMA)

                filas.append({
                    "fecha": fecha.isoformat(),
                    "dia_semana": dia,
                    "tipo_dia": tipo,
                    "hora": hora,
                    "linea": est.linea,
                    "estacion": est.estacion,
                    "tipo_zona": est.tipo_zona,
                    "es_transferencia": est.es_transferencia,
                    "clima": "Lluvia" if llueve else "Seco",
                    "evento_especial": evento,
                    "indice_ocupacion": indice,
                    "_peso": est.peso_demanda,
                })
        fecha += timedelta(days=1)

    datos = pd.DataFrame(filas)

    # Capacidad de referencia por estación (pasajeros/hora que atiende sin
    # aglomeración). Se escala para que un día laboral promedio sume un
    # volumen del orden del reportado por el Metro.
    capacidad_base = 1000 + 1300 * datos["_peso"]
    laborales = datos["tipo_dia"] == "Laboral"
    total_dia = (datos.loc[laborales, "indice_ocupacion"] * capacidad_base[laborales]).sum() \
        / datos.loc[laborales, "fecha"].nunique()
    escala = USOS_DIA_LABORAL_REFERENCIA / total_dia

    estaciones["capacidad_referencia_hora"] = (
        ((1000 + 1300 * estaciones["peso_demanda"]) * escala / 50).round() * 50
    ).astype(int)
    capacidad = datos.merge(estaciones[["estacion", "linea", "capacidad_referencia_hora"]],
                            on=["estacion", "linea"], how="left")["capacidad_referencia_hora"]

    datos["pasajeros_hora"] = (datos["indice_ocupacion"] * capacidad).round().astype(int)
    # El índice se recalcula desde el conteo entero para que el CSV sea
    # coherente consigo mismo (pasajeros / capacidad = índice).
    datos["indice_ocupacion"] = (datos["pasajeros_hora"] / capacidad).round(3)
    datos["nivel_congestion"] = datos["indice_ocupacion"].apply(clasificar)
    datos = datos.drop(columns="_peso")

    return estaciones, datos


if __name__ == "__main__":
    estaciones, datos = generar()
    estaciones.to_csv(CARPETA / "estaciones.csv", index=False, encoding="utf-8")
    datos.to_csv(CARPETA / "afluencia_metro_medellin.csv", index=False, encoding="utf-8")

    print(f"estaciones.csv              -> {len(estaciones)} filas")
    print(f"afluencia_metro_medellin.csv -> {len(datos)} filas, {datos.shape[1]} columnas")
    print("\nDistribución de la etiqueta:")
    print(datos["nivel_congestion"].value_counts(normalize=True).round(3).to_string())
    laboral = datos[datos["tipo_dia"] == "Laboral"]
    print("\nPasajeros promedio en un día laboral:",
          int(laboral.groupby("fecha")["pasajeros_hora"].sum().mean()))
