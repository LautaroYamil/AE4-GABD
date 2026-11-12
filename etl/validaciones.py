"""
Bitácora del ETL y validaciones de los merges.

- Bitacora: imprime cada mensaje en pantalla y además lo guarda, para escribir
  al final un log legible (.txt) y una tabla de métricas (.csv).
- validar_merge: controles posteriores a cada cruce (filas antes/después,
  nulos introducidos, duplicados y claves sin match).
"""
import pandas as pd


def fmt(numero):
    """Formatea un número con punto de miles (estilo argentino): 1234567 -> 1.234.567"""
    if isinstance(numero, float) and not numero.is_integer():
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{int(numero):,}".replace(",", ".")


class Bitacora:
    def __init__(self):
        self.lineas = []     # texto del log
        self.metricas = []   # filas para el CSV de validaciones

    def info(self, texto=""):
        print(texto)
        self.lineas.append(texto)

    def titulo(self, texto):
        self.info("")
        self.info("=" * 78)
        self.info(texto)
        self.info("=" * 78)

    def metrica(self, etapa, indicador, valor, detalle=""):
        """Registra un número clave del proceso (se imprime y va al CSV)."""
        self.metricas.append(
            {"etapa": etapa, "indicador": indicador, "valor": valor, "detalle": detalle}
        )
        extra = f"  ({detalle})" if detalle else ""
        self.info(f"  - {indicador}: {fmt(valor)}{extra}")

    def guardar(self, carpeta):
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "log_etl.txt").write_text("\n".join(self.lineas), encoding="utf-8")
        pd.DataFrame(self.metricas).to_csv(
            carpeta / "validaciones.csv", index=False, encoding="utf-8", lineterminator="\n"
        )


def validar_merge(bitacora, nombre, antes, despues, columna_traida, columna_clave):
    """
    Controles después de un merge LEFT (izquierda = tabla que no queremos perder).

    1. Filas antes == filas después. Si aumentan, la clave de la tabla derecha
       estaba repetida y el merge duplicó registros (error grave -> se frena).
    2. Filas duplicadas después del cruce (esperado: 0).
    3. Nulos introducidos: filas cuya clave no encontró pareja en la otra tabla.
    4. Devuelve las claves sin match con su cantidad de filas, para guardarlas.
    """
    etapa = f"merge {nombre}"
    bitacora.info(f"\nValidación post-merge: {nombre}")
    bitacora.metrica(etapa, "filas antes del merge", len(antes))
    bitacora.metrica(etapa, "filas después del merge", len(despues))
    if len(antes) != len(despues):
        raise ValueError(f"El merge '{nombre}' cambió la cantidad de filas: revisar claves duplicadas")
    bitacora.metrica(etapa, "filas duplicadas después del merge", int(despues.duplicated().sum()))

    sin_match = despues[columna_traida].isna()
    bitacora.metrica(etapa, "nulos introducidos (filas sin match)", int(sin_match.sum()),
                     f"{fmt(round(sin_match.mean() * 100, 3))} % de las filas")
    porcentaje_match = (1 - sin_match.mean()) * 100
    bitacora.metrica(etapa, "porcentaje de filas con match", round(porcentaje_match, 3))

    claves_sin_match = (
        despues.loc[sin_match, columna_clave].value_counts().rename_axis("codigo").reset_index(name="filas")
    )
    bitacora.metrica(etapa, "claves distintas sin match", len(claves_sin_match))
    return claves_sin_match
