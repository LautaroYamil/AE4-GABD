-- =============================================================================
-- 06_validaciones_dw.sql - Controles de integridad del DW después de la carga
--   docker exec -it ae4_postgres psql -U dw_user -d dw_agro -f /sql/06_validaciones_dw.sql
-- Cada control dice qué resultado se espera.
-- =============================================================================

\echo '== 1. Filas por tabla (deben coincidir con los CSV de data/processed)'
SELECT 'dim_tiempo' AS tabla, COUNT(*) AS filas FROM dw.dim_tiempo
UNION ALL SELECT 'dim_departamento', COUNT(*) FROM dw.dim_departamento
UNION ALL SELECT 'dim_cultivo', COUNT(*) FROM dw.dim_cultivo
UNION ALL SELECT 'fact_produccion', COUNT(*) FROM dw.fact_produccion
UNION ALL SELECT 'fact_clima_diario', COUNT(*) FROM dw.fact_clima_diario;

\echo '== 2. Claves foráneas huérfanas (esperado: 0 en todas)'
SELECT 'produccion sin tiempo' AS control, COUNT(*) FROM dw.fact_produccion f
    LEFT JOIN dw.dim_tiempo t ON t.id_fecha = f.id_fecha WHERE t.id_fecha IS NULL
UNION ALL SELECT 'produccion sin departamento', COUNT(*) FROM dw.fact_produccion f
    LEFT JOIN dw.dim_departamento d ON d.id_departamento = f.id_departamento WHERE d.id_departamento IS NULL
UNION ALL SELECT 'produccion sin cultivo', COUNT(*) FROM dw.fact_produccion f
    LEFT JOIN dw.dim_cultivo c ON c.id_cultivo = f.id_cultivo WHERE c.id_cultivo IS NULL
UNION ALL SELECT 'clima sin departamento', COUNT(*) FROM dw.fact_clima_diario f
    LEFT JOIN dw.dim_departamento d ON d.id_departamento = f.id_departamento WHERE d.id_departamento IS NULL;

\echo '== 3. La producción siempre cae el 1 de julio (inicio de campaña) (esperado: 0)'
SELECT COUNT(*) AS filas_fuera_del_1_de_julio
FROM dw.fact_produccion f JOIN dw.dim_tiempo t ON t.id_fecha = f.id_fecha
WHERE NOT (t.dia = 1 AND t.mes = 7);

\echo '== 4. Clima completo: cada departamento con clima tiene un dato por día (esperado: 9131 días en todos)'
SELECT MIN(dias) AS minimo, MAX(dias) AS maximo, COUNT(*) AS departamentos
FROM (SELECT id_departamento, COUNT(*) AS dias FROM dw.fact_clima_diario GROUP BY id_departamento) x;

\echo '== 5. La vista de producción no pierde ni duplica filas (esperado: las dos cifras iguales)'
SELECT (SELECT COUNT(*) FROM dw.fact_produccion f JOIN dw.dim_tiempo t ON t.id_fecha = f.id_fecha
        WHERE t.campania >= '2000/2001') AS filas_fact_desde_2000,
       (SELECT COUNT(*) FROM dw.vw_produccion_lluvia) AS filas_vista;

\echo '== 6. Totales de control (comparar con la bitácora del ETL)'
SELECT SUM(produccion_t) AS produccion_total_t, SUM(superficie_sembrada_ha) AS sembrada_total_ha
FROM dw.fact_produccion;
SELECT ROUND(SUM(lluvia_mm), 0) AS lluvia_total_mm, COUNT(*) FILTER (WHERE lluvia_mm IS NULL) AS dias_sin_dato
FROM dw.fact_clima_diario;
