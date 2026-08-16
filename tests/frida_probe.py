"""打包后 frida 可用性探针（本地验证用）。

验证 PyInstaller 能否正确收集并加载 frida（含其原生扩展）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import frida
    print("frida import OK, version:", frida.__version__)
    print("frida __file__:", frida.__file__)
    print("_frida:", frida._frida.__file__)
except Exception as exc:  # noqa: BLE001
    print("frida import FAILED:", type(exc).__name__, exc)
    sys.exit(1)

# 进一步验证原生模块可实例化（attach 会失败，但类型应存在）
try:
    mgr = frida.get_device_manager()
    print("device manager OK:", type(mgr).__name__)
except Exception as exc:  # noqa: BLE001
    print("device manager FAILED:", type(exc).__name__, exc)
    sys.exit(1)

print("FRIDA PROBE OK")
sys.exit(0)
