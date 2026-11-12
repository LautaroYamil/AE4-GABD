-- =============================================================================
-- 04_permisos.sql - Usuario de solo lectura para Superset
-- Superset solo necesita consultar: así no puede modificar el DW por error.
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'superset_lector') THEN
        CREATE ROLE superset_lector LOGIN PASSWORD 'lector_pass';
    END IF;
END $$;

GRANT CONNECT ON DATABASE dw_agro TO superset_lector;
GRANT USAGE ON SCHEMA dw TO superset_lector;
GRANT SELECT ON ALL TABLES IN SCHEMA dw TO superset_lector;   -- incluye las vistas
