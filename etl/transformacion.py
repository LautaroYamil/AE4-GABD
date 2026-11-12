"""
Transformación: arma las dimensiones y las tablas de hechos del modelo estrella
y hace los cruces (merge) entre las dos fuentes, con sus validaciones.
Decisiones de modelado en docs/decisiones.md (D11 a D15).
"""
import pandas as pd

import config
from validaciones import validar_merge

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def campania_de(fechas):
    """La campaña va de julio a junio: el 15/03/2023 pertenece a la campaña 2022/2023."""
    inicio = fechas.dt.year.where(fechas.dt.month >= 7, fechas.dt.year - 1)
    return inicio.astype(str) + "/" + (inicio + 1).astype(str)


def construir_dim_tiempo():
    """Un registro por día, desde el inicio de la primera campaña cargada hasta el fin de la última."""
    desde = pd.Timestamp(f"{config.CAMPANIA_DESDE_CARGA[:4]}-07-01")
    hasta = pd.Timestamp(f"{config.CAMPANIA_HASTA[5:]}-06-30")
    fechas = pd.Series(pd.date_range(desde, hasta, freq="D"))
    return pd.DataFrame({
        "id_fecha": fechas.dt.strftime("%Y%m%d").astype(int),   # clave AAAAMMDD: legible y ordenable
        "fecha": fechas.dt.date,
        "dia": fechas.dt.day,
        "nombre_dia": fechas.dt.dayofweek.map(lambda d: DIAS[d]),
        "mes": fechas.dt.month,
        "nombre_mes": fechas.dt.month.map(lambda m: MESES[m - 1]),
        "trimestre": fechas.dt.quarter,
        "anio": fechas.dt.year,
        "campania": campania_de(fechas),
        "es_mes_lluvia_verano": fechas.dt.month.isin(config.MESES_LLUVIA_VERANO),
    })


def construir_dim_departamento(est, codigos_con_clima):
    """Departamentos tal como vienen en las estimaciones (código INDEC, nombre y provincia)."""
    dep = (est[["departamento_id", "departamento", "provincia_id", "provincia"]]
           .drop_duplicates()
           .rename(columns={"departamento_id": "codigo_indec", "departamento": "nombre"})
           .sort_values("codigo_indec")
           .reset_index(drop=True))
    if not dep["codigo_indec"].is_unique:
        raise ValueError("Un código de departamento aparece con dos nombres o dos provincias")
    dep.insert(0, "id_departamento", range(1, len(dep) + 1))   # clave subrogada
    dep["es_nea"] = dep["provincia_id"].isin(config.PROVINCIAS_NEA)
    # Código terminado en 000 = la Secretaría no sabe el departamento, solo la provincia (D12)
    dep["es_sin_definir"] = dep["codigo_indec"].str.endswith("000")
    dep["tiene_clima"] = dep["codigo_indec"].isin(codigos_con_clima)
    return dep


def construir_dim_cultivo(est):
    cul = (est.groupby("cultivo")["campania"].agg(primera_campania="min", ultima_campania="max")
           .reset_index().rename(columns={"cultivo": "nombre"}))
    cul.insert(0, "id_cultivo", range(1, len(cul) + 1))
    return cul


def construir_fact_produccion(est, dim_departamento, dim_cultivo, dim_tiempo, bitacora):
    """Una fila por cultivo, departamento y campaña."""
    bitacora.titulo("TRANSFORMACIÓN - FACT_PRODUCCION")

    # Merge 1: estimaciones -> dim_departamento por código INDEC (LEFT: no se pierde producción)
    antes = est
    con_depto = est.merge(dim_departamento[["id_departamento", "codigo_indec"]],
                          left_on="departamento_id", right_on="codigo_indec",
                          how="left", validate="many_to_one")
    validar_merge(bitacora, "estimaciones -> dim_departamento", antes, con_depto,
                  "id_departamento", "departamento_id")

    # Merge 2: -> dim_cultivo por nombre de cultivo
    antes = con_depto
    con_cultivo = con_depto.merge(dim_cultivo[["id_cultivo", "nombre"]], left_on="cultivo", right_on="nombre",
                                  how="left", validate="many_to_one")
    validar_merge(bitacora, "estimaciones -> dim_cultivo", antes, con_cultivo, "id_cultivo", "cultivo")

    # La producción es anual: se ancla al 1 de julio en que empieza la campaña (D13)
    con_cultivo["id_fecha"] = (con_cultivo["campania"].str[:4] + "0701").astype(int)
    if not con_cultivo["id_fecha"].isin(dim_tiempo["id_fecha"]).all():
        raise ValueError("Hay campañas fuera de dim_tiempo")

    fact = con_cultivo[["id_fecha", "id_departamento", "id_cultivo", "superficie_sembrada_ha",
                        "superficie_cosechada_ha", "produccion_tm"]].rename(columns={"produccion_tm": "produccion_t"})
    if fact.duplicated(["id_fecha", "id_departamento", "id_cultivo"]).any():
        raise ValueError("fact_produccion tiene filas repetidas para la misma clave")
    bitacora.metrica("fact_produccion", "filas", len(fact))
    return fact


def construir_fact_clima(clima, dim_departamento, bitacora):
    """Una fila por departamento y día."""
    bitacora.titulo("TRANSFORMACIÓN - FACT_CLIMA_DIARIO")

    # Merge 3: clima -> dim_departamento por código INDEC (el nombre del archivo de la NASA)
    antes = clima
    con_depto = clima.merge(dim_departamento[["id_departamento", "codigo_indec"]],
                            left_on="departamento_id", right_on="codigo_indec",
                            how="left", validate="many_to_one")
    sin_match = validar_merge(bitacora, "clima -> dim_departamento", antes, con_depto,
                              "id_departamento", "departamento_id")
    # Un departamento sin ninguna producción en las estimaciones no está en la dimensión.
    # Su clima no se puede comparar con nada, así que se excluye (D14)
    con_depto = con_depto[con_depto["id_departamento"].notna()]
    bitacora.metrica("fact_clima_diario", "filas excluidas por departamento sin producción",
                     len(antes) - len(con_depto))

    con_depto["id_fecha"] = con_depto["fecha"].dt.strftime("%Y%m%d").astype(int)
    fact = con_depto[["id_fecha", "id_departamento", "lluvia_mm"]].copy()
    fact["id_departamento"] = fact["id_departamento"].astype(int)
    bitacora.metrica("fact_clima_diario", "filas", len(fact))
    return fact, sin_match


def validar_cruce_produccion_lluvia(fact_produccion, fact_clima, dim_departamento, dim_tiempo, bitacora):
    """
    Merge 4 (el cruce analítico de las dos fuentes): producción del NEA de cada
    campaña con la lluvia de octubre a marzo de ese departamento y esa campaña.
    En el DW lo hace la vista vw_produccion_lluvia; acá se valida que el cruce funcione.
    """
    bitacora.titulo("VALIDACIÓN DEL CRUCE PRODUCCIÓN - LLUVIA")
    tiempo = dim_tiempo[["id_fecha", "campania", "es_mes_lluvia_verano"]]
    lluvia = (fact_clima.merge(tiempo, on="id_fecha")
              .query("es_mes_lluvia_verano")
              .groupby(["id_departamento", "campania"], as_index=False)["lluvia_mm"].sum())

    prod = fact_produccion.merge(tiempo[["id_fecha", "campania"]], on="id_fecha")
    nea = dim_departamento.loc[dim_departamento["es_nea"], "id_departamento"]
    prod = prod[prod["id_departamento"].isin(nea) & (prod["campania"] >= config.CAMPANIA_DESDE)]

    cruce = prod.merge(lluvia, on=["id_departamento", "campania"], how="left", validate="many_to_one")
    sin_lluvia = validar_merge(bitacora, "producción NEA -> lluvia de la campaña", prod, cruce,
                               "lluvia_mm", "id_departamento")
    codigos = dim_departamento.set_index("id_departamento")["codigo_indec"]
    bitacora.info(f"  departamentos sin lluvia: {sorted(codigos[sin_lluvia['codigo']].tolist())} "
                  "(son los 'sin definir': no tienen un punto para pedirle el clima a la NASA)")
