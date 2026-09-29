#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 剪映官方曲库音乐桥接器（v7.7）
================================================================
核心理念（用户定调）：我们能控制剪映，剪映曲库音乐全部正版授权，用它不侵权。
技术闭环（2026-09-29 实测验证）：
  剪映曲库歌曲在 GUI 搜索/预览/下载后，会以完整 mp3 落盘到本地缓存：
    %LOCALAPPDATA%\\JianyingPro\\User Data\\Cache\\music\\<hash>.mp3
  实测：131 个缓存文件，其中包含 151s/128kbps 完整歌曲（短视频 BGM 标准音质）。
  因此「云端音乐直调」= GUI 触发下载一次 → 缓存桥接器扫描选歌 → 引擎直接混音，
  全程正版、零 GUI 添加按钮依赖（剪映 11.5 的添加按钮交互不稳定，不赌它）。

用法：
    from jianying_music_bridge import JianyingMusicBridge
    bridge = JianyingMusicBridge()
    songs = bridge.scan()            # 扫描曲库缓存，返回完整歌曲列表
    best = bridge.pick("科技", prefer_latest=True)   # 按关键词/时长/最新选歌
    print(best["path"])              # 引擎直接用它做 BGM

缓存路径可配置（CACHE_DIRS），支持多用户/多安装目录扫描。
"""
import os
import glob
import time
import subprocess
from typing import List, Optional, Dict


class JianyingMusicBridge:
    # 剪映曲库音乐缓存目录（实测位置）；%LOCALAPPDATA% 自动展开，可追加多路径
    CACHE_DIRS = [
        os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Cache\music"),
        r"D:\JianyingPro\User Data\Cache\music",
    ]

    def __init__(self, min_duration_s: float = 30.0):
        self.min_duration_s = min_duration_s

    def _probe_duration(self, path: str) -> Optional[float]:
        """ffprobe 读时长（秒），失败返回 None"""
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
        """扫描曲库缓存，返回完整歌曲（时长≥min_duration_s，按最近修改排序）"""
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
                    continue  # 跳过按钮音效等短片段
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
        """选歌：按最近修改优先（=最近下载的曲库歌）；
        可给关键词做文件名弱匹配（缓存是 hash 名，命中率有限，主要靠最新排序）；
        max_duration_s 可限定不超过某时长（避免歌比视频长太多）。
        """
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
