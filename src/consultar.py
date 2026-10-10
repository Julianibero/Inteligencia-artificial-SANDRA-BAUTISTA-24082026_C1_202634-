"""
Consulta a qué grupo pertenece una estación según el día.

Ejemplos:
    python src/consultar.py --resumen
    python src/consultar.py --estacion "San Antonio"
    python src/consultar.py --estacion Estadio --dia Sábado

Si los resultados todavía no existen, ejecuta primero el agrupamiento.
"""

import argparse

import pandas as pd

from agrupamiento import CARPETA_RESULTADOS, ejecutar

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def cargar():
    ruta = CARPETA_RESULTADOS / "asignaciones.csv"
    if not ruta.exists():
        print("No hay resultados guardados; ejecutando el agrupamiento...")
        ejecutar(verboso=False)
    return (pd.read_csv(ruta),
            pd.read_csv(CARPETA_RESULTADOS / "resumen_grupos.csv"))


def main():
    p = argparse.ArgumentParser(description="Consulta los grupos de demanda del Metro.")
    p.add_argument("--estacion")
    p.add_argument("--linea", choices=["A", "B", "a", "b"])
    p.add_argument("--dia", choices=DIAS)
    p.add_argument("--resumen", action="store_true", help="muestra los grupos encontrados")
    a = p.parse_args()

    asignaciones, resumen = cargar()

    if a.resumen or not a.estacion:
        print("Grupos encontrados por k-means:\n")
        for f in resumen.itertuples():
            print(f"  {f.grupo}. {f.nombre:<20} {f.perfiles:>4} perfiles ({f.porcentaje}%)"
                  f"  · hora pico {f.hora_pico}:00")
        if not a.estacion:
            return

    filas = asignaciones[asignaciones["estacion"].str.lower() == a.estacion.strip().lower()]
    if a.linea:
        filas = filas[filas["linea"] == a.linea.upper()]
    if filas.empty:
        disponibles = ", ".join(sorted(asignaciones["estacion"].unique()))
        raise SystemExit(f"Estación no encontrada: '{a.estacion}'.\nDisponibles: {disponibles}")
    if a.dia:
        filas = filas[filas["dia_semana"] == a.dia]

    nombre = filas["estacion"].iloc[0]
    print(f"\nEstación {nombre}{' · ' + a.dia if a.dia else ''}: "
          f"{len(filas)} días analizados")
    conteo = filas["nombre_grupo"].value_counts()
    for grupo, n in conteo.items():
        print(f"  {grupo:<20} {n:>3} días ({n / len(filas):.0%})")
    eventos = filas[filas["hubo_evento"] == 1]
    if len(eventos):
        print(f"  (de esos días, {len(eventos)} tuvieron partido en el estadio y quedaron en: "
              f"{', '.join(eventos['nombre_grupo'].unique())})")


if __name__ == "__main__":
    main()
