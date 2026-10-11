#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 剪映官方曲库音乐桥接器（v7.7，v8 起由 jyfactory/media.py 取代）
================================================================
核心：剪映曲库音乐全部正版授权，缓存扫描选歌，引擎直接混音，全程正版零侵权。
缓存路径可配置（CACHE_DIRS），支持多用户/多安装目录扫描。
"""
import os
import glob
import time
import subprocess
from typing import List, Optional, Dict


class JianyingMusicBridge:
    CACHE_DIRS = [
        r"C:\Users\HuaWei\AppData\Local\JianyingPro\User Data\Cache\music",
        r"D:\JianyingPro\User Data\Cache\music",
    ]

    def __init__(self, min_duration_s: float = 30.0):
        self.min_duration_s = min_duration_s

    def _probe_duration(self, path: str) -> Optional[float]:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", path],
                capture_output=True, text=True, timeout=15,
            ).stdout.strip()
            return float(out) if out else None
        except Exception:
            return None

    def scan(self) -> List[Dict]:
        songs = []
        seen = set()
        for d in self.CACHE_DIRS:
            if not os.path.isdir(d):
                continue
            for p in glob.glob(os.path.join(d, "*.mp3")):
                if p in seen:
                    continue
                seen.add(p)
                dur = self._probe_duration(p)
                if dur is None or dur < self.min_duration_s:
                    continue
                songs.append({
                    "path": p,
                    "duration_s": round(dur, 1),
                    "mtime": os.path.getmtime(p),
                    "size_mb": round(os.path.getsize(p) / 1048576, 2),
                })
        songs.sort(key=lambda s: s["mtime"], reverse=True)
        return songs

    def pick(self, keyword: str = "", prefer_latest: bool = True,
             max_duration_s: Optional[float] = None) -> Optional[Dict]:
        songs = self.scan()
        if not songs:
            return None
        if max_duration_s:
            songs = [s for s in songs if s["duration_s"] <= max_duration_s]
            if not songs:
                return None
        if keyword:
            for s in songs:
                name = os.path.basename(s["path"]).lower()
                if keyword.lower() in name:
                    return s
        return songs[0] if prefer_latest else songs[0]

    def list_songs(self, limit: int = 10) -> str:
        songs = self.scan()
        if not songs:
            return "（剪映曲库缓存暂无完整歌曲，先在剪映音乐库搜索/预览一首）"
        lines = []
        for i, s in enumerate(songs[:limit]):
            t = time.strftime("%m-%d %H:%M", time.localtime(s["mtime"]))
            lines.append(f"{i+1}. {s['duration_s']}s/{s['size_mb']}MB [{t}] {os.path.basename(s['path'])}")
        return "\n".join(lines)


if __name__ == "__main__":
    bridge = JianyingMusicBridge()
    print(bridge.list_songs())
