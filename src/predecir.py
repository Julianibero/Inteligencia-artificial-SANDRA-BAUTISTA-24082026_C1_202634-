"""
Consulta el modelo ya entrenado para un caso concreto.

Ejemplos:
    python src/predecir.py --estacion "San Antonio" --dia Viernes --hora 18
    python src/predecir.py --estacion Estadio --dia Sábado --hora 19 --evento
    python src/predecir.py --estacion "La Estrella" --dia Domingo --hora 6 --lluvia

Si el modelo todavía no existe, lo entrena primero.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd

from modelo_congestion import RUTA_MODELO, entrenar, predecir

RAIZ = Path(__file__).resolve().parent.parent
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def cargar_modelo():
    if not RUTA_MODELO.exists():
        print("No hay modelo guardado; entrenando...")
        entrenar(verboso=False)
    return joblib.load(RUTA_MODELO)


def buscar_estacion(nombre: str, linea: str | None) -> pd.Series:
    """Trae del catálogo los datos fijos de la estación (zona, transferencia)."""
    catalogo = pd.read_csv(RAIZ / "data" / "estaciones.csv")
    filas = catalogo[catalogo["estacion"].str.lower() == nombre.strip().lower()]
    if linea:
        filas = filas[filas["linea"] == linea.upper()]
    if filas.empty:
        disponibles = ", ".join(sorted(catalogo["estacion"].unique()))
        raise SystemExit(f"Estación no encontrada: '{nombre}'.\nDisponibles: {disponibles}")
    return filas.iloc[0]  # San Antonio está en A y B: por defecto se toma la A


def tipo_de_dia(dia: str, festivo: bool) -> str:
    if festivo or dia == "Domingo":
        return "Domingo_Festivo"
    return "Sábado" if dia == "Sábado" else "Laboral"


def main():
    p = argparse.ArgumentParser(description="Predice la congestión de una estación.")
    p.add_argument("--estacion", required=True)
    p.add_argument("--linea", choices=["A", "B", "a", "b"])
    p.add_argument("--dia", required=True, choices=DIAS)
    p.add_argument("--hora", required=True, type=int, help="hora de inicio, de 4 a 22")
    p.add_argument("--festivo", action="store_true")
    p.add_argument("--lluvia", action="store_true")
    p.add_argument("--evento", action="store_true", help="hay evento masivo cerca")
    a = p.parse_args()

    if not 4 <= a.hora <= 22:
        raise SystemExit("La hora debe estar entre 4 y 22 (horario de operación).")

    est = buscar_estacion(a.estacion, a.linea)
    resultado = predecir(
        cargar_modelo(), estacion=est["estacion"], linea=est["linea"],
        tipo_zona=est["tipo_zona"], es_transferencia=int(est["es_transferencia"]),
        dia_semana=a.dia, tipo_dia=tipo_de_dia(a.dia, a.festivo), hora=a.hora,
        clima="Lluvia" if a.lluvia else "Seco", evento_especial=int(a.evento))

    print(f"Estación {est['estacion']} (línea {est['linea']}), {a.dia} {a.hora}:00"
          f"{', festivo' if a.festivo else ''}{', con lluvia' if a.lluvia else ''}"
          f"{', con evento' if a.evento else ''}")
    print(f"Nivel de congestión esperado: {resultado['prediccion'].upper()}")
    print("Probabilidades:", resultado["probabilidades"])


if __name__ == "__main__":
    main()
