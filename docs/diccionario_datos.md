# Diccionario de datos · esquema `dw` (base `dw_agro`)

## dim_tiempo

Un registro por día, del 01/07/1995 al 30/06/2025 (10.958 filas).

| Columna | Tipo | Descripción |
|---|---|---|
| id_fecha | INTEGER PK | Fecha en formato AAAAMMDD |
| fecha | DATE | Fecha |
| dia | SMALLINT | Día del mes |
| nombre_dia | VARCHAR | lunes … domingo |
| mes | SMALLINT | 1 a 12 |
| nombre_mes | VARCHAR | enero … diciembre |
| trimestre | SMALLINT | 1 a 4 |
| anio | SMALLINT | Año calendario |
| campania | CHAR(9) | Campaña agrícola de julio a junio, ej. `2022/2023` |
| es_mes_lluvia_verano | BOOLEAN | Verdadero de octubre a marzo (ventana de lluvia de los cultivos de verano) |

## dim_departamento

Departamentos que aparecen en las estimaciones (423 filas, 78 del NEA). Es la dimensión que conecta las dos fuentes. La justifican P2 (qué departamentos perdieron más), P3 (lluvia por departamento) y P4 (NEA contra el país).

| Columna | Tipo | Descripción |
|---|---|---|
| id_departamento | INTEGER PK | Clave subrogada |
| codigo_indec | CHAR(5) UNIQUE | Código INDEC: provincia (2 dígitos) + departamento (3 dígitos) |
| nombre | VARCHAR | Nombre del departamento o partido |
| provincia_id | CHAR(2) | Código INDEC de la provincia |
| provincia | VARCHAR | Nombre de la provincia |
| es_nea | BOOLEAN | Misiones, Corrientes, Chaco o Formosa |
| es_sin_definir | BOOLEAN | Código `XX000`: solo se conoce la provincia (D12) |
| tiene_clima | BOOLEAN | Tiene datos de la NASA |

## dim_cultivo

33 cultivos, sin subcultivos y con la cebada unificada (D04, D05). La justifican P1 (rendimiento por cultivo) y P4 (participación por cultivo).

| Columna | Tipo | Descripción |
|---|---|---|
| id_cultivo | INTEGER PK | Clave subrogada |
| nombre | VARCHAR UNIQUE | Cultivo, ej. `soja total`, `maíz`, `yerba mate` |
| primera_campania | CHAR(9) | Primera campaña con datos en el período |
| ultima_campania | CHAR(9) | Última campaña con datos |

## fact_produccion

Grano: cultivo × departamento × campaña (57.472 filas). Fuente: estimaciones agrícolas.

| Columna | Tipo | Descripción |
|---|---|---|
| id_fecha | INTEGER FK → dim_tiempo | 1 de julio en que empieza la campaña (D13) |
| id_departamento | INTEGER FK → dim_departamento | |
| id_cultivo | INTEGER FK → dim_cultivo | |
| superficie_sembrada_ha | INTEGER | Hectáreas sembradas (aditiva) |
| superficie_cosechada_ha | INTEGER | Hectáreas cosechadas (aditiva). Nunca mayor que la sembrada |
| produccion_t | INTEGER | Toneladas producidas (aditiva) |

PK: (id_fecha, id_departamento, id_cultivo). El rendimiento no se guarda, porque es un cociente: se calcula como Σ produccion_t × 1000 ÷ Σ superficie_cosechada_ha.

## fact_clima_diario

Grano: departamento × día (675.694 filas, 74 departamentos del NEA). Fuente: NASA POWER.

| Columna | Tipo | Descripción |
|---|---|---|
| id_fecha | INTEGER FK → dim_tiempo | Día |
| id_departamento | INTEGER FK → dim_departamento | |
| lluvia_mm | NUMERIC(6,2) | Lluvia del día en mm. Se puede sumar en el tiempo. Nulo = sin dato |

PK: (id_fecha, id_departamento).

## Vistas (alimentan el dashboard)

| Vista | Grano | Qué agrega |
|---|---|---|
| vw_lluvia_campania | departamento × campaña | `lluvia_oct_mar_mm`, `lluvia_normal_mm` (promedio de las 25 campañas), `tipo_campania` (Seca, Normal o Húmeda) |
| vw_produccion_lluvia | cultivo × departamento × campaña (desde 2000/01) | Medidas de producción, más la producción y la superficie cosechada de las 5 campañas anteriores (`*_5_anteriores`, `*_con_base`), más la lluvia y el tipo de campaña. Cruza las dos fuentes |
| vw_lluvia_mensual | departamento × mes × campaña | `lluvia_mm` del mes y `lluvia_normal_mm` de ese mes en ese departamento |

## Archivos auxiliares del ETL (no son tablas del DW)

| Archivo | Contenido |
|---|---|
| `data/processed/rechazados.csv` | Filas rechazadas, con la columna `motivo` |
| `data/processed/validaciones/log_etl.txt` | Bitácora completa del ETL |
| `data/processed/validaciones/validaciones.csv` | Métricas de cada paso (etapa, indicador, valor) |
| `data/processed/validaciones/clima_sin_departamento.csv` | Códigos con clima que no cruzaron |
