from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.database import init_database
from app.routers import (
    auth,
    dify,
    exports,
    invoices,
    orders,
    reminders,
    system
)
from app.services.auth import require_login
from app.services.scheduler import start_reminder_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    scheduler = start_reminder_scheduler()
    app.state.reminder_scheduler = scheduler

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    application = FastAPI(
        title="供应链订单与发票台账助手",
        version="0.2.0",
        lifespan=lifespan
    )
    application.middleware("http")(require_login)
    application.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static"
    )
    application.include_router(auth.router)
    application.include_router(system.router)
    application.include_router(dify.router)
    application.include_router(invoices.router)
    application.include_router(orders.router)
    application.include_router(reminders.router)
    application.include_router(exports.router)
    return application


app = create_app()
