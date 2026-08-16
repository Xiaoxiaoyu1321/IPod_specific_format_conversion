"""数据模型：格式规格、任务状态与转换任务定义。

本模块不依赖任何 GUI 框架，可被 core / GUI / CLI 三方共用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class TaskStatus(str, Enum):
    """单个转换任务的实时状态。"""

    PENDING = "等待中"
    DECRYPTING = "解密中"
    CONVERTING = "转换中"
    EMBEDDING = "嵌入封面"
    COMPLETED = "完成"
    FAILED = "失败"
    SKIPPED = "跳过"

    def __str__(self) -> str:  # 便于直接打印/显示中文
        return self.value


class FormatKind(str, Enum):
    """支持的转换类型（枚举值同时作为配置文件中的存储值）。"""

    FLAC2M4A = "flac2m4a"
    OGG2M4A = "ogg2m4a"
    OGG2MP3 = "ogg2mp3"
    WAV2M4A = "wav2m4a"
    MGG2M4A = "mgg2m4a"
    MFLAC2M4A = "mflac2m4a"
    VIDEO2MP4 = "video2mp4"
    VIDEO2MPG = "video2mpg"


# 视频类转换允许的源文件后缀
VIDEO_SOURCE_EXTS = (
    ".mp4", ".mkv", ".mov", ".avi", ".flv", ".webm",
    ".m4v", ".ts", ".wmv", ".mpg", ".mpeg",
)


@dataclass(frozen=True)
class FormatSpec:
    """一种转换类型的规格描述。"""

    source_exts: tuple  # 源文件后缀集合（小写，含点）
    target_ext: str     # 目标文件后缀（小写，含点）
    label: str          # 界面/日志中展示的名称
    is_video: bool = False
    needs_decrypt: bool = False  # 是否需先经 QQ 音乐进程解密


FORMAT_SPECS: dict[FormatKind, FormatSpec] = {
    FormatKind.FLAC2M4A: FormatSpec(
        (".flac",), ".m4a", "FLAC → M4A（ALAC 无损）"
    ),
    FormatKind.OGG2M4A: FormatSpec(
        (".ogg",), ".m4a", "OGG → M4A（ALAC 无损）"
    ),
    FormatKind.OGG2MP3: FormatSpec(
        (".ogg",), ".mp3", "OGG → MP3"
    ),
    FormatKind.WAV2M4A: FormatSpec(
        (".wav",), ".m4a", "WAV → M4A（ALAC 无损）"
    ),
    FormatKind.MGG2M4A: FormatSpec(
        (".mgg",), ".m4a", "QQ音乐 MGG → M4A", needs_decrypt=True
    ),
    FormatKind.MFLAC2M4A: FormatSpec(
        (".mflac",), ".m4a", "QQ音乐 MFLAC → M4A", needs_decrypt=True
    ),
    FormatKind.VIDEO2MP4: FormatSpec(
        VIDEO_SOURCE_EXTS, ".mp4", "视频 → iPod 兼容 MP4", is_video=True
    ),
    FormatKind.VIDEO2MPG: FormatSpec(
        VIDEO_SOURCE_EXTS, ".mpg", "视频 → MPG", is_video=True
    ),
}


@dataclass
class ConversionTask:
    """一个待转换/转换中的任务。"""

    kind: FormatKind
    source: Path
    output: Path
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0        # 0.0 - 100.0
    message: str = ""

    @property
    def name(self) -> str:
        return self.source.name

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "source": str(self.source),
            "output": str(self.output),
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversionTask":
        return cls(
            kind=FormatKind(data["kind"]),
            source=Path(data["source"]),
            output=Path(data["output"]),
            status=TaskStatus(data.get("status", TaskStatus.PENDING.value)),
            progress=float(data.get("progress", 0.0)),
            message=data.get("message", ""),
        )

    def __str__(self) -> str:
        return f"[{self.status}] {self.name} {self.progress:.0f}% {self.message}"
