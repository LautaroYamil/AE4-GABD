# Decisiones y supuestos

Cada decisión indica qué se hizo, por qué y cuántas filas afectó. Los números salen de
`data/processed/validaciones/log_etl.txt` (se regenera con `python etl/run_etl.py`).

## Fuentes y alcance

**D01 · Dos fuentes reales.**

| Fuente | Organismo | Licencia | Archivo en `data/raw/` |
|---|---|---|---|
| Estimaciones agrícolas | Secretaría de Agricultura, Ganadería y Pesca | CC BY 4.0 | `estimaciones-agricolas-2026-03.csv` (160.499 filas) |
| Clima diario NASA POWER | NASA | uso libre | `nasa_power/<código INDEC>.csv` (76 archivos) |

- A la NASA hay que pedirle un punto (latitud y longitud). Usamos el centro de cada departamento del NEA que publica Georef.
- Ese dato se usa solo para armar el pedido en `etl/descargar_datos.py`: no se guarda ni se carga al DW.
- El cruce entre las dos fuentes se hace por el **código INDEC del departamento**, que usan las dos.
- **Período:** campañas 2000/01 a 2024/25. Se cargan también las campañas 1995/96 a 1999/00, solo para calcular el promedio de las 5 campañas anteriores a 2000/01 (D16).
- **Producción:** de todo el país, porque P4 la compara con el total nacional.
- **Clima:** solo de los 76 departamentos del NEA (Misiones, Corrientes, Chaco, Formosa).

## Limpieza: estimaciones agrícolas

**D02 · Filas sin ubicación.**
- 8 filas de 1979–1980 tienen el texto `NULL` en provincia y departamento.
- Se rechazan (van a `rechazados.csv`): sin departamento no se pueden ubicar.

**D03 · Período.**
- Se excluyen 89.467 filas de campañas anteriores a 1995/96.
- La campaña tiene la forma `AAAA/AAAA`, así que se puede comparar como texto.

**D04 · Doble conteo.**
- "soja total" = "soja 1ra" + "soja 2da" (comprobado: coincide en el 99,6 % de los departamentos-campaña).
- "trigo total" incluye a "trigo candeal", y "poroto total" incluye a los tipos de poroto.
- Se dejan solo los totales y se excluyen 12.961 filas de subcultivos.
- Si no, la soja contaría dos veces.

**D05 · Cebada.**
- Hasta 2015/16 viene en dos filas: cervecera y forrajera. Desde 2016/17 viene como "cebada total".
- Se suman las dos partes para tener una sola serie "cebada"; eso une 563 filas.

**D06 · Ceros.**
- Se excluyen 24 filas con todo en cero (nada sembrado, cosechado ni producido): no aportan información.
- Se **conservan** 2.533 filas con superficie sembrada y nada cosechado. Son pérdidas totales (sequía, inundación) y son justamente lo que mide el KPI 3.

**D07 · Outliers.**
- Se rechazan los rendimientos mayores a 4 veces la mediana del cultivo: son 4 filas.
- Ejemplo: la soja de San Alberto (Córdoba) en 2011/12, con 19.902 kg/ha. Lo normal es 2.500 kg/ha, y el máximo posible ronda los 6.000.

**D08 · Columnas que no pasan al DW.**
- `anio`: en yerba mate y té es el año en que *termina* la campaña; en el resto, el año en que *empieza*. Se usa `campania`, que es igual para todos los cultivos.
- `rendimiento_kgxha`: es un cociente y no se puede sumar.
  - El rendimiento se calcula siempre como Σ toneladas × 1000 ÷ Σ hectáreas cosechadas.
  - Nunca se promedian rendimientos.

## Limpieza: clima

**D09 · Fecha.** La NASA da el año y el número de día del año (1 a 366), no el mes y el día. Se convierte a fecha.

**D10 · Valores.**
- No hay datos faltantes: la NASA los marca con −999 y hay 0. Si aparecieran, se pasarían a nulo para no sumarlos como lluvia.
- Hay 3 días con más de 300 mm (máximo 491 mm, Corrientes, 27/11/2015). Se conservan: el mismo día hubo valores parecidos en departamentos vecinos, así que son tormentas y no errores.
- La temperatura máxima no responde ninguna pregunta, así que no pasa al DW.

## Modelo y cruces

**D11 · Modelo estrella con dos tablas de hechos que comparten dimensiones.**
- `fact_produccion` tiene una fila por cultivo, departamento y campaña.
- `fact_clima_diario` tiene una fila por departamento y día.
- Tienen grano distinto, así que no se pueden juntar en una sola tabla.
- Se usan claves subrogadas en `dim_departamento` y `dim_cultivo`. La clave de `dim_tiempo` es AAAAMMDD.

**D12 · "Sin definir".**
- Las estimaciones usan el código `XX000` cuando solo saben la provincia.
- En el NEA pasa en Corrientes hasta 2017/18, en Formosa hasta 2020/21, en Misiones hasta 2010/11 y en Chaco en 2000/01.
- Se cargan como un departamento "sin definir" de cada provincia, para que los totales provinciales den exactos.
- No tienen clima, porque no hay un punto para pedírselo a la NASA.

**D13 · La producción es anual.**
- Se ancla al **1 de julio** en que empieza la campaña. Así las dos tablas de hechos usan la misma `dim_tiempo` y se cruzan por el atributo `campania`.
- La campaña va de julio a junio, que es la convención de la Secretaría de Agricultura.

**D14 · Cruces del ETL.**
- Todos los cruces son **LEFT JOIN**: la tabla de la izquierda (la producción o el clima) no puede perder filas.
  - Si una clave no encuentra pareja, la fila queda con un nulo. Así se cuenta y se informa, en vez de desaparecer en silencio como pasaría con un INNER JOIN.
- `validate="many_to_one"` hace que pandas se frene si la tabla de la derecha tiene la clave repetida, porque eso duplicaría filas.
- Después de cada cruce se controlan:
  - las filas antes y después;
  - los nulos introducidos;
  - las filas duplicadas;
  - las claves sin match.
- Los resultados se imprimen y quedan en `validaciones/`.

| Cruce | Clave | Resultado |
|---|---|---|
| estimaciones → dim_departamento | código INDEC | 57.472 → 57.472 filas, 100 % de cruce |
| estimaciones → dim_cultivo | nombre del cultivo | 57.472 → 57.472 filas, 100 % de cruce |
| clima → dim_departamento | código INDEC (nombre del archivo) | 97,37 % de cruce |
| producción NEA → lluvia de la campaña | departamento + campaña | 97,75 % de cruce |

- **Clima sin departamento:** 34028 (Formosa) y 34063 (Ramón Lista) no tienen ninguna producción en el período. Su clima no se puede comparar con nada, así que se excluye (18.262 filas).
- **Producción sin lluvia:** son los 4 "sin definir" del NEA (D12).

**D15 · Tipo de campaña.**
- Para los cultivos de verano, la lluvia que importa es la de **octubre a marzo** (de la siembra al llenado de grano).
- Se compara con la normal del departamento, que es el promedio de 2000/01 a 2024/25.
- **Seca:** menos del 80 % de lo normal. **Húmeda:** más del 120 %. **Normal:** entre los dos.
- El cruce se hace en la vista `vw_produccion_lluvia`.

**D16 · KPI 1 contra las 5 campañas anteriores.**
- El maíz del NEA rinde casi el doble que en 2000. Comparar contra el promedio de todo el período haría que los primeros años den siempre bajos solo por tecnología.
- Por eso cada campaña se compara con las 5 anteriores del mismo cultivo y departamento.
- Se exige que haya al menos 3 de esas 5 campañas; si no, la fila no entra en el KPI.

## Limitaciones

- La producción es anual: no se sabe en qué mes se perdió el cultivo.
- Son estimaciones oficiales, no un censo.
- La lluvia viene de un modelo con datos satelitales, en una grilla de unos 55 km. No es la medición de un pluviómetro, y 20 departamentos chicos comparten la serie de un vecino.
- La ventana de octubre a marzo no sirve para el girasol (se siembra en invierno), el trigo (cultivo de invierno) ni el arroz (se riega).
- Yerba mate y té llegan solo hasta 2023/24, y a la yerba le faltan 2020/21 y 2021/22.
- Hay factores que no están en los datos: plagas, calor y precios. Por ejemplo, 2023/24 fue húmeda y aun así rindió mal. La chicharrita del maíz es una explicación posible, pero hay que verificarla con otra fuente antes de afirmarlo.
