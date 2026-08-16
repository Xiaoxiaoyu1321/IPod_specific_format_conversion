"""元数据工具：ffprobe 探测、标签提取、封面提取/嵌入。"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional

from .logger import Logger  # noqa: F401

_log = Logger()


class MetadataError(RuntimeError):
    """元数据读取失败。"""


def probe(ffprobe: Path, src: Path) -> dict:
    """调用 ffprobe 读取文件的格式与流信息（JSON）。"""
    cmd = [
        str(ffprobe), "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(src),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MetadataError(f"ffprobe 执行失败：{exc}") from exc
    if result.returncode != 0:
        raise MetadataError(f"ffprobe 无法读取 {src.name}")
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise MetadataError(f"ffprobe 输出解析失败：{exc}") from exc


def collect_tags(probe_data: dict) -> Dict[str, str]:
    """合并流与格式标签（流标签优先），统一转为字符串。"""
    tags: Dict[str, str] = {}
    streams = probe_data.get("streams") or []
    for stream in streams:
        if stream.get("codec_type") == "audio":
            for k, v in (stream.get("tags") or {}).items():
                tags[str(k)] = str(v)
            break
    for k, v in (probe_data.get("format", {}).get("tags") or {}).items():
        tags.setdefault(str(k), str(v))
    return tags


def duration_sec(probe_data: dict) -> Optional[float]:
    """尝试获取音频时长（秒），失败返回 None。"""
    try:
        return float(probe_data["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        try:
            stream = next(
                s for s in (probe_data.get("streams") or [])
                if s.get("codec_type") == "audio"
            )
            return float(stream["duration"])
        except (StopIteration, KeyError, TypeError, ValueError):
            return None


def extract_cover(ffmpeg: Path, src: Path, dest: Path,
                  should_stop: Optional[callable] = None) -> bool:
    """尝试从源文件提取封面图到 dest，成功返回 True。"""
    if dest.exists():
        dest.unlink()
    cmd = [
        str(ffmpeg), "-y",
        "-i", str(src),
        "-an", "-vcodec", "copy", "-update", "1",
        str(dest),
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if should_stop and should_stop():
        return False
    return dest.is_file() and dest.stat().st_size > 0


def _image_mime(path: Path) -> str:
    return ("image/png" if path.suffix.lower() == ".png" else "image/jpeg")


def embed_cover(file: Path, cover: Path) -> bool:
    """用 mutagen 把封面嵌入音频文件（M4A covr / MP3 APIC / FLAC pictures）。"""
    try:
        with open(cover, "rb") as fh:
            data = fh.read()
        suffix = file.suffix.lower()
        if suffix == ".m4a":
            from mutagen.mp4 import MP4, MP4Cover

            audio = MP4(str(file))
            fmt = (MP4Cover.FORMAT_PNG if cover.suffix.lower() == ".png"
                   else MP4Cover.FORMAT_JPEG)
            audio.tags["covr"] = [MP4Cover(data, imageformat=fmt)]
            audio.save()
        elif suffix == ".mp3":
            from mutagen.id3 import APIC, ID3, ID3NoHeaderError

            try:
                audio = ID3(str(file))
            except ID3NoHeaderError:
                audio = ID3()
            audio.add(APIC(encoding=3, mime=_image_mime(cover), type=3,
                           desc="Cover", data=data))
            audio.save(str(file))
        elif suffix == ".flac":
            from mutagen.flac import FLAC, Picture

            picture = Picture()
            picture.type = 3
            picture.mime = _image_mime(cover)
            picture.data = data
            audio = FLAC(str(file))
            audio.clear_pictures()
            audio.add_picture(picture)
            audio.save()
        else:
            return False
        return True
    except Exception:  # noqa: BLE001 —— 封面嵌入失败不应中断转换
        return False


def embed_lyrics(file: Path, text: str) -> bool:
    """把歌词文本嵌入音频文件（M4A ©lyr / MP3 USLT / FLAC LYRICS 注释）。"""
    try:
        suffix = file.suffix.lower()
        if suffix == ".m4a":
            from mutagen.mp4 import MP4

            audio = MP4(str(file))
            audio.tags["©lyr"] = [text]
            audio.save()
        elif suffix == ".mp3":
            from mutagen.id3 import ID3, ID3NoHeaderError, USLT

            try:
                audio = ID3(str(file))
            except ID3NoHeaderError:
                audio = ID3()
            audio.add(USLT(encoding=3, lang="zho", desc="", text=text))
            audio.save(str(file))
        elif suffix == ".flac":
            from mutagen.flac import FLAC

            audio = FLAC(str(file))
            audio["LYRICS"] = text
            audio.save()
        else:
            return False
        return True
    except Exception:  # noqa: BLE001 —— 歌词嵌入失败不应中断转换
        return False
