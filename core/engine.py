"""转换引擎：任务发现、QQ 音乐解密、格式转换、封面/歌词增强与清理。

引擎不依赖 GUI，通过回调（log_cb / task_cb）对外汇报进度，
GUI 与 CLI 分别以信号/print 订阅这些回调。
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, List, Optional

from . import albumart, lyrics, metadata
from .config import DATA_DIR, PROJECT_ROOT
from .converter import ConversionError, Converter
from .decrypt import QQMusicDecryptor
from .ffmpeg import FFmpegError, FFmpegLocator
from .logger import Logger
from .models import (
    FORMAT_SPECS, ConversionTask, FormatKind, TaskStatus,
)

# 需要先解密再转换的类型
_DECRYPT_KINDS = (FormatKind.MGG2M4A, FormatKind.MFLAC2M4A)

# 临时目录（打包后位于 exe 旁，可写且持久）
_TEMP_ROOT = DATA_DIR / "temp"
_WAV_TEMP = _TEMP_ROOT / "wav"
_PIC_TEMP = _TEMP_ROOT / "pic"
_DE_TEMP = _TEMP_ROOT / "decrypted"


class ConversionEngine:
    def __init__(
        self,
        config,
        log_cb: Optional[Callable[[str], None]] = None,
        task_cb: Optional[Callable[[ConversionTask], None]] = None,
    ):
        self.config = config
        self.log = Logger()
        if log_cb:
            self.log.add_handler(log_cb)
        self.task_cb = task_cb
        self._stop = threading.Event()
        self._ffmpeg: Optional[Path] = None
        self._ffprobe: Optional[Path] = None
        self._converter: Optional[Converter] = None
        self.locator = FFmpegLocator(config)

    # ---- 对外控制 ----
    def stop(self) -> None:
        """请求停止：当前 ffmpeg 进程会被终止，循环在检查点退出。"""
        self._stop.set()

    def reset(self) -> None:
        self._stop.clear()

    # ---- 工具准备 ----
    def _ensure_tools(self) -> None:
        if self._ffmpeg is None:
            self._ffmpeg, self._ffprobe = self.locator.locate()
            self._converter = Converter(self._ffmpeg, self._ffprobe,
                                        self.config.threads)

    # ---- 任务发现 ----
    def discover(self) -> List[ConversionTask]:
        """根据配置扫描输入目录，生成普通转换任务（解密类任务由 run 特殊处理）。"""
        tasks: List[ConversionTask] = []
        seen: set = set()
        input_dir = Path(self.config.input_dir)
        if not input_dir.is_dir():
            self.log.warning(f"输入目录不存在：{input_dir}")
            return tasks
        for kind_value in self.config.kinds:
            kind = FormatKind(kind_value)
            spec = FORMAT_SPECS[kind]
            if spec.needs_decrypt:
                continue
            for src in sorted(input_dir.rglob("*")):
                if not src.is_file() or src.suffix.lower() not in spec.source_exts:
                    continue
                if src in seen:
                    continue
                seen.add(src)
                tasks.append(ConversionTask(
                    kind=kind,
                    source=src,
                    output=Path(self.config.output_dir) / (src.stem + spec.target_ext),
                ))
        return tasks

    # ---- 主流程 ----
    def run(self, tasks: Optional[List[ConversionTask]] = None) -> None:
        """执行全部转换。tasks 为空时自动调用 discover()。"""
        self._ensure_tools()
        if tasks is None:
            tasks = self.discover()

        # 解密类任务不走 discover，单独处理
        decrypt_kinds = [k for k in _DECRYPT_KINDS if k.value in self.config.kinds]
        normal_tasks = [t for t in tasks if t.kind not in decrypt_kinds]

        if decrypt_kinds:
            decrypted = self._run_decrypt()
            for path in decrypted:
                kind = (FormatKind.MGG2M4A if path.suffix.lower() == ".ogg"
                        else FormatKind.MFLAC2M4A)
                normal_tasks.append(ConversionTask(
                    kind=kind,
                    source=path,
                    output=Path(self.config.output_dir) / (path.stem + ".m4a"),
                ))

        if not normal_tasks:
            self.log.warning("没有找到可转换的文件，请检查输入目录与所选格式")
            return

        self.log.info(f"共 {len(normal_tasks)} 个任务开始处理")
        for task in normal_tasks:
            if self._stop.is_set():
                self.log.warning("收到停止请求，剩余任务已跳过")
                break
            self._convert_one(task)
        self.log.info("全部任务处理完毕")

    # ---- QQ 音乐解密 ----
    def _run_decrypt(self) -> List[Path]:
        src_dir = Path(self.config.qq_music_dir or self.config.input_dir)
        exts = [FORMAT_SPECS[k].source_exts[0]
                for k in _DECRYPT_KINDS if k.value in self.config.kinds]
        decryptor = QQMusicDecryptor(
            PROJECT_ROOT / "bin" / "decrypt-qm" / "hook_qq_music.js",
            self.config.process_name,
        )
        batch = ConversionTask(
            kind=_DECRYPT_KINDS[0],
            source=src_dir,
            output=_DE_TEMP,
            status=TaskStatus.DECRYPTING,
        )
        self._emit_task(batch)
        self.log.info(f"开始解密 {src_dir} 中的 QQ 音乐文件…")

        def on_progress(pct: float) -> None:
            batch.progress = pct
            self._emit_task(batch)

        try:
            decrypted = decryptor.decrypt_dir(
                src_dir, _DE_TEMP, exts,
                progress_cb=on_progress,
                log_cb=self.log.info,
                should_stop=self._stop.is_set,
            )
        except Exception as exc:  # noqa: BLE001 —— 解密失败不应阻断普通转换
            batch.status = TaskStatus.FAILED
            batch.message = str(exc)
            self._emit_task(batch)
            self.log.error(f"解密失败：{exc}")
            return []
        batch.status = TaskStatus.COMPLETED
        batch.progress = 100.0
        self._emit_task(batch)
        return decrypted

    # ---- 单任务转换 ----
    def _convert_one(self, task: ConversionTask) -> None:
        if task.output.exists():
            task.status = TaskStatus.SKIPPED
            task.message = "输出文件已存在"
            self._emit_task(task)
            self.log.info(f"跳过 {task.name}（输出已存在）")
            return

        task.status = TaskStatus.CONVERTING
        task.progress = 0.0
        task.message = ""
        self._emit_task(task)
        self.log.info(f"开始转换：{task.name}")

        try:
            if FORMAT_SPECS[task.kind].is_video:
                self._convert_video(task)
            else:
                self._convert_audio(task)
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            task.message = ""
            self.log.info(f"完成：{task.name} → {task.output.name}")
        except ConversionError as exc:
            task.status = TaskStatus.FAILED
            task.message = str(exc)
            self.log.error(f"转换失败 {task.name}：{exc}")
        except Exception as exc:  # noqa: BLE001 —— 兜底，避免单个文件拖垮整体
            task.status = TaskStatus.FAILED
            task.message = str(exc)
            self.log.error(f"转换失败 {task.name}：{exc}")
        finally:
            self._emit_task(task)

    def _convert_video(self, task: ConversionTask) -> None:
        duration = metadata.duration_sec(metadata.probe(self._ffprobe, task.source))
        if task.kind == FormatKind.VIDEO2MP4:
            self._converter.to_video_mp4(
                task.source, task.output, duration,
                lambda p: self._set_progress(task, p),
                self._stop.is_set,
            )
        else:
            self._converter.to_video_mpg(
                task.source, task.output, duration,
                lambda p: self._set_progress(task, p),
                self._stop.is_set,
            )

    def _convert_audio(self, task: ConversionTask) -> None:
        src = task.source
        probe_data = metadata.probe(self._ffprobe, src)
        tags = metadata.collect_tags(probe_data)
        duration = metadata.duration_sec(probe_data)

        # 1) 封面：先尝试从源文件提取，失败且允许联网时再搜索下载
        cover = self._prepare_cover(task, tags)

        # 2) 转换
        if task.kind == FormatKind.OGG2MP3:
            self._converter.to_mp3(
                src, task.output, tags, duration,
                lambda p: self._set_progress(task, p),
                self._stop.is_set,
            )
        else:
            self._convert_to_m4a(task, src, tags, duration)

        # 3) 嵌入封面
        if cover and task.output.suffix.lower() == ".m4a":
            task.status = TaskStatus.EMBEDDING
            task.progress = 100.0
            self._emit_task(task)
            if metadata.embed_cover(task.output, cover):
                self.log.info(f"封面已嵌入：{task.output.name}")
            else:
                self.log.warning(f"封面嵌入失败：{task.output.name}")

        # 4) 歌词（可选）
        if self.config.download_lyrics and task.output.suffix.lower() == ".m4a":
            self._fetch_lyrics(task, tags)

        # 5) 清理临时文件
        self._cleanup(task, cover)

    def _convert_to_m4a(self, task: ConversionTask, src: Path,
                        tags: dict, duration: Optional[float]) -> None:
        """音频 → M4A：非 WAV 源先转 1411Kbps WAV 中间格式再转 ALAC。"""
        if src.suffix.lower() == ".wav":
            self._converter.to_m4a(
                src, task.output, tags, duration,
                lambda p: self._set_progress(task, p),
                self._stop.is_set,
            )
            return
        # 两段式：wav（0-60%）→ alac（60-100%）
        wav = _WAV_TEMP / (src.stem + ".wav")
        wav.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._converter.to_wav(
                src, wav, duration,
                lambda p: self._set_progress(task, p * 0.6),
                self._stop.is_set,
            )
            wav_duration = metadata.duration_sec(metadata.probe(self._ffprobe, wav))
            self._converter.to_m4a(
                wav, task.output, tags, wav_duration,
                lambda p: self._set_progress(task, 60 + p * 0.4),
                self._stop.is_set,
            )
        finally:
            if not self.config.keep_temp and wav.exists():
                try:
                    wav.unlink()
                except OSError:
                    pass

    # ---- 辅助 ----
    def _prepare_cover(self, task: ConversionTask, tags: dict) -> Optional[Path]:
        if task.kind == FormatKind.OGG2MP3:
            return None  # MP3 封面嵌入暂不支持，保持与旧版一致
        pic_dir = _PIC_TEMP
        pic_dir.mkdir(parents=True, exist_ok=True)
        pic_file = pic_dir / (task.source.stem + ".jpg")
        if metadata.extract_cover(self._ffmpeg, task.source, pic_file,
                                  self._stop.is_set):
            return pic_file
        if pic_file.exists():
            pic_file.unlink()
        if self.config.download_cover:
            url = albumart.search_album_art_url(
                tags.get("title", ""), tags.get("artist", ""))
            if url and albumart.download_album_art(url, pic_file):
                self.log.info(f"已下载封面：{task.source.stem}")
                return pic_file
        return None

    def _fetch_lyrics(self, task: ConversionTask, tags: dict) -> None:
        text = lyrics.fetch_lyrics(tags.get("title", ""), tags.get("artist", ""))
        if not text:
            self.log.info(f"未找到歌词：{task.source.stem}")
            return
        out = task.output.with_suffix(".lrc")
        try:
            out.write_text(text, encoding="utf-8")
            self.log.info(f"歌词已保存：{out.name}")
        except OSError as exc:
            self.log.warning(f"歌词保存失败：{exc}")

    def _cleanup(self, task: ConversionTask, cover: Optional[Path]) -> None:
        if not self.config.keep_temp_pic and cover and cover.parent == _PIC_TEMP:
            try:
                cover.unlink()
            except OSError:
                pass

    def _set_progress(self, task: ConversionTask, pct: float) -> None:
        task.progress = round(max(0.0, min(100.0, pct)), 1)
        self._emit_task(task)

    def _emit_task(self, task: ConversionTask) -> None:
        if self.task_cb:
            try:
                self.task_cb(task)
            except Exception:  # noqa: BLE001
                pass
