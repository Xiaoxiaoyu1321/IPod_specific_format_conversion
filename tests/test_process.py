"""子进程静默执行 helper 测试。"""
import os
import sys
import unittest
from subprocess import PIPE

from core import process


class TestProcessHelper(unittest.TestCase):
    def test_create_no_window_value(self):
        # Windows 下应为 CREATE_NO_WINDOW（0x08000000）；其余平台为 0
        if os.name == "nt":
            self.assertEqual(process.CREATE_NO_WINDOW, 0x08000000)
        else:
            self.assertEqual(process.CREATE_NO_WINDOW, 0)

    def test_run_works(self):
        result = process.run(
            [sys.executable, "-c", "print('silent-ok')"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("silent-ok", result.stdout)

    def test_popen_works(self):
        proc = process.popen(
            [sys.executable, "-c", "print('popen-ok')"],
            stdout=PIPE, text=True,
        )
        out, _ = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("popen-ok", out)


if __name__ == "__main__":
    unittest.main()
