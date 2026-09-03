from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import (
    DIFY_API_BASE_URL,
    DIFY_API_KEY,
    DIFY_ORDER_API_KEY
)
from app.services.dify import run_file_workflow


router = APIRouter(prefix="/api/dify", tags=["Dify"])


@router.post("/extract")
async def extract_invoice(
    document_type: str = Form("销售发票"),
    invoice_file: UploadFile = File(...)
):
    if not DIFY_API_BASE_URL or not DIFY_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Dify 配置缺失，请检查 .env 文件。"
        )

    content_type = (
        invoice_file.content_type
        or "application/octet-stream"
    )

    if content_type.startswith("image/"):
        file_type = "image"
    elif content_type == "application/pdf":
        file_type = "document"
    else:
        raise HTTPException(
            status_code=400,
            detail="当前只支持图片和 PDF 文件。"
        )

    file_content = await invoice_file.read()
    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="上传的发票文件为空。"
        )

    return await run_file_workflow(
        api_key=DIFY_API_KEY,
        filename=invoice_file.filename,
        content_type=content_type,
        file_content=file_content,
        file_type=file_type,
        file_variable="invoice_file",
        inputs={"document_type": document_type}
    )


@router.post("/orders/extract")
async def extract_order(
    order_type: str = Form(...),
    order_file: UploadFile = File(...)
):
    if order_type not in {"销售订单", "采购订单"}:
        raise HTTPException(
            status_code=422,
            detail="order_type 必须是销售订单或采购订单。"
        )

    if not DIFY_API_BASE_URL or not DIFY_ORDER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="订单 Dify 配置缺失，请检查 .env 文件。"
        )

    content_type = (
        order_file.content_type
        or "application/octet-stream"
    )
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="当前订单智能识别只支持 PNG、JPG 等图片文件。"
        )

    file_content = await order_file.read()
    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="上传的订单文件为空。"
        )

    return await run_file_workflow(
        api_key=DIFY_ORDER_API_KEY,
        filename=order_file.filename,
        content_type=content_type,
        file_content=file_content,
        file_type="image",
        file_variable="order_file",
        inputs={"order_type": order_type}
    )
