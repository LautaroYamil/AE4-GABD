-- =============================================================================
-- 01_ddl.sql - Estructura del Data Warehouse (esquema dw)
-- Modelo estrella con dos tablas de hechos que comparten dimensiones:
--   fact_produccion   (cultivo x departamento x campaña)  <- estimaciones agrícolas
--   fact_clima_diario (departamento x día)                <- NASA POWER
-- =============================================================================
DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

-- Un registro por día, del 01/07/1995 al 30/06/2025
CREATE TABLE dw.dim_tiempo (
    id_fecha              INTEGER     PRIMARY KEY,           -- AAAAMMDD
    fecha                 DATE        NOT NULL UNIQUE,
    dia                   SMALLINT    NOT NULL CHECK (dia BETWEEN 1 AND 31),
    nombre_dia            VARCHAR(10) NOT NULL,
    mes                   SMALLINT    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nombre_mes            VARCHAR(10) NOT NULL,
    trimestre             SMALLINT    NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    anio                  SMALLINT    NOT NULL,
    campania              CHAR(9)     NOT NULL,              -- julio a junio, ej. 2022/2023
    es_mes_lluvia_verano  BOOLEAN     NOT NULL               -- octubre a marzo
);

CREATE TABLE dw.dim_departamento (
    id_departamento  INTEGER     PRIMARY KEY,                -- clave subrogada
    codigo_indec     CHAR(5)     NOT NULL UNIQUE,            -- código que usan las dos fuentes
    nombre           VARCHAR(80) NOT NULL,
    provincia_id     CHAR(2)     NOT NULL,
    provincia        VARCHAR(40) NOT NULL,
    es_nea           BOOLEAN     NOT NULL,
    es_sin_definir   BOOLEAN     NOT NULL,                   -- código XX000: solo se sabe la provincia
    tiene_clima      BOOLEAN     NOT NULL
);

CREATE TABLE dw.dim_cultivo (
    id_cultivo        INTEGER     PRIMARY KEY,
    nombre            VARCHAR(40) NOT NULL UNIQUE,
    primera_campania  CHAR(9)     NOT NULL,
    ultima_campania   CHAR(9)     NOT NULL,
    CHECK (primera_campania <= ultima_campania)
);

-- Grano: un cultivo, en un departamento, en una campaña.
-- id_fecha = 1 de julio en que empieza la campaña (ver D13).
-- El rendimiento NO se guarda: es un cociente y no se puede sumar.
CREATE TABLE dw.fact_produccion (
    id_fecha                 INTEGER NOT NULL REFERENCES dw.dim_tiempo (id_fecha),
    id_departamento          INTEGER NOT NULL REFERENCES dw.dim_departamento (id_departamento),
    id_cultivo               INTEGER NOT NULL REFERENCES dw.dim_cultivo (id_cultivo),
    superficie_sembrada_ha   INTEGER NOT NULL CHECK (superficie_sembrada_ha >= 0),
    superficie_cosechada_ha  INTEGER NOT NULL CHECK (superficie_cosechada_ha >= 0),
    produccion_t             INTEGER NOT NULL CHECK (produccion_t >= 0),
    PRIMARY KEY (id_fecha, id_departamento, id_cultivo),
    CHECK (superficie_cosechada_ha <= superficie_sembrada_ha)
);

-- Grano: un departamento en un día.
CREATE TABLE dw.fact_clima_diario (
    id_fecha         INTEGER NOT NULL REFERENCES dw.dim_tiempo (id_fecha),
    id_departamento  INTEGER NOT NULL REFERENCES dw.dim_departamento (id_departamento),
    lluvia_mm        NUMERIC(6, 2) CHECK (lluvia_mm >= 0),   -- nulo = la NASA no tiene el dato
    PRIMARY KEY (id_fecha, id_departamento)
);

-- Índices para los cruces por departamento y cultivo (id_fecha ya está primero en la PK)
CREATE INDEX ix_produccion_departamento ON dw.fact_produccion (id_departamento);
CREATE INDEX ix_produccion_cultivo      ON dw.fact_produccion (id_cultivo);
CREATE INDEX ix_clima_departamento      ON dw.fact_clima_diario (id_departamento);
CREATE INDEX ix_tiempo_campania         ON dw.dim_tiempo (campania);
