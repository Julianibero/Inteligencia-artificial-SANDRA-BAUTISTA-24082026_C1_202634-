"""Pruebas de calidad del dataset (D1 a D9)."""
import pandas as pd

import generar_dataset as gen

COLUMNAS = ["fecha", "dia_semana", "tipo_dia", "hora", "linea", "estacion",
            "tipo_zona", "es_transferencia", "clima", "evento_especial",
            "indice_ocupacion", "pasajeros_hora", "nivel_congestion"]


def test_d1_columnas_esperadas(datos):
    assert list(datos.columns) == COLUMNAS


def test_d2_sin_valores_nulos(datos):
    assert datos.isna().sum().sum() == 0


def test_d3_sin_registros_duplicados(datos):
    clave = ["fecha", "hora", "linea", "estacion"]
    assert not datos.duplicated(subset=clave).any()


def test_d4_horas_dentro_del_horario_de_operacion(datos):
    assert datos["hora"].between(4, 22).all()
    domingos = datos[datos["tipo_dia"] == "Domingo_Festivo"]
    assert domingos["hora"].between(5, 21).all()


def test_d5_estaciones_coinciden_con_el_catalogo(datos, estaciones):
    assert estaciones["estacion"].nunique() == 27          # 21 en A + 7 en B - San Antonio
    assert len(estaciones) == 28                           # San Antonio cuenta en A y en B
    assert (estaciones["linea"] == "A").sum() == 21
    assert (estaciones["linea"] == "B").sum() == 7
    en_datos = set(map(tuple, datos[["estacion", "linea"]].drop_duplicates().values))
    en_catalogo = set(map(tuple, estaciones[["estacion", "linea"]].values))
    assert en_datos == en_catalogo


def test_d6_valores_categoricos_validos(datos):
    assert set(datos["nivel_congestion"]) == {"Bajo", "Medio", "Alto"}
    assert set(datos["tipo_dia"]) == {"Laboral", "Sábado", "Domingo_Festivo"}
    assert set(datos["clima"]) == {"Seco", "Lluvia"}
    assert set(datos["dia_semana"]) == set(gen.DIAS)
    assert set(datos["evento_especial"]) <= {0, 1}
    assert set(datos["es_transferencia"]) <= {0, 1}


def test_d7_etiqueta_coherente_con_el_indice(datos, estaciones):
    # La etiqueta debe salir exactamente de los umbrales documentados...
    assert (datos["indice_ocupacion"].apply(gen.clasificar) == datos["nivel_congestion"]).all()
    # ...y el índice debe ser pasajeros / capacidad de la estación.
    union = datos.merge(estaciones, on=["estacion", "linea"])
    recalculado = (union["pasajeros_hora"] / union["capacidad_referencia_hora"]).round(3)
    assert (recalculado - union["indice_ocupacion"]).abs().max() < 0.001
    assert (datos["pasajeros_hora"] >= 0).all()


def test_d8_festivos_tratados_como_domingo(datos):
    for festivo in gen.FESTIVOS:
        del_dia = datos[datos["fecha"] == festivo.isoformat()]
        assert len(del_dia) > 0
        assert (del_dia["tipo_dia"] == "Domingo_Festivo").all()


def test_d9_el_generador_es_reproducible(datos):
    _, regenerado = gen.generar()
    pd.testing.assert_frame_equal(regenerado.reset_index(drop=True), datos,
                                  check_dtype=False)
