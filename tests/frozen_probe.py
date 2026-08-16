"""PyInstaller 冻结路径探针（本地验证用，非测试套件成员）。

打包后运行，验证：
    1. PROJECT_ROOT 指向解压目录（_MEIPASS），内置资源可定位
    2. DATA_DIR 指向 exe 所在目录，config.json 可写入且持久
    3. FFmpegLocator 能找到内置的 ffmpeg / ffprobe
"""
import json
import os
import sys
from pathlib import Path

# 保证从任意位置（含 PyInstaller 分析）都能 import core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DATA_DIR, DEFAULT_CONFIG_PATH, PROJECT_ROOT, AppConfig
from core.engine import ConversionEngine
from core.ffmpeg import FFmpegLocator

print("== frozen 探针 ==")
print("FROZEN:", bool(getattr(sys, "frozen", False)))
print("PROJECT_ROOT:", PROJECT_ROOT)
print("DATA_DIR:", DATA_DIR)

# 1) config 应写入 DATA_DIR（可写、持久）
cfg = AppConfig(input_dir="x", output_dir="y")
DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
DEFAULT_CONFIG_PATH.write_text(json.dumps(cfg.to_dict()), encoding="utf-8")
print("config written:", DEFAULT_CONFIG_PATH)

# 2) 内置资源（Frida 脚本）应位于 PROJECT_ROOT
js = PROJECT_ROOT / "bin" / "decrypt-qm" / "hook_qq_music.js"
print("frida js exists:", js.is_file(), js)

# 3) locator 应找到内置 ffmpeg
ffmpeg, ffprobe = FFmpegLocator(cfg).locate()
print("ffmpeg:", ffmpeg)
print("ffprobe:", ffprobe)

# 4) 引擎可构建（工具定位懒加载）
engine = ConversionEngine(cfg)
print("engine ok:", type(engine).__name__)

ok = all([
    DEFAULT_CONFIG_PATH.is_file(),
    js.is_file(),
    ffmpeg.is_file(),
    ffprobe.is_file(),
])
print("RESULT:", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
