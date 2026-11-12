-- =============================================================================
-- 05_consultas_analiticas.sql - Respuestas a las preguntas de negocio
--   docker exec -it ae4_postgres psql -U dw_user -d dw_agro -f /sql/05_consultas_analiticas.sql
-- Rendimiento = Σ toneladas × 1000 / Σ hectáreas cosechadas (cociente de sumas, nunca promedio de rendimientos)
-- =============================================================================

\echo '== P1. Rendimiento del NEA según el tipo de campaña (100 = promedio de las 5 campañas anteriores)'
SELECT cultivo, tipo_campania,
       ROUND(100.0 * (SUM(produccion_con_base_t)::numeric / NULLIF(SUM(cosechada_con_base_ha), 0))
                   / (SUM(produccion_5_anteriores_t)::numeric / NULLIF(SUM(cosechada_5_anteriores_ha), 0)), 1)
           AS rendimiento_vs_5_anteriores_pct,
       COUNT(*) AS departamentos_campania
FROM dw.vw_produccion_lluvia
WHERE es_nea
  AND cultivo IN ('soja total', 'maíz', 'algodón', 'sorgo', 'arroz')
  AND tipo_campania <> 'Sin dato'
  AND produccion_con_base_t IS NOT NULL
GROUP BY cultivo, tipo_campania
ORDER BY cultivo, tipo_campania;

\echo '== P1. Soja del NEA campaña por campaña: rendimiento vs base y lluvia vs normal'
SELECT p.campania,
       ROUND(100.0 * (SUM(p.produccion_con_base_t)::numeric / NULLIF(SUM(p.cosechada_con_base_ha), 0))
                   / (SUM(p.produccion_5_anteriores_t)::numeric / NULLIF(SUM(p.cosechada_5_anteriores_ha), 0)), 1)
           AS rendimiento_vs_base_pct,
       l.lluvia_vs_normal_pct
FROM dw.vw_produccion_lluvia p
JOIN (SELECT campania, ROUND(100.0 * SUM(lluvia_oct_mar_mm) / SUM(lluvia_normal_mm), 1) AS lluvia_vs_normal_pct
      FROM dw.vw_lluvia_campania GROUP BY campania) l ON l.campania = p.campania
WHERE p.es_nea AND p.cultivo = 'soja total'
GROUP BY p.campania, l.lluvia_vs_normal_pct
ORDER BY p.campania;

\echo '== P2. Superficie perdida (sembrada y no cosechada) del NEA por campaña, cultivos de secano'
SELECT campania,
       SUM(superficie_sembrada_ha) AS sembrada_ha,
       SUM(superficie_sembrada_ha - superficie_cosechada_ha) AS perdida_ha,
       ROUND(100.0 * SUM(superficie_sembrada_ha - superficie_cosechada_ha) / SUM(superficie_sembrada_ha), 1)
           AS perdida_pct
FROM dw.vw_produccion_lluvia
WHERE es_nea AND cultivo IN ('soja total', 'maíz', 'algodón', 'sorgo', 'girasol')
GROUP BY campania
ORDER BY campania;

\echo '== P2. Los 10 departamentos del NEA con más superficie perdida en campañas secas'
SELECT provincia, departamento,
       SUM(superficie_sembrada_ha - superficie_cosechada_ha) AS perdida_ha,
       ROUND(100.0 * SUM(superficie_sembrada_ha - superficie_cosechada_ha) / SUM(superficie_sembrada_ha), 1)
           AS perdida_pct
FROM dw.vw_produccion_lluvia
WHERE es_nea AND tipo_campania = 'Seca'
  AND cultivo IN ('soja total', 'maíz', 'algodón', 'sorgo', 'girasol')
GROUP BY provincia, departamento
ORDER BY perdida_ha DESC
LIMIT 10;

\echo '== P3. Campañas secas (< 80 % de la lluvia normal de octubre a marzo) por provincia'
SELECT campania, provincia,
       COUNT(*) FILTER (WHERE tipo_campania = 'Seca') AS departamentos_secos,
       COUNT(*) AS departamentos,
       ROUND(100.0 * SUM(lluvia_oct_mar_mm) / SUM(lluvia_normal_mm), 1) AS lluvia_vs_normal_pct
FROM dw.vw_lluvia_campania
GROUP BY campania, provincia
HAVING COUNT(*) FILTER (WHERE tipo_campania = 'Seca') > 0
ORDER BY campania, provincia;

\echo '== P3. Campaña 2022/2023: lluvia de cada mes vs la normal de ese mes (promedio de los departamentos del NEA)'
SELECT mes_de_campania,
       ROUND(AVG(lluvia_mm), 0) AS lluvia_mm,
       ROUND(AVG(lluvia_normal_mm), 0) AS normal_mm,
       ROUND(100.0 * SUM(lluvia_mm) / SUM(lluvia_normal_mm), 0) AS pct_de_lo_normal
FROM dw.vw_lluvia_mensual
WHERE campania = '2022/2023'
GROUP BY mes_de_campania
ORDER BY mes_de_campania;

\echo '== P4. Participación del NEA en la producción nacional (promedio de 5 campañas al inicio y al final)'
SELECT cultivo,
       ROUND(100.0 * SUM(produccion_t) FILTER (WHERE es_nea AND campania <= '2004/2005')
                   / NULLIF(SUM(produccion_t) FILTER (WHERE campania <= '2004/2005'), 0), 1) AS nea_2000_2005_pct,
       ROUND(100.0 * SUM(produccion_t) FILTER (WHERE es_nea AND campania >= '2020/2021')
                   / NULLIF(SUM(produccion_t) FILTER (WHERE campania >= '2020/2021'), 0), 1) AS nea_2020_2025_pct
FROM dw.vw_produccion_lluvia
WHERE cultivo IN ('algodón', 'arroz', 'yerba mate', 'té', 'soja total', 'maíz', 'girasol', 'sorgo')
GROUP BY cultivo
ORDER BY nea_2020_2025_pct DESC;
