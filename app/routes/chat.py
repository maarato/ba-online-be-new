import os
import json
from flask import Blueprint, jsonify, request
from app.services.llm_client import LLMClient
from app.services.chat_store import ensure_session, add_message, get_messages, reset_session
from app.services.apolo_orchestrator import run_apolo

chat_bp = Blueprint("chat_bp", __name__)


@chat_bp.get("/")
def chat_index():
    return jsonify({
        "route": "chat",
        "status": "ready",
        "message": "Base de APIs de chat",
    })


@chat_bp.post("/stream")
def chat_stream():
    """POST /chat/stream
    Body JSON:
      - sessionId: string (camelCase)
      - message: string (acepta también 'messeage' por compatibilidad)
    Usa historial en SQLite, llama Groq y retorna estructura requerida.
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("sessionId") or data.get("session_id")
    message = data.get("message") or data.get("messeage")

    if not session_id or not message:
        return jsonify({
            "error": "invalid_request",
            "detail": "sessionId y message son requeridos",
        }), 400

    # Memoria: asegura sesión y agrega mensaje del usuario
    ensure_session(session_id)
    add_message(session_id, "user", message)

    # Construir historial para LLM
    max_ctx = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))
    history = get_messages(session_id, limit=max_ctx)

    system_prompt = os.getenv("SYSTEM_PROMPT", "Eres un asistente útil y conciso.")
    messages = [{"role": "system", "content": system_prompt}] + history

    try:
        provider = os.getenv("LLM_PROVIDER", "groq").lower()

        # Orquestador Apolo - respuesta directa
        result = run_apolo(session_id=session_id, history=messages[1:], provider=provider)
        
        # Guardar respuesta completa del asistente
        message = result.get("message", "")
        add_message(session_id, "assistant", message)
        
        # Respuesta JSON directa
        return jsonify({
            "message": message,
            "summary": result.get("summary"),
            "step": result.get("step", "asking")
        })
    except Exception as e:
        return jsonify({
            "error": "llm_call_failed",
            "detail": str(e),
        }), 500


@chat_bp.post("/reset")
def chat_reset():
    """POST /chat/reset
    Body JSON:
      - sessionId: string (camelCase)
    Elimina el historial de conversación de esa sesión y la fila de sesión.
    Retorna success y un message informativo.
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("sessionId") or data.get("session_id")

    if not session_id:
        return jsonify({
            "success": False,
            "message": "sessionId es requerido",
        }), 400

    info = reset_session(session_id)
    if info["had_conversation"]:
        return jsonify({
            "success": True,
            "message": f"Sesión {session_id} reiniciada; {info['messages_deleted']} mensajes borrados.",
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": f"No había conversación para la sesión {session_id}. Nada que borrar.",
        }), 200