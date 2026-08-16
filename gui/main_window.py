"""主窗口：FluentWindow 导航框架 + 三页（转换/任务/设置）。"""
from __future__ import annotations

from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (
    FluentIcon as FIF, FluentWindow, InfoBar, InfoBarPosition,
    NavigationItemPosition, setTheme, setThemeColor, Theme,
)

from core.config import AppConfig, DEFAULT_CONFIG_PATH, load_config, save_config
from core.engine import ConversionEngine
from core.models import TaskStatus

from .pages.home_page import HomePage
from .pages.settings_page import SettingsPage
from .pages.tasks_page import TasksPage
from .worker import EngineWorker


class MainWindow(FluentWindow):
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        super().__init__()
        self.config_path = config_path
        self.config = load_config(config_path)

        setTheme(Theme.AUTO)
        setThemeColor("#0078d4")

        # 页面
        self.home_page = HomePage(self.config, self)
        self.tasks_page = TasksPage(self)
        self.settings_page = SettingsPage(self.config, self)

        self.addSubInterface(self.home_page, FIF.HOME, "转换")
        self.addSubInterface(self.tasks_page, FIF.LIBRARY, "任务")
        self.addSubInterface(self.settings_page, FIF.SETTING, "设置",
                             NavigationItemPosition.BOTTOM)

        # 状态
        self._worker: EngineWorker | None = None
        self._engine: ConversionEngine | None = None
        self._total = 0
        self._done = 0

        # 信号
        self.home_page.start_requested.connect(self.start_conversion)
        self.home_page.stop_requested.connect(self.stop_conversion)
        self.settings_page.saved.connect(self.on_settings_saved)

        self.resize(1024, 720)
        self.setWindowTitle("IPod 格式转换")

    # ---- 启动/停止 ----
    def start_conversion(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        # 采集界面状态 → 配置
        config = AppConfig()
        self.home_page.collect_into(config)
        self.settings_page.collect_into(config)
        self.config = config
        try:
            save_config(config, self.config_path)
        except OSError:
            pass  # 配置保存失败不影响转换

        if not config.input_dir or not config.output_dir:
            InfoBar.warning(
                "请先设置目录", "输入目录与输出目录不能为空",
                parent=self, position=InfoBarPosition.TOP_RIGHT, duration=3000,
            )
            return
        if not config.kinds:
            InfoBar.warning(
                "请选择格式", "至少选择一种转换类型",
                parent=self, position=InfoBarPosition.TOP_RIGHT, duration=3000,
            )
            return

        self.tasks_page.clear()
        self._total = 0
        self._done = 0
        self.home_page.append_log("———— 开始新任务 ————")

        engine = ConversionEngine(config)
        worker = EngineWorker(engine, self)
        worker.log_signal.connect(self.home_page.append_log)
        worker.task_signal.connect(self.tasks_page.on_task)
        worker.task_signal.connect(self.home_page.on_task)
        worker.task_signal.connect(self._on_task)
        worker.done_signal.connect(self._on_done)

        self._engine = engine
        self._worker = worker
        self.home_page.set_running(True)
        worker.start()

    def stop_conversion(self) -> None:
        if self._engine is not None:
            self._engine.stop()
        self.home_page.append_log("正在停止…（当前 ffmpeg 进程将被终止）")

    def _on_task(self, task) -> None:
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                           TaskStatus.SKIPPED):
            self._done += 1
            self._total = max(self._total, self._done)

    def _on_done(self, ok: bool, err: str) -> None:
        self.home_page.set_running(False)
        if ok:
            InfoBar.success(
                "完成", f"全部任务处理完毕（完成 {self._done} 项）",
                parent=self, position=InfoBarPosition.TOP_RIGHT, duration=4000,
            )
        else:
            InfoBar.error(
                "出错", err,
                parent=self, position=InfoBarPosition.TOP_RIGHT, duration=6000,
            )
        self._engine = None

    def on_settings_saved(self) -> None:
        config = AppConfig()
        self.home_page.collect_into(config)
        self.settings_page.collect_into(config)
        self.config = config
        try:
            save_config(config, self.config_path)
        except OSError as exc:
            InfoBar.error("保存失败", str(exc), parent=self,
                          position=InfoBarPosition.TOP_RIGHT, duration=3000)
            return
        InfoBar.success("已保存", "配置已写入 config.json", parent=self,
                        position=InfoBarPosition.TOP_RIGHT, duration=3000)

    # ---- 关闭清理 ----
    def closeEvent(self, event) -> None:  # noqa: N802 —— Qt 命名约定
        if (self._worker is not None and self._worker.isRunning()
                and self._engine is not None):
            self._engine.stop()
            self._worker.wait(5000)
        super().closeEvent(event)


def run() -> int:
    """启动 GUI（供 main.py 调用）。"""
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("IPod 格式转换")
    window = MainWindow()
    window.show()
    return app.exec_()
