# BA BE New - Flask API

Proyecto mínimo en Flask con:
- GET `/` (raíz): retorna información del servidor en JSON.
- GET `/health`: retorna estado simple del servidor.
- Prefijos de rutas: `/chat/` y `/brief/` con endpoints base de ejemplo.

## Requisitos
- Python 3.8+ (recomendado 3.10+)

## Instalación y ejecución (Windows)
```powershell
# (Opcional) Crear entorno virtual
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Instalar dependencias
python -m pip install -r requirements.txt

# Ejecutar servidor
python run.py
```

Servidor por defecto en `http://localhost:5000/`.

## Endpoints
- `GET /` → Información del servidor (nombre, versión de Python, host, uptime, etc.)
- `GET /health` → `{ "status": "ok" }` con uptime
- `GET /chat/` → Respuesta base: `{"route":"chat","status":"ready"}`
- `GET /brief/` → Respuesta base: `{"route":"brief","status":"ready"}`

## Configuración por variables de entorno (.env)
Crea un archivo `.env` en `ba-be-new/` con:
```
APP_ENV=development
PORT=5000

# OpenAI
OPENAI_API_KEY=coloca_tu_api_key_de_openai
OPENAI_MODEL=gpt-4o-mini

# Groq
GROQ_API_KEY=coloca_tu_api_key_de_groq
GROQ_MODEL=llama-3.1-8b-instant

# Opcionales para memoria y contexto
# CHAT_DB_PATH=./data/chat.sqlite3
# MAX_CONTEXT_MESSAGES=20
# SYSTEM_PROMPT=Eres un asistente útil y conciso.
```
El proyecto carga estas variables automáticamente al iniciar (usa `python-dotenv`).

## Interfaz LLM (OpenAI / Groq)
Se incluye un cliente unificado en `app/services/llm_client.py`.

Ejemplo de uso en código Python:
```python
from app.services.llm_client import call_llm

result = call_llm(
    provider="openai",  # o "groq"
    prompt="Resume en 3 puntos las ventajas de Flask",
    system="Eres un asistente útil y conciso.",
    temperature=0.2,
)
print(result["text"])  # texto generado
```

También puedes usar la clase directamente:
```python
from app.services.llm_client import LLMClient

client = LLMClient(provider="groq")
text = client.chat([
    {"role": "system", "content": "Responde en español."},
    {"role": "user", "content": "Explica brevemente qué es un LLM."}
])
print(text)
```

- El proveedor se selecciona por argumento (`openai` o `groq`).
- Las API Keys y modelos por defecto se toman de `.env`.
- Puedes sobreescribir el modelo pasando `model="..."` en las llamadas.

## Memoria conversacional (SQLite)
- El historial de chat por `sessionId` se almacena en SQLite.
- Archivo por defecto: `./data/chat.sqlite3` (configurable con `CHAT_DB_PATH`).
- Se usa `MAX_CONTEXT_MESSAGES` para limitar los últimos N mensajes en el contexto.
- Puedes ajustar el `SYSTEM_PROMPT` desde `.env`.

## API `POST /chat/stream`
- Body JSON: `{ "sessionId": string, "message": string }` (también acepta el campo `messeage`)
- Persiste el mensaje del usuario y la respuesta del asistente en SQLite (por `sessionId`).
- Respuesta: `{ "message": string, "summary": null, "step": "asking" }`

Ejemplo de prueba con `curl` (Windows/PowerShell usa `curl.exe`):
```powershell
curl.exe -X POST http://localhost:5000/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"demo-123\",\"message\":\"Escribe un haiku sobre el mar\"}"
```
Respuesta típica:
```json
{
  "message": "...texto generado por el LLM...",
  "summary": null,
  "step": "asking"
}
```

## API `POST /chat/reset`
- Body JSON: `{ "sessionId": string }`
- Efecto: elimina todos los mensajes asociados a esa `sessionId` y la fila de sesión.
- Respuesta éxito: `{ "success": true, "message": "Sesión <id> reiniciada; <n> mensajes borrados." }`
- Respuesta sin conversación previa: `{ "success": false, "message": "No había conversación para la sesión <id>. Nada que borrar." }`

Ejemplo con `curl`:
```powershell
curl.exe -X POST http://localhost:5000/chat/reset \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"demo-123\"}"
```