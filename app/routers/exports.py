from datetime import date

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.excel import build_ledger_workbook


router = APIRouter(prefix="/api/export", tags=["导出"])


@router.get("/ledger.xlsx")
def export_ledger_excel():
    filename = (
        "supply_chain_ledger_"
        f"{date.today().strftime('%Y%m%d')}.xlsx"
    )
    return StreamingResponse(
        build_ledger_workbook(),
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        }
    )
