"""
Modelo de aprendizaje no supervisado: agrupamiento de los patrones horarios de
demanda de las estaciones del Metro de Medellín.

Actividad 4 - Inteligencia Artificial - Métodos de aprendizaje no supervisado.
Base teórica: capítulo 16 de Palma Méndez y Marín Morales (2008), técnicas de
agrupamiento. Se usan k-means (agrupamiento por particiones) y el método
jerárquico aglomerativo de Ward, y se comparan sus resultados.

Idea: cada estación, cada día, tiene un "perfil" de 19 valores (qué parte de su
demanda diaria entra en cada hora, de 4:00 a 22:00). El algoritmo agrupa los
perfiles que se parecen SIN que nadie le diga qué tipo de día o de estación es.
Después revisamos si los grupos que encontró tienen sentido.

Uso:
    python src/agrupamiento.py
"""

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parent.parent
RUTA_AFLUENCIA = RAIZ / "data" / "afluencia_metro_medellin.csv"
RUTA_PERFILES = RAIZ / "data" / "perfiles_estacion_dia.csv"
CARPETA_RESULTADOS = RAIZ / "resultados"
RUTA_MODELO = CARPETA_RESULTADOS / "modelo_kmeans.joblib"

SEMILLA = 42
HORAS = list(range(4, 23))                       # 4:00 a 22:00
COLUMNAS_PERFIL = [f"h{h:02d}" for h in HORAS]   # h04, h05, ..., h22
CLAVE = ["fecha", "linea", "estacion"]
K_CANDIDATOS = range(2, 11)

# Orden y nombre con el que se presentan los grupos. El nombre se asigna
# DESPUÉS de agrupar, mirando qué tipo de día y de zona predomina en cada grupo.
NOMBRES = [
    (("Laboral", "Residencial"), "Laboral residencial"),
    (("Laboral", "Centro_Empleo"), "Laboral centro"),
    (("Laboral", "Mixta"), "Laboral mixta"),
    (("Sábado", None), "Sábado"),
    (("Domingo_Festivo", None), "Domingo y festivo"),
]

# Estilo de los gráficos
FONDO, TEXTO, TEXTO_SUAVE, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
AZUL, GRIS = "#2a78d6", "#c3c2b7"
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
MARCADORES = ["o", "s", "^", "D", "v"]


# --------------------------------------------------------------------------
# 1. Datos: de registros por hora a perfiles diarios
# --------------------------------------------------------------------------
def cargar_afluencia(ruta: Path = RUTA_AFLUENCIA) -> pd.DataFrame:
    datos = pd.read_csv(ruta)
    necesarias = set(CLAVE + ["hora", "pasajeros_hora", "tipo_dia", "tipo_zona",
                              "dia_semana", "evento_especial"])
    faltantes = necesarias - set(datos.columns)
    if faltantes:
        raise ValueError(f"Al archivo le faltan columnas: {sorted(faltantes)}")
    return datos


def construir_perfiles(datos: pd.DataFrame) -> pd.DataFrame:
    """
    Una fila por estación y día. Las columnas h04..h22 dicen qué fracción de
    los pasajeros del día entró en cada hora (suman 1). Así se compara la
    FORMA de la demanda y no el tamaño de la estación.
    """
    tabla = datos.pivot_table(index=CLAVE, columns="hora", values="pasajeros_hora",
                              aggfunc="sum", fill_value=0)
    tabla = tabla.reindex(columns=HORAS, fill_value=0)
    total = tabla.sum(axis=1)
    fracciones = tabla.div(total, axis=0).round(5)
    fracciones.columns = COLUMNAS_PERFIL

    contexto = datos.groupby(CLAVE).agg(
        dia_semana=("dia_semana", "first"), tipo_dia=("tipo_dia", "first"),
        tipo_zona=("tipo_zona", "first"),
        hubo_evento=("evento_especial", "max"))
    perfiles = contexto.join(fracciones)
    perfiles.insert(4, "pasajeros_dia", total.astype(int))
    return perfiles.reset_index()


def matriz(perfiles: pd.DataFrame) -> np.ndarray:
    """Solo las 19 fracciones horarias: lo único que ve el algoritmo."""
    return perfiles[COLUMNAS_PERFIL].to_numpy()


# --------------------------------------------------------------------------
# 2. Elección del número de grupos
# --------------------------------------------------------------------------
def construir_kmeans(k: int) -> Pipeline:
    """Estandariza cada hora y aplica k-means (10 arranques distintos)."""
    return Pipeline([("escala", StandardScaler()),
                     ("kmeans", KMeans(n_clusters=k, n_init=10, random_state=SEMILLA))])


def evaluar_k(X: np.ndarray, candidatos=K_CANDIDATOS) -> pd.DataFrame:
    """Inercia (para el método del codo) y silueta para cada k."""
    filas = []
    for k in candidatos:
        modelo = construir_kmeans(k).fit(X)
        Xs = modelo.named_steps["escala"].transform(X)
        etiquetas = modelo.named_steps["kmeans"].labels_
        filas.append({"k": k,
                      "inercia": round(float(modelo.named_steps["kmeans"].inertia_), 1),
                      "silueta": round(float(silhouette_score(Xs, etiquetas)), 4)})
    return pd.DataFrame(filas)


def detectar_codo(evaluacion: pd.DataFrame) -> int:
    """
    Método del codo automatizado: normaliza la curva de inercia y elige el k
    más alejado de la recta que une el primer y el último punto.
    """
    x = evaluacion["k"].to_numpy(float)
    y = evaluacion["inercia"].to_numpy(float)
    xn = (x - x.min()) / (x.max() - x.min())
    yn = (y - y.min()) / (y.max() - y.min())
    distancia = np.abs(yn - (yn[0] + (yn[-1] - yn[0]) * xn))
    return int(x[distancia.argmax()])


# --------------------------------------------------------------------------
# 3. Interpretación de los grupos
# --------------------------------------------------------------------------
def nombrar_grupos(perfiles: pd.DataFrame, etiquetas: np.ndarray) -> dict:
    """
    Da nombre a cada grupo según el tipo de día (y de zona, si es laboral) que
    predomina en él. Estas columnas NO se usaron para agrupar: solo sirven
    para interpretar el resultado.
    """
    nombres = {}
    for g in np.unique(etiquetas):
        miembros = perfiles[etiquetas == g]
        dia = miembros["tipo_dia"].mode()[0]
        zona = miembros["tipo_zona"].mode()[0] if dia == "Laboral" else None
        nombre = dict(NOMBRES).get((dia, zona), f"Grupo {g}")
        while nombre in nombres.values():
            nombre += " (2)"
        nombres[int(g)] = nombre
    return nombres


def renumerar(etiquetas: np.ndarray, nombres: dict) -> tuple[np.ndarray, dict]:
    """Numera los grupos del 1 al k en el orden de la lista NOMBRES."""
    orden = [n for _, n in NOMBRES]
    viejos = sorted(nombres, key=lambda g: orden.index(nombres[g])
                    if nombres[g] in orden else 99)
    mapa = {viejo: nuevo for nuevo, viejo in enumerate(viejos, start=1)}
    return np.vectorize(mapa.get)(etiquetas), {mapa[g]: n for g, n in nombres.items()}


def grupo_esperado(perfiles: pd.DataFrame) -> pd.Series:
    """Agrupación 'de referencia' para validar: tipo de zona en días laborales y tipo de día en los demás."""
    return pd.Series(np.where(perfiles["tipo_dia"] == "Laboral",
                              "Laboral-" + perfiles["tipo_zona"], perfiles["tipo_dia"]),
                     index=perfiles.index)


def resumen_grupos(perfiles: pd.DataFrame, grupos: np.ndarray, nombres: dict) -> pd.DataFrame:
    filas = []
    for g in sorted(nombres):
        m = perfiles[grupos == g]
        medio = m[COLUMNAS_PERFIL].mean()
        filas.append({
            "grupo": g, "nombre": nombres[g], "perfiles": len(m),
            "porcentaje": round(len(m) / len(perfiles) * 100, 1),
            "hora_pico": HORAS[int(medio.to_numpy().argmax())],
            "fraccion_en_pico": round(float(medio.max()), 3),
            "pasajeros_dia_promedio": int(m["pasajeros_dia"].mean()),
            "estaciones_distintas": m["estacion"].nunique(),
            "con_evento": int(m["hubo_evento"].sum()),
        })
    return pd.DataFrame(filas)


def asignar(modelo: Pipeline, mapa: dict, perfil: list[float]) -> int:
    """Asigna un perfil nuevo (19 fracciones) al grupo más cercano."""
    crudo = int(modelo.predict(np.asarray(perfil, float).reshape(1, -1))[0])
    return mapa[crudo]


# --------------------------------------------------------------------------
# 4. Gráficos
# --------------------------------------------------------------------------
def _ejes(ax):
    ax.set_facecolor(FONDO)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)
    ax.tick_params(colors=TEXTO_SUAVE, length=0)
    ax.grid(axis="y", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)


def grafico_codo_silueta(evaluacion: pd.DataFrame, k: int, ruta):
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.9), facecolor=FONDO)
    for ax, col, titulo in [(a, "inercia", "Método del codo: inercia"),
                            (b, "silueta", "Coeficiente de silueta")]:
        _ejes(ax)
        ax.plot(evaluacion["k"], evaluacion[col], color=AZUL, lw=2, marker="o", ms=5)
        fila = evaluacion[evaluacion["k"] == k].iloc[0]
        ax.plot([k], [fila[col]], marker="o", ms=11, mfc="none", mec=TEXTO, mew=1.5)
        ax.annotate(f"k = {k}", (k, fila[col]), xytext=(10, 10),
                    textcoords="offset points", fontsize=9, color=TEXTO)
        ax.set_xticks(evaluacion["k"])
        ax.set_xlabel("Número de grupos (k)", color=TEXTO_SUAVE)
        ax.set_title(titulo, color=TEXTO, loc="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)


def grafico_perfiles(perfiles, grupos, nombres, ruta):
    """Un panel por grupo: su perfil medio en azul y los demás en gris."""
    medios = {g: perfiles[grupos == g][COLUMNAS_PERFIL].mean().to_numpy() for g in nombres}
    tope = max(m.max() for m in medios.values()) * 1.12
    fig, rejilla = plt.subplots(2, 3, figsize=(11, 6.6), sharey=True, facecolor=FONDO)
    ejes = rejilla.ravel()
    for ax in ejes[len(nombres):]:
        ax.axis("off")
    for ax, g in zip(ejes, sorted(nombres)):
        _ejes(ax)
        for otro, m in medios.items():
            if otro != g:
                ax.plot(HORAS, m, color=GRIS, lw=1)
        ax.plot(HORAS, medios[g], color=AZUL, lw=2.4)
        ax.set_ylim(0, tope)
        ax.set_xticks([5, 8, 12, 17, 21])
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        n = int((grupos == g).sum())
        ax.set_title(f"{g}. {nombres[g]}\n{n} perfiles", color=TEXTO, loc="left",
                     fontsize=10, fontweight="bold")
        ax.set_xlabel("Hora del día", color=TEXTO_SUAVE, fontsize=9)
    for ax in (ejes[0], ejes[3]):
        ax.set_ylabel("Parte de la demanda diaria", color=TEXTO_SUAVE)
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)


def grafico_pca(modelo, X, grupos, nombres, ruta):
    """Proyección a 2 dimensiones solo para poder dibujar los grupos."""
    Xs = modelo.named_steps["escala"].transform(X)
    pca = PCA(n_components=2, random_state=SEMILLA).fit(Xs)
    P = pca.transform(Xs)
    fig, ax = plt.subplots(figsize=(7.5, 5.2), facecolor=FONDO)
    _ejes(ax)
    ax.grid(False)
    for i, g in enumerate(sorted(nombres)):
        sel = grupos == g
        ax.scatter(P[sel, 0], P[sel, 1], s=14, color=COLORES[i], marker=MARCADORES[i],
                   alpha=0.75, edgecolors=FONDO, linewidths=0.4, label=f"{g}. {nombres[g]}")
        cx, cy = P[sel].mean(axis=0)
        ax.annotate(nombres[g], (cx, cy), fontsize=9, color=TEXTO, fontweight="bold",
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", fc=FONDO, ec=REJILLA, alpha=0.9))
    var = pca.explained_variance_ratio_
    ax.set_xlabel(f"Componente principal 1 ({var[0]:.0%} de la variación)", color=TEXTO_SUAVE)
    ax.set_ylabel(f"Componente principal 2 ({var[1]:.0%})", color=TEXTO_SUAVE)
    ax.legend(frameon=False, fontsize=8, loc="best", labelcolor=TEXTO)
    ax.set_title("Los cinco grupos vistos en dos dimensiones", color=TEXTO, loc="left",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)
    return [round(float(v), 4) for v in var]


def grafico_dendrograma(X, k, ruta):
    Xs = StandardScaler().fit_transform(X)
    enlaces = linkage(Xs, method="ward")
    corte = (enlaces[-k, 2] + enlaces[-k + 1, 2]) / 2
    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=FONDO)
    _ejes(ax)
    ax.grid(False)
    dendrogram(enlaces, truncate_mode="lastp", p=25, color_threshold=0,
               above_threshold_color=AZUL, show_leaf_counts=True,
               leaf_font_size=8, ax=ax)
    ax.axhline(corte, color=TEXTO, lw=1, ls="--")
    ax.text(ax.get_xlim()[1], corte, f"  corte en {k} grupos", va="bottom", ha="right",
            fontsize=9, color=TEXTO)
    ax.set_ylabel("Distancia (Ward)", color=TEXTO_SUAVE)
    ax.set_xlabel("Perfiles agrupados (entre paréntesis, cuántos hay en cada rama)",
                  color=TEXTO_SUAVE)
    ax.set_title("Dendrograma del agrupamiento jerárquico", color=TEXTO, loc="left",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    plt.close(fig)


# --------------------------------------------------------------------------
# 5. Programa principal
# --------------------------------------------------------------------------
def ejecutar(guardar: bool = True, verboso: bool = True) -> dict:
    def decir(*a):
        if verboso:
            print(*a)

    decir("1) Construyendo perfiles diarios por estación...")
    perfiles = construir_perfiles(cargar_afluencia())
    X = matriz(perfiles)
    decir(f"   {len(perfiles):,} perfiles (estación-día) de {X.shape[1]} horas cada uno")

    decir("\n2) Probando de 2 a 10 grupos con k-means...")
    evaluacion = evaluar_k(X)
    decir(evaluacion.to_string(index=False))
    k = detectar_codo(evaluacion)
    k_silueta = int(evaluacion.loc[evaluacion["silueta"].idxmax(), "k"])
    decir(f"   el codo de la inercia está en k = {k} "
          f"(la silueta más alta está en k = {k_silueta})")

    decir(f"\n3) Agrupando con k-means (k = {k})...")
    modelo = construir_kmeans(k).fit(X)
    crudas = modelo.named_steps["kmeans"].labels_
    nombres_crudos = nombrar_grupos(perfiles, crudas)
    grupos, nombres = renumerar(crudas, nombres_crudos)
    mapa = {c: grupos[np.argmax(crudas == c)] for c in np.unique(crudas)}
    Xs = modelo.named_steps["escala"].transform(X)
    silueta = round(float(silhouette_score(Xs, grupos)), 4)

    decir("\n4) Comparando con el agrupamiento jerárquico de Ward...")
    ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit(Xs).labels_
    ari_metodos = round(float(adjusted_rand_score(grupos, ward)), 4)
    ari_referencia = round(float(adjusted_rand_score(grupo_esperado(perfiles), grupos)), 4)
    decir(f"   coincidencia k-means vs. Ward (ARI): {ari_metodos}")
    decir(f"   coincidencia con tipo de día y zona (ARI): {ari_referencia}")
    decir(f"   silueta del agrupamiento final: {silueta}")

    resumen = resumen_grupos(perfiles, grupos, nombres)
    decir("\n5) Grupos encontrados:")
    decir(resumen.to_string(index=False))

    perfiles = perfiles.assign(grupo=grupos, nombre_grupo=[nombres[g] for g in grupos])
    cruce = pd.crosstab([perfiles["tipo_dia"], perfiles["tipo_zona"]], perfiles["grupo"])

    metricas = {
        "perfiles": len(perfiles),
        "horas_por_perfil": X.shape[1],
        "evaluacion_k": evaluacion.to_dict(orient="records"),
        "k_elegido": k,
        "k_mayor_silueta": k_silueta,
        "silueta_final": silueta,
        "ari_kmeans_vs_ward": ari_metodos,
        "ari_vs_tipo_dia_y_zona": ari_referencia,
        "grupos": resumen.to_dict(orient="records"),
    }

    if guardar:
        decir("\n6) Guardando resultados en resultados/ ...")
        CARPETA_RESULTADOS.mkdir(exist_ok=True)
        perfiles.drop(columns=["grupo", "nombre_grupo"]).to_csv(
            RUTA_PERFILES, index=False, encoding="utf-8")
        joblib.dump({"modelo": modelo, "mapa": mapa, "nombres": nombres}, RUTA_MODELO)
        evaluacion.to_csv(CARPETA_RESULTADOS / "evaluacion_k.csv", index=False)
        resumen.to_csv(CARPETA_RESULTADOS / "resumen_grupos.csv", index=False)
        cruce.to_csv(CARPETA_RESULTADOS / "grupos_vs_tipo_dia_zona.csv")
        perfiles[CLAVE + ["dia_semana", "tipo_dia", "tipo_zona", "hubo_evento",
                          "grupo", "nombre_grupo"]].to_csv(
            CARPETA_RESULTADOS / "asignaciones.csv", index=False, encoding="utf-8")
        grafico_codo_silueta(evaluacion, k, CARPETA_RESULTADOS / "codo_silueta.png")
        grafico_perfiles(perfiles, grupos, nombres, CARPETA_RESULTADOS / "perfiles_por_grupo.png")
        metricas["varianza_pca"] = grafico_pca(modelo, X, grupos, nombres,
                                               CARPETA_RESULTADOS / "pca_grupos.png")
        grafico_dendrograma(X, k, CARPETA_RESULTADOS / "dendrograma.png")
        (CARPETA_RESULTADOS / "metricas.json").write_text(
            json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
        decir("   listo: perfiles, asignaciones, métricas y 4 gráficos")

    return {"modelo": modelo, "mapa": mapa, "nombres": nombres, "perfiles": perfiles,
            "grupos": grupos, "ward": ward, "metricas": metricas, "X": X}


if __name__ == "__main__":
    ejecutar()
