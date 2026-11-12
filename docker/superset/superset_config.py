# Configuración de Superset para el TP (uso local, no productivo).
import os

# Clave para firmar sesiones. En un entorno real debería ser secreta.
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "ae4-agro-nea-clave-solo-para-uso-local")

# Metadatos de Superset (usuarios, gráficos, dashboards) en el mismo PostgreSQL,
# en una base separada del Data Warehouse.
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://dw_user:dw_pass@postgres:5432/superset_meta"

# Interfaz en español y números con formato argentino (1.234.567,8)
BABEL_DEFAULT_LOCALE = "es"
LANGUAGES = {
    "es": {"flag": "es", "name": "Español"},
    "en": {"flag": "us", "name": "English"},
}
D3_FORMAT = {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$", ""]}

# Uso local: sin políticas de seguridad de contenido que molesten en localhost
TALISMAN_ENABLED = False
