"""Pruebas de los perfiles diarios que alimentan el agrupamiento (D1 a D6)."""
import numpy as np

import agrupamiento as ag


def test_d1_un_perfil_por_estacion_y_dia(perfiles):
    assert len(perfiles) == 28 * 56                  # 28 estación-línea × 56 días
    assert not perfiles.duplicated(subset=ag.CLAVE).any()


def test_d2_diecinueve_horas_por_perfil(perfiles):
    assert all(c in perfiles.columns for c in ag.COLUMNAS_PERFIL)
    assert len(ag.COLUMNAS_PERFIL) == 19


def test_d3_sin_valores_nulos(perfiles):
    assert perfiles[ag.COLUMNAS_PERFIL + ["pasajeros_dia"]].isna().sum().sum() == 0


def test_d4_cada_perfil_suma_uno(perfiles):
    sumas = perfiles[ag.COLUMNAS_PERFIL].sum(axis=1)
    assert np.allclose(sumas, 1.0, atol=1e-3)
    assert (perfiles[ag.COLUMNAS_PERFIL] >= 0).all().all()


def test_d5_los_totales_coinciden_con_el_archivo_original():
    datos = ag.cargar_afluencia()
    perfiles = ag.construir_perfiles(datos)
    assert perfiles["pasajeros_dia"].sum() == datos["pasajeros_hora"].sum()


def test_d6_domingos_sin_servicio_a_las_4_ni_a_las_22(perfiles):
    domingos = perfiles[perfiles["tipo_dia"] == "Domingo_Festivo"]
    assert (domingos["h04"] == 0).all() and (domingos["h22"] == 0).all()
