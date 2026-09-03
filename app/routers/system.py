from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import (
    DIFY_API_BASE_URL,
    DIFY_API_KEY,
    DIFY_ORDER_API_KEY,
    STATIC_DIR
)


router = APIRouter(tags=["系统"])


@router.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "dify_base_url": DIFY_API_BASE_URL,
        "dify_invoice_api_key_configured": bool(DIFY_API_KEY),
        "dify_order_api_key_configured": bool(DIFY_ORDER_API_KEY)
    }
