"""
Ingesta: lee cada fuente cruda por separado, sin transformar nada.
Todo se lee como texto (dtype=str) para que pandas no adivine tipos:
los tipos se convierten después, en la limpieza, con controles.
"""
import pandas as pd

import config


def leer_estimaciones():
    """Fuente 1. CSV separado por coma, UTF-8, con comillas (verificado al abrirlo)."""
    # keep_default_na=False: un vacío queda como "" y el texto "NULL" queda como "NULL",
    # así los vemos y decidimos qué hacer en la limpieza.
    return pd.read_csv(config.ARCHIVO_ESTIMACIONES, dtype=str, keep_default_na=False, encoding="utf-8")


def leer_clima():
    """
    Fuente 2. Un CSV por departamento. Cada archivo trae un encabezado de texto
    que termina en la línea '-END HEADER-'; los datos empiezan después.
    El código INDEC del departamento es el nombre del archivo (ej. 54098.csv).
    """
    tablas = []
    for ruta in sorted(config.DIR_CLIMA_RAW.glob("*.csv")):
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        inicio_datos = lineas.index("-END HEADER-") + 1
        tabla = pd.read_csv(ruta, skiprows=inicio_datos)
        tabla["departamento_id"] = ruta.stem
        tablas.append(tabla)
    return pd.concat(tablas, ignore_index=True)
