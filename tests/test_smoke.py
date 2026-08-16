"""core 逻辑冒烟测试（标准库 unittest，无需 pytest）。

运行：python -m unittest discover -s tests -v
"""
import tempfile
import unittest
from pathlib import Path

from core.config import AppConfig, load_config, save_config
from core.engine import ConversionEngine
from core.models import FORMAT_SPECS, ConversionTask, FormatKind, TaskStatus


class TestModels(unittest.TestCase):
    def test_format_specs_complete(self):
        self.assertEqual(len(FORMAT_SPECS), 8)
        self.assertTrue(FORMAT_SPECS[FormatKind.MGG2M4A].needs_decrypt)
        self.assertTrue(FORMAT_SPECS[FormatKind.VIDEO2MP4].is_video)

    def test_task_roundtrip(self):
        task = ConversionTask(
            kind=FormatKind.FLAC2M4A,
            source=Path("/a/b.flac"),
            output=Path("/o/b.m4a"),
            status=TaskStatus.COMPLETED,
            progress=100.0,
        )
        restored = ConversionTask.from_dict(task.to_dict())
        self.assertEqual(restored.kind, task.kind)
        self.assertEqual(restored.status, task.status)


class TestConfig(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "config.json"
            cfg = AppConfig(input_dir="a", output_dir="b",
                            kinds=["flac2m4a", "mgg2m4a"], threads=8)
            save_config(cfg, path)
            loaded = load_config(path)
            self.assertEqual(loaded, cfg)

    def test_defaults_on_missing(self):
        with tempfile.TemporaryDirectory() as d:
            loaded = load_config(Path(d) / "nope.json")
            self.assertIsInstance(loaded, AppConfig)
            self.assertTrue(loaded.kinds)

    def test_bad_threads_fallback(self):
        cfg = AppConfig.from_dict({"threads": 0, "kinds": []})
        self.assertEqual(cfg.threads, 1)
        self.assertTrue(cfg.kinds)


class TestDiscover(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "in"
        self.src.mkdir()
        (self.src / "a.flac").write_bytes(b"fake-flac")
        (self.src / "b.ogg").write_bytes(b"fake-ogg")
        (self.src / "c.txt").write_text("not audio", encoding="utf-8")
        (self.src / "sub").mkdir()
        (self.src / "sub" / "d.wav").write_bytes(b"fake-wav")

    def tearDown(self):
        self.tmp.cleanup()

    def test_discover_flac_ogg(self):
        cfg = AppConfig(input_dir=str(self.src),
                        output_dir=str(self.root / "out"),
                        kinds=["flac2m4a", "ogg2m4a"])
        engine = ConversionEngine(cfg)
        tasks = engine.discover()
        self.assertEqual(len(tasks), 2)
        names = {t.source.name for t in tasks}
        self.assertEqual(names, {"a.flac", "b.ogg"})
        for t in tasks:
            self.assertEqual(t.output.suffix, ".m4a")

    def test_discover_recursive_video(self):
        cfg = AppConfig(input_dir=str(self.src),
                        output_dir=str(self.root / "out"),
                        kinds=["video2mp4"])
        engine = ConversionEngine(cfg)
        tasks = engine.discover()
        self.assertEqual(len(tasks), 0)  # 目录里没有视频文件

    def test_discover_skips_decrypt_kinds(self):
        cfg = AppConfig(input_dir=str(self.src),
                        output_dir=str(self.root / "out"),
                        kinds=["mgg2m4a"])
        engine = ConversionEngine(cfg)
        self.assertEqual(engine.discover(), [])

    def test_discover_missing_dir(self):
        cfg = AppConfig(input_dir=str(self.root / "missing"),
                        output_dir=str(self.root / "out"),
                        kinds=["flac2m4a"])
        engine = ConversionEngine(cfg)
        self.assertEqual(engine.discover(), [])


class TestEngineFlow(unittest.TestCase):
    """不依赖 ffmpeg 的流程测试：输出已存在时应跳过。"""

    def test_skip_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "in"
            src.mkdir()
            out = root / "out"
            out.mkdir()
            (src / "a.flac").write_bytes(b"x")
            output_file = out / "a.m4a"
            output_file.write_bytes(b"existing")
            cfg = AppConfig(input_dir=str(src), output_dir=str(out),
                            kinds=["flac2m4a"])
            engine = ConversionEngine(cfg)
            # 不调用 run()（需要 ffmpeg），直接验证 _convert_one 的跳过逻辑
            task = ConversionTask(kind=FormatKind.FLAC2M4A,
                                  source=src / "a.flac", output=output_file)
            engine._convert_one(task)
            self.assertEqual(task.status, TaskStatus.SKIPPED)
            self.assertIn("已存在", task.message)


if __name__ == "__main__":
    unittest.main()
