import json
import os
from typing import Dict, List, Optional

from app.services.llm_client import LLMClient
from app.services.chat_store import get_apolo_state, set_apolo_state

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "llm", "prompts")

DEFAULT_SLOTS = [
    "idea_negocio",
    "clientes_objetivos",
    "region_operacion",
    "market_scope",
    "modelo_ingresos",
    "tipo_producto",
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


def _merge_updates(state: Dict[str, Optional[str]], updates: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    merged = {**state}
    for k, v in (updates or {}).items():
        if k in DEFAULT_SLOTS and v not in (None, ""):
            merged[k] = v
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


def _get_next(provider: str, history: List[Dict[str, str]], state: Dict[str, Optional[str]]) -> str:
    system = _load_prompt_text("apolo.next.json")
    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": f"Estado actual (JSON): {json.dumps(state, ensure_ascii=False)}"})

    client = LLMClient(provider=provider)
    return client.chat(messages=messages, temperature=0.2)


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


def run_apolo(session_id: str, history: List[Dict[str, str]], provider: str) -> Dict[str, str]:
    """Orquestador MULTI-CALL.

    1) extract → updates → merge → persistir state
    2) Si faltan slots → next → confirmación breve + pregunta
       Si todos completos → summary → resumen final

    Retorna dict con {"message": texto_final, "step": "asking"|"summary", "summary": texto_o_null}
    """
    state = get_apolo_state(session_id) or _default_state()

    # 1) extract
    updates = _extract_updates(provider, history, state)
    state = _merge_updates(state, updates)
    set_apolo_state(session_id, state)

    missing = _missing_slots(state)

    if missing:
        # 2a) next → respuesta directa
        message = _get_next(provider, history, state)
        message = _guard_output(provider, message, step="asking")
        return {"message": message, "step": "asking", "summary": None}
    else:
        # 2b) final validator → resumen extendido y cierre
        final_text = _get_final(provider, history, state)
        final_text = _guard_output(provider, final_text, step="finished")
        return {"message": final_text, "step": "finished", "summary": final_text}