import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse

from app.config import (
    APP_COOKIE_SECURE,
    APP_PASSWORD,
    APP_SESSION_HOURS,
    APP_USERNAME,
    SESSION_COOKIE_NAME,
    STATIC_DIR
)
from app.schemas import LoginRequest
from app.services.auth import (
    auth_is_configured,
    create_session_token,
    verify_session_token
)


router = APIRouter()


@router.get("/login", include_in_schema=False)
def login_page(request: Request):
    username = verify_session_token(
        request.cookies.get(SESSION_COOKIE_NAME)
    )
    if username:
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(STATIC_DIR / "login.html")


@router.post("/api/auth/login")
def login(credentials: LoginRequest, response: Response):
    if not auth_is_configured():
        raise HTTPException(
            status_code=500,
            detail=(
                "登录认证配置无效：密码至少8位，"
                "会话密钥至少32位。"
            )
        )

    username_correct = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        APP_USERNAME.encode("utf-8")
    )
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        APP_PASSWORD.encode("utf-8")
    )

    if not username_correct or not password_correct:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误。"
        )

    max_age = APP_SESSION_HOURS * 3600
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(credentials.username),
        max_age=max_age,
        httponly=True,
        secure=APP_COOKIE_SECURE,
        samesite="lax",
        path="/"
    )

    return {
        "status": "ok",
        "username": credentials.username,
        "expires_in": max_age
    }


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/"
    )
    return {
        "status": "ok",
        "message": "已退出登录。"
    }
