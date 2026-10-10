"""Boilerplate: loads `.env` from the repo root and picks the models.

You don't need to read this file to follow the course.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load `.env` from the repo root, wherever the step is run from.
load_dotenv(REPO_ROOT / ".env")

# "provider:model-name" strings. init_chat_model() and init_embeddings() read them (see step 01).
MODEL = os.getenv("MODEL", "google_genai:gemini-flash-latest")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "google_genai:gemini-embedding-001")

# The environment variable each provider reads its key from.
_KEY_FOR_PROVIDER = {
    "google_genai": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def check_api_keys() -> None:
    """Exits with a friendly message if the key for MODEL or EMBEDDING_MODEL is missing."""
    for model in (MODEL, EMBEDDING_MODEL):
        provider = model.split(":", 1)[0]
        key_name = _KEY_FOR_PROVIDER.get(provider)
        if key_name is None:  # Ollama and other local providers need no key.
            continue
        value = os.getenv(key_name, "")
        if not value or value.startswith("paste-your"):
            sys.exit(
                f"{key_name} is not set (needed for {model}).\n"
                "Copy .env.example to .env in the repo root and paste your key into it."
            )


# Check now, before a step creates its model: a missing key then gives this clear message
# instead of a long validation error from the provider's package.
check_api_keys()
