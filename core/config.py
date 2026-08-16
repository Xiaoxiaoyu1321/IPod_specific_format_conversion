"""配置管理：AppConfig 数据类 + JSON 持久化。

配置文件默认位于仓库根目录 config.json，由 GUI/CLI 共用。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from .models import FormatKind

# 仓库根目录（core 位于 <root>/core/）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"

# ffmpeg 下载地址（Windows 静态构建；其他平台建议 brew install ffmpeg 或放入 bin/ffmpeg）
DEFAULT_FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z"

# 各转换类型默认勾选状态
DEFAULT_KINDS = [FormatKind.FLAC2M4A.value]


@dataclass
class AppConfig:
    """全部可配置项。字段均提供默认值，保证从空配置也能启动。"""

    input_dir: str = ""                              # 源文件目录
    output_dir: str = ""                             # 输出目录
    qq_music_dir: str = ""                           # QQ 音乐下载目录（mgg/mflac 解密源）
    ffmpeg_dir: str = ""                             # 自定义 ffmpeg 目录（含 ffmpeg/ffprobe）
    ffmpeg_download_url: str = DEFAULT_FFMPEG_URL    # ffmpeg 自动下载地址
    kinds: list = field(default_factory=lambda: list(DEFAULT_KINDS))  # 选中的转换类型
    keep_temp: bool = False                          # 保留 wav 等中间缓存
    keep_temp_pic: bool = False                      # 保留封面缓存
    download_cover: bool = True                      # 自动联网下载专辑封面
    download_lyrics: bool = False                    # 自动联网下载歌词
    threads: int = 4                                 # ffmpeg 线程数
    process_name: str = "QQMusic.exe"                # QQ 音乐进程名（解密用）

    # ---- 序列化 ----
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        clean = {k: v for k, v in (data or {}).items() if k in known}
        cfg = cls(**clean)
        # 兜底校验
        if not isinstance(cfg.kinds, list) or not cfg.kinds:
            cfg.kinds = list(DEFAULT_KINDS)
        cfg.threads = max(1, int(cfg.threads or 1))
        return cfg


def load_config(path: Optional[Path] = None) -> AppConfig:
    """从磁盘加载配置；文件不存在或损坏时返回默认配置。"""
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not path.is_file():
        return AppConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AppConfig.from_dict(data)
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return AppConfig()


def save_config(config: AppConfig, path: Optional[Path] = None) -> Path:
    """保存配置到磁盘，返回实际写入路径。"""
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
