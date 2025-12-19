from __future__ import annotations

import secrets
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import Config
from app.runtime.mode import is_demo_mode



class DemoBasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Simple Basic Auth gate for hosted demo environments.

    - Enabled only in demo mode AND when DEMO_BASIC_AUTH_PASSWORD is set.
    - Lets /health pass through without auth (useful for platform health checks).
    - Applies to all other routes, including UI and /api/chat.
    """

    def __init__(self, app, realm: str = "Demo"):
        super().__init__(app)
        self.realm = realm

    async def dispatch(self, request: Request, call_next):
        # Always allow health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Only enforce in demo mode, and only if password is configured
        password = (Config.DEMO_BASIC_AUTH_PASSWORD or "").strip()
        if not is_demo_mode() or not password:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return self._unauthorized()

        # Decode Basic auth
        try:
            import base64
            encoded = auth.split(" ", 1)[1].strip()
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, provided_password = decoded.split(":", 1)
        except Exception:
            return self._unauthorized()

        # Username is not important; password is the gate.
        if not secrets.compare_digest(provided_password, password):
            return self._unauthorized()

        return await call_next(request)

    def _unauthorized(self) -> Response:
        return Response(
            content="Unauthorized",
            status_code=HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
        )
