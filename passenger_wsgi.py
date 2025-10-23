# passenger_wsgi.py
import os, sys

# Ruta base del proyecto (la carpeta donde está este archivo)
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

# (Opcional) variables de entorno
#os.environ.setdefault("PYTHON_EGG_CACHE", os.path.join(BASE_DIR, "python-eggs"))
#os.environ.setdefault("FLASK_ENV", "production")

# Importa el objeto WSGI como "application"
from run import app as application