"""把 core.ConversionEngine 跑在后台线程，并通过 Qt 信号回传进度。"""
from __future__ import annotations

from PyQt5.QtCore import QThread, pyqtSignal

from core.engine import ConversionEngine


class EngineWorker(QThread):
    """在后台线程运行转换引擎。

    信号：
        log_signal(str)         —— 日志行
        task_signal(object)     —— core.models.ConversionTask（进度/状态变化）
        done_signal(bool, str)  —— (是否成功, 错误信息)
    """

    log_signal = pyqtSignal(str)
    task_signal = pyqtSignal(object)
    done_signal = pyqtSignal(bool, str)

    def __init__(self, engine: ConversionEngine, parent=None):
        super().__init__(parent)
        self._engine = engine
        # 订阅引擎回调 → 转发为 Qt 信号
        self._engine.log.add_handler(self.log_signal.emit)
        self._engine.task_cb = self.task_signal.emit

    def stop(self) -> None:
        self._engine.stop()

    def run(self) -> None:
        try:
            self._engine.run()
            self.done_signal.emit(True, "")
        except Exception as exc:  # noqa: BLE001 —— 兜底上报给界面
            self.done_signal.emit(False, str(exc))
