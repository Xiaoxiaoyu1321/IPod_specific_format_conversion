"""封面/歌词嵌入测试：使用合成的 PNG 与最小 MP3/FLAC 文件，无需 ffmpeg。"""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from core import metadata


def make_png(path: Path) -> None:
    """生成 1x1 红色 PNG。"""
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = chunk(b"IEND", b"")
    path.write_bytes(sig + ihdr + idat + iend)


def make_min_flac(path: Path) -> None:
    """生成含合法 STREAMINFO 的最小 FLAC 文件（无音频帧）。"""
    si = struct.pack(">HH", 4096, 4096)                    # min/max blocksize
    si += b"\x00\x00\x00" + b"\x00\x00\x00"                # min/max framesize
    sr, ch, bps, total = 44100, 2, 16, 0
    si += struct.pack(">Q", (sr << 44) | (ch << 41) | (bps << 36) | total)
    si += b"\x00" * 16                                     # MD5
    header = bytes([0x80]) + len(si).to_bytes(3, "big")    # last-block + STREAMINFO
    path.write_bytes(b"fLaC" + header + si)


class TestCoverEmbedding(unittest.TestCase):
    def test_embed_cover_mp3(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            mp3 = root / "t.mp3"
            mp3.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00")
            cover = root / "c.png"
            make_png(cover)

            self.assertTrue(metadata.embed_cover(mp3, cover))

            from mutagen.id3 import ID3
            tags = ID3(str(mp3))
            apic = tags.get("APIC:Cover")
            self.assertIsNotNone(apic, "MP3 应包含 APIC 封面帧")
            self.assertEqual(apic.mime, "image/png")

    def test_embed_cover_flac(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            flac = root / "t.flac"
            make_min_flac(flac)
            cover = root / "c.png"
            make_png(cover)

            self.assertTrue(metadata.embed_cover(flac, cover))

            from mutagen.flac import FLAC
            audio = FLAC(str(flac))
            self.assertEqual(len(audio.pictures), 1, "FLAC 应包含 1 张封面图")
            self.assertEqual(audio.pictures[0].mime, "image/png")


class TestLyricsEmbedding(unittest.TestCase):
    LYRICS = "[00:00.00]测试歌词"

    def test_embed_lyrics_mp3(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            mp3 = root / "t.mp3"
            mp3.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00")

            self.assertTrue(metadata.embed_lyrics(mp3, self.LYRICS))

            from mutagen.id3 import ID3
            tags = ID3(str(mp3))
            uslt = tags.getall("USLT")
            self.assertTrue(uslt, "MP3 应包含 USLT 歌词帧")
            self.assertEqual(uslt[0].text, self.LYRICS)

    def test_embed_lyrics_flac(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            flac = root / "t.flac"
            make_min_flac(flac)

            self.assertTrue(metadata.embed_lyrics(flac, self.LYRICS))

            from mutagen.flac import FLAC
            audio = FLAC(str(flac))
            # mutagen 的 VorbisComment 值以列表形式返回
            self.assertEqual(audio.get("LYRICS"), [self.LYRICS])


if __name__ == "__main__":
    unittest.main()
