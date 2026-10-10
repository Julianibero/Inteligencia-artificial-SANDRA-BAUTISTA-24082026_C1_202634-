"""Configuración común: rutas y una única ejecución del agrupamiento para todas las pruebas."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))


@pytest.fixture(scope="session")
def resultado():
    from agrupamiento import ejecutar
    return ejecutar(guardar=False, verboso=False)


@pytest.fixture(scope="session")
def perfiles(resultado):
    return resultado["perfiles"]
