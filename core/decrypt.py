"""QQ 音乐加密文件（.mgg/.mflac）解密。

原理：通过 Frida 附加正在运行的 QQMusic.exe，调用 QQMusicCommon.dll 中
EncAndDesMediaFile 类的公开接口读取已解密的明文数据，写出为 .ogg/.flac。

本模块仅为学习交流使用，仅允许处理用户合法拥有版权的本地文件。
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Callable, Iterable, List, Optional

# .mgg → ogg，.mflac → flac
_TARGET_SUFFIX = {".mgg": ".ogg", ".mflac": ".flac"}


class DecryptError(RuntimeError):
    """解密流程失败。"""


class QQMusicDecryptor:
    def __init__(self, js_path: Path, process_name: str = "QQMusic.exe"):
        self.js_path = Path(js_path)
        self.process_name = process_name

    def decrypt_dir(
        self,
        src_dir: Path,
        out_dir: Path,
        exts: Iterable[str] = (".mgg", ".mflac"),
        progress_cb: Optional[Callable[[float], None]] = None,
        log_cb: Optional[Callable[[str], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        skip_existing: bool = True,
    ) -> List[Path]:
        """解密 src_dir（含子目录）下所有匹配后缀的文件。

        :return: 解密后文件的完整路径列表（位于 out_dir）
        """
        try:
            import frida
        except ImportError as exc:
            # 区分“未安装”与“导入失败”（如 frida 17.x 在 Python 3.9 上不兼容），
            # 把真实原因透传给用户，便于诊断
            raise DecryptError(
                f"frida 加载失败：{exc}。请确认安装了与当前 Python 兼容的 frida"
                "（Python 3.9 请使用 frida 16.x，见 requirements.txt）"
            ) from exc
        if not self.js_path.is_file():
            raise DecryptError(f"缺少 Frida 脚本：{self.js_path}")

        src_dir = Path(src_dir)
        if not src_dir.is_dir():
            raise DecryptError(f"源目录不存在：{src_dir}")

        exts = tuple(ext.lower() if ext.startswith(".") else "." + ext.lower()
                     for ext in exts)
        files = sorted(
            p for p in src_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in exts
        )
        if not files:
            if log_cb:
                log_cb("未找到待解密的 QQ 音乐文件")
            return []

        # 附加 QQ 音乐进程并注入脚本
        try:
            session = frida.attach(self.process_name)
        except Exception as exc:  # noqa: BLE001 —— frida 抛出的异常类型较多
            raise DecryptError(
                f"无法附加进程 {self.process_name}（请先启动 QQ 音乐）：{exc}"
            ) from exc

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        decrypted: List[Path] = []
        try:
            script = session.create_script(self.js_path.read_text(encoding="utf-8"))
            script.load()
            total = len(files)
            for idx, src in enumerate(files, 1):
                if should_stop and should_stop():
                    break
                target = out_dir / (src.stem + _TARGET_SUFFIX[src.suffix.lower()])
                if skip_existing and target.exists():
                    decrypted.append(target)
                    continue
                # 先写临时文件再原子改名，避免半成品
                tmp = out_dir / (hashlib.md5(str(src).encode()).hexdigest() + ".part")
                script.exports_sync.decrypt(str(src), str(tmp))
                os.replace(tmp, target)
                decrypted.append(target)
                if log_cb:
                    log_cb(f"解密完成：{src.name} → {target.name}")
                if progress_cb:
                    progress_cb(idx * 100.0 / total)
        except Exception as exc:  # noqa: BLE001 —— 统一包装为 DecryptError
            raise DecryptError(f"解密失败：{exc}") from exc
        finally:
            try:
                session.detach()
            except Exception:  # noqa: BLE001
                pass
        return decrypted
