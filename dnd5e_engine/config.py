"""Loads .env so OPENAI_* and DND5E_* are visible to the server and scripts.
Import this early (server/ingest do). Safe to import when .env is absent."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"


def embedding_model() -> str:
    return os.environ.get("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def embedding_api_key() -> str | None:
    return os.environ.get("OPENAI_EMBEDDING_API_KEY")
