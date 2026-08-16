"""IPod 格式转换核心包。

纯逻辑层，不依赖任何 GUI 框架。GUI 与 CLI 均通过本包驱动：
    - core.engine.ConversionEngine  转换引擎（主入口）
    - core.config.AppConfig         配置
    - core.models.*                 数据模型
"""
from .config import AppConfig, load_config, save_config
from .engine import ConversionEngine
from .models import ConversionTask, FormatKind, TaskStatus

__version__ = "3.0.0"

__all__ = [
    "AppConfig",
    "ConversionEngine",
    "ConversionTask",
    "FormatKind",
    "TaskStatus",
    "load_config",
    "save_config",
]
