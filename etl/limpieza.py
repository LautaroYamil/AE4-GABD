"""
Limpieza de cada fuente por separado. Cada paso deja su número en la bitácora.
Los criterios están justificados en docs/decisiones.md (D02 a D10).
"""
import pandas as pd

import config

COLUMNAS_NUMERICAS = ["superficie_sembrada_ha", "superficie_cosechada_ha", "produccion_tm", "rendimiento_kgxha"]


def limpiar_estimaciones(est, bitacora):
    """Devuelve (estimaciones limpias, filas rechazadas con su motivo)."""
    bitacora.titulo("LIMPIEZA 1 - ESTIMACIONES AGRÍCOLAS")
    etapa = "limpieza estimaciones"
    bitacora.metrica(etapa, "filas leídas", len(est))
    rechazados = []

    # 1. Quitar espacios de los textos
    for col in ["cultivo", "campania", "provincia", "provincia_id", "departamento", "departamento_id"]:
        est[col] = est[col].str.strip()

    # 2. Filas sin ubicación: traen el texto 'NULL' en provincia y departamento (D02)
    sin_ubicacion = est["departamento_id"].isin(["NULL", ""])
    rechazados.append(est[sin_ubicacion].assign(motivo="sin provincia ni departamento (texto NULL)"))
    est = est[~sin_ubicacion].copy()
    bitacora.metrica(etapa, "filas sin departamento (rechazadas)", int(sin_ubicacion.sum()))

    # 3. Tipos: las cuatro medidas son números enteros sin negativos (verificado en la exploración).
    #    errors="raise": si algún día llega un texto raro, el ETL se frena en vez de inventar un valor.
    for col in COLUMNAS_NUMERICAS:
        est[col] = pd.to_numeric(est[col], errors="raise").astype("int64")
        if (est[col] < 0).any():
            raise ValueError(f"Hay valores negativos en {col}")

    # 4. Período: la campaña "AAAA/AAAA" se puede comparar como texto (D03)
    en_periodo = est["campania"].between(config.CAMPANIA_DESDE_CARGA, config.CAMPANIA_HASTA)
    bitacora.metrica(etapa, "filas fuera del período (excluidas)", int((~en_periodo).sum()),
                     f"se carga {config.CAMPANIA_DESDE_CARGA} a {config.CAMPANIA_HASTA}")
    est = est[en_periodo].copy()

    # 5. Doble conteo: los subcultivos ya están sumados en su "total" (D04)
    es_subcultivo = est["cultivo"].isin(config.SUBCULTIVOS)
    bitacora.metrica(etapa, "filas de subcultivos (excluidas por doble conteo)", int(es_subcultivo.sum()),
                     ", ".join(config.SUBCULTIVOS))
    est = est[~es_subcultivo].copy()

    # 6. Duplicados: filas idénticas y clave repetida (cultivo, campaña, departamento)
    clave = ["cultivo", "campania", "departamento_id"]
    duplicadas = est.duplicated()
    rechazados.append(est[duplicadas].assign(motivo="fila duplicada"))
    est = est[~duplicadas].copy()
    bitacora.metrica(etapa, "filas duplicadas (rechazadas)", int(duplicadas.sum()))
    if est.duplicated(clave).any():
        raise ValueError("Hay claves repetidas (mismo cultivo, campaña y departamento)")

    # 7. Columnas que no pasan al DW (D08):
    #    - 'anio': en yerba y té es el año final de la campaña y en el resto el inicial. Se usa 'campania'.
    #    - 'rendimiento_kgxha': es un cociente, no se puede sumar. Se recalcula siempre como
    #      producción / superficie cosechada.
    est = est.drop(columns=["anio", "rendimiento_kgxha"])

    # 8. Cebada: hasta 2015/16 viene en dos filas (cervecera y forrajera) y desde 2016/17 en una
    #    ("cebada total"). Se suman las dos partes para tener una sola serie "cebada" (D05)
    est["cultivo"] = est["cultivo"].replace(config.NOMBRES_UNIFICADOS)
    filas_antes = len(est)
    textos = ["cultivo", "campania", "provincia", "provincia_id", "departamento", "departamento_id"]
    medidas = ["superficie_sembrada_ha", "superficie_cosechada_ha", "produccion_tm"]
    est = est.groupby(textos, as_index=False)[medidas].sum()
    bitacora.metrica(etapa, "filas de cebada unidas (cervecera + forrajera)", filas_antes - len(est))

    # 9. Filas vacías: nada sembrado, nada cosechado, nada producido. No aportan información (D06)
    vacias = (est["superficie_sembrada_ha"] == 0) & (est["superficie_cosechada_ha"] == 0) & (est["produccion_tm"] == 0)
    bitacora.metrica(etapa, "filas con todo en cero (excluidas)", int(vacias.sum()))
    est = est[~vacias].copy()

    # 10. Ceros que SÍ se conservan: sembrado y nada cosechado = pérdida total por clima (D06)
    perdida_total = (est["superficie_sembrada_ha"] > 0) & (est["superficie_cosechada_ha"] == 0)
    bitacora.metrica(etapa, "filas con pérdida total (se conservan)", int(perdida_total.sum()))

    # 11. Outliers: rendimiento imposible, más de N veces la mediana del cultivo (D07)
    cosechadas = est["superficie_cosechada_ha"] > 0
    rendimiento = (est["produccion_tm"] * 1000 / est["superficie_cosechada_ha"]).where(cosechadas)
    mediana = rendimiento.groupby(est["cultivo"]).median()
    outlier = rendimiento > est["cultivo"].map(mediana) * config.VECES_MEDIANA_OUTLIER
    rechazados.append(est[outlier].assign(
        motivo=f"rendimiento mayor a {config.VECES_MEDIANA_OUTLIER} veces la mediana del cultivo"))
    est = est[~outlier].copy()
    bitacora.metrica(etapa, "filas con rendimiento imposible (rechazadas)", int(outlier.sum()))

    # 12. Control: no puede haber más superficie cosechada que sembrada
    if (est["superficie_cosechada_ha"] > est["superficie_sembrada_ha"]).any():
        raise ValueError("Hay filas con superficie cosechada mayor a la sembrada")
    bitacora.metrica(etapa, "filas limpias", len(est))

    rechazados = pd.concat(rechazados, ignore_index=True)
    return est, rechazados


def limpiar_clima(clima, bitacora):
    """Devuelve una fila por departamento y día: departamento_id, fecha, lluvia_mm."""
    bitacora.titulo("LIMPIEZA 2 - CLIMA NASA POWER")
    etapa = "limpieza clima"
    bitacora.metrica(etapa, "filas leídas", len(clima))

    # 1. Fecha: la NASA da el año y el número de día del año (1 a 366), no mes y día (D09)
    clima["fecha"] = pd.to_datetime(clima["YEAR"] * 1000 + clima["DOY"], format="%Y%j")

    # 2. Faltantes: la NASA los marca con -999. Se pasan a nulo para no sumarlos como lluvia.
    faltante = clima["PRECTOTCORR"] == config.VALOR_FALTANTE_NASA
    clima["lluvia_mm"] = clima["PRECTOTCORR"].mask(faltante)
    bitacora.metrica(etapa, "días sin dato de lluvia (-999)", int(faltante.sum()))
    if (clima["lluvia_mm"] < 0).any():
        raise ValueError("Hay lluvias negativas distintas de -999")

    # 3. Duplicados: un departamento no puede tener dos valores para el mismo día
    duplicadas = clima.duplicated(["departamento_id", "fecha"])
    bitacora.metrica(etapa, "días repetidos (eliminados)", int(duplicadas.sum()))
    clima = clima[~duplicadas]

    # 4. Extremos: más de 300 mm en un día. Se conservan: coinciden en departamentos vecinos
    #    el mismo día, así que son tormentas reales y no errores (D10)
    bitacora.metrica(etapa, "días con más de 300 mm (se conservan)", int((clima["lluvia_mm"] > 300).sum()))

    # 5. Solo pasa la lluvia: la temperatura máxima no responde ninguna pregunta (D10)
    clima = clima[["departamento_id", "fecha", "lluvia_mm"]].copy()
    bitacora.metrica(etapa, "filas limpias", len(clima))
    return clima
