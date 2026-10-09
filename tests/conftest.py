"""Configuración común de las pruebas: rutas y un único entrenamiento compartido."""
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "data"))


@pytest.fixture(scope="session")
def datos():
    return pd.read_csv(RAIZ / "data" / "afluencia_metro_medellin.csv")


@pytest.fixture(scope="session")
def estaciones():
    return pd.read_csv(RAIZ / "data" / "estaciones.csv")


@pytest.fixture(scope="session")
def entrenamiento():
    """Entrena una sola vez para todas las pruebas (no escribe archivos)."""
    from modelo_congestion import entrenar
    return entrenar(guardar=False, verboso=False)
