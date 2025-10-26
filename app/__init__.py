import os
import time
import socket
import platform
import flask
from datetime import datetime, timezone
from flask import Flask, jsonify
from dotenv import load_dotenv

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

    # Init DB
    from .services.chat_store import init_db
    init_db()

    # Blueprints
    from .routes.chat import chat_bp
    from .routes.brief import brief_bp
    from .routes.contacts import contacts_bp
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(brief_bp, url_prefix="/brief")
    app.register_blueprint(contacts_bp)

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