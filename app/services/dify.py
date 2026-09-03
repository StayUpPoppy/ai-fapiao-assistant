from typing import Any

import httpx
from fastapi import HTTPException

from app.config import DIFY_API_BASE_URL, DIFY_USER


async def run_file_workflow(
    *,
    api_key: str,
    filename: str | None,
    content_type: str,
    file_content: bytes,
    file_type: str,
    file_variable: str,
    inputs: dict[str, Any]
) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            upload_response = await client.post(
                f"{DIFY_API_BASE_URL}/files/upload",
                headers=headers,
                data={"user": DIFY_USER},
                files={
                    "file": (
                        filename or "upload",
                        file_content,
                        content_type
                    )
                }
            )
            upload_response.raise_for_status()
            upload_file_id = upload_response.json()["id"]

            workflow_inputs = dict(inputs)
            workflow_inputs[file_variable] = [
                {
                    "transfer_method": "local_file",
                    "upload_file_id": upload_file_id,
                    "type": file_type
                }
            ]

            workflow_response = await client.post(
                f"{DIFY_API_BASE_URL}/workflows/run",
                headers={
                    **headers,
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": workflow_inputs,
                    "response_mode": "blocking",
                    "user": DIFY_USER
                }
            )
            workflow_response.raise_for_status()
            workflow_result = workflow_response.json()
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json()
        except ValueError:
            detail = error.response.text

        raise HTTPException(
            status_code=error.response.status_code,
            detail=detail
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail=f"无法连接到 Dify：{str(error)}"
        ) from error

    return {
        "workflow_run_id": workflow_result.get(
            "workflow_run_id"
        ),
        "status": workflow_result.get(
            "data", {}
        ).get("status"),
        "outputs": workflow_result.get(
            "data", {}
        ).get("outputs", {})
    }
