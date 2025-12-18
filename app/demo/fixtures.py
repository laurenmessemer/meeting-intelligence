import json
from pathlib import Path
from typing import Any, Dict, Optional

_DEMO_DIR = Path(__file__).resolve().parent / "data"

def _read_text(name: str) -> str:
    path = _DEMO_DIR / name
    return path.read_text(encoding="utf-8")

def _read_json(name: str) -> Dict[str, Any]:
    path = _DEMO_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))

def demo_memory_seed() -> Dict[str, Any]:
    """
    Return memory seed payload.
    You can shape this to match your MemoryRepo create APIs.
    """
    return _read_json("memory_seed.json")
