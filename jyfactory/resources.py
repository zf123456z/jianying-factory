#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 剪映官方资源搜索引擎
按中文名字搜索剪映官方的滤镜、转场、特效、文字动画、音色
"""
import csv
import os
from typing import List, Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

CATEGORY_FILES = {
    "filter": "filters.csv", "filters": "filters.csv", "滤镜": "filters.csv",
    "transition": "transitions.csv", "transitions": "transitions.csv", "转场": "transitions.csv",
    "effect": "video_scene_effects.csv", "effects": "video_scene_effects.csv", "特效": "video_scene_effects.csv",
    "animation": "text_animations.csv", "animations": "text_animations.csv", "文字动画": "text_animations.csv",
    "tts": "tts_speakers.csv", "voice": "tts_speakers.csv", "音色": "tts_speakers.csv",
    "音效": "cloud_sound_effects.csv",
}


def search_assets(keyword: str, category: str = None, limit: int = 10) -> List[Dict]:
    results = []
    if category:
        files = []
        for key, fname in CATEGORY_FILES.items():
            if category.lower() in key.lower() or key in category:
                files.append(fname)
        if not files:
            files = [f"{category}.csv"]
    else:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    for fname in files:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("identifier") or row.get("speaker_id") or row.get("name_hint", "")
                desc = row.get("description", "")
                if keyword.lower() in name.lower() or keyword in desc:
                    row["match_name"] = name
                    row["source"] = fname
                    results.append(row)

    results.sort(key=lambda x: 0 if keyword in x.get("match_name", "") else 1)
    return results[:limit]


def list_categories():
    print("📚 剪映官方资源库：")
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        count = 0
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("#") and line.strip():
                    count += 1
        count -= 1
        print(f"  {fname:<35} {count:>5} 个")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        list_categories()
        sys.exit(0)
    keyword = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else None
    results = search_assets(keyword, category)
    print(f"🔍 搜索 '{keyword}' {'在'+category if category else ''} 找到 {len(results)} 个：")
    for r in results:
        name = r.get("match_name", "")
        cat = r.get("source", "").replace(".csv", "")
        print(f"  - {name:<25} [{cat}]")
