"""
Modelo de aprendizaje supervisado: árbol de decisión que predice el nivel de
congestión (Bajo / Medio / Alto) de una estación del Metro de Medellín.

Actividad 3 - Inteligencia Artificial - Métodos de aprendizaje supervisado.
Base teórica: capítulo 17 de Palma Méndez (2008), aprendizaje de árboles y
reglas de decisión. Se usa el criterio de entropía (ganancia de información),
el mismo que emplean ID3 y C4.5.

Uso:
    python src/modelo_congestion.py

Pasos que ejecuta:
    1. Carga y valida el dataset.
    2. Separa variables predictoras (X) y etiqueta (y).
    3. Divide en entrenamiento (80 %) y prueba (20 %).
    4. Busca los mejores hiperparámetros con validación cruzada.
    5. Evalúa en el conjunto de prueba y lo compara con una línea base.
    6. Guarda métricas, reglas del árbol y gráficos en resultados/.
"""

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # permite generar los gráficos sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import (GridSearchCV, StratifiedKFold,
                                     train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

RAIZ = Path(__file__).resolve().parent.parent
RUTA_DATOS = RAIZ / "data" / "afluencia_metro_medellin.csv"
CARPETA_RESULTADOS = RAIZ / "resultados"
RUTA_MODELO = CARPETA_RESULTADOS / "arbol_congestion.joblib"

SEMILLA = 42
ETIQUETA = "nivel_congestion"
CLASES = ["Bajo", "Medio", "Alto"]  # orden lógico, de menor a mayor

# Variables predictoras. Todas se conocen ANTES de que ocurra la hora que se
# quiere predecir (calendario, estación, pronóstico del clima, eventos).
CATEGORICAS = ["estacion", "linea", "tipo_zona", "dia_semana", "tipo_dia", "clima"]
NUMERICAS = ["hora", "es_transferencia", "evento_especial"]
PREDICTORAS = CATEGORICAS + NUMERICAS

# Columnas que NO pueden entrar al modelo: la etiqueta se calcula a partir de
# ellas, así que usarlas sería "hacer trampa" (fuga de información).
EXCLUIDAS = ["fecha", "pasajeros_hora", "indice_ocupacion"]

# Estilo de los gráficos.
FONDO, TEXTO, TEXTO_SUAVE, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
AZUL, NARANJA = "#2a78d6", "#eb6834"
ESCALA_AZUL = LinearSegmentedColormap.from_list(
    "azul", ["#f3f7fd", "#9ec5f4", "#2a78d6", "#0d366b"])


# --------------------------------------------------------------------------
# 1. Datos
# --------------------------------------------------------------------------
def cargar_datos(ruta: Path = RUTA_DATOS) -> pd.DataFrame:
    """Lee el CSV y verifica que tenga lo mínimo para entrenar."""
    datos = pd.read_csv(ruta)
    faltantes = set(PREDICTORAS + [ETIQUETA]) - set(datos.columns)
    if faltantes:
        raise ValueError(f"Al dataset le faltan columnas: {sorted(faltantes)}")
    if datos[PREDICTORAS + [ETIQUETA]].isna().any().any():
        raise ValueError("El dataset tiene valores nulos en columnas del modelo.")
    return datos


def separar_xy(datos: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Devuelve X (solo predictoras) e y (etiqueta)."""
    return datos[PREDICTORAS].copy(), datos[ETIQUETA].copy()


# --------------------------------------------------------------------------
# 2. Modelo
# --------------------------------------------------------------------------
def construir_modelo(**parametros_arbol) -> Pipeline:
    """
    Pipeline = preparación de datos + árbol de decisión.

    scikit-learn implementa CART, que solo acepta números, así que las
    variables categóricas se convierten a columnas 0/1 (one-hot). Con
    handle_unknown="ignore" el modelo no se rompe si llega una categoría que
    no vio al entrenar.
    """
    preparacion = ColumnTransformer([
        ("categoricas", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
        ("numericas", "passthrough", NUMERICAS),
    ])
    arbol = DecisionTreeClassifier(criterion="entropy", random_state=SEMILLA,
                                   **parametros_arbol)
    return Pipeline([("preparacion", preparacion), ("arbol", arbol)])


def buscar_mejor_arbol(X_train, y_train) -> GridSearchCV:
    """
    Prueba varias combinaciones de profundidad y tamaño mínimo de hoja con
    validación cruzada de 5 particiones y se queda con la mejor. Limitar la
    profundidad y el tamaño de hoja es la forma de "podar" el árbol para que
    no memorice los datos de entrenamiento (sobreajuste).
    """
    rejilla = {
        "arbol__max_depth": [3, 5, 8, 10, 12, 15, None],
        "arbol__min_samples_leaf": [1, 5, 10, 20, 40],
    }
    particiones = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    busqueda = GridSearchCV(construir_modelo(), rejilla, cv=particiones,
                            scoring="accuracy", n_jobs=-1)
    busqueda.fit(X_train, y_train)
    return busqueda


def nombres_de_variables(modelo: Pipeline) -> list[str]:
    """Nombres legibles de las columnas después del one-hot."""
    crudos = modelo.named_steps["preparacion"].get_feature_names_out()
    return [n.replace("categoricas__", "").replace("numericas__", "") for n in crudos]


def predecir(modelo: Pipeline, estacion: str, linea: str, tipo_zona: str,
             es_transferencia: int, dia_semana: str, tipo_dia: str, hora: int,
             clima: str = "Seco", evento_especial: int = 0) -> dict:
    """Predice el nivel de congestión de un caso y devuelve las probabilidades."""
    caso = pd.DataFrame([{
        "estacion": estacion, "linea": linea, "tipo_zona": tipo_zona,
        "dia_semana": dia_semana, "tipo_dia": tipo_dia, "clima": clima,
        "hora": hora, "es_transferencia": es_transferencia,
        "evento_especial": evento_especial,
    }])[PREDICTORAS]
    probabilidades = modelo.predict_proba(caso)[0]
    return {
        "prediccion": modelo.predict(caso)[0],
        "probabilidades": {c: round(float(p), 3)
                           for c, p in zip(modelo.classes_, probabilidades)},
    }


# --------------------------------------------------------------------------
# 3. Evaluación
# --------------------------------------------------------------------------
def evaluar(modelo: Pipeline, X_test, y_test) -> dict:
    predicho = modelo.predict(X_test)
    return {
        "exactitud": round(accuracy_score(y_test, predicho), 4),
        "f1_macro": round(f1_score(y_test, predicho, average="macro"), 4),
        "matriz_confusion": confusion_matrix(y_test, predicho, labels=CLASES).tolist(),
        "reporte": classification_report(y_test, predicho, labels=CLASES, digits=3),
    }


def importancia_por_variable(modelo: Pipeline) -> pd.Series:
    """Suma la importancia de las columnas one-hot de vuelta a su variable original."""
    importancias = modelo.named_steps["arbol"].feature_importances_
    acumulado = {v: 0.0 for v in PREDICTORAS}
    for nombre, valor in zip(nombres_de_variables(modelo), importancias):
        original = next(v for v in PREDICTORAS if nombre == v or nombre.startswith(v + "_"))
        acumulado[original] += valor
    return pd.Series(acumulado).sort_values(ascending=False)


def curva_de_profundidad(X_train, y_train, profundidades) -> pd.DataFrame:
    """Exactitud en entrenamiento y en validación cruzada según la profundidad."""
    from sklearn.model_selection import cross_validate
    particiones = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    filas = []
    for p in profundidades:
        r = cross_validate(construir_modelo(max_depth=p), X_train, y_train,
                           cv=particiones, scoring="accuracy",
                           return_train_score=True, n_jobs=-1)
        filas.append({"profundidad": p,
                      "entrenamiento": r["train_score"].mean(),
                      "validacion": r["test_score"].mean()})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------
# 4. Gráficos
# --------------------------------------------------------------------------
def _lienzo(ancho, alto):
    fig, ax = plt.subplots(figsize=(ancho, alto), facecolor=FONDO)
    ax.set_facecolor(FONDO)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)
    ax.tick_params(colors=TEXTO_SUAVE, length=0)
    return fig, ax


def grafico_matriz_confusion(matriz, ruta):
    matriz = np.array(matriz)
    fig, ax = _lienzo(5.6, 4.8)
    ax.imshow(matriz, cmap=ESCALA_AZUL, vmin=0)
    total_fila = matriz.sum(axis=1, keepdims=True)
    for i in range(len(CLASES)):
        for j in range(len(CLASES)):
            claro = matriz[i, j] > matriz.max() * 0.55
            ax.text(j, i - 0.08, f"{matriz[i, j]:,}".replace(",", "."), ha="center",
                    va="center", fontsize=13, fontweight="bold",
                    color="white" if claro else TEXTO)
            ax.text(j, i + 0.2, f"{matriz[i, j] / total_fila[i, 0]:.0%}", ha="center",
                    va="center", fontsize=9, color="white" if claro else TEXTO_SUAVE)
    ax.set_xticks(range(len(CLASES)), CLASES)
    ax.set_yticks(range(len(CLASES)), CLASES)
    ax.set_xlabel("Nivel que predijo el modelo", color=TEXTO_SUAVE)
    ax.set_ylabel("Nivel real", color=TEXTO_SUAVE)
    ax.set_title("Matriz de confusión (conjunto de prueba)", color=TEXTO,
                 loc="left", fontsize=12, fontweight="bold", pad=12)
    for lado in ax.spines.values():
        lado.set_visible(False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)


def grafico_importancia(importancias: pd.Series, ruta):
    datos = importancias.sort_values()
    fig, ax = _lienzo(6.8, 4.2)
    barras = ax.barh(datos.index, datos.values, color=AZUL, height=0.6)
    for barra, valor in zip(barras, datos.values):
        ax.text(valor + 0.008, barra.get_y() + barra.get_height() / 2,
                f"{valor:.1%}", va="center", fontsize=9, color=TEXTO_SUAVE)
    ax.set_xlim(0, datos.max() * 1.15)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", colors=TEXTO)
    ax.set_title("Importancia de cada variable en el árbol", color=TEXTO,
                 loc="left", fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)


def grafico_profundidad(curva: pd.DataFrame, mejor_profundidad, ruta):
    fig, ax = _lienzo(6.8, 4.2)
    ax.plot(curva["profundidad"], curva["entrenamiento"], color=NARANJA, lw=2,
            marker="o", ms=5, label="Entrenamiento")
    ax.plot(curva["profundidad"], curva["validacion"], color=AZUL, lw=2,
            marker="o", ms=5, label="Validación cruzada")
    ultimo = curva.iloc[-1]
    ax.text(ultimo["profundidad"] + 0.3, ultimo["entrenamiento"],
            f"{ultimo['entrenamiento']:.1%}", va="center", fontsize=9, color=TEXTO_SUAVE)
    ax.text(ultimo["profundidad"] + 0.3, ultimo["validacion"],
            f"{ultimo['validacion']:.1%}", va="center", fontsize=9, color=TEXTO_SUAVE)
    if mejor_profundidad is not None:
        ax.axvline(mejor_profundidad, color=TEXTO_SUAVE, lw=1, ls=":")
        ax.text(mejor_profundidad + 0.2, curva["validacion"].min(),
                f"profundidad elegida: {mejor_profundidad}", fontsize=9, color=TEXTO_SUAVE)
    ax.set_xlim(curva["profundidad"].min() - 0.5, curva["profundidad"].max() + 2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(axis="y", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("Profundidad máxima del árbol", color=TEXTO_SUAVE)
    ax.set_ylabel("Exactitud", color=TEXTO_SUAVE)
    ax.legend(frameon=False, loc="lower right", labelcolor=TEXTO)
    ax.set_title("Más profundidad no siempre es mejor (sobreajuste)", color=TEXTO,
                 loc="left", fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)


def grafico_arbol(modelo: Pipeline, ruta, niveles=2):
    fig, ax = plt.subplots(figsize=(12, 6), facecolor=FONDO)
    plot_tree(modelo.named_steps["arbol"], max_depth=niveles,
              feature_names=nombres_de_variables(modelo),
              class_names=list(modelo.classes_), filled=True, rounded=True,
              impurity=False, proportion=True, fontsize=10, ax=ax)
    orden = ", ".join(modelo.classes_)
    ax.set_title(f"Primeros {niveles} niveles del árbol de decisión\n"
                 f"value = proporción de cada clase en el nodo, en el orden [{orden}]",
                 color=TEXTO, loc="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, facecolor=FONDO)
    plt.close(fig)


# --------------------------------------------------------------------------
# 5. Programa principal
# --------------------------------------------------------------------------
def entrenar(guardar: bool = True, verboso: bool = True) -> dict:
    """Ejecuta todo el flujo y devuelve el modelo junto con sus métricas."""
    def decir(*a):
        if verboso:
            print(*a)

    decir("1) Cargando datos...")
    datos = cargar_datos()
    X, y = separar_xy(datos)
    decir(f"   {len(datos):,} registros | {len(PREDICTORAS)} variables predictoras")
    decir("   Distribución de la etiqueta:",
          y.value_counts(normalize=True).round(3).reindex(CLASES).to_dict())

    decir("\n2) Dividiendo en entrenamiento (80 %) y prueba (20 %)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEMILLA)
    decir(f"   entrenamiento: {len(X_train):,} | prueba: {len(X_test):,}")

    decir("\n3) Línea base: predecir siempre la clase más frecuente...")
    base = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    exactitud_base = round(accuracy_score(y_test, base.predict(X_test)), 4)
    decir(f"   exactitud de la línea base: {exactitud_base:.1%}")

    decir("\n4) Buscando el mejor árbol con validación cruzada (5 particiones)...")
    busqueda = buscar_mejor_arbol(X_train, y_train)
    modelo = busqueda.best_estimator_
    mejores = {k.replace("arbol__", ""): v for k, v in busqueda.best_params_.items()}
    decir(f"   mejores hiperparámetros: {mejores}")
    decir(f"   exactitud media en validación cruzada: {busqueda.best_score_:.1%}")

    decir("\n5) Evaluando en el conjunto de prueba (datos que el árbol nunca vio)...")
    metricas = evaluar(modelo, X_test, y_test)
    exactitud_train = round(accuracy_score(y_train, modelo.predict(X_train)), 4)
    arbol = modelo.named_steps["arbol"]
    decir(f"   exactitud en prueba:        {metricas['exactitud']:.1%}")
    decir(f"   exactitud en entrenamiento: {exactitud_train:.1%}")
    decir(f"   F1 macro:                   {metricas['f1_macro']:.3f}")
    decir(f"   tamaño del árbol: profundidad {arbol.get_depth()}, {arbol.get_n_leaves()} hojas")
    decir("\n" + metricas["reporte"])

    importancias = importancia_por_variable(modelo)
    decir("Importancia de las variables:")
    decir(importancias.round(3).to_string())

    resumen = {
        "registros": len(datos),
        "registros_entrenamiento": len(X_train),
        "registros_prueba": len(X_test),
        "variables_predictoras": PREDICTORAS,
        "mejores_hiperparametros": mejores,
        "exactitud_linea_base": exactitud_base,
        "exactitud_validacion_cruzada": round(float(busqueda.best_score_), 4),
        "exactitud_entrenamiento": exactitud_train,
        "exactitud_prueba": metricas["exactitud"],
        "f1_macro_prueba": metricas["f1_macro"],
        "profundidad_arbol": int(arbol.get_depth()),
        "hojas_arbol": int(arbol.get_n_leaves()),
        "clases": CLASES,
        "matriz_confusion": metricas["matriz_confusion"],
        "importancia_variables": {k: round(float(v), 4) for k, v in importancias.items()},
    }

    if guardar:
        decir("\n6) Guardando resultados en resultados/ ...")
        CARPETA_RESULTADOS.mkdir(exist_ok=True)
        joblib.dump(modelo, RUTA_MODELO)
        (CARPETA_RESULTADOS / "metricas.json").write_text(
            json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
        (CARPETA_RESULTADOS / "reporte_clasificacion.txt").write_text(
            metricas["reporte"], encoding="utf-8")
        (CARPETA_RESULTADOS / "reglas_arbol.txt").write_text(
            export_text(arbol, feature_names=nombres_de_variables(modelo), max_depth=4),
            encoding="utf-8")

        curva = curva_de_profundidad(X_train, y_train, [2, 4, 6, 8, 10, 12, 14, 16, 20, 25])
        curva.round(4).to_csv(CARPETA_RESULTADOS / "curva_profundidad.csv", index=False)

        grafico_matriz_confusion(metricas["matriz_confusion"],
                                 CARPETA_RESULTADOS / "matriz_confusion.png")
        grafico_importancia(importancias, CARPETA_RESULTADOS / "importancia_variables.png")
        grafico_profundidad(curva, mejores["max_depth"],
                            CARPETA_RESULTADOS / "curva_profundidad.png")
        grafico_arbol(modelo, CARPETA_RESULTADOS / "arbol_decision.png")
        decir("   listo: metricas.json, reporte_clasificacion.txt, reglas_arbol.txt,")
        decir("          curva_profundidad.csv y 4 gráficos .png")

    return {"modelo": modelo, "resumen": resumen,
            "X_test": X_test, "y_test": y_test}


if __name__ == "__main__":
    entrenar()
