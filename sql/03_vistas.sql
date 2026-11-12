-- =============================================================================
-- 03_vistas.sql - Vistas analíticas que alimentan el dashboard
-- Acá se hace el cruce entre las dos fuentes: producción y lluvia se unen por
-- departamento y campaña.
-- =============================================================================

-- Lluvia de octubre a marzo de cada departamento y campaña, comparada con su normal.
-- Normal = promedio de las campañas 2000/2001 a 2024/2025 del mismo departamento.
CREATE VIEW dw.vw_lluvia_campania AS
WITH por_campania AS (
    SELECT c.id_departamento, t.campania, SUM(c.lluvia_mm) AS lluvia_oct_mar_mm
    FROM dw.fact_clima_diario c
    JOIN dw.dim_tiempo t ON t.id_fecha = c.id_fecha
    WHERE t.es_mes_lluvia_verano
    GROUP BY c.id_departamento, t.campania
),
con_normal AS (
    SELECT p.*, AVG(p.lluvia_oct_mar_mm) OVER (PARTITION BY p.id_departamento) AS lluvia_normal_mm
    FROM por_campania p
)
SELECT n.id_departamento, n.campania, d.provincia, d.nombre AS departamento,
       n.lluvia_oct_mar_mm, n.lluvia_normal_mm,
       CASE WHEN n.lluvia_oct_mar_mm < 0.8 * n.lluvia_normal_mm THEN 'Seca'
            WHEN n.lluvia_oct_mar_mm > 1.2 * n.lluvia_normal_mm THEN 'Húmeda'
            ELSE 'Normal' END AS tipo_campania
FROM con_normal n
JOIN dw.dim_departamento d ON d.id_departamento = n.id_departamento;

-- Producción por cultivo, departamento y campaña (desde 2000/2001), con:
--  * lo producido y cosechado en las 5 campañas anteriores (base del KPI de rendimiento),
--  * la lluvia y el tipo de campaña del departamento (solo NEA; el resto queda 'Sin dato').
CREATE VIEW dw.vw_produccion_lluvia AS
WITH con_base AS (
    SELECT f.id_departamento, f.id_cultivo, t.campania, t.anio AS anio_inicio,
           f.superficie_sembrada_ha, f.superficie_cosechada_ha, f.produccion_t,
           SUM(f.produccion_t)            OVER ventana AS produccion_5_anteriores_t,
           SUM(f.superficie_cosechada_ha) OVER ventana AS cosechada_5_anteriores_ha,
           COUNT(*)                       OVER ventana AS campanias_anteriores
    FROM dw.fact_produccion f
    JOIN dw.dim_tiempo t ON t.id_fecha = f.id_fecha
    WINDOW ventana AS (PARTITION BY f.id_departamento, f.id_cultivo
                       ORDER BY t.anio RANGE BETWEEN 5 PRECEDING AND 1 PRECEDING)
)
SELECT b.campania, b.anio_inicio, c.nombre AS cultivo, d.provincia, d.nombre AS departamento,
       d.codigo_indec, d.es_nea,
       b.superficie_sembrada_ha, b.superficie_cosechada_ha, b.produccion_t,
       -- Para comparar rendimientos se usan solo las filas que tienen base
       -- (al menos 3 de las 5 campañas anteriores con superficie cosechada)
       CASE WHEN b.campanias_anteriores >= 3 AND b.cosechada_5_anteriores_ha > 0
            THEN b.produccion_t END            AS produccion_con_base_t,
       CASE WHEN b.campanias_anteriores >= 3 AND b.cosechada_5_anteriores_ha > 0
            THEN b.superficie_cosechada_ha END AS cosechada_con_base_ha,
       CASE WHEN b.campanias_anteriores >= 3 AND b.cosechada_5_anteriores_ha > 0
            THEN b.produccion_5_anteriores_t END AS produccion_5_anteriores_t,
       CASE WHEN b.campanias_anteriores >= 3 AND b.cosechada_5_anteriores_ha > 0
            THEN b.cosechada_5_anteriores_ha END AS cosechada_5_anteriores_ha,
       l.lluvia_oct_mar_mm, l.lluvia_normal_mm,
       COALESCE(l.tipo_campania, 'Sin dato') AS tipo_campania
FROM con_base b
JOIN dw.dim_cultivo c      ON c.id_cultivo = b.id_cultivo
JOIN dw.dim_departamento d ON d.id_departamento = b.id_departamento
LEFT JOIN dw.vw_lluvia_campania l ON l.id_departamento = b.id_departamento AND l.campania = b.campania
WHERE b.campania >= '2000/2001';

-- Lluvia de cada departamento por mes y campaña, y la normal de ese mes en ese
-- departamento (promedio de las 25 campañas). Sirve para ver en qué meses faltó.
CREATE VIEW dw.vw_lluvia_mensual AS
WITH por_mes AS (
    SELECT c.id_departamento, t.campania, t.mes, t.nombre_mes, SUM(c.lluvia_mm) AS lluvia_mm
    FROM dw.fact_clima_diario c
    JOIN dw.dim_tiempo t ON t.id_fecha = c.id_fecha
    GROUP BY c.id_departamento, t.campania, t.mes, t.nombre_mes
)
SELECT m.campania, m.mes, m.nombre_mes,
       -- julio = 01 ... junio = 12, así el mes ordena igual que la campaña
       LPAD((((m.mes + 5) % 12) + 1)::text, 2, '0') || ' ' || m.nombre_mes AS mes_de_campania,
       d.provincia, d.nombre AS departamento,
       m.lluvia_mm,
       AVG(m.lluvia_mm) OVER (PARTITION BY m.id_departamento, m.mes) AS lluvia_normal_mm
FROM por_mes m
JOIN dw.dim_departamento d ON d.id_departamento = m.id_departamento;
