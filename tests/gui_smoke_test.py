#!/usr/bin/env python3
"""GUI 冒烟测试：在无显示环境（offscreen）下验证界面可构建。

说明：macOS 下 qfluentwidgets 使用原生无边框窗口（qframelesswindow），
离屏模式下没有真实 NSWindow，因此本测试将 updateFrameless 临时替换为
空操作，仅验证代码路径与控件 API 正确性。

运行：
    QT_QPA_PLATFORM=offscreen .venv/bin/python tests/gui_smoke_test.py
"""
import sys

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# 保证从任意位置运行都能 import core / gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- 仅在 macOS + 无显示环境下的测试钩子 ----
if sys.platform == "darwin":
    try:
        import qframelesswindow.mac as _qfm

        def _fake_update_frameless(self):
            # 离屏模式下没有真实 NSWindow，仅初始化私有属性以通过构造
            self._MacFramelessWindow__nsWindow = None

        _qfm.MacFramelessWindow.updateFrameless = _fake_update_frameless
        _qfm.MacFramelessWindow._hideSystemTitleBar = lambda self, *a: None
        _qfm.MacFramelessWindow.setSystemTitleBarButtonVisible = (
            lambda self, *a: None)
        _qfm.MacFramelessWindow._updateSystemButtonRect = lambda self: None
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 无法注入测试钩子：{exc}")

from PyQt5.QtWidgets import QApplication  # noqa: E402

from core.config import AppConfig  # noqa: E402
from gui.main_window import MainWindow  # noqa: E402
from gui.pages.home_page import HomePage  # noqa: E402
from gui.pages.settings_page import SettingsPage  # noqa: E402
from gui.pages.tasks_page import TasksPage  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])

    # 1) 三个页面独立构建
    cfg = AppConfig(input_dir="/tmp/in", output_dir="/tmp/out")
    pages = [HomePage(cfg), TasksPage(), SettingsPage(cfg)]
    for page in pages:
        assert page.objectName(), "页面缺少 objectName"
    print("页面构建成功：", [p.objectName() for p in pages])

    # 2) 主窗口（FluentWindow）构建
    win = MainWindow()
    win.show()
    names = [win.stackedWidget.widget(i).objectName()
             for i in range(win.stackedWidget.count())]
    print("主窗口构建成功，子页面：", names)

    # 3) 模拟一次配置采集
    collected = AppConfig()
    win.home_page.collect_into(collected)
    win.settings_page.collect_into(collected)
    print("配置采集成功：kinds =", collected.kinds, "threads =", collected.threads)

    print("GUI 冒烟测试通过 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
