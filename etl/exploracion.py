"""
Exploración inicial de las dos fuentes crudas (data/raw/), ANTES de limpiar nada.

    python etl/exploracion.py

De acá salen los problemas que después resuelve la limpieza. No modifica ningún
archivo: solo lee e imprime.
"""
import pandas as pd

import config
from ingesta import leer_clima, leer_estimaciones

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

COLUMNAS_NUMERICAS = [
    "superficie_sembrada_ha", "superficie_cosechada_ha", "produccion_tm", "rendimiento_kgxha",
]


def titulo(texto):
    print("\n" + "=" * 78 + "\n" + texto + "\n" + "=" * 78)


def explorar_estimaciones():
    titulo("1. ESTIMACIONES AGRÍCOLAS (Secretaría de Agricultura)")
    est = leer_estimaciones()
    print(f"Filas: {len(est):,} | Columnas: {list(est.columns)}")
    print(est.head(3).to_string())

    print("\n1.1 Valores vacíos o con el texto 'NULL' por columna:")
    for col in est.columns:
        vacios, nulos = (est[col] == "").sum(), (est[col] == "NULL").sum()
        if vacios or nulos:
            print(f"  {col}: vacíos={vacios}  'NULL'={nulos}")
    print(est[est["departamento_id"] == "NULL"].to_string())

    print("\n1.2 Columnas numéricas (¿se pueden convertir? ¿decimales? ¿negativos?):")
    for col in COLUMNAS_NUMERICAS:
        numeros = pd.to_numeric(est[col], errors="coerce")
        print(f"  {col}: no numéricos={numeros.isna().sum()}  decimales={(numeros % 1 != 0).sum()}  "
              f"negativos={(numeros < 0).sum()}  ceros={(numeros == 0).sum()}  máximo={numeros.max():,.0f}")
        est[col] = numeros

    print("\n1.3 Duplicados:")
    clave = ["cultivo", "campania", "departamento_id"]
    print(f"  filas idénticas: {est.duplicated().sum()}")
    print(f"  clave repetida (cultivo, campaña, departamento): {est.duplicated(clave).sum()} "
          "(son filas 'NULL' del punto 1.1)")
    print(f"  códigos de departamento con más de un nombre: "
          f"{(est.groupby('departamento_id')['departamento'].nunique() > 1).sum()}")

    print("\n1.4 Columna 'anio' vs campaña: ¿'anio' es el primer año de la campaña?")
    distinto = est[est["campania"].str[:4] != est["anio"]]
    print(f"  filas donde no coincide: {len(distinto):,}, por cultivo: {distinto['cultivo'].value_counts().to_dict()}")
    print(distinto[["cultivo", "anio", "campania"]].drop_duplicates().head(3).to_string())

    print("\n1.5 Coherencia entre superficies y producción:")
    sin_area = (est["superficie_cosechada_ha"] == 0) & (est["produccion_tm"] > 0)
    print(f"  producción > 0 sin superficie cosechada: {sin_area.sum():,} -> "
          f"{est.loc[sin_area, 'cultivo'].value_counts().to_dict()}")
    perdida_total = (est["superficie_sembrada_ha"] > 0) & (est["superficie_cosechada_ha"] == 0)
    print(f"  sembrado pero nada cosechado (pérdida total): {perdida_total.sum():,}")
    mas_cosecha = est["superficie_cosechada_ha"] > est["superficie_sembrada_ha"]
    print(f"  cosechada > sembrada: {mas_cosecha.sum()} -> {est.loc[mas_cosecha, 'cultivo'].value_counts().to_dict()}")
    con_area = est[est["superficie_cosechada_ha"] > 0]
    calculado = con_area["produccion_tm"] * 1000 / con_area["superficie_cosechada_ha"]
    diferencia = (calculado - con_area["rendimiento_kgxha"]).abs() / con_area["rendimiento_kgxha"]
    print(f"  rendimiento informado distinto de producción/superficie (> 5 %): "
          f"{(diferencia > 0.05).sum()} de {len(con_area):,}")

    print("\n1.6 Cultivos 'total' que incluyen a otros (riesgo de contar dos veces):")
    cobertura = est.groupby("cultivo")["campania"].agg(["min", "max", "count"])
    for cultivo in ["soja total", "soja 1ra", "soja 2da", "trigo total", "trigo candeal", "poroto total",
                    "poroto alubia", "cebada cervecera", "cebada forrajera", "cebada total"]:
        print(f"  {cultivo}: {cobertura.loc[cultivo, 'min']} a {cobertura.loc[cultivo, 'max']}")
    desde = est["campania"] >= "2000/2001"
    llave = ["campania", "departamento_id"]
    total = est[desde & (est["cultivo"] == "soja total")].groupby(llave)["produccion_tm"].sum()
    partes = est[desde & est["cultivo"].isin(["soja 1ra", "soja 2da"])].groupby(llave)["produccion_tm"].sum()
    comparacion = pd.concat([total.rename("total"), partes.rename("partes")], axis=1).fillna(0)
    iguales = ((comparacion["total"] - comparacion["partes"]).abs() <= 1).mean()
    print(f"  -> soja total = soja 1ra + soja 2da en el {iguales:.1%} de los departamentos-campaña")

    print("\n1.7 Rendimientos extremos desde 2000/2001 (veces la mediana del cultivo):")
    periodo = est[desde & (est["superficie_cosechada_ha"] > 0)].copy()
    periodo["veces"] = periodo["rendimiento_kgxha"] / periodo.groupby("cultivo")["rendimiento_kgxha"].transform("median")
    print(periodo.sort_values("veces", ascending=False)
          [["cultivo", "campania", "provincia", "departamento", "rendimiento_kgxha", "veces"]].head(5).to_string())

    print("\n1.8 Cobertura por cultivo (primera y última campaña, filas):")
    print(cobertura.sort_values("max").to_string())
    return est


def explorar_clima(est):
    titulo("2. CLIMA DIARIO NASA POWER (un archivo por departamento del NEA)")
    archivos = sorted(config.DIR_CLIMA_RAW.glob("*.csv"))
    print(f"Archivos: {len(archivos)}. Encabezado del primero:")
    print("\n".join(archivos[0].read_text(encoding="utf-8").splitlines()[:12]))

    clima = leer_clima()
    print(f"\nFilas: {len(clima):,} | Columnas: {list(clima.columns)}")
    print(f"  filas por archivo: {clima.groupby('departamento_id').size().unique()}")
    for col in ["PRECTOTCORR", "T2M_MAX"]:
        valores = clima[col]
        print(f"  {col}: faltantes ({config.VALOR_FALTANTE_NASA})={(valores == config.VALOR_FALTANTE_NASA).sum()}  "
              f"mín={valores[valores != config.VALOR_FALTANTE_NASA].min()}  máx={valores.max()}")
    print(f"  días con más de 300 mm: {(clima['PRECTOTCORR'] > 300).sum()}")

    # La NASA da año y número de día del año (DOY), no mes y día
    fechas = pd.to_datetime(clima["YEAR"] * 1000 + clima["DOY"], format="%Y%j")
    print(f"  fechas: {fechas.min().date()} a {fechas.max().date()} | repetidas por departamento: "
          f"{clima.assign(f=fechas).duplicated(['departamento_id', 'f']).sum()}")

    firma = clima.groupby("departamento_id")["PRECTOTCORR"].sum().round(2)
    print(f"  series de lluvia distintas: {firma.nunique()} de {len(firma)} departamentos "
          "(los departamentos chicos caen en la misma celda de la grilla de la NASA)")

    print("\n2.1 Cruce clima -> estimaciones por código INDEC del departamento:")
    codigos_est = set(est["departamento_id"])
    sin_match = sorted(set(clima["departamento_id"]) - codigos_est)
    print(f"  departamentos con clima que no aparecen en las estimaciones: {sin_match}")
    nea = est[est["provincia_id"].isin(config.PROVINCIAS_NEA) & (est["campania"] >= config.CAMPANIA_DESDE)]
    sin_clima = nea[~nea["departamento_id"].isin(set(clima["departamento_id"]))]
    print(f"  filas de producción del NEA sin clima: {len(sin_clima)} -> "
          f"{sin_clima.groupby(['departamento_id', 'departamento']).size().to_dict()}")

    inicio = fechas.dt.year.where(fechas.dt.month >= 7, fechas.dt.year - 1)
    clima["campania"] = inicio.astype(str) + "/" + (inicio + 1).astype(str)
    verano = clima[fechas.dt.month.isin(config.MESES_LLUVIA_VERANO)]
    por_campania = (verano.groupby(["campania", "departamento_id"])["PRECTOTCORR"].sum()
                    .groupby("campania").mean().round(0))
    print("\n2.2 Lluvia octubre-marzo (mm), promedio de los departamentos del NEA:")
    print(por_campania.to_string())


if __name__ == "__main__":
    estimaciones = explorar_estimaciones()
    explorar_clima(estimaciones)
