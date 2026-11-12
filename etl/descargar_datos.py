"""
Descarga las fuentes originales a data/raw/ (solo las que todavía no están).

    python etl/descargar_datos.py

- Estimaciones agrícolas: un CSV, se guarda sin tocar.
- Clima NASA POWER: un pedido por cada departamento del NEA. A la NASA hay que
  darle un punto (latitud y longitud): usamos el centro de cada departamento que
  publica Georef. Esa lista se lee en memoria solo para armar el pedido; no se
  guarda. Cada respuesta se guarda tal cual en data/raw/nasa_power/<código INDEC>.csv

No hace falta correrlo para reproducir el trabajo: los archivos ya vienen en data/raw/.
Solo usa la biblioteca estándar de Python (urllib), sin dependencias extra.
"""
import csv
import io
import time
import urllib.parse
import urllib.request

import config


def descargar(url, destino, intentos=3):
    """Baja una URL a un archivo. Reintenta si el servidor falla."""
    # El servidor de Georef rechaza (403) el identificador por defecto de Python,
    # así que mandamos uno genérico de navegador.
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(pedido, timeout=180) as respuesta:
                contenido = respuesta.read()
            destino.write_bytes(contenido)
            return
        except Exception as error:  # noqa: BLE001 - mostramos cualquier error de red
            print(f"    intento {intento} falló: {error}")
            time.sleep(5 * intento)
    raise RuntimeError(f"No se pudo descargar {url}")


def descargar_si_falta(url, destino):
    if destino.exists():
        print(f"  ya existe: {destino.name}")
        return
    print(f"  descargando {destino.name} ...")
    descargar(url, destino)


def departamentos_nea():
    """Devuelve (código, nombre, lat, lon) del centro de cada departamento del NEA (Georef)."""
    pedido = urllib.request.Request(config.URL_CENTROIDES, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pedido, timeout=180) as respuesta:
        texto = respuesta.read().decode("utf-8")
    filas = list(csv.DictReader(io.StringIO(texto)))
    return [
        (f["id"], f["nombre"], f["centroide_lat"], f["centroide_lon"])
        for f in filas
        if f["provincia_id"] in config.PROVINCIAS_NEA
    ]


def main():
    config.DIR_RAW.mkdir(parents=True, exist_ok=True)
    config.DIR_CLIMA_RAW.mkdir(parents=True, exist_ok=True)

    print("Fuente 1: estimaciones agrícolas")
    descargar_si_falta(config.URL_ESTIMACIONES, config.ARCHIVO_ESTIMACIONES)

    lista = departamentos_nea()
    print(f"\nFuente 2: clima NASA POWER, {len(lista)} departamentos del NEA")
    for numero, (id_depto, nombre, lat, lon) in enumerate(lista, start=1):
        destino = config.DIR_CLIMA_RAW / f"{id_depto}.csv"
        if destino.exists():
            continue
        parametros = urllib.parse.urlencode({
            "parameters": config.VARIABLES_NASA,
            "community": "AG",
            "latitude": lat,
            "longitude": lon,
            "start": config.CLIMA_DESDE,
            "end": config.CLIMA_HASTA,
            "format": "CSV",
        })
        print(f"  [{numero}/{len(lista)}] {id_depto} {nombre}")
        descargar(f"{config.URL_NASA_POWER}?{parametros}", destino)
        time.sleep(1)  # pausa corta para no saturar el servicio de la NASA

    print("\nListo.")


if __name__ == "__main__":
    main()
