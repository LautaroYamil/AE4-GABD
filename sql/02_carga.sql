-- =============================================================================
-- 02_carga.sql - Carga de los CSV del ETL (data/processed, montado en /data/processed)
-- Primero las dimensiones y después los hechos, para que las FK se puedan validar.
-- =============================================================================
COPY dw.dim_tiempo (id_fecha, fecha, dia, nombre_dia, mes, nombre_mes, trimestre, anio, campania,
                    es_mes_lluvia_verano)
FROM '/data/processed/dim_tiempo.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

COPY dw.dim_departamento (id_departamento, codigo_indec, nombre, provincia_id, provincia, es_nea,
                          es_sin_definir, tiene_clima)
FROM '/data/processed/dim_departamento.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

COPY dw.dim_cultivo (id_cultivo, nombre, primera_campania, ultima_campania)
FROM '/data/processed/dim_cultivo.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

COPY dw.fact_produccion (id_fecha, id_departamento, id_cultivo, superficie_sembrada_ha,
                         superficie_cosechada_ha, produccion_t)
FROM '/data/processed/fact_produccion.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

COPY dw.fact_clima_diario (id_fecha, id_departamento, lluvia_mm)
FROM '/data/processed/fact_clima_diario.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

ANALYZE;

SELECT 'dim_tiempo' AS tabla, COUNT(*) AS filas FROM dw.dim_tiempo
UNION ALL SELECT 'dim_departamento', COUNT(*) FROM dw.dim_departamento
UNION ALL SELECT 'dim_cultivo', COUNT(*) FROM dw.dim_cultivo
UNION ALL SELECT 'fact_produccion', COUNT(*) FROM dw.fact_produccion
UNION ALL SELECT 'fact_clima_diario', COUNT(*) FROM dw.fact_clima_diario;
