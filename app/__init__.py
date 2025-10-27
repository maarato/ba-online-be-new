import os
import time
import socket
import platform
import flask
from datetime import datetime, timezone
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

# Cargar variables desde .env si existe
load_dotenv()

SERVER_START = time.time()


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def build_server_info():
    return {
        "name": "ba-be-new",
        "framework": "flask",
        "flask_version": flask.__version__,
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "environment": os.environ.get("APP_ENV", "development"),
        "time_utc": iso_now(),
        "uptime_seconds": round(time.time() - SERVER_START, 2),
        "status": "ok",
    }


def create_app():
    app = Flask(__name__)

    # Configurar CORS: orígenes permitidos
    default_allowed = [
        "http://localhost",
        "http://localhost:3000",
        "https://alexsaurio.com",
        "https://www.alexsaurio.com",
        "https://topconsultants.io",
        "https://www.topconsultants.io",
    ]
    env_allowed = os.environ.get("ALLOWED_ORIGINS")
    allowed_origins = [o.strip() for o in env_allowed.split(",") if o.strip()] if env_allowed else default_allowed
    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
    )

    # Init DB
    from .services.chat_store import init_db
    init_db()

    # Blueprints
    from .routes.chat import chat_bp
    from .routes.brief import brief_bp
    from .routes.contacts import contact_bp
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(brief_bp, url_prefix="/brief")
    # contact_bp ya define url_prefix='/api/contact' en el blueprint.
    # Registramos sin prefijo adicional para que sea accesible en '/api/contact'.
    app.register_blueprint(contact_bp)

    @app.get("/")
    def index():
        """API raíz: información del servidor en JSON"""
        return jsonify(build_server_info())

    @app.get("/health")
    def health():
        """API health: estado simple del servidor"""
        return jsonify({
            "status": "ok",
            "uptime_seconds": round(time.time() - SERVER_START, 2),
        }), 200

    return app