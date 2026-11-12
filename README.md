# AE4 · Integración de datos y analítica — Producción agrícola del NEA y lluvia

Trabajo Integrador AE4 de Gestión Avanzada de Bases de Datos (UCP).

**Recorrido del trabajo:** preguntas de negocio → 2 fuentes de datos abiertos → ETL en Python → Data Warehouse en PostgreSQL → dashboard en Apache Superset → hallazgos.

| Documento | Contenido |
|---|---|
| `docs/decisiones.md` | Decisiones de limpieza, cruce y modelado, con su justificación |
| `docs/diccionario_datos.md` | Tablas y vistas del DW |
| `docs/hallazgos.md` | Respuestas a las 4 preguntas y recomendación |
| `docs/informe/Informe_AE4_Agro_NEA.pdf` | Informe final (9 páginas). Se regenera con `python docs/informe/generar_informe.py` (requiere `pip install reportlab pillow`) |
| `docs/guion_exposicion.md` | Guion de la exposición de 15 minutos y preguntas probables |
| `docs/presentacion/Presentacion_AE4_Agro_NEA.pptx` | Diapositivas de la exposición (13 más 3 de respaldo), con el guion en las notas |

## Definición del negocio

**Contexto.**
El NEA (Misiones, Corrientes, Chaco y Formosa) produce el 100 % de la yerba mate y el té del país y la mitad del arroz. El Chaco suma, además, una agricultura extensa de soja, maíz, algodón y sorgo. Casi toda esa producción es de secano: depende de la lluvia, no de riego.
En las últimas campañas hubo sequías fuertes, y en 2024/25 se perdió un tercio de la superficie sembrada de secano.
Este trabajo cruza la producción de cada departamento con la lluvia que recibió para medir:
- cuánto depende el rendimiento de la lluvia;
- qué departamentos pierden más;
- en qué meses falta el agua;
- qué peso tiene el NEA en la producción del país.

**Supuestos.**
1. La campaña agrícola va de julio a junio, como la define la Secretaría de Agricultura.
2. Para los cultivos de verano, la lluvia que importa es la de octubre a marzo. Una campaña es *seca* si llovió menos del 80 % de lo normal del departamento, y *húmeda* si llovió más del 120 %.
3. La lluvia del departamento es la que da la NASA para su punto central (un modelo satelital, no un pluviómetro). Para no contar dos veces, se usan solo los cultivos "total" (ver D04).

**Alcance.**
- Campañas 2000/01 a 2024/25.
- Producción de todo el país, porque P4 la compara con el total nacional.
- Clima de los 76 departamentos del NEA.

**Limitaciones.**
- La producción es anual: no se sabe en qué mes se perdió el cultivo.
- La lluvia es modelada, en una grilla de unos 55 km.
- Plagas, calor y precios no están en los datos.
- Yerba mate y té llegan solo hasta 2023/24.
- El detalle está en `docs/decisiones.md`.

## Preguntas y KPIs

| | Pregunta |
|---|---|
| P1 | ¿Cuánto rinden la soja, el maíz, el algodón y el sorgo del NEA en campañas secas frente a las normales y las húmedas? |
| P2 | ¿Qué porcentaje de la superficie sembrada no se cosechó en cada campaña, y qué departamentos perdieron más? |
| P3 | ¿Qué campañas fueron más secas que lo normal en cada departamento, y en qué meses faltó la lluvia? |
| P4 | ¿Qué participación tiene el NEA en la producción nacional de algodón, arroz, yerba mate y té, y cómo cambió entre 2000/01 y 2024/25? |

| KPI | Fórmula | Unidad |
|---|---|---|
| ⭐ Rendimiento vs 5 campañas anteriores | (Σ t ÷ Σ ha cosechadas) ÷ (Σ t ÷ Σ ha cosechadas de las 5 campañas anteriores), mismo cultivo y departamento × 100 | % |
| Lluvia vs lo normal | Σ lluvia de octubre a marzo ÷ promedio de esa suma en 2000/01–2024/25 × 100 | % |
| Superficie perdida | (Σ ha sembradas − Σ ha cosechadas) ÷ Σ ha sembradas × 100 | % |

## Fuentes

1. **Estimaciones agrícolas.** Secretaría de Agricultura, Ganadería y Pesca, licencia CC BY 4.0. Superficie, producción y rendimiento por cultivo, campaña y departamento.
   https://datos.magyp.gob.ar/dataset/estimaciones-agricolas
2. **Clima diario NASA POWER**, uso libre. Lluvia diaria en el centro de cada uno de los 76 departamentos del NEA, del 01/07/2000 al 30/06/2025.
   https://power.larc.nasa.gov

Los archivos originales están en `data/raw/`, tal como se descargaron el 10/11/2026. No hace falta internet para reproducir el trabajo.

## Cómo reproducir

**Requisito:** Docker Desktop. Python 3.11 o superior es opcional, solo para correr el ETL fuera de Docker.

```powershell
docker compose up -d --build
```

- La primera vez tarda unos 3 minutos: PostgreSQL crea y carga el DW, y Superset importa el dashboard.
- Para ver el avance: `docker compose logs -f superset`. Está listo cuando aparece `Superset listo`.
- Después hay que abrir **http://localhost:8088** (usuario `admin`, contraseña `admin`), ir a **Dashboards** y abrir **"Producción agrícola del NEA y lluvia"**.

### ETL desde los CSV crudos (opcional: los CSV procesados ya vienen incluidos)

```powershell
python -m pip install -r requirements.txt
python etl/exploracion.py   # (opcional) muestra los problemas de los datos crudos
python etl/run_etl.py       # regenera data/processed/ (unos segundos)
```

Sin Python: `docker compose --profile etl run --rm etl`.

El DW se carga solo cuando se crea la base. Si se vuelve a correr el ETL, hay que recrearla:

```powershell
docker compose down -v
docker compose up -d --build
```

### Consultas y controles

```powershell
docker exec -it ae4_postgres psql -U dw_user -d dw_agro -f /sql/05_consultas_analiticas.sql   # respuestas P1-P4
docker exec -it ae4_postgres psql -U dw_user -d dw_agro -f /sql/06_validaciones_dw.sql        # integridad
```

Para conectarse con un cliente SQL:
- host `localhost`, puerto **5433**, base `dw_agro`;
- usuario `dw_user` y contraseña `dw_pass`;
- o el usuario de solo lectura `superset_lector` con contraseña `lector_pass`.

## Estructura

```
data/raw/                 fuentes originales (estimaciones + nasa_power/)
data/processed/           salida del ETL: dim_*.csv, fact_*.csv, rechazados.csv, validaciones/
etl/                      config, descarga, exploración, ingesta, limpieza, transformación, validaciones, run_etl
sql/                      01 DDL · 02 carga · 03 vistas · 04 permisos · 05 consultas · 06 validaciones
dashboard/                export del dashboard de Superset (.zip)
docker/                   configuración de PostgreSQL y Superset
docs/                     decisiones, diccionario, hallazgos
docker-compose.yml        PostgreSQL 16.4 + Superset 4.1.4 (+ ETL opcional)
```

## Problemas comunes

| Síntoma | Solución |
|---|---|
| `port is already allocated` | Cambiar el número de la izquierda en `ports:` de `docker-compose.yml` |
| El dashboard aparece vacío | `docker compose down -v` y después `docker compose up -d --build` |
