"""轻量日志器：支持回调转发（供 GUI 信号使用）与直接打印（供 CLI 使用）。"""
from __future__ import annotations

from typing import Callable, List


class Logger:
    """将日志行分发给注册的处理器；echo=True 时同时打印到控制台。"""

    def __init__(self, echo: bool = False):
        self.echo = echo
        self._handlers: List[Callable[[str], None]] = []

    def add_handler(self, handler: Callable[[str], None]) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    def clear_handlers(self) -> None:
        self._handlers.clear()

    def _emit(self, level: str, msg: str) -> None:
        line = f"[{level}] {msg}"
        for handler in self._handlers:
            try:
                handler(line)
            except Exception:
                pass  # 处理器异常不影响核心流程
        if self.echo:
            print(line)

    def info(self, msg: str) -> None:
        self._emit("Info", msg)

    def warning(self, msg: str) -> None:
        self._emit("Warning", msg)

    def error(self, msg: str) -> None:
        self._emit("Error", msg)
