"""
Genera los documentos de la actividad en PDF con normas APA (7.ª edición):

    docs/Entrega_Actividad3.pdf          documento de entrega con los enlaces
    docs/Descripcion_de_los_datos.pdf    a partir de docs/descripcion_datos.md
    docs/Pruebas_realizadas.pdf          a partir de docs/pruebas.md

Formato aplicado: portada de trabajo estudiantil, número de página arriba a la
derecha, Times New Roman 12 a doble espacio, márgenes de 2,54 cm, sangría de
1,27 cm, títulos por niveles, tablas y figuras numeradas con título en cursiva,
notas de tabla y lista de referencias con sangría francesa en página aparte.

Uso:
    1. Completar la sección CONFIGURACIÓN.
    2. python docs/generar_pdfs_apa.py
Mientras un dato falte, aparece en el PDF como [PENDIENTE: ...].
"""

import json
import re
from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak,
                                Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# ------------------------------ CONFIGURACIÓN ------------------------------
REPO_URL = "https://github.com/Julianibero/Inteligencia-artificial-SANDRA-BAUTISTA-24082026_C1_202634-"
VIDEO_URL = "https://www.youtube.com/watch?v=slo6jjVrCpQ"
RAMA = "Actividad-3---M%C3%A9todos-de-aprendizaje-supervisado"  # rama de la actividad
INTEGRANTES = ["Julian Vega Joya", "Alejandro Mora"]
TUTOR = "Sandra Bautista"
CURSO = "Inteligencia Artificial (24082026_C1_202634)"
PROGRAMA = "Ingeniería de Software"
INSTITUCION = "Corporación Universitaria Iberoamericana"
FECHA = "9 de octubre de 2026"
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
MARGEN = 2.54 * cm
ANCHO_UTIL = letter[0] - 2 * MARGEN
SANGRIA = 1.27 * cm


# ------------------------------- Fuentes -----------------------------------
def _registrar(nombre, candidatos):
    """Registra la primera familia de fuente TTF que exista en el equipo."""
    for regular, negrita, cursiva, negrita_cursiva in candidatos:
        archivos = [Path(regular), Path(negrita), Path(cursiva), Path(negrita_cursiva)]
        if all(a.exists() for a in archivos):
            for sufijo, archivo in zip(["", "-B", "-I", "-BI"], archivos):
                pdfmetrics.registerFont(TTFont(nombre + sufijo, str(archivo)))
            pdfmetrics.registerFontFamily(nombre, normal=nombre, bold=nombre + "-B",
                                          italic=nombre + "-I",
                                          boldItalic=nombre + "-BI")
            return nombre
    return None


SERIF = _registrar("Serif", [
    # Times New Roman en Windows y macOS
    ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf",
     "C:/Windows/Fonts/timesi.ttf", "C:/Windows/Fonts/timesbi.ttf"),
    ("/System/Library/Fonts/Supplemental/Times New Roman.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"),
    # Liberation Serif (Linux): mismas medidas que Times New Roman
    ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
]) or "Times-Roman"

MONO = _registrar("Mono", [
    ("C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/courbd.ttf",
     "C:/Windows/Fonts/couri.ttf", "C:/Windows/Fonts/courbi.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationMono-Italic.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationMono-BoldItalic.ttf"),
]) or "Courier"


# -------------------------------- Estilos ----------------------------------
def _estilo(nombre, **kw):
    base = dict(fontName=SERIF, fontSize=12, leading=24, alignment=TA_LEFT,
                splitLongWords=1)
    base.update(kw)
    return ParagraphStyle(nombre, **base)


CUERPO = _estilo("cuerpo", firstLineIndent=SANGRIA)
SIN_SANGRIA = _estilo("sin_sangria")
CENTRO = _estilo("centro", alignment=TA_CENTER)
TITULO_DOC = _estilo("titulo_doc", alignment=TA_CENTER, fontName=SERIF + "-B"
                     if SERIF != "Times-Roman" else "Times-Bold")
NIVEL_1 = _estilo("nivel_1", alignment=TA_CENTER, keepWithNext=1,
                  fontName=TITULO_DOC.fontName)
NIVEL_2 = _estilo("nivel_2", keepWithNext=1, fontName=TITULO_DOC.fontName)
NIVEL_3 = _estilo("nivel_3", keepWithNext=1,
                  fontName=SERIF + "-BI" if SERIF != "Times-Roman" else "Times-BoldItalic")
VINETA = _estilo("vineta", leftIndent=SANGRIA, bulletIndent=SANGRIA * 0.45,
                 bulletFontName=SERIF)
REFERENCIA = _estilo("referencia", leftIndent=SANGRIA, firstLineIndent=-SANGRIA)
ROTULO = _estilo("rotulo", keepWithNext=1, fontName=TITULO_DOC.fontName)
TITULO_TABLA = _estilo("titulo_tabla", keepWithNext=1,
                       fontName=SERIF + "-I" if SERIF != "Times-Roman" else "Times-Italic")
NOTA = _estilo("nota")
CELDA = _estilo("celda", fontSize=10.5, leading=13.5)
CELDA_ENC = _estilo("celda_enc", fontSize=10.5, leading=13.5, alignment=TA_CENTER)
CODIGO = ParagraphStyle("codigo", fontName=MONO, fontSize=9.5, leading=13,
                        leftIndent=SANGRIA)


# ------------------------- Conversión de Markdown --------------------------
def en_linea(texto: str) -> str:
    """Convierte negrita, cursiva, código y enlaces de Markdown a marcado de ReportLab."""
    codigos = []

    def guardar_codigo(m):
        codigos.append(m.group(1))
        return f"\x00{len(codigos) - 1}\x00"

    texto = re.sub(r"`([^`]+)`", guardar_codigo, texto)
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = re.sub(r"(\d) (%)", "\\1\u00a0\\2", texto)  # evita separar el número del %
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2"><u>\1</u></link>', texto)
    texto = re.sub(r"(?<![\"'>])(https?://[^\s<]+)", r'<link href="\1">\1</link>', texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", texto)

    def poner_codigo(m):
        c = codigos[int(m.group(1))]
        c = c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<font face="{MONO}" size="10">{c}</font>'

    return re.sub(r"\x00(\d+)\x00", poner_codigo, texto)


def _medir(celda: str) -> tuple[float, float]:
    """Ancho de la palabra más larga y ancho total de una celda, en puntos."""
    celda = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", celda).replace("**", "").replace("*", "")
    mas_larga = total = 0.0
    for i, trozo in enumerate(celda.split("`")):
        fuente, tam = (MONO, 10) if i % 2 else (SERIF, CELDA.fontSize)
        for palabra in trozo.split():
            w = pdfmetrics.stringWidth(palabra, fuente, tam)
            mas_larga = max(mas_larga, w)
        total += pdfmetrics.stringWidth(trozo, fuente, tam)
    return mas_larga, total


def tabla_apa(filas: list[list[str]]) -> Table:
    """Tabla con estilo APA: solo líneas horizontales, sin colores."""
    columnas = len(filas[0])
    relleno = 9
    minimos, totales = [], []
    for j in range(columnas):
        medidas = [_medir(f[j]) for f in filas]
        minimos.append(max(m[0] for m in medidas) + relleno)
        totales.append(min(max(m[1] for m in medidas), 260) + relleno)
    if sum(minimos) >= ANCHO_UTIL:
        anchos = [ANCHO_UTIL * m / sum(minimos) for m in minimos]
    else:
        extra = [max(t - m, 0) for t, m in zip(totales, minimos)]
        sobra = ANCHO_UTIL - sum(minimos)
        if sum(extra) == 0:
            anchos = [m + sobra / columnas for m in minimos]
        else:
            anchos = [m + sobra * e / sum(extra) for m, e in zip(minimos, extra)]

    datos = [[Paragraph(en_linea(c), CELDA_ENC) for c in filas[0]]]
    datos += [[Paragraph(en_linea(c), CELDA) for c in f] for f in filas[1:]]
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, "black"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, "black"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, "black"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def figura(ruta: Path):
    img = Image(str(ruta))
    escala = min(ANCHO_UTIL / img.drawWidth, 9.5 * cm / img.drawHeight)
    img.drawWidth *= escala
    img.drawHeight *= escala
    img.hAlign = "CENTER"
    return img


def markdown_a_flujo(md: str, carpeta_base: Path):
    """
    Convierte el subconjunto de Markdown usado en los documentos del proyecto.
    Devuelve (título, elementos). Las tablas y figuras deben ir precedidas por
    las líneas **Tabla N** / **Figura N** y *Título*, como pide APA.
    """
    lineas = md.splitlines()
    titulo = ""
    elementos = []
    en_referencias = False
    rotulo_pendiente = []
    i = 0

    def leer_parrafo(i):
        partes = []
        while i < len(lineas) and lineas[i].strip() and not re.match(
                r"^(#|\||- |\d+\. |```|!\[)", lineas[i].strip()):
            partes.append(lineas[i].strip())
            i += 1
        return " ".join(partes), i

    while i < len(lineas):
        linea = lineas[i].rstrip()
        s = linea.strip()

        if not s:
            i += 1
            continue

        if s.startswith("# "):
            titulo = s[2:].strip()
            elementos.append(Paragraph(en_linea(titulo), TITULO_DOC))
            i += 1
            continue

        if s.startswith("## "):
            texto = s[3:].strip()
            en_referencias = texto.lower() == "referencias"
            if en_referencias:
                elementos.append(PageBreak())
            elementos.append(Paragraph(en_linea(texto), NIVEL_1))
            i += 1
            continue

        if s.startswith("### "):
            elementos.append(Paragraph(en_linea(s[4:]), NIVEL_2))
            i += 1
            continue

        if s.startswith("#### "):
            elementos.append(Paragraph(en_linea(s[5:]), NIVEL_3))
            i += 1
            continue

        if s.startswith("```"):
            i += 1
            bloque = []
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                bloque.append(lineas[i])
                i += 1
            i += 1
            elementos.append(KeepTogether([Spacer(1, 4),
                                           Preformatted("\n".join(bloque), CODIGO),
                                           Spacer(1, 10)]))
            continue

        if s.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in celdas):
                    filas.append(celdas)
                i += 1
            bloque = rotulo_pendiente + [Spacer(1, 2), tabla_apa(filas), Spacer(1, 6)]
            rotulo_pendiente = []
            elementos.append(CondPageBreak(5 * cm))
            elementos += bloque
            continue

        if s.startswith("!["):
            m = re.match(r"!\[[^\]]*\]\(([^)]+)\)", s)
            ruta = (carpeta_base / m.group(1)).resolve()
            elementos.append(KeepTogether(rotulo_pendiente + [figura(ruta), Spacer(1, 10)]))
            rotulo_pendiente = []
            i += 1
            continue

        if re.match(r"^(- |\d+\. )", s):
            numerada = bool(re.match(r"^\d+\. ", s))
            n = 0
            while i < len(lineas) and re.match(r"^(- |\d+\. )", lineas[i].strip()):
                n += 1
                texto = re.sub(r"^(- |\d+\. )", "", lineas[i].strip())
                vineta = f"{n}." if numerada else "•"
                elementos.append(Paragraph(en_linea(texto), VINETA, bulletText=vineta))
                i += 1
            continue

        texto, i = leer_parrafo(i)
        if re.fullmatch(r"\*\*(Tabla|Figura) \d+\*\*", texto):
            rotulo_pendiente = [Paragraph(en_linea(texto), ROTULO)]
        elif rotulo_pendiente and re.fullmatch(r"\*[^*].*\*", texto):
            rotulo_pendiente.append(Paragraph(en_linea(texto[1:-1]), TITULO_TABLA))
        elif texto.startswith("*Nota.*"):
            elementos.append(Paragraph(en_linea(texto), NOTA))
        elif en_referencias:
            elementos.append(Paragraph(en_linea(texto), REFERENCIA))
        else:
            elementos.append(Paragraph(en_linea(texto), CUERPO))

    return titulo, elementos


# ------------------------------ Documento APA ------------------------------
def pendiente(que: str) -> str:
    return f"**[PENDIENTE: {que}]**"


def unir_nombres(nombres: list[str]) -> str:
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def portada(titulo: str):
    """Portada de trabajo estudiantil según APA 7."""
    lineas = [
        unir_nombres(INTEGRANTES),
        f"{PROGRAMA}, {INSTITUCION}",
        CURSO,
        TUTOR or "[PENDIENTE: nombre del docente]",
        FECHA,
    ]
    flujo = [Spacer(1, 4.5 * cm), Paragraph(en_linea(titulo), TITULO_DOC), Spacer(1, 24)]
    flujo += [Paragraph(en_linea(l) if not l.startswith("[PENDIENTE")
                        else f"<b>{l}</b>", CENTRO) for l in lineas]
    return flujo + [PageBreak()]


def numero_pagina(lienzo, doc):
    lienzo.saveState()
    lienzo.setFont(SERIF, 12)
    lienzo.drawRightString(letter[0] - MARGEN, letter[1] - 1.27 * cm, str(doc.page))
    lienzo.restoreState()


def construir_pdf(md: str, carpeta_base: Path, salida: Path):
    titulo, cuerpo = markdown_a_flujo(md, carpeta_base)
    doc = SimpleDocTemplate(str(salida), pagesize=letter, leftMargin=MARGEN,
                            rightMargin=MARGEN, topMargin=MARGEN, bottomMargin=MARGEN,
                            title=titulo, author=unir_nombres(INTEGRANTES))
    doc.build(portada(titulo) + cuerpo, onFirstPage=numero_pagina,
              onLaterPages=numero_pagina)
    print(f"  {salida.relative_to(RAIZ)}")


# ---------------------------- Documento de entrega -------------------------
def enlace_repo(ruta: str, carpeta: bool = False) -> str:
    if not REPO_URL:
        return f"`{ruta}`"
    base = REPO_URL.rstrip("/").removesuffix(".git")
    tipo = "tree" if carpeta else "blob"
    medio = f"-/{tipo}" if "gitlab" in base else tipo
    return f"[{ruta}]({base}/{medio}/{RAMA}/{ruta})"


def md_entrega() -> str:
    """Llena la plantilla docs/entrega_plantilla.md con métricas y enlaces."""
    m = json.loads((RAIZ / "resultados" / "metricas.json").read_text(encoding="utf-8"))
    pct = lambda v: f"{v * 100:.1f} %".replace(".", ",")

    def miles(n):
        return f"{n:,}".replace(",", " ") if n >= 10000 else str(n)

    mc = m["matriz_confusion"]
    valores = {
        "REGISTROS": f"{miles(m['registros'])} ({miles(m['registros_entrenamiento'])} / "
                     f"{miles(m['registros_prueba'])})",
        "EXACTITUD": pct(m["exactitud_prueba"]),
        "BASE": pct(m["exactitud_linea_base"]),
        "CV": pct(m["exactitud_validacion_cruzada"]),
        "TRAIN": pct(m["exactitud_entrenamiento"]),
        "F1": f"{m['f1_macro_prueba']:.3f}".replace(".", ","),
        "GRAVES": f"{mc[0][2] + mc[2][0]} de {miles(m['registros_prueba'])}",
        "REPO": (lambda u: f"[{u}]({u})")(f"{REPO_URL}/tree/{RAMA}") if REPO_URL else pendiente("enlace del repositorio"),
        "VIDEO": f"[{VIDEO_URL}]({VIDEO_URL})" if VIDEO_URL else pendiente("enlace del video"),
    }
    texto = (DOCS / "entrega_plantilla.md").read_text(encoding="utf-8")
    for clave, valor in valores.items():
        texto = texto.replace("{{" + clave + "}}", valor)
    texto = re.sub(r"\{\{ARCHIVO:([^}]+)\}\}", lambda x: enlace_repo(x.group(1)), texto)
    texto = re.sub(r"\{\{CARPETA:([^}]+)\}\}", lambda x: enlace_repo(x.group(1), True), texto)
    if "{{" in texto:
        raise ValueError("Quedó un marcador sin reemplazar en la plantilla de entrega.")
    return texto


if __name__ == "__main__":
    print("PDF generados:")
    construir_pdf(md_entrega(), DOCS, DOCS / "Entrega_Actividad3.pdf")
    construir_pdf((DOCS / "descripcion_datos.md").read_text(encoding="utf-8"), DOCS,
                  DOCS / "Descripcion_de_los_datos.pdf")
    construir_pdf((DOCS / "pruebas.md").read_text(encoding="utf-8"), DOCS,
                  DOCS / "Pruebas_realizadas.pdf")
    faltan = [n for n, v in [("REPO_URL", REPO_URL), ("VIDEO_URL", VIDEO_URL),
                             ("TUTOR", TUTOR)] if not v]
    if faltan:
        print("Falta completar en la configuración:", ", ".join(faltan))
