from flask import Blueprint, jsonify

brief_bp = Blueprint("brief_bp", __name__)


@brief_bp.get("/")
def brief_index():
    return jsonify({
        "route": "brief",
        "status": "ready",
        "message": "Base de APIs de brief",
    })