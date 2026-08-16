#!/usr/bin/env python3
"""无 GUI 的核心命令行入口（类似 Clash 的 core 独立运行方式）。

示例：
    python main_cli.py -i ~/Music/in -o ~/Music/out -f flac2m4a -f ogg2mp3
    python main_cli.py -i ~/QQMusic -o ~/Music/out -f mgg2m4a --qq-music-dir ~/QQMusic
"""
import argparse
import sys

from core.config import AppConfig, load_config, save_config
from core.engine import ConversionEngine
from core.models import FormatKind


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipod-converter",
        description="IPod 格式转换核心（无 GUI）",
    )
    parser.add_argument("-i", "--input", help="输入目录")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument(
        "-f", "--format", action="append", dest="formats",
        choices=[k.value for k in FormatKind],
        help="转换类型（可多次指定）",
    )
    parser.add_argument("--qq-music-dir", help="QQ 音乐下载目录（mgg/mflac 解密源）")
    parser.add_argument("--ffmpeg-dir", help="ffmpeg 所在目录")
    parser.add_argument("--threads", type=int, help="ffmpeg 线程数")
    parser.add_argument("--keep-temp", action="store_true", help="保留中间缓存")
    parser.add_argument("--keep-pic", action="store_true", help="保留封面缓存")
    parser.add_argument("--no-cover", action="store_true", help="不自动下载封面")
    parser.add_argument("--lyrics", action="store_true", help="自动下载歌词")
    parser.add_argument("--config", help="配置文件路径（默认 config.json）")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    config = load_config(args.config) if args.config else load_config()
    if args.input:
        config.input_dir = args.input
    if args.output:
        config.output_dir = args.output
    if args.qq_music_dir:
        config.qq_music_dir = args.qq_music_dir
    if args.ffmpeg_dir:
        config.ffmpeg_dir = args.ffmpeg_dir
    if args.formats:
        config.kinds = args.formats
    if args.threads:
        config.threads = args.threads
    if args.keep_temp:
        config.keep_temp = True
    if args.keep_pic:
        config.keep_temp_pic = True
    if args.no_cover:
        config.download_cover = False
    if args.lyrics:
        config.download_lyrics = True

    if not config.input_dir or not config.output_dir:
        print("[Error] 必须提供输入目录与输出目录（-i / -o）")
        return 2
    if not config.kinds:
        print("[Error] 至少指定一种转换类型（-f）")
        return 2

    save_config(config, args.config) if args.config else save_config(config)

    engine = ConversionEngine(config, log_cb=print)
    try:
        engine.run()
    except Exception as exc:  # noqa: BLE001 —— CLI 层统一收口错误
        print(f"[Error] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
