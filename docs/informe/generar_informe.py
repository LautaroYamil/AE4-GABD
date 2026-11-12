"""
Genera el informe PDF del trabajo (docs/informe/Informe_AE4_Agro_NEA.pdf).

    python -m pip install reportlab pillow
    python docs/informe/generar_informe.py

Antes de entregarlo: completar INTEGRANTES. Las imágenes de los gráficos están en
docs/informe/img/ (capturas del dashboard de Superset).
"""
from pathlib import Path

from PIL import Image as ImagenPIL
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# ----------------------------------------------------------------- completar
INTEGRANTES = ["(nombre y apellido)", "(nombre y apellido)", "(nombre y apellido)"]
FECHA = "Noviembre de 2026"

CARPETA = Path(__file__).resolve().parent
IMG = CARPETA / "img"
SALIDA = CARPETA / "Informe_AE4_Agro_NEA.pdf"

# ----------------------------------------------------------------- fuentes y estilos
# Arial (Windows) o DejaVu (Linux): las fuentes base del PDF no tienen Σ, →, ≥ ni −
for carpeta, nombres in [("C:/Windows/Fonts", ("arial.ttf", "arialbd.ttf", "ariali.ttf")),
                         ("/usr/share/fonts/truetype/dejavu", ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf",
                                                               "DejaVuSans-Oblique.ttf"))]:
    if Path(carpeta, nombres[0]).exists():
        pdfmetrics.registerFont(TTFont("Texto", str(Path(carpeta, nombres[0]))))
        pdfmetrics.registerFont(TTFont("Texto-B", str(Path(carpeta, nombres[1]))))
        pdfmetrics.registerFont(TTFont("Texto-I", str(Path(carpeta, nombres[2]))))
        pdfmetrics.registerFontFamily("Texto", normal="Texto", bold="Texto-B", italic="Texto-I",
                                      boldItalic="Texto-B")
        break
else:
    raise SystemExit("No se encontró Arial ni DejaVu Sans")

VERDE = colors.HexColor("#2F5D3A")
VERDE_CLARO = colors.HexColor("#E8F0E6")
GRIS = colors.HexColor("#555555")
ANCHO = A4[0] - 4 * cm

CUERPO = ParagraphStyle("cuerpo", fontName="Texto", fontSize=10, leading=13.6, alignment=TA_JUSTIFY,
                        spaceAfter=5)
VINETA = ParagraphStyle("vineta", parent=CUERPO, leftIndent=12, bulletIndent=2, spaceAfter=2.5)
H1 = ParagraphStyle("h1", fontName="Texto-B", fontSize=15, leading=19, textColor=VERDE, spaceBefore=6,
                    spaceAfter=7)
H2 = ParagraphStyle("h2", fontName="Texto-B", fontSize=11.5, leading=15, textColor=VERDE, spaceBefore=7,
                    spaceAfter=4)
CELDA = ParagraphStyle("celda", fontName="Texto", fontSize=8.6, leading=10.8)
CELDA_B = ParagraphStyle("celda_b", parent=CELDA, fontName="Texto-B", textColor=colors.white)
NOTA = ParagraphStyle("nota", fontName="Texto-I", fontSize=8.5, leading=11, textColor=GRIS, spaceAfter=6,
                      alignment=TA_CENTER)


def p(texto, estilo=CUERPO):
    return Paragraph(texto, estilo)


def vinetas(items):
    return [Paragraph(t, VINETA, bulletText="•") for t in items]


def tabla(filas, anchos, encabezado=True):
    datos = [[Paragraph(str(c), CELDA_B if (encabezado and i == 0) else CELDA) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=[a * ANCHO for a in anchos], repeatRows=1 if encabezado else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, VERDE_CLARO])]
    if encabezado:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), VERDE))
    t.setStyle(TableStyle(estilo))
    return t


def imagen(nombre, ancho_relativo=1.0, pie=None):
    ruta = IMG / nombre
    ancho_px, alto_px = ImagenPIL.open(ruta).size
    ancho = ANCHO * ancho_relativo
    elementos = [Image(str(ruta), width=ancho, height=ancho * alto_px / ancho_px)]
    if pie:
        elementos.append(p(pie, NOTA))
    return KeepTogether(elementos)


def lado_a_lado(izq, der, pie=None, proporcion=0.5):
    """Dos imágenes en la misma fila."""
    celdas = []
    for nombre, fraccion in ((izq, proporcion), (der, 1 - proporcion)):
        ancho_px, alto_px = ImagenPIL.open(IMG / nombre).size
        ancho = ANCHO * fraccion - 6
        celdas.append(Image(str(IMG / nombre), width=ancho, height=ancho * alto_px / ancho_px))
    t = Table([celdas], colWidths=[ANCHO * proporcion, ANCHO * (1 - proporcion)])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return KeepTogether([t] + ([p(pie, NOTA)] if pie else []))


# ----------------------------------------------------------------- diagramas
def caja(d, x, y, ancho, alto, titulo, lineas, color):
    d.add(Rect(x, y, ancho, alto, fillColor=colors.white, strokeColor=color, strokeWidth=1.2))
    d.add(Rect(x, y + alto - 16, ancho, 16, fillColor=color, strokeColor=color))
    d.add(String(x + ancho / 2, y + alto - 12, titulo, fontName="Texto-B", fontSize=8.5,
                 fillColor=colors.white, textAnchor="middle"))
    for i, linea in enumerate(lineas):
        d.add(String(x + 5, y + alto - 28 - i * 10.5, linea, fontName="Texto", fontSize=7.4))


def diagrama_estrella():
    d = Drawing(ANCHO, 300)
    hecho, dim = colors.HexColor("#B7472A"), VERDE
    # posiciones (x, y, ancho, alto)
    tiempo = (ANCHO / 2 - 70, 196, 140, 104)
    prod = (20, 86, 150, 86)
    clima = (ANCHO - 170, 100, 150, 58)
    cultivo = (0, 0, 130, 58)
    depto = (ANCHO / 2 - 72, 0, 144, 84)
    for (a, b) in [(prod, tiempo), (prod, depto), (prod, cultivo), (clima, tiempo), (clima, depto)]:
        d.add(Line(a[0] + a[2] / 2, a[1] + a[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2,
                   strokeColor=colors.HexColor("#888888"), strokeWidth=1))
    caja(d, *tiempo, "dim_tiempo (10.958 días)", ["id_fecha (PK, AAAAMMDD)", "fecha · día · nombre_día",
                                                  "mes · nombre_mes · trimestre", "año · campaña (jul-jun)",
                                                  "es_mes_lluvia_verano (oct-mar)", "1/7/1995 a 30/6/2025"], dim)
    caja(d, *prod, "fact_produccion (57.472)", ["FK id_fecha (1/7 de la campaña)", "FK id_departamento",
                                                "FK id_cultivo", "superficie_sembrada_ha  Σ",
                                                "superficie_cosechada_ha  Σ", "produccion_t  Σ"], hecho)
    caja(d, *clima, "fact_clima_diario (675.694)", ["FK id_fecha · FK id_departamento", "lluvia_mm  Σ",
                                                    "grano: departamento × día"], hecho)
    caja(d, *cultivo, "dim_cultivo (33)", ["id_cultivo (PK) · nombre", "primera / última campaña",
                                           "Fuente: estimaciones"], dim)
    caja(d, *depto, "dim_departamento (423)", ["id_departamento (PK)", "codigo_indec (clave de cruce)",
                                               "nombre · provincia", "es_nea · es_sin_definir",
                                               "tiene_clima"], dim)
    return d


def diagrama_flujo():
    pasos = [("2 fuentes", "data/raw"), ("Ingesta", "ingesta.py"), ("Limpieza", "limpieza.py"),
             ("Transformación", "y merges"), ("CSV del DW", "data/processed"), ("PostgreSQL", "COPY + vistas"),
             ("Superset", "dashboard")]
    d = Drawing(ANCHO, 46)
    ancho_caja, separacion = (ANCHO - 6 * 12) / 7, 12
    for i, (titulo, sub) in enumerate(pasos):
        x = i * (ancho_caja + separacion)
        d.add(Rect(x, 6, ancho_caja, 36, fillColor=VERDE_CLARO, strokeColor=VERDE, strokeWidth=1))
        d.add(String(x + ancho_caja / 2, 27, titulo, fontName="Texto-B", fontSize=7.6, textAnchor="middle"))
        d.add(String(x + ancho_caja / 2, 15, sub, fontName="Texto", fontSize=6.8, textAnchor="middle",
                     fillColor=GRIS))
        if i < len(pasos) - 1:
            xf = x + ancho_caja
            d.add(Polygon([xf + 2, 21, xf + separacion - 2, 24, xf + 2, 27], fillColor=VERDE, strokeColor=VERDE))
    return d


# ----------------------------------------------------------------- pie de página
def pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Texto", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.2 * cm, "AE4 · Producción agrícola del NEA y lluvia")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


# ================================================================= contenido
h = []

# --- Portada y resumen
h += [Spacer(1, 3 * cm),
      p("Trabajo Integrador AE4 · Integración de datos y analítica",
        ParagraphStyle("a", parent=CUERPO, alignment=TA_CENTER, textColor=GRIS, fontSize=11)),
      p("Producción agrícola del NEA y lluvia",
        ParagraphStyle("t", fontName="Texto-B", fontSize=24, leading=30, alignment=TA_CENTER, textColor=VERDE,
                       spaceBefore=8, spaceAfter=6)),
      p("¿Cuánto depende de la lluvia la agricultura del noreste argentino? Campañas 2000/01 a 2024/25",
        ParagraphStyle("s", parent=CUERPO, alignment=TA_CENTER, fontSize=12, leading=16)),
      Spacer(1, 1.2 * cm),
      p("Gestión Avanzada de Bases de Datos · Ingeniería en Sistemas · Universidad de la Cuenca del Plata (Posadas)",
        ParagraphStyle("u", parent=CUERPO, alignment=TA_CENTER)),
      p("<b>Integrantes:</b> " + " · ".join(INTEGRANTES), ParagraphStyle("i", parent=CUERPO, alignment=TA_CENTER)),
      p(FECHA, ParagraphStyle("f", parent=CUERPO, alignment=TA_CENTER)),
      Spacer(1, 1.5 * cm),
      p("Resumen", H2)]
h += [p("Se cruzaron dos fuentes abiertas (las <i>Estimaciones agrícolas</i> de la Secretaría de Agricultura y "
        "la lluvia diaria de <i>NASA POWER</i>) por el código INDEC de cada departamento, para medir cuánto "
        "depende la producción del NEA de la lluvia. El proceso completo es reproducible: un ETL en Python "
        "(pandas) limpia y cruza los datos, un Data Warehouse en PostgreSQL los organiza en un modelo estrella "
        "con dos tablas de hechos, y un dashboard en Apache Superset responde las cuatro preguntas de negocio. "
        "Todo se levanta con un solo comando (Docker Compose)."),
      p("<b>Principales resultados:</b> en las campañas secas la soja, el maíz, el sorgo y el algodón del NEA "
        "rinden entre 10 % y 18 % menos que su promedio reciente, mientras que el arroz (que se riega) no cae; "
        "en 2024/25 se perdió el 32,9 % de la superficie sembrada de secano; 2022/23 fue la campaña más seca "
        "del período (62 % de la lluvia normal); y el NEA pasó de producir el 70 % del algodón del país al 25 %."),
      PageBreak()]

# --- 1. Negocio
h += [p("1. Definición del negocio", H1), p("1.1 Contexto", H2),
      p("El NEA (Misiones, Corrientes, Chaco y Formosa) produce el 100 % de la yerba mate y el té del país y "
        "alrededor de la mitad del arroz. El Chaco suma además una agricultura extensiva de soja, maíz, algodón y "
        "sorgo. Casi toda esa producción es de <b>secano</b>: depende de la lluvia y no de riego. En las últimas "
        "campañas hubo sequías fuertes, con pérdidas de cosecha muy visibles. Para un productor, una cooperativa o "
        "el Estado provincial, la pregunta práctica es cuánto pesa la lluvia en el resultado de la campaña, qué "
        "cultivos y departamentos son más vulnerables y en qué momento del año se define la cosecha. Este trabajo "
        "responde esas preguntas con datos oficiales de 25 campañas."),
      p("1.2 Preguntas de negocio", H2),
      tabla([["", "Pregunta"],
             ["P1", "¿Cuánto rinden la soja, el maíz, el algodón y el sorgo del NEA en las campañas secas frente a "
                    "las normales y las húmedas?"],
             ["P2", "¿Qué porcentaje de la superficie sembrada no se cosechó en cada campaña, y qué departamentos "
                    "perdieron más?"],
             ["P3", "¿Qué campañas fueron más secas que lo normal en cada departamento, y en qué meses faltó la "
                    "lluvia?"],
             ["P4", "¿Qué participación tiene el NEA en la producción nacional de algodón, arroz, yerba mate y té, "
                    "y cómo cambió entre 2000/01 y 2024/25?"]], [0.07, 0.93]),
      p("1.3 Indicadores (KPI)", H2),
      tabla([["KPI", "Fórmula", "Unidad", "Responde"],
             ["<b>KPI 1 (principal)</b> · Rendimiento vs promedio de las 5 campañas anteriores",
              "(Σ toneladas ÷ Σ ha cosechadas de la campaña) ÷ (Σ toneladas ÷ Σ ha cosechadas de las 5 campañas "
              "anteriores), mismo cultivo y departamento × 100", "%", "P1"],
             ["<b>KPI 2</b> · Lluvia de octubre a marzo vs lo normal",
              "Σ lluvia oct–mar de la campaña ÷ promedio de esa suma en 2000/01–2024/25, mismo departamento × 100",
              "%", "P1, P3"],
             ["<b>KPI 3</b> · Superficie perdida",
              "(Σ ha sembradas − Σ ha cosechadas) ÷ Σ ha sembradas × 100", "%", "P2"]],
            [0.27, 0.48, 0.11, 0.14]),
      Spacer(1, 4),
      p("El KPI 1 compara contra las 5 campañas anteriores y no contra el promedio de todo el período porque el "
        "rendimiento tiene tendencia: el maíz del NEA rinde hoy casi el doble que en 2000. Contra un promedio fijo, "
        "los primeros años saldrían siempre bajos por tecnología y no por clima."),
      p("1.4 Supuestos, alcance y limitaciones", H2)]
h += vinetas([
    "<b>Supuesto 1:</b> la campaña agrícola va de julio a junio (convención de la Secretaría de Agricultura).",
    "<b>Supuesto 2:</b> para los cultivos de verano la lluvia que importa es la de octubre a marzo. Una campaña "
    "es <i>seca</i> si llovió menos del 80 % de lo normal del departamento y <i>húmeda</i> si llovió más del 120 %.",
    "<b>Supuesto 3:</b> la lluvia de un departamento es la que estima la NASA en su punto central (modelo "
    "satelital, no pluviómetro). Para no contar dos veces se usan solo los cultivos «total».",
    "<b>Alcance:</b> campañas 2000/01 a 2024/25; producción de todo el país (P4 compara con el total nacional); "
    "clima de los 76 departamentos del NEA.",
    "<b>Limitaciones:</b> la producción es anual (no se sabe en qué mes se perdió); la lluvia es modelada, en una "
    "grilla de unos 55 km; plagas, calor y precios no están en los datos; yerba mate y té llegan hasta 2023/24.",
])

# --- 2. Fuentes
h += [p("2. Fuentes de datos", H1),
      p("Se usan <b>dos fuentes reales</b>, de organismos distintos, que comparten una clave: el <b>código INDEC "
        "del departamento</b> (5 dígitos: 2 de provincia y 3 de departamento). Los archivos originales están en "
        "<i>data/raw/</i> tal como se descargaron el 10/11/2026."),
      tabla([["", "Estimaciones agrícolas", "Clima diario NASA POWER"],
             ["Organismo", "Secretaría de Agricultura, Ganadería y Pesca", "NASA (Prediction Of Worldwide Energy "
                                                                          "Resources)"],
             ["Licencia", "CC BY 4.0", "Uso libre"],
             ["Contenido", "Superficie sembrada y cosechada (ha), producción (t) y rendimiento (kg/ha) por cultivo, "
                           "campaña y departamento", "Lluvia diaria (mm) y temperatura máxima en un punto"],
             ["Tamaño", "1 CSV, 160.499 filas, 41 cultivos, campañas 1969/70 a 2024/25",
              "76 CSV (uno por departamento del NEA), 9.131 días cada uno: 693.956 filas"],
             ["Formato", "Separador coma, UTF-8, con comillas", "Encabezado de texto hasta «-END HEADER-»; fecha "
                                                               "como año + día del año"],
             ["Clave de cruce", "Columna <i>departamento_id</i>", "Nombre del archivo (ej. 54098.csv = San Ignacio)"]],
            [0.16, 0.42, 0.42]),
      Spacer(1, 4),
      p("A la NASA hay que pedirle los datos para una latitud y longitud. Se usó el punto central de cada "
        "departamento que publica Georef (Jefatura de Gabinete) solo como parámetro de la descarga "
        "(<i>etl/descargar_datos.py</i>); ese dato no se guarda ni se carga al DW, por lo que no es una tercera "
        "fuente.")]

# --- 3. Exploración
h += [p("3. Exploración de los datos", H1),
      p("Antes de limpiar se revisaron columnas, tipos, nulos, rangos y duplicados con <i>etl/exploracion.py</i>. "
        "Los problemas encontrados y su tratamiento:"),
      tabla([["Problema encontrado", "Evidencia", "Tratamiento"],
             ["Doble conteo: «soja total» = «soja 1ra» + «soja 2da»; «trigo total» incluye al candeal; «poroto "
              "total» a sus tipos", "Coincide en el 99,6 % de los departamentos-campaña", "Se usan solo los totales "
                                                                                       "(D04)"],
             ["La cebada cambia de nombre: cervecera y forrajera hasta 2015/16, «cebada total» desde 2016/17",
              "Las series no se superponen", "Se suman en una sola serie «cebada» (D05)"],
             ["La columna <i>anio</i> cambia de significado", "En yerba y té es el año final de la campaña; en el "
                                                              "resto, el inicial", "Se usa <i>campania</i> (D08)"],
             ["Filas con el texto «NULL» en provincia y departamento", "8 filas de 1979–1980", "Se rechazan (D02)"],
             ["Departamentos «sin definir» (código XX000)", "0,85 % de la producción; en el NEA hasta 2020/21",
              "Se cargan como departamento «sin definir» de su provincia (D12)"],
             ["Sembrado y nada cosechado", "2.533 filas en el período", "Se conservan: es la pérdida que mide el "
                                                                        "KPI 3 (D06)"],
             ["Rendimiento imposible", "Soja San Alberto 2011/12: 19.902 kg/ha (8 veces la mediana)",
              "Se rechaza todo rendimiento mayor a 4 veces la mediana del cultivo (D07)"],
             ["Fecha de la NASA como año + día del año", "Columnas YEAR y DOY", "Se convierte a fecha (D09)"],
             ["Lluvias extremas", "3 días con más de 300 mm (máx. 491 mm, Corrientes, 27/11/2015)",
              "Se conservan: el mismo día hubo valores altos en departamentos vecinos (D10)"],
             ["Departamentos chicos con la misma lluvia", "20 de 76 comparten la celda de la grilla de la NASA",
              "Se documenta como limitación"]],
            [0.40, 0.33, 0.27])]

# --- 4. ETL
h += [PageBreak(), p("4. Proceso ETL", H1),
      diagrama_flujo(),
      p("El ETL está escrito en Python con pandas, en módulos cortos y comentados (<i>etl/</i>). Todos los "
        "parámetros (período, umbrales, cultivos a excluir) están en <i>config.py</i>. Corre en unos 5 segundos y "
        "produce los mismos archivos byte a byte en Windows y en Linux."),
      p("4.1 Ingesta", H2),
      p("Cada fuente se lee por separado (<i>ingesta.py</i>) y <b>todo como texto</b>, para que pandas no adivine "
        "tipos: los tipos se convierten después, con controles. Si llega un valor que no se puede convertir, el ETL "
        "se detiene en vez de inventar un dato."),
      p("4.2 Limpieza", H2),
      tabla([["Paso", "Filas afectadas", "Destino"],
             ["Filas leídas de las estimaciones", "160.499", ""],
             ["Sin departamento (texto NULL)", "8", "rechazados.csv"],
             ["Fuera del período (antes de 1995/96)", "89.467", "excluidas"],
             ["Subcultivos (doble conteo)", "12.961", "excluidas"],
             ["Duplicados exactos", "0", "rechazados.csv"],
             ["Cebada cervecera + forrajera unidas", "563", "sumadas"],
             ["Todo en cero (nada sembrado ni producido)", "24", "excluidas"],
             ["Pérdida total (sembrado sin cosecha)", "2.533", "se conservan"],
             ["Rendimiento imposible (outlier)", "4", "rechazados.csv"],
             ["<b>Estimaciones limpias</b>", "<b>57.472</b>", ""],
             ["Clima: días sin dato (−999), repetidos", "0 y 0", ""],
             ["<b>Clima limpio</b> (solo la lluvia; la temperatura no responde ninguna pregunta)", "<b>693.956</b>",
              ""]], [0.62, 0.18, 0.20]),
      Spacer(1, 4),
      p("Se cargan 5 campañas antes de 2000/01 solo para poder calcular el KPI 1 de la primera campaña analizada. "
        "El rendimiento informado por la fuente no pasa al DW: es un cociente y no se puede sumar; se recalcula "
        "siempre como Σ toneladas × 1000 ÷ Σ hectáreas cosechadas."),
      p("4.3 Merge: cómo se cruzan las dos fuentes", H2),
      p("La clave es el <b>código INDEC del departamento</b>. El problema es que las fuentes tienen distinto "
        "detalle: la producción es una fila por campaña y la lluvia, una fila por día. Cruzarlas directamente "
        "repetiría cada fila de producción 365 veces. Por eso primero se suma la lluvia de octubre a marzo de cada "
        "departamento y campaña, y recién después se cruza por <b>departamento + campaña</b>."),
      p("Todos los cruces son <b>LEFT JOIN</b>: la tabla de la izquierda no puede perder filas. Si una clave no "
        "encuentra pareja, la fila queda con un nulo que se cuenta y se informa; con un INNER JOIN esas filas "
        "desaparecerían en silencio. Además, <i>validate=\"many_to_one\"</i> detiene el ETL si la tabla de la "
        "derecha tiene la clave repetida, porque eso duplicaría filas."),
      KeepTogether(tabla([["Cruce", "Clave", "Filas antes / después", "Duplicados", "Con match", "Sin match"],
             ["Estimaciones → dim_departamento", "código INDEC", "57.472 / 57.472", "0", "100 %", "—"],
             ["Estimaciones → dim_cultivo", "nombre del cultivo", "57.472 / 57.472", "0", "100 %", "—"],
             ["Clima → dim_departamento", "código INDEC", "693.956 / 693.956", "0", "97,37 %",
              "2 departamentos de Formosa sin producción: se excluye su clima"],
             ["<b>Producción NEA → lluvia de la campaña</b>", "<b>departamento + campaña</b>", "6.697 / 6.697",
              "0", "97,75 %", "los 4 «sin definir» (no tienen punto para pedir clima)"]],
            [0.21, 0.15, 0.15, 0.135, 0.10, 0.255])),
      Spacer(1, 4),
      p("Las validaciones se imprimen en pantalla y quedan guardadas en <i>data/processed/validaciones/</i> "
        "(<i>log_etl.txt</i>, <i>validaciones.csv</i> y <i>clima_sin_departamento.csv</i>). El último cruce es el "
        "cruce analítico entre las dos fuentes; en el DW lo repite la vista <i>vw_produccion_lluvia</i>.")]

# --- 5. DW
h += [p("5. Data Warehouse", H1),
      p("PostgreSQL 16, esquema <i>dw</i>. Es un <b>modelo estrella con dos tablas de hechos</b> que comparten "
        "dimensiones: la producción y el clima tienen granos distintos (campaña y día), así que no pueden ir en "
        "la misma tabla."),
      KeepTogether([diagrama_estrella(), p("Σ = métrica aditiva. Hay 5 tablas físicas.", NOTA)]),
      tabla([["Tabla", "Grano", "Filas", "Justificación"],
             ["fact_produccion", "cultivo × departamento × campaña", "57.472", "Hechos de P1, P2 y P4. Tres FK y "
                                                                               "tres métricas aditivas"],
             ["fact_clima_diario", "departamento × día", "675.694", "Hechos de P1 y P3"],
             ["dim_tiempo", "día", "10.958", "Fecha, día, mes, trimestre, año y campaña"],
             ["dim_departamento", "departamento", "423", "Une las dos fuentes. P2, P3 y P4 (NEA contra el país)"],
             ["dim_cultivo", "cultivo", "33", "P1 (rendimiento por cultivo) y P4 (participación por cultivo)"]],
            [0.19, 0.25, 0.10, 0.46]),
      p("Decisiones de modelado", H2)]
h += vinetas([
    "La producción es anual: se ancla al <b>1 de julio</b> en que empieza la campaña. Así las dos tablas de hechos "
    "usan la misma <i>dim_tiempo</i> y se cruzan por su atributo <i>campania</i> (D13).",
    "El <b>rendimiento no se guarda</b> en la tabla de hechos: es un cociente y no se puede sumar. Se calcula "
    "en las vistas y en el dashboard como cociente de sumas.",
    "Claves subrogadas en departamento y cultivo; en tiempo, la clave AAAAMMDD (legible y ordenable).",
    "Integridad: PK compuestas en los hechos, FK a las tres dimensiones, CHECK de valores no negativos, de "
    "superficie cosechada ≤ sembrada y de rangos de día, mes y trimestre. Índices por departamento, cultivo y "
    "campaña.",
    "Superset se conecta con un usuario de <b>solo lectura</b> (<i>superset_lector</i>).",
])
h += [KeepTogether([p("Vistas y consultas analíticas", H2), tabla([["Objeto", "Qué hace", "Alimenta"],
             ["vw_lluvia_campania", "Lluvia oct–mar por departamento y campaña, su normal y el tipo de campaña "
                                    "(seca, normal, húmeda)", "KPI 2, P3"],
             ["vw_produccion_lluvia", "Producción con la base de las 5 campañas anteriores (función de ventana "
                                      "<i>RANGE 5 PRECEDING</i>) y la lluvia de la campaña: cruza las dos fuentes",
              "KPI 1, KPI 3, P1, P2, P4"],
             ["vw_lluvia_mensual", "Lluvia de cada mes vs la normal de ese mes", "P3"],
             ["05_consultas_analiticas.sql", "8 consultas que responden P1 a P4", "Hallazgos"],
             ["06_validaciones_dw.sql", "Conteos, FK huérfanas, completitud del clima, totales de control",
              "Control"]], [0.27, 0.53, 0.20])]),
      Spacer(1, 4),
      p("<b>Controles después de la carga:</b> 0 claves foráneas huérfanas; los 74 departamentos con clima tienen "
        "los 9.131 días; la vista de producción tiene las mismas 47.269 filas que la tabla de hechos desde "
        "2000/01; y los totales del DW (3.062.965.947 t; 1.025.883.200 ha sembradas; 2.522.678 mm de lluvia) "
        "coinciden con los del ETL.")]

# --- 6. Dashboard
h += [PageBreak(), p("6. Dashboard", H1),  # el dashboard arranca en página nueva: KPIs y filtros juntos
      p("Apache Superset 4.1, accesible en http://localhost:8088. Se importa solo al levantar el proyecto, a partir "
        "del export <i>dashboard/dashboard_agro_nea.zip</i>. Tiene 3 KPIs (el principal destacado), 7 gráficos "
        "titulados con la pregunta que responden y 3 filtros."),
      imagen("kpis.png", 1.0, "KPIs para la campaña 2024/25, soja, todo el NEA (valores por defecto de los filtros)."),
      tabla([["Filtro", "Afecta a", "No afecta a (por qué)"],
             ["Campaña (por defecto 2024/2025)", "Los 3 KPIs y la tabla de departamentos",
              "Gráficos que muestran todas las campañas"],
             ["Provincia (opcional)", "Todo", "P4: compara el NEA contra el país"],
             ["Cultivo (por defecto soja)", "KPI 1, KPI 3 y los gráficos por campaña",
              "Lluvia y gráficos que ya comparan varios cultivos"]], [0.30, 0.35, 0.35])]

# --- 7. Hallazgos
h += [p("7. Hallazgos", H1),
      p("P1 · ¿Cuánto rinden los cultivos en campañas secas, normales y húmedas?", H2),
      lado_a_lado("p1_tipo_campania.png", "p1_por_campania.png",
                  "Izquierda: rendimiento vs 5 campañas anteriores según el tipo de campaña (2000/01–2024/25). "
                  "Derecha: soja del NEA, campaña por campaña.", 0.42),
      tabla([["Cultivo", "Campaña seca", "Normal", "Húmeda"],
             ["Maíz", "82 %", "101 %", "116 %"], ["Sorgo", "83 %", "96 %", "108 %"],
             ["Soja", "84 %", "98 %", "114 %"], ["Algodón", "90 %", "108 %", "115 %"],
             ["Arroz (con riego)", "102 %", "107 %", "95 %"]], [0.40, 0.20, 0.20, 0.20]),
      Spacer(1, 4),
      p("En una campaña seca los cultivos de secano rinden entre 10 % y 18 % menos que su promedio reciente, y en "
        "una húmeda entre 8 % y 16 % más. El arroz, que se riega, no sigue el patrón: eso confirma que la diferencia "
        "viene del agua. La soja del NEA rindió 78 % en 2022/23 (62 % de la lluvia normal) y 51 % en 2024/25 (73 % "
        "de la lluvia). En 2023/24 rindió 53 % con lluvia normal: ahí hubo otra causa que estos datos no explican."),
      p("P2 · ¿Qué parte de lo sembrado no se cosechó?", H2),
      lado_a_lado("p2_perdida_campania.png", "p2_departamentos.png",
                  "Izquierda: superficie perdida de soja en el NEA por campaña. Derecha: departamentos con más "
                  "pérdida en 2024/25.", 0.55),
      p("En los cultivos de secano del NEA la superficie perdida queda por debajo del 9 % en 15 de las 25 campañas, "
        "pero se dispara en las secas: 19,6 % en 2008/09, 34,0 % en 2011/12 y 32,9 % en 2024/25 (476.661 ha). "
        "También fue alta en 2012/13 (18,5 %) y 2023/24 (21,9 %) con lluvia normal o alta: la sequía no es la única "
        "causa. Los diez departamentos con más hectáreas perdidas en campañas secas son del Chaco, encabezados por "
        "Almirante Brown (340.650 ha, el 23,7 % de lo sembrado), 12 de Octubre y Chacabuco."),
      p("P3 · ¿Qué campañas fueron secas y en qué meses faltó la lluvia?", H2),
      lado_a_lado("p3_lluvia_campania.png", "p3_lluvia_meses.png",
                  "Izquierda: lluvia de octubre a marzo vs lo normal. Derecha: lluvia de cada mes vs su normal "
                  "(marrón = menos, verde = más).", 0.58),
      p("2022/23 fue la campaña más seca del período: 62 % de la lluvia normal, con los 25 departamentos de Chaco y "
        "los 25 de Corrientes en situación de sequía. Lo que faltó fue la lluvia de noviembre (43 % de lo normal), "
        "diciembre (44 %), enero (58 %) y febrero (50 %): los meses de siembra y crecimiento. Las otras campañas "
        "secas fueron 2011/12, 2024/25 (los 17 departamentos de Misiones en sequía) y 2021/22."),
      KeepTogether([p("P4 · ¿Qué parte de la producción nacional aporta el NEA?", H2),
                    imagen("p4_participacion.png", 0.85,
                           "Participación del NEA en la producción nacional, por cultivo y campaña.")]),
      tabla([["Cultivo", "2000/01 – 2004/05", "2020/21 – 2024/25"],
             ["Yerba mate y té", "100 %", "100 %"], ["Arroz", "50,3 %", "51,3 %"],
             ["<b>Algodón</b>", "<b>70,3 %</b>", "<b>25,4 %</b>"], ["Girasol", "9,2 %", "6,0 %"],
             ["Soja", "3,4 %", "2,4 %"]], [0.40, 0.30, 0.30]),
      Spacer(1, 4),
      p("El NEA mantiene la totalidad de la yerba mate y el té y la mitad del arroz, pero perdió el liderazgo del "
        "algodón: pasó de producir 7 de cada 10 toneladas del país a 1 de cada 4.")]

# --- 8. Recomendación
h += [p("8. Recomendación", H1)]
h += vinetas([
    "<b>Gestionar la sequía como el principal riesgo de la agricultura de secano del Chaco.</b> En campañas secas "
    "se pierde hasta un tercio de lo sembrado. Conviene priorizar los departamentos con más pérdidas (Almirante "
    "Brown, 12 de Octubre, Chacabuco) para seguros agrícolas, reservas de agua y variedades tolerantes.",
    "<b>Seguir la lluvia de noviembre a febrero como alerta temprana.</b> El déficit aparece meses antes de la "
    "cosecha; medirlo permite anticipar la caída de rendimiento y de superficie cosechada.",
    "<b>Investigar el desplazamiento del algodón fuera del NEA</b>, que este análisis muestra pero no explica.",
])
h += [p("Limitaciones y trabajo futuro", H2),
      p("La caída de 2023/24 con lluvia normal muestra que el clima no explica todo: antes de atribuirla a una causa "
        "(por ejemplo, la chicharrita del maíz) hay que verificarla con otra fuente. Como continuación, se podría "
        "sumar temperatura (golpes de calor), calendarios de siembra por cultivo (para el girasol y el trigo, que no "
        "son de verano) y datos de pluviómetros para validar la lluvia modelada.")]

# --- 9. Reproducibilidad
h += [p("9. Reproducibilidad y entregables", H1),
      p("Requisito: Docker Desktop. Desde la carpeta del proyecto, <b>docker compose up -d --build</b> crea el DW, "
        "carga los CSV procesados e importa el dashboard (unos 3 minutos la primera vez). El ETL se vuelve a correr "
        "con <b>python etl/run_etl.py</b> (o sin Python, con <b>docker compose --profile etl run --rm etl</b>). "
        "El procedimiento completo se probó desde cero borrando la base (<b>docker compose down -v</b>)."),
      p("<b>Entregables:</b> <i>data/raw/</i> (las dos fuentes sin modificar) y <i>data/processed/</i> (tablas del "
        "DW en CSV, rechazados y validaciones); <i>etl/</i> (ETL en Python); <i>sql/</i> (DDL, carga, vistas, "
        "permisos, consultas y validaciones); <i>dashboard/</i> (export de Superset); <i>docker-compose.yml</i> y "
        "<i>docker/</i>; <i>docs/</i> (decisiones, diccionario de datos, hallazgos y este informe) y "
        "<i>README.md</i> con la definición del negocio y los pasos para reproducir.")]

doc = SimpleDocTemplate(str(SALIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.9 * cm, title="Producción agrícola del NEA y lluvia",
                        author=", ".join(INTEGRANTES), subject="Trabajo Integrador AE4 - GABD")
doc.build(h, onFirstPage=pie_pagina, onLaterPages=pie_pagina)
print("PDF generado:", SALIDA)
