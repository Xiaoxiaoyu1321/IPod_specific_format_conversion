"""专辑封面：通过 QQ 音乐公开搜索接口查找并下载封面图。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests

SEARCH_URL = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
_HEADERS = {
    "Referer": "https://y.qq.com/portal/player.html",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
}


def search_album_art_url(title: str, artist: str, timeout: float = 10.0) -> Optional[str]:
    """按“歌名+歌手”搜索，返回 300x300 封面 URL；失败返回 None。"""
    query = f"{title} {artist}".strip()
    if not query:
        return None
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"w": query, "format": "json"},
            headers=_HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        song_list = ((data.get("data") or {}).get("song") or {}).get("list") or []
        if not song_list:
            return None
        album_mid = song_list[0].get("albummid")
        if not album_mid:
            return None
        return f"https://y.qq.com/music/photo_new/T002R300x300M000{album_mid}.jpg"
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def download_album_art(url: str, dest: Path, timeout: float = 30.0) -> bool:
    """下载封面到 dest；成功且文件非空返回 True。"""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return dest.is_file() and dest.stat().st_size > 0
    except (requests.RequestException, OSError):
        return False
