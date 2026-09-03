"""ASGI 启动入口。

业务代码位于 app 包中；保留 main:app 入口以兼容现有启动命令。
"""

from app.application import app

__all__ = ["app"]
