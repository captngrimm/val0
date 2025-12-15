# PX01 – Val-0 (Telegram Bot) – DEV README

Este archivo es para **mí futuro** y para cualquier IA que me ayude con el código.  
La fuente de verdad SIEMPRE es el código que está en **GitHub (`main`)**.  
El servidor en `/opt/val0` es una **copia que corre** lo que hay en Git.

---

## 1. Visión rápida

Val-0 es un bot de Telegram que:

- Habla con el usuario usando OpenAI (GPT).
- Guarda memoria en SQLite (`val0_memory.db`).
- Soporta:
  - Mensajes de texto.
  - Notas y búsqueda de notas (`/note`, `/notes`, `/search`).
  - Notas de voz (Whisper).
  - Búsqueda de lugares con Google Places (`/place …`).

---

## 2. Estructura de carpetas (resumen)

Ruta base: `/opt/val0`

- `bot.py` → archivo principal del bot (comandos, handlers, llamada a OpenAI).
- `memory_store.py` → acceso directo a SQLite (mensajes, facts, notas).
- `val0_memory.db` → base de datos SQLite.

Carpetas clave:

- `memory/`
  - `database.py`, `memory_engine.py`, `schema.sql` → sistema de memoria extendida (FAISS, etc).
- `faiss/`
  - `faiss_index.py`, `faiss_store/`, `memory_embeddings.py` → memoria semántica.
- `voice/`
  - `__init__.py`, `whisper_engine.cpython-310.pyc` → componentes de voz (actualmente usamos Whisper vía OpenAI directo en `bot.py`).
- `places/`
  - `places_engine.py` → integración con Google Places API.
- `engagement/`
  - `emoji_engine.py`, `sticker_engine.py` → futuro: reacciones, stickers, etc.
- `reminders/`
  - `reminder_engine.py` → futuro: recordatorios.
- `doc_intel/`, `files/`, `shortcuts/`, `tts/`, `util/`, `system/`, `tasks/` → piezas del ecosistema Val-0 / PX01 (muchas listas para expansión futura).

Backups y utilidades:

- `backups/` → snapshots viejos (bot.py, memory_store.py, val0_memory.db).
- `backup_val0.sh` → script para hacer backup (por completar/usar).
- `bot.py.before_*` → versiones anteriores de desarrollo.
- `tests/` → pruebas.
- `tmp/` → archivos temporales (por ejemplo, audios para Whisper).

---

## 3. Variables de entorno requeridas (`.env`)

Archivo: `/opt/val0/.env`

Debe contener (sin espacios raros, una por línea):

```bash
OPENAI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
GOOGLE_PLACES_API_KEY=...
