"""
ETL completo: ingesta -> limpieza -> transformación -> CSV listos para el DW.

    python etl/run_etl.py

Salida en data/processed/ (una tabla del DW por archivo) y en data/processed/validaciones/.
"""
import time

import config
from ingesta import leer_clima, leer_estimaciones
from limpieza import limpiar_clima, limpiar_estimaciones
from transformacion import (construir_dim_cultivo, construir_dim_departamento, construir_dim_tiempo,
                            construir_fact_clima, construir_fact_produccion, validar_cruce_produccion_lluvia)
from validaciones import Bitacora


def guardar(tabla, nombre):
    # lineterminator="\n": el mismo archivo byte a byte en Windows y en Linux (Docker)
    tabla.to_csv(config.DIR_PROCESADOS / f"{nombre}.csv", index=False, encoding="utf-8", lineterminator="\n")


def main():
    inicio = time.time()
    bitacora = Bitacora()
    config.DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)

    # 1. Ingesta: cada fuente por separado
    estimaciones = leer_estimaciones()
    clima = leer_clima()

    # 2. Limpieza
    estimaciones, rechazados = limpiar_estimaciones(estimaciones, bitacora)
    clima = limpiar_clima(clima, bitacora)

    # 3. Dimensiones
    dim_tiempo = construir_dim_tiempo()
    dim_departamento = construir_dim_departamento(estimaciones, set(clima["departamento_id"]))
    dim_cultivo = construir_dim_cultivo(estimaciones)
    bitacora.titulo("DIMENSIONES")
    bitacora.metrica("dimensiones", "dim_tiempo (días)", len(dim_tiempo))
    bitacora.metrica("dimensiones", "dim_departamento", len(dim_departamento),
                     f"{int(dim_departamento['es_nea'].sum())} del NEA")
    bitacora.metrica("dimensiones", "dim_cultivo", len(dim_cultivo))

    # 4. Hechos y cruces
    fact_produccion = construir_fact_produccion(estimaciones, dim_departamento, dim_cultivo, dim_tiempo, bitacora)
    fact_clima, clima_sin_match = construir_fact_clima(clima, dim_departamento, bitacora)
    validar_cruce_produccion_lluvia(fact_produccion, fact_clima, dim_departamento, dim_tiempo, bitacora)

    # 5. Guardar
    guardar(dim_tiempo, "dim_tiempo")
    guardar(dim_departamento, "dim_departamento")
    guardar(dim_cultivo, "dim_cultivo")
    guardar(fact_produccion, "fact_produccion")
    guardar(fact_clima, "fact_clima_diario")
    guardar(rechazados, "rechazados")
    config.DIR_VALIDACIONES.mkdir(parents=True, exist_ok=True)
    clima_sin_match.to_csv(config.DIR_VALIDACIONES / "clima_sin_departamento.csv", index=False,
                           encoding="utf-8", lineterminator="\n")
    bitacora.info(f"\nETL terminado en {time.time() - inicio:.0f} segundos.")
    bitacora.guardar(config.DIR_VALIDACIONES)


if __name__ == "__main__":
    main()
