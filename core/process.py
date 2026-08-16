"""子进程创建辅助。

Windows 的 GUI（PyInstaller --windowed）应用没有控制台，若不显式指定
CREATE_NO_WINDOW，每次用 subprocess 启动外部程序（ffmpeg/ffprobe）时，
Windows 都会为子进程新建一个前台控制台窗口（黑色 cmd 闪窗）。
本模块提供跨平台标志，统一让子进程静默后台执行。
"""
from __future__ import annotations

import os
import subprocess

# Windows: 0x08000000，禁止子进程创建控制台窗口；其他平台无此概念，传 0 即可
CREATE_NO_WINDOW = (
    getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if os.name == "nt"
    else 0
)


def run(args, **kwargs):
    """subprocess.run 的静默包装（Windows 下不弹控制台窗口）。"""
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    return subprocess.run(args, **kwargs)


def popen(args, **kwargs):
    """subprocess.Popen 的静默包装（Windows 下不弹控制台窗口）。"""
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    return subprocess.Popen(args, **kwargs)
