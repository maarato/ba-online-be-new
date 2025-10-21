import os
from typing import List, Dict, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

try:
    from groq import Groq
except Exception:  # pragma: no cover
    Groq = None


class LLMClient:
    """Cliente unificado para LLMs (OpenAI y Groq).

    Uso:
        client = LLMClient(provider="openai")
        text = client.chat([
            {"role": "system", "content": "Eres útil y conciso."},
            {"role": "user", "content": "Dime un haiku sobre el mar."}
        ])
    """

    def __init__(self, provider: str, model: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider.lower().strip()
        if self.provider not in {"openai", "groq"}:
            raise ValueError(f"Proveedor no soportado: {provider}")

        if self.provider == "openai":
            if OpenAI is None:
                raise RuntimeError("Paquete 'openai' no disponible. Añádelo a requirements.")
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Falta OPENAI_API_KEY en entorno/.env")
            self.client = OpenAI(api_key=api_key)
            self.default_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        elif self.provider == "groq":
            if Groq is None:
                raise RuntimeError("Paquete 'groq' no disponible. Añádelo a requirements.")
            api_key = api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("Falta GROQ_API_KEY en entorno/.env")
            self.client = Groq(api_key=api_key)
            self.default_model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Realiza una llamada de chat y retorna el texto de la primera elección."""
        mdl = model or self.default_model
        resp = self.client.chat.completions.create(
            model=mdl,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content


def call_llm(
    provider: str,
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> Dict[str, str]:
    """Función de conveniencia para llamadas rápidas a LLM por proveedor.

    Retorna dict con provider, model y text.
    """
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    client = LLMClient(provider=provider, model=model)
    text = client.chat(messages=messages, temperature=temperature, max_tokens=max_tokens)
    return {"provider": client.provider, "model": client.default_model if model is None else model, "text": text}