import re
import uuid

from fastapi import HTTPException, status
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings

LUCIDE_SCRIPT_URL = "https://unpkg.com/lucide@1.48.0/dist/umd/lucide.min.js"
LUCIDE_SCRIPT_INTEGRITY = "sha384-Hh7C333mXel+qppGoFs4qAOXp7h67eur4XsQVF2bvHAM3MQ4DX4cQI7oRCzb98J4"
REDOC_SCRIPT_URL = "https://cdn.jsdelivr.net/npm/redoc@2.5.4/bundles/redoc.standalone.js"

APP_CSP = "; ".join(
    [
        "default-src 'self'",
        f"script-src 'self' {LUCIDE_SCRIPT_URL}",
        "style-src 'self' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https://covers.openlibrary.org",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

# FastAPI's Swagger UI and ReDoc pages boot from inline scripts and load their
# bundles from jsDelivr, so they get a looser policy scoped to those paths only.
DOCS_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly",
        "connect-src 'self'",
        "worker-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
    ]
)

BASE_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "X-Frame-Options": "DENY",
}

_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_BODY_METHODS = {"POST", "PUT", "PATCH"}


def security_headers_for(path: str, docs_paths: frozenset) -> dict[str, str]:
    csp = DOCS_CSP if path in docs_paths else APP_CSP
    return {**BASE_SECURITY_HEADERS, "Content-Security-Policy": csp}


def resolve_request_id(incoming: str | None) -> str:
    """Reuse a well-formed upstream request id, otherwise mint a new one."""
    if incoming and _REQUEST_ID.match(incoming):
        return incoming
    return str(uuid.uuid4())


async def ensure_writes_enabled() -> None:
    """Kill switch for every mutating route (WRITES_ENABLED=false)."""
    if not settings.WRITES_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Writes are temporarily disabled.",
        )


class _BodyTooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """Reject request bodies above ``max_bytes`` before they are buffered.

    A declared Content-Length above the limit gets 413 right away. Bodies sent
    without one are counted while streaming and cut off at the limit.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in _BODY_METHODS:
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > self.max_bytes):
            await self._reject(scope, receive, send)
            return

        received = 0
        exceeded = False
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received, exceeded
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    exceeded = True
                    raise _BodyTooLarge
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                if exceeded:
                    # FastAPI turns body-read errors into a generic 400; answer 413 instead.
                    await self._reject(scope, receive, send)
                    return
            if not exceeded:
                await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except _BodyTooLarge:
            if not response_started:
                await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            {"detail": "Request body too large."},
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        )
        await response(scope, receive, send)
