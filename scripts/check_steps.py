"""Smoke test: every step imports cleanly, builds its chain or agent, and has a README.

This does not call any model, so it needs no API key (a placeholder key is set below, because the
model classes check that one exists). It catches the two most common ways a tutorial rots after a
LangChain upgrade: an import moves and a step stops loading, or a step keeps using an API that
LangChain has deprecated. It also runs step 14's fake-model tests, which need no key either.

Usage (from the repo root):
    python scripts/check_steps.py
"""

from __future__ import annotations

import importlib
import os
import sys
import traceback
import warnings
from pathlib import Path

STEPS_DIR = Path(__file__).resolve().parent.parent / "steps"

# The model classes refuse to start without a key. Nothing here sends a request.
os.environ.setdefault("GOOGLE_API_KEY", "placeholder-key-for-import-checks")


def import_isolated(path: Path):
    """Imports a step file as a top-level module, with its folder first on sys.path.

    Steps reuse the same module names (app, shop_tools, knowledge...), so modules loaded from one
    step folder are forgotten before the next one is imported.
    """
    sys.path.insert(0, str(path.parent))
    try:
        return importlib.import_module(path.stem)
    finally:
        sys.path.pop(0)
        for name, module in list(sys.modules.items()):
            file = getattr(module, "__file__", None)
            if file and Path(file).resolve().is_relative_to(STEPS_DIR):
                del sys.modules[name]


def deprecations_from_steps(caught: list[warnings.WarningMessage]) -> list[str]:
    """Returns deprecation warnings raised by code in steps/, not by LangChain's own internals."""
    return [
        f"{Path(w.filename).name}:{w.lineno}: {w.message}"
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and Path(w.filename).resolve().is_relative_to(STEPS_DIR)
    ]


def check(path: Path) -> str | None:
    """Checks one step file. Returns an error message, or None if it is fine."""
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            module = import_isolated(path)
        deprecated = deprecations_from_steps(caught)
        if deprecated:
            return "uses deprecated LangChain APIs:\n  " + "\n  ".join(deprecated)

        if path.name == "app.py":
            for name in ("ask", "DEMO_PROMPTS"):
                if not hasattr(module, name):
                    return f"app.py does not define `{name}`"
        # Step 14's test file: run its tests. They use a fake model, so no key is needed.
        for name in dir(module):
            if name.startswith("test_"):
                getattr(module, name)()
        return None
    except Exception:  # Report any failure, then keep checking the other files.
        return traceback.format_exc(limit=3)


def main() -> int:
    step_dirs = sorted(p for p in STEPS_DIR.iterdir() if p.is_dir() and p.name.startswith("step"))
    failures = 0
    checked = 0
    for step_dir in step_dirs:
        if not (step_dir / "README.md").exists():
            failures += 1
            print(f"FAIL  {step_dir.name}: README.md is missing")
        # app.py for steps 01-13; every example file in step 14. Helper files are imported by them.
        files = (
            [step_dir / "app.py"]
            if (step_dir / "app.py").exists()
            else sorted(step_dir.glob("*.py"))
        )
        for path in files:
            checked += 1
            error = check(path)
            label = path.relative_to(STEPS_DIR.parent).as_posix()
            if error:
                failures += 1
                print(f"FAIL  {label}\n{error}")
            else:
                print(f"ok    {label}")

    print(f"\n{checked} files checked, {failures} problems.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
