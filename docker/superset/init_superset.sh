#!/bin/bash
# Inicializa Superset y después arranca el servidor web.
# Se ejecuta cada vez que arranca el contenedor; los pasos son seguros de repetir.
set -e

echo ">> Migrando la base interna de Superset..."
superset db upgrade

echo ">> Creando usuario admin (si ya existe, sigue)..."
superset fab create-admin --username admin --firstname Admin --lastname AE4 \
    --email admin@ae4.local --password admin || true

echo ">> Inicializando roles y permisos..."
superset init

# El dashboard se importa una sola vez (la marca queda en un volumen), así no se
# pisan los cambios que hagan desde la interfaz en arranques posteriores.
MARCA=/app/superset_home/.dashboard_importado
if [ ! -f "$MARCA" ]; then
    for zip in /app/dashboard/*.zip; do
        [ -f "$zip" ] || continue
        echo ">> Importando dashboard $zip ..."
        # Superset exporta la conexión con la contraseña tapada (XXXXXXXXXX) y no deja
        # importarla así. Se arma una copia temporal del zip con la contraseña del
        # usuario de solo lectura; el zip original queda intacto.
        python - "$zip" /tmp/dashboard_a_importar.zip <<'EOF'
import sys, zipfile
origen, destino = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(origen) as zin, zipfile.ZipFile(destino, "w") as zout:
    for nombre in zin.namelist():
        datos = zin.read(nombre)
        if "/databases/" in nombre:
            datos = datos.replace(b"XXXXXXXXXX", b"lector_pass")
        zout.writestr(nombre, datos)
EOF
        superset import-dashboards --path /tmp/dashboard_a_importar.zip --username admin
    done
    # Por si no había zip (o para asegurar los datos de conexión): fija la conexión
    # al DW con el usuario de solo lectura. Si no existía, la crea.
    echo ">> Configurando la conexión al Data Warehouse..."
    superset set-database-uri --database_name "DW Agro" \
        --uri "postgresql+psycopg2://superset_lector:lector_pass@postgres:5432/dw_agro"
    touch "$MARCA"
fi

echo ">> Superset listo en http://localhost:8088 (usuario admin / admin)"
exec /usr/bin/run-server.sh
