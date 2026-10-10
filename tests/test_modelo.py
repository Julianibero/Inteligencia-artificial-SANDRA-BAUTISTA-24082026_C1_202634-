"""Pruebas del agrupamiento (M1 a M10)."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

import agrupamiento as ag


def test_m1_el_codo_esta_en_cinco_grupos(resultado):
    assert resultado["metricas"]["k_elegido"] == 5


def test_m2_separacion_aceptable_entre_grupos(resultado):
    """Una silueta mayor que 0,25 indica una estructura de grupos razonable."""
    assert resultado["metricas"]["silueta_final"] > 0.25


def test_m3_ningun_grupo_vacio_ni_diminuto(resultado):
    tamanos = pd.Series(resultado["grupos"]).value_counts()
    assert len(tamanos) == 5
    assert tamanos.min() / tamanos.sum() > 0.05


def test_m4_kmeans_y_jerarquico_coinciden(resultado):
    assert resultado["metricas"]["ari_kmeans_vs_ward"] > 0.90


def test_m5_los_grupos_tienen_sentido_operativo(resultado):
    """Sin conocer el tipo de día ni de zona, los grupos los recuperan casi por completo."""
    assert resultado["metricas"]["ari_vs_tipo_dia_y_zona"] > 0.85


def test_m6_no_mezcla_dias_laborales_con_fines_de_semana(resultado):
    p = resultado["perfiles"].assign(laboral=lambda t: t["tipo_dia"] == "Laboral")
    pureza = p.groupby("grupo")["laboral"].mean()
    assert ((pureza > 0.9) | (pureza < 0.1)).all()


def test_m7_resultado_reproducible():
    X = ag.matriz(ag.construir_perfiles(ag.cargar_afluencia()))
    a = ag.construir_kmeans(5).fit(X).named_steps["kmeans"].labels_
    b = ag.construir_kmeans(5).fit(X).named_steps["kmeans"].labels_
    assert adjusted_rand_score(a, b) == 1.0


def test_m8_los_dias_de_partido_se_parecen_al_centro(resultado):
    """Con partido, Estadio y Suramericana cargan en la tarde como una estación del centro."""
    p = resultado["perfiles"]
    con_evento = p[p["hubo_evento"] == 1]
    assert (con_evento["nombre_grupo"] == "Laboral centro").mean() > 0.9


PERFIL_MANANA = [0.03, 0.08, 0.12, 0.11, 0.08, 0.055, 0.045, 0.045, 0.05, 0.05,
                 0.045, 0.045, 0.05, 0.055, 0.05, 0.04, 0.03, 0.02, 0.01]


@pytest.mark.parametrize("perfil,esperado", [
    (PERFIL_MANANA, "Laboral residencial"),        # pico a las 6:00
    (PERFIL_MANANA[::-1], "Laboral centro"),       # el mismo, invertido: pico en la tarde
])
def test_m9_asigna_perfiles_nuevos(resultado, perfil, esperado):
    g = ag.asignar(resultado["modelo"], resultado["mapa"], perfil)
    assert resultado["nombres"][g] == esperado


def test_m10_archivo_incompleto_se_rechaza(tmp_path):
    ruta = tmp_path / "malo.csv"
    pd.DataFrame({"estacion": ["Niquía"], "hora": [6]}).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match="faltan columnas"):
        ag.cargar_afluencia(ruta)
