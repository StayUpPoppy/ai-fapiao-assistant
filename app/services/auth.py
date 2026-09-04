import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import (
    APP_PASSWORD,
    APP_SESSION_HOURS,
    APP_SESSION_SECRET,
    APP_USERNAME,
    SESSION_COOKIE_NAME
)


def encode_session_payload(data: dict) -> str:
    content = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    ).encode("utf-8")
    return (
        base64.urlsafe_b64encode(content)
        .rstrip(b"=")
        .decode("ascii")
    )


def decode_session_payload(value: str) -> dict:
    padding = "=" * (-len(value) % 4)
    content = base64.urlsafe_b64decode(value + padding)
    return json.loads(content.decode("utf-8"))


def create_session_token(username: str) -> str:
    payload = encode_session_payload({
        "username": username,
        "expires_at": (
            int(time.time())
            + APP_SESSION_HOURS * 3600
        )
    })
    signature = hmac.new(
        APP_SESSION_SECRET.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256
    ).hexdigest()
    return f"{payload}.{signature}"


def verify_session_token(token: str | None) -> str | None:
    if not token or not APP_SESSION_SECRET:
        return None

    try:
        payload, signature = token.split(".", maxsplit=1)
        expected_signature = hmac.new(
            APP_SESSION_SECRET.encode("utf-8"),
            payload.encode("ascii"),
            hashlib.sha256
        ).hexdigest()

        if not secrets.compare_digest(
            signature,
            expected_signature
        ):
            return None

        session_data = decode_session_payload(payload)

        if int(session_data.get("expires_at", 0)) <= int(
            time.time()
        ):
            return None

        username = session_data.get("username")

        if not isinstance(username, str):
            return None

        if not secrets.compare_digest(
            username.encode("utf-8"),
            APP_USERNAME.encode("utf-8")
        ):
            return None

        return username
    except (
        ValueError,
        TypeError,
        KeyError,
        UnicodeDecodeError,
        binascii.Error
    ):
        return None


def auth_is_configured() -> bool:
    return (
        bool(APP_USERNAME)
        and len(APP_PASSWORD) >= 8
        and len(APP_SESSION_SECRET) >= 32
    )


async def require_login(request: Request, call_next):
    public_paths = {
        "/login",
        "/api/auth/login",
        "/static/ui.css"
    }

    if request.url.path in public_paths:
        return await call_next(request)

    username = verify_session_token(
        request.cookies.get(SESSION_COOKIE_NAME)
    )

    if username:
        request.state.username = username
        return await call_next(request)

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=401,
            content={"detail": "未登录或登录已过期。"}
        )

    next_url = request.url.path
    if request.url.query:
        next_url += f"?{request.url.query}"

    return RedirectResponse(
        url=f"/login?next={quote(next_url, safe='')}",
        status_code=303
    )
