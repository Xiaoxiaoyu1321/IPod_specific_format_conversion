"""ffmpeg/ffprobe 定位与自动下载。

查找顺序：
1. 配置中显式指定的 ffmpeg_dir
2. 仓库 bin/ffmpeg 目录
3. 系统 PATH
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, Optional, Tuple

import requests

from .config import PROJECT_ROOT, DEFAULT_FFMPEG_URL, AppConfig


class FFmpegError(RuntimeError):
    """ffmpeg 未找到或下载失败。"""


class FFmpegLocator:
    def __init__(self, config: AppConfig):
        self.config = config

    # ---- 定位 ----
    def _exe_name(self, name: str) -> str:
        return name + (".exe" if os.name == "nt" else "")

    def _find(self, name: str) -> Optional[Path]:
        exe = self._exe_name(name)
        candidates = []
        if self.config.ffmpeg_dir:
            candidates.append(Path(self.config.ffmpeg_dir) / exe)
        candidates.append(PROJECT_ROOT / "bin" / "ffmpeg" / exe)
        for cand in candidates:
            if cand.is_file():
                return cand
        hit = shutil.which(name)
        if hit:
            return Path(hit)
        return None

    def locate(self) -> Tuple[Path, Path]:
        """返回 (ffmpeg, ffprobe) 路径；缺失时抛出 FFmpegError。"""
        ffmpeg = self._find("ffmpeg")
        ffprobe = self._find("ffprobe")
        if not ffmpeg or not ffprobe:
            raise FFmpegError(
                "未找到 ffmpeg/ffprobe。请将 ffmpeg 放入 bin/ffmpeg 目录、"
                "在设置中指定其所在目录，或使用“下载 ffmpeg”功能。"
            )
        return ffmpeg, ffprobe

    # ---- 下载 ----
    def download(self, url: Optional[str] = None,
                 progress_cb: Optional[Callable[[float], None]] = None) -> Tuple[Path, Path]:
        """下载 ffmpeg 压缩包并尝试自动解压到 bin/ffmpeg。

        :param progress_cb: 下载进度回调 (0-100)
        :return: (ffmpeg, ffprobe) 路径
        """
        url = url or self.config.ffmpeg_download_url or DEFAULT_FFMPEG_URL
        bin_dir = PROJECT_ROOT / "bin" / "ffmpeg"
        dl_dir = bin_dir / "download"
        dl_dir.mkdir(parents=True, exist_ok=True)
        archive = dl_dir / "ffmpeg.7z"

        # 1. 流式下载
        try:
            resp = requests.get(url, stream=True, timeout=60,
                                headers={"User-Agent": "IPod-format-converter"})
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise FFmpegError(f"下载 ffmpeg 失败：{exc}") from exc

        total = int(resp.headers.get("content-length", 0))
        done = 0
        with open(archive, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=256 * 1024):
                if not chunk:
                    continue
                fh.write(chunk)
                done += len(chunk)
                if progress_cb and total:
                    progress_cb(min(100.0, done * 100.0 / total))

        # 2. 尝试 7z 解压
        try:
            import py7zr
            with py7zr.SevenZipFile(archive) as zf:
                zf.extractall(bin_dir)
        except Exception as exc:  # noqa: BLE001 —— 解压失败给出人工指引
            raise FFmpegError(
                f"7z 自动解压失败（{exc}），请手动解压 {archive} 到 {bin_dir}"
            ) from exc

        # 3. 重新定位
        ffmpeg, ffprobe = self.locate()
        return ffmpeg, ffprobe
