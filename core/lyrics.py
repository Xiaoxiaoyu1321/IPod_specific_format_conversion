"""歌词下载（QQ 音乐公开接口），可选的增强功能。"""
from __future__ import annotations

import json
import re
from typing import Optional

import requests

from .albumart import _HEADERS

LYRIC_URL = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"


def fetch_lyrics(title: str, artist: str, timeout: float = 10.0) -> Optional[str]:
    """按“歌名+歌手”搜索并返回 LRC 歌词文本；失败返回 None。"""
    query = f"{title} {artist}".strip()
    if not query:
        return None
    try:
        search_resp = requests.get(
            "https://c.y.qq.com/soso/fcgi-bin/client_search_cp",
            params={"w": query, "format": "json"},
            headers=_HEADERS,
            timeout=timeout,
        )
        search_resp.raise_for_status()
        song_list = (((search_resp.json().get("data") or {})
                      .get("song") or {}).get("list")) or []
        if not song_list:
            return None
        song_mid = song_list[0].get("songmid")
        if not song_mid:
            return None

        lyric_resp = requests.get(
            LYRIC_URL,
            params={"songmid": song_mid, "format": "json"},
            headers=_HEADERS,
            timeout=timeout,
        )
        lyric_resp.raise_for_status()
        # 接口返回的是被转义过的 JSON 字符串（含 \n），需二次解析
        raw = lyric_resp.text
        text = _extract_lyric_field(raw)
        return text or None
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def _extract_lyric_field(raw: str) -> str:
    """从响应中抽取 lyric 字段：兼容 `{"lyric": "..."}` 与 `lyric=...;` 两种形态。"""
    m = re.search(r'"lyric"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if m:
        try:
            return json.loads(f'"{m.group(1)}"')
        except json.JSONDecodeError:
            return m.group(1)
    m = re.search(r"lyric\s*=\s*'([^']*)'", raw)
    if m:
        return m.group(1)
    return ""
