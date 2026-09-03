import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from app.config import DINGTALK_SECRET, DINGTALK_WEBHOOK


def build_dingtalk_signed_url() -> str:
    if not DINGTALK_WEBHOOK or not DINGTALK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="钉钉配置缺失，请检查 .env 文件。"
        )

    timestamp = str(int(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{DINGTALK_SECRET}"
    signature = hmac.new(
        DINGTALK_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(signature).decode("utf-8")
    separator = "&" if "?" in DINGTALK_WEBHOOK else "?"
    return (
        f"{DINGTALK_WEBHOOK}{separator}"
        f"{urlencode({'timestamp': timestamp, 'sign': sign})}"
    )


async def send_dingtalk_text(content: str) -> dict:
    signed_url = build_dingtalk_signed_url()
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(signed_url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"调用钉钉接口失败：{str(error)}"
        ) from error

    try:
        result = response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="钉钉返回了无法解析的响应。"
        ) from error

    if result.get("errcode") != 0:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "钉钉发送失败",
                "dingtalk_response": result
            }
        )
    return result
