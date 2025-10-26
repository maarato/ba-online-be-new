import json
import os
from typing import Dict, List, Optional

from app.services.llm_client import LLMClient
from app.services.chat_store import get_apolo_state, set_apolo_state

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "llm", "prompts")

DEFAULT_SLOTS = [
    "idea_negocio",
    "usuarios_objetivos",
    "region_operacion",
    "market_scope",
    "modelo_ingresos",
    "tipo_producto",
    "integraciones",
    "timeline",
    "capital_inicial",
]


def _load_prompt_text(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Si el archivo es JSON con campo 'system'/'instructions' o 'content' array
            if isinstance(data, dict):
                if "system" in data:
                    return data["system"]
                if "instructions" in data:
                    return data["instructions"]
                if "content" in data and isinstance(data["content"], list):
                    return "\n".join([str(x) for x in data["content"]])
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            f.seek(0)
            return f.read()


def _default_state() -> Dict[str, Optional[str]]:
    return {k: None for k in DEFAULT_SLOTS}


def _normalize_state_keys(state: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    s = {**state}
    # Migrar valor antiguo 'clientes_objetivos' a 'usuarios_objetivos'
    if "clientes_objetivos" in s:
        if s.get("usuarios_objetivos") in (None, ""):
            s["usuarios_objetivos"] = s.get("clientes_objetivos")
        s.pop("clientes_objetivos", None)
    # Asegurar presencia de claves canónicas
    for k in DEFAULT_SLOTS:
        s.setdefault(k, None)
    return s


def _merge_updates(state: Dict[str, Optional[str]], updates: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    merged = {**state}
    for k, v in (updates or {}).items():
        # Normalizar clave antigua a nueva canónica
        canonical_k = "usuarios_objetivos" if k == "clientes_objetivos" else k
        if canonical_k in DEFAULT_SLOTS and v not in (None, ""):
            merged[canonical_k] = v
    return merged


def _extract_updates(provider: str, history: List[Dict[str, str]], state: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    system = _load_prompt_text("apolo.extract.json")
    # Añadimos el estado actual como parte del contexto
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": f"Estado actual (JSON): {json.dumps(state, ensure_ascii=False)}"})

    client = LLMClient(provider=provider)
    text = client.chat(messages=messages, temperature=0.2)

    # Intentar parsear un objeto JSON con clave "updates"
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            obj = json.loads(text[start : end + 1])
            updates = obj.get("updates") if isinstance(obj, dict) else None
            return updates or {}
    except Exception:
        pass
    return {}


def _missing_slots(state: Dict[str, Optional[str]]) -> List[str]:
    return [k for k in DEFAULT_SLOTS if state.get(k) in (None, "")]


# Plantillas deterministas de preguntas por slot
QUESTION_TEMPLATES: Dict[str, str] = {
    "idea_negocio": "Para empezar, ¿puedes describir brevemente tu idea de negocio? (1–3 líneas)",
    "usuarios_objetivos": "¿Quiénes serán los usuarios del sistema a desarrollar? Indica roles/perfiles y si son clientes internos o externos. Puedes dar un ejemplo.",
    "region_operacion": "¿En qué región/país(es) operará inicialmente el sistema?",
    "market_scope": "¿Prevés ampliar el alcance a otras regiones/segmentos a futuro? Si es así, ¿cuáles?",
    "modelo_ingresos": "¿Cuál será el modelo de ingresos principal? (p.ej., venta directa, suscripción, publicidad, transacciones, etc.)",
    "tipo_producto": "Para aclarar el tipo de producto: ¿el sistema será el producto final, facilitará el acceso al producto (e-commerce/marketplace) o apoyará operaciones internas (ERP/CRM/automatización)?",
    "integraciones": "¿El sistema debe integrarse con herramientas/sistemas/servicios existentes (ERP, CRM, pasarelas de pago, proveedores externos, APIs)? Menciona ejemplos si existen.",
    "timeline": "¿Cuál es el timeline estimado para el desarrollo y lanzamiento (hitos y fechas tentativas)?",
    "capital_inicial": "¿Con qué capital inicial cuentas para este proyecto? (rango o monto)"
}

def _get_next(provider: str, history: List[Dict[str, str]], state: Dict[str, Optional[str]]) -> str:
    system = _load_prompt_text("apolo.next.json")
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": f"Estado actual (JSON): {json.dumps(state, ensure_ascii=False)}"})

    # Ayuda determinista: calcular el próximo slot vacío en orden canónico
    missing = _missing_slots(state)
    next_slot = missing[0] if missing else None
    if next_slot:
        messages.append({"role": "user", "content": f"Próximo slot vacío canónico: {next_slot}"})

    client = LLMClient(provider=provider)
    raw = client.chat(messages=messages, temperature=0.2)

    # Intentar parsear salida JSON del prompt next
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            obj = json.loads(raw[start : end + 1])
            pregunta_llm = obj.get("pregunta")
            confirm = obj.get("confirmacion_breve")
            slot_actual = obj.get("slot_actual")
            parts: List[str] = []
            if confirm and isinstance(confirm, str) and confirm.strip():
                parts.append(confirm.strip())
            # Si tenemos next_slot, imponemos la pregunta del slot canónico
            if next_slot:
                pregunta_final = QUESTION_TEMPLATES.get(next_slot)
                # Usamos la pregunta del LLM SOLO si coincide el slot seleccionado
                if isinstance(slot_actual, str) and slot_actual == next_slot and isinstance(pregunta_llm, str) and pregunta_llm.strip():
                    pregunta_final = pregunta_llm.strip()
                if pregunta_final:
                    parts.append(pregunta_final)
            else:
                # Sin next_slot (no debería ocurrir aquí), usa lo que venga del LLM
                if pregunta_llm and isinstance(pregunta_llm, str) and pregunta_llm.strip():
                    parts.append(pregunta_llm.strip())
            if parts:
                return "\n\n".join(parts)
    except Exception:
        pass
    # Fallback determinista: si falla el parseo, usa plantilla del próximo slot
    if next_slot:
        return QUESTION_TEMPLATES.get(next_slot, raw)
    return raw


def _get_final(provider: str, history: List[Dict[str, str]], state: Dict[str, Optional[str]]) -> str:
    system = _load_prompt_text("apolo.final.json")
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": f"Estado final (JSON): {json.dumps(state, ensure_ascii=False)}"})

    client = LLMClient(provider=provider)
    return client.chat(messages=messages, temperature=0.2)


def _get_summary(provider: str, history: List[Dict[str, str]], state: Dict[str, Optional[str]]) -> str:
    system = _load_prompt_text("apolo.summary.json")
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": f"Estado final (JSON): {json.dumps(state, ensure_ascii=False)}"})

    client = LLMClient(provider=provider)
    return client.chat(messages=messages, temperature=0.2)


def _guard_output(provider: str, text: str, step: str) -> str:
    guard = _load_prompt_text("apolo.output.guard.json")
    messages = [
        {"role": "system", "content": guard},
        {"role": "user", "content": f"Paso: {step}\n\nMensaje original:\n{text}"},
    ]
    client = LLMClient(provider=provider)
    return client.chat(messages=messages, temperature=0.0)


def _first_intro_message() -> str:
    return (
        "Hola, soy Apolo, un Business Analyst online. Estoy aquí para ayudarte a estructurar y dar forma a tu idea de proyecto, "
        "recopilando información clave en 9 etapas. Te haré preguntas breves y puntuales para avanzar de manera ordenada."
    )


def run_apolo(session_id: str, history: List[Dict[str, str]], provider: str) -> Dict[str, str]:
    """Orquestador MULTI-CALL.

    1) extract → updates → merge → persistir state
    2) Si faltan slots → next → confirmación breve + pregunta
       Si todos completos → final → resumen extendido

    Retorna dict con {"message": texto_final, "step": "asking"|"done", "summary": texto_o_null}
    """
    # Cargar estado y normalizar claves antiguas
    state = get_apolo_state(session_id) or _default_state()
    state = _normalize_state_keys(state)

    # 1) extract
    updates = _extract_updates(provider, history, state)
    state = _merge_updates(state, updates)
    set_apolo_state(session_id, state)

    missing = _missing_slots(state)
    is_first_response = not any(m.get("role") == "assistant" for m in history)

    if missing:
        # 2a) next → respuesta directa
        message = _get_next(provider, history, state)
        if is_first_response:
            intro = _first_intro_message()
            message = intro + "\n\n" + message
        message = _guard_output(provider, message, step="asking")
        return {"message": message, "step": "asking", "summary": None}
    else:
        # 2b) final validator → resumen extendido y cierre
        final_text = _get_final(provider, history, state)
        final_text = _guard_output(provider, final_text, step="done")
        return {"message": final_text, "step": "done", "summary": final_text}
