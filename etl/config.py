"""
Parámetros del proyecto en un solo lugar: rutas, fuentes, período y umbrales.
Si hay que cambiar un criterio, se cambia acá y no en el medio del código.
"""
from pathlib import Path

# --- Rutas -------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_CLIMA_RAW = DIR_RAW / "nasa_power"          # un CSV de clima por departamento
DIR_PROCESADOS = RAIZ / "data" / "processed"
DIR_VALIDACIONES = DIR_PROCESADOS / "validaciones"

# --- Fuente 1: Estimaciones agrícolas (Secretaría de Agricultura, CC BY 4.0) ---
URL_ESTIMACIONES = (
    "https://datos.magyp.gob.ar/dataset/9e1e77ba-267e-4eaa-a59f-3296e86b5f36/resource/"
    "95d066e6-8a0f-4a80-b59d-6f28f88eacd5/download/estimaciones-agricolas-2026-03.csv"
)
ARCHIVO_ESTIMACIONES = DIR_RAW / "estimaciones-agricolas-2026-03.csv"

# --- Fuente 2: Clima diario NASA POWER (uso libre) ----------------------------
URL_NASA_POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
VARIABLES_NASA = "PRECTOTCORR,T2M_MAX"   # lluvia (mm/día) y temperatura máxima (°C)
CLIMA_DESDE = "20000701"                 # inicio de la campaña 2000/2001
CLIMA_HASTA = "20250630"                 # fin de la campaña 2024/2025
VALOR_FALTANTE_NASA = -999               # así marca la NASA un dato que no tiene
# Solo para ubicar el punto que se le pide a la NASA (centro de cada departamento).
# No se guarda ni se carga al DW: no es una fuente del trabajo.
URL_CENTROIDES = "https://infra.datos.gob.ar/georef/departamentos.csv"

# --- Alcance -------------------------------------------------------------------
# Códigos INDEC de las provincias del NEA (los usan las dos fuentes)
PROVINCIAS_NEA = {"18": "Corrientes", "22": "Chaco", "34": "Formosa", "54": "Misiones"}
CAMPANIA_DESDE = "2000/2001"       # primera campaña que se analiza
CAMPANIA_DESDE_CARGA = "1995/1996"  # se cargan 5 campañas antes, solo para el promedio de 2000/2001
CAMPANIA_HASTA = "2024/2025"

# --- Reglas de limpieza (ver docs/decisiones.md) ------------------------------
# Cultivos que ya están sumados dentro de otro "total": se excluyen para no contar dos veces
SUBCULTIVOS = ["soja 1ra", "soja 2da", "trigo candeal", "poroto alubia", "poroto negro", "poroto otros"]
# La cebada cambia de nombre en 2016/2017; las tres series no se superponen
NOMBRES_UNIFICADOS = {"cebada cervecera": "cebada", "cebada forrajera": "cebada", "cebada total": "cebada"}
# Rendimiento imposible: más de 4 veces la mediana del cultivo en el período
VECES_MEDIANA_OUTLIER = 4

# --- Lluvia -------------------------------------------------------------------
MESES_LLUVIA_VERANO = [10, 11, 12, 1, 2, 3]   # octubre a marzo: ciclo de los cultivos de verano
LIMITE_CAMPANIA_SECA = 0.8                     # menos del 80 % de lo normal
LIMITE_CAMPANIA_HUMEDA = 1.2                   # más del 120 % de lo normal
