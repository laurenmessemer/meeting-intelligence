import os
import contextvars
from typing import Optional

_demo_mode_ctx = contextvars.ContextVar("demo_mode", default=None)

def set_request_demo_mode(value: Optional[bool]):
    if value is not None:
        _demo_mode_ctx.set(bool(value))

def get_app_mode() -> str:
    mode = (os.getenv("APP_MODE") or "demo").strip().lower()
    if mode not in {"demo", "prod", "dev"}:
        return "demo"
    return mode

def is_demo_mode() -> bool:
    request_override = _demo_mode_ctx.get()
    if request_override is not None:
        return request_override
    return get_app_mode() == "demo"
