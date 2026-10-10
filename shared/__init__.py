"""Boilerplate shared by every step: settings, printing and fake shop data.

Nothing in this package is LangChain; it only keeps the step files short.
You can skip this folder while you learn.
"""

from pathlib import Path

from shared.config import EMBEDDING_MODEL, MODEL
from shared.console import print_message, print_updates, run_demo

# The shop's policy handbook (Markdown files), searched from step 09.
HANDBOOK_DIR = Path(__file__).resolve().parent / "handbook"

__all__ = ["EMBEDDING_MODEL", "HANDBOOK_DIR", "MODEL", "print_message", "print_updates", "run_demo"]
