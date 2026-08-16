"""ffmpeg 转换封装：带进度解析（-progress pipe:1）与可中断支持。"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional

# QQ 音乐 ogg 标签里带的无意义字段，不写入输出元数据
_DENY_TAGS = {
    "end", "endserial", "endgran",
    "encoder", "encoder_settings", "creation_time", "handler_name",
}

# 大 OGG 文件探测需要加大这两个参数
_PROBE_ARGS = ["-analyzeduration", "2147483647", "-probesize", "2147483647"]


class ConversionError(RuntimeError):
    """转换执行失败。"""


class Converter:
    def __init__(self, ffmpeg: Path, ffprobe: Path, threads: int = 4):
        self.ffmpeg = Path(ffmpeg)
        self.ffprobe = Path(ffprobe)
        self.threads = max(1, int(threads))

    # ---- 底层执行 ----
    def run(
        self,
        args: List[str],
        duration: Optional[float] = None,
        progress_cb: Optional[Callable[[float], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
    ) -> None:
        """执行一条 ffmpeg 命令并解析进度。

        :param args: ffmpeg 参数（不含可执行文件本身，含 -i 与输出路径）
        :param duration: 总时长（秒），用于把 out_time 换算成百分比
        """
        cmd = [
            str(self.ffmpeg), "-y",
            "-progress", "pipe:1", "-nostats",
            "-threads", str(self.threads),
            *args,
        ]
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
        except OSError as exc:
            raise ConversionError(f"无法启动 ffmpeg：{exc}") from exc

        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                line = line.strip()
                if should_stop and should_stop():
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    raise ConversionError("任务已取消")
                if progress_cb:
                    if line.startswith("out_time_us="):
                        self._emit_progress(progress_cb, line, duration)
                    elif line.startswith("progress=end"):
                        progress_cb(100.0)
        finally:
            proc.stdout.close()
        rc = proc.wait()
        if rc != 0:
            raise ConversionError(
                f"ffmpeg 执行失败（exit={rc}）：{' '.join(str(c) for c in cmd[:10])}…"
            )

    @staticmethod
    def _emit_progress(progress_cb: Callable[[float], None],
                       line: str, duration: Optional[float]) -> None:
        try:
            micros = int(line.split("=", 1)[1].strip())
        except (ValueError, IndexError):
            return
        if not duration or duration <= 0:
            return
        pct = max(0.0, min(99.0, micros / (duration * 1_000_000) * 100.0))
        progress_cb(pct)

    # ---- 元数据参数 ----
    @staticmethod
    def _metadata_args(tags: Dict[str, str]) -> List[str]:
        args: List[str] = []
        for key, value in (tags or {}).items():
            k = str(key).lower()
            if k in _DENY_TAGS or not isinstance(value, str) or not value:
                continue
            args.extend(["-metadata", f"{k}={value}"])
        return args

    # ---- 音频转换 ----
    def to_wav(self, src: Path, wav: Path, duration: Optional[float] = None,
               progress_cb: Optional[Callable[[float], None]] = None,
               should_stop: Optional[Callable[[], bool]] = None) -> None:
        """转成 iPod 无损标准：pcm_s16le / 44.1kHz / 双声道（1411Kbps）。"""
        self.run(
            ["-i", str(src), "-vn",
             "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
             "-map_metadata", "0", str(wav)],
            duration=duration, progress_cb=progress_cb, should_stop=should_stop,
        )

    def to_m4a(self, src: Path, out: Path, tags: Optional[Dict[str, str]] = None,
               duration: Optional[float] = None,
               progress_cb: Optional[Callable[[float], None]] = None,
               should_stop: Optional[Callable[[], bool]] = None) -> None:
        """转 ALAC 无损 M4A，携带元数据。"""
        self.run(
            [*_PROBE_ARGS, "-i", str(src), "-vn", "-acodec", "alac",
             *self._metadata_args(tags), str(out)],
            duration=duration, progress_cb=progress_cb, should_stop=should_stop,
        )

    def to_mp3(self, src: Path, out: Path, tags: Optional[Dict[str, str]] = None,
               duration: Optional[float] = None,
               progress_cb: Optional[Callable[[float], None]] = None,
               should_stop: Optional[Callable[[], bool]] = None) -> None:
        """转 MP3（libmp3lame）。"""
        self.run(
            [*_PROBE_ARGS, "-i", str(src), "-vn", "-acodec", "libmp3lame",
             *self._metadata_args(tags), str(out)],
            duration=duration, progress_cb=progress_cb, should_stop=should_stop,
        )

    def to_flac(self, src: Path, out: Path, tags: Optional[Dict[str, str]] = None,
                duration: Optional[float] = None,
                progress_cb: Optional[Callable[[float], None]] = None,
                should_stop: Optional[Callable[[], bool]] = None) -> None:
        """转 FLAC（无损，保留源采样率/位深）。"""
        self.run(
            [*_PROBE_ARGS, "-i", str(src), "-vn", "-acodec", "flac",
             *self._metadata_args(tags), str(out)],
            duration=duration, progress_cb=progress_cb, should_stop=should_stop,
        )

    def copy_file(self, src: Path, out: Path,
                  progress_cb: Optional[Callable[[float], None]] = None,
                  should_stop: Optional[Callable[[], bool]] = None) -> None:
        """整文件复制（源与目标同格式时使用，如 mflac 解密产物→flac）。"""
        if should_stop and should_stop():
            raise ConversionError("任务已取消")
        total = src.stat().st_size
        out.parent.mkdir(parents=True, exist_ok=True)
        done = 0
        with open(src, "rb") as fsrc, open(out, "wb") as fdst:
            while True:
                if should_stop and should_stop():
                    fdst.close()
                    out.unlink(missing_ok=True)
                    raise ConversionError("任务已取消")
                chunk = fsrc.read(1024 * 1024)
                if not chunk:
                    break
                fdst.write(chunk)
                done += len(chunk)
                if progress_cb and total:
                    progress_cb(min(100.0, done * 100.0 / total))
        if progress_cb:
            progress_cb(100.0)

    # ---- 视频转换 ----
    def to_video_mp4(self, src: Path, out: Path, duration: Optional[float] = None,
                     progress_cb: Optional[Callable[[float], None]] = None,
                     should_stop: Optional[Callable[[], bool]] = None) -> None:
        """转 iPod 兼容 MP4：H.264 baseline + AAC 160k。"""
        self.run(
            ["-i", str(src),
             "-vf", "scale=320:240:force_original_aspect_ratio=decrease,"
                    "pad=320:240:(ow-iw)/2:(oh-ih)/2",
             "-c:a", "aac", "-b:a", "160k",
             "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
             "-pix_fmt", "yuv420p", "-r", "30", "-crf", "23", "-b:v", "1500k",
             "-movflags", "+faststart", str(out)],
            duration=duration, progress_cb=progress_cb, should_stop=should_stop,
        )

    def to_video_mpg(self, src: Path, out: Path, duration: Optional[float] = None,
                     progress_cb: Optional[Callable[[float], None]] = None,
                     should_stop: Optional[Callable[[], bool]] = None) -> None:
        """转 MPG：mpeg2video + mp3。"""
        self.run(
            ["-i", str(src),
             "-vf", "scale=320:240:force_original_aspect_ratio=decrease,"
                    "pad=320:240:(ow-iw)/2:(oh-ih)/2",
             "-r", "30", "-c:v", "mpeg2video", "-b:v", "1000k",
             "-c:a", "mp3", "-b:a", "160k", str(out)],
            duration=duration, progress_cb=progress_cb, should_stop=should_stop,
        )
