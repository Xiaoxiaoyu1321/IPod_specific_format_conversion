"""端到端测试：使用“假 ffmpeg/ffprobe”验证完整转换流程。

不依赖真实 ffmpeg：脚本模拟 ffmpeg 的 -progress 输出并生成目标文件，
ffprobe 返回固定 JSON 元数据。用于验证引擎的发现→探测→转换→回调链路。
"""
import os
import shutil
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from core.config import DATA_DIR, AppConfig
from core.engine import ConversionEngine
from core.models import ConversionTask, FormatKind, TaskStatus

FAKE_FFMPEG = """#!/usr/bin/env python3
import os, sys, time
args = sys.argv[1:]
out = args[-1]
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
sys.stdout.write("out_time_us=100000\\nprogress=continue\\n")
sys.stdout.flush()
time.sleep(0.02)
sys.stdout.write("progress=end\\n")
sys.stdout.flush()
open(out, "wb").close()
"""

FAKE_FFPROBE = """#!/usr/bin/env python3
import sys
print('{"streams":[{"codec_type":"audio","duration":"1.0",'
      '"tags":{"title":"测试歌曲","artist":"测试歌手"}}],'
      '"format":{"duration":"1.0","tags":{}}}')
"""


def make_fake_bins(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in (("ffmpeg", FAKE_FFMPEG), ("ffprobe", FAKE_FFPROBE)):
        path = directory / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)
    return directory


def make_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"".join(struct.pack("<hh", 0, 0) for _ in range(4410)))


# Windows 上无法执行无扩展名的假 ffmpeg 脚本，
# 由 GitHub Actions 中的真实打包产物冒烟启动测试覆盖。
@unittest.skipIf(os.name == "nt", "Windows 平台请通过打包产物冒烟测试验证")
class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin_dir = make_fake_bins(self.root / "bin")
        self.src = self.root / "in"
        self.src.mkdir()
        self.out = self.root / "out"
        self.out.mkdir()

    def tearDown(self):
        self.tmp.cleanup()
        # 清理引擎可能写入数据目录 temp/ 的中间文件
        shutil.rmtree(DATA_DIR / "temp", ignore_errors=True)

    def _engine(self, kinds, **kw) -> ConversionEngine:
        cfg = AppConfig(
            input_dir=str(self.src),
            output_dir=str(self.out),
            ffmpeg_dir=str(self.bin_dir),
            kinds=kinds,
            download_cover=False,
            **kw,
        )
        self.tasks_log = []
        return ConversionEngine(cfg, log_cb=lambda m: None,
                                task_cb=self.tasks_log.append)

    def test_wav_to_m4a_pipeline(self):
        make_wav(self.src / "tone.wav")
        engine = self._engine(["wav2m4a"])
        engine.run()
        self.assertTrue((self.out / "tone.m4a").exists())
        completed = [t for t in self.tasks_log
                     if t.status == TaskStatus.COMPLETED]
        self.assertTrue(completed, "应至少有一个完成的任务")
        self.assertEqual(completed[-1].source.name, "tone.wav")
        self.assertEqual(completed[-1].output.name, "tone.m4a")

    def test_flac_two_stage_pipeline(self):
        make_wav(self.src / "song.flac")  # 内容无关，仅验证流程
        engine = self._engine(["flac2m4a"])
        engine.run()
        self.assertTrue((self.out / "song.m4a").exists())
        self.assertTrue(any(t.status == TaskStatus.COMPLETED
                            for t in self.tasks_log))

    def test_skip_existing_in_run(self):
        make_wav(self.src / "old.wav")
        (self.out / "old.m4a").write_bytes(b"x")
        engine = self._engine(["wav2m4a"])
        engine.run()
        self.assertTrue(any(t.status == TaskStatus.SKIPPED
                            for t in self.tasks_log))

    def test_mp3_and_flac_targets(self):
        # 绕过解密，直接验证新目标格式的转换分支（mgg 解密产物为 ogg）
        make_wav(self.src / "a.ogg")
        make_wav(self.src / "b.flac")
        engine = self._engine([])
        engine._ensure_tools()  # run() 会自动调用，直接调 _convert_one 需手动
        tasks = [
            ConversionTask(kind=FormatKind.MGG2MP3,
                           source=self.src / "a.ogg",
                           output=self.out / "a.mp3"),
            ConversionTask(kind=FormatKind.MGG2FLAC,
                           source=self.src / "a.ogg",
                           output=self.out / "a.flac"),
            ConversionTask(kind=FormatKind.MFLAC2FLAC,
                           source=self.src / "b.flac",
                           output=self.out / "b.flac"),
        ]
        for task in tasks:
            engine._convert_one(task)
        self.assertTrue((self.out / "a.mp3").exists())
        self.assertTrue((self.out / "a.flac").exists())
        self.assertTrue((self.out / "b.flac").exists())
        # mflac→flac 为整文件复制，内容应一致
        self.assertEqual((self.out / "b.flac").read_bytes(),
                         (self.src / "b.flac").read_bytes())
        self.assertTrue(all(t.status == TaskStatus.COMPLETED for t in tasks))

    def test_decrypt_missing_src_dir_no_crash(self):
        # QQ 音乐目录不存在：应优雅失败，不中断引擎
        cfg = AppConfig(input_dir=str(self.root / "missing"),
                        output_dir=str(self.out),
                        ffmpeg_dir=str(self.bin_dir),
                        kinds=["mgg2m4a"])
        engine = ConversionEngine(cfg, log_cb=lambda m: None)
        engine.run()  # 不应抛异常

    def test_stop_request(self):
        make_wav(self.src / "a.wav")
        make_wav(self.src / "b.wav")
        engine = self._engine(["wav2m4a"])
        engine.stop()  # 预先停止：所有任务应被跳过
        engine.run()
        self.assertFalse(any(t.status == TaskStatus.COMPLETED
                             for t in self.tasks_log))


if __name__ == "__main__":
    unittest.main()
