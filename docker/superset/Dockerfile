# Imagen oficial de Superset + driver de PostgreSQL (la imagen oficial no lo trae).
FROM apache/superset:4.1.4

USER root
RUN pip install --no-cache-dir psycopg2-binary==2.9.10
USER superset
