"""Pruebas del modelo de árbol de decisión (M1 a M11)."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import recall_score

import modelo_congestion as mc


def test_m1_sin_fuga_de_informacion():
    """El modelo no puede usar columnas de las que se deriva la etiqueta."""
    assert not set(mc.PREDICTORAS) & set(mc.EXCLUIDAS)
    assert mc.ETIQUETA not in mc.PREDICTORAS


def test_m2_exactitud_minima_en_prueba(entrenamiento):
    assert entrenamiento["resumen"]["exactitud_prueba"] >= 0.80


def test_m3_supera_ampliamente_la_linea_base(entrenamiento):
    r = entrenamiento["resumen"]
    assert r["exactitud_prueba"] - r["exactitud_linea_base"] >= 0.25


def test_m4_sobreajuste_controlado(entrenamiento):
    r = entrenamiento["resumen"]
    assert r["exactitud_entrenamiento"] - r["exactitud_prueba"] <= 0.05


def test_m5_detecta_la_congestion_alta(entrenamiento):
    """La clase Alto es la que más importa operativamente."""
    e = entrenamiento
    recall = recall_score(e["y_test"], e["modelo"].predict(e["X_test"]),
                          labels=["Alto"], average=None)[0]
    assert recall >= 0.70


def test_m6_casi_no_hay_errores_graves(entrenamiento):
    """Confundir Bajo con Alto (o al revés) debe ser menos del 1 % de los casos."""
    m = np.array(entrenamiento["resumen"]["matriz_confusion"])  # orden Bajo, Medio, Alto
    assert (m[0, 2] + m[2, 0]) / m.sum() < 0.01


def test_m7_entrenamiento_reproducible(datos):
    X, y = mc.separar_xy(datos)
    a = mc.construir_modelo(min_samples_leaf=10).fit(X, y).predict(X)
    b = mc.construir_modelo(min_samples_leaf=10).fit(X, y).predict(X)
    assert (a == b).all()


CASOS = [
    # estación, línea, zona, transf., día, tipo de día, hora, clima, evento, esperado
    ("San Antonio", "A", "Centro_Empleo", 1, "Viernes", "Laboral", 18, "Seco", 0, "Alto"),
    ("Niquía", "A", "Residencial", 0, "Lunes", "Laboral", 6, "Seco", 0, "Alto"),
    ("Niquía", "A", "Residencial", 0, "Lunes", "Domingo_Festivo", 6, "Seco", 0, "Bajo"),
    ("La Estrella", "A", "Residencial", 0, "Domingo", "Domingo_Festivo", 6, "Lluvia", 0, "Bajo"),
    ("Poblado", "A", "Centro_Empleo", 0, "Martes", "Laboral", 22, "Seco", 0, "Bajo"),
    ("Madera", "A", "Residencial", 0, "Martes", "Laboral", 7, "Seco", 0, "Medio"),
    ("Estadio", "B", "Mixta", 0, "Sábado", "Sábado", 19, "Seco", 0, "Bajo"),
    ("Estadio", "B", "Mixta", 0, "Sábado", "Sábado", 19, "Seco", 1, "Alto"),
]


@pytest.mark.parametrize("est,lin,zona,tr,dia,tipo,hora,clima,evento,esperado", CASOS)
def test_m8_casos_de_sentido_comun(entrenamiento, est, lin, zona, tr, dia, tipo,
                                   hora, clima, evento, esperado):
    r = mc.predecir(entrenamiento["modelo"], est, lin, zona, tr, dia, tipo, hora,
                    clima, evento)
    assert r["prediccion"] == esperado


def test_m9_estacion_desconocida_no_rompe_el_modelo(entrenamiento):
    r = mc.predecir(entrenamiento["modelo"], "Estación Nueva", "A", "Mixta", 0,
                    "Jueves", "Laboral", 12)
    assert r["prediccion"] in mc.CLASES


def test_m10_probabilidades_validas(entrenamiento):
    e = entrenamiento
    proba = e["modelo"].predict_proba(e["X_test"])
    assert proba.shape == (len(e["X_test"]), 3)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_m11_cargar_datos_rechaza_archivo_incompleto(tmp_path):
    ruta = tmp_path / "malo.csv"
    pd.DataFrame({"estacion": ["Niquía"], "hora": [6]}).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match="faltan columnas"):
        mc.cargar_datos(ruta)
