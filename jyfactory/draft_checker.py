#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 草稿检查工具
读草稿JSON，自动检查问题
"""

import json
from . import config
import os
import sys

DRAFT_DIR = config.DRAFT_DIR


def check_draft(draft_name: str):
    """检查草稿"""
    draft_path = os.path.join(DRAFT_DIR, draft_name, "draft_content.json")

    if not os.path.exists(draft_path):
        print(f"❌ 草稿不存在：{draft_name}")
        return

    with open(draft_path, "r", encoding="utf-8") as f:
        draft = json.load(f)

    print(f"=" * 60)
    print(f"🔍 检查草稿：{draft_name}")
    print(f"=" * 60)

    total_dur = draft.get("duration", 0) / 1_000_000
    print(f"✅ 总时长：{total_dur:.1f} 秒")

    tracks = draft.get("tracks", [])
    issues = []

    for track in tracks:
        track_type = track.get("type", "unknown")
        segments = track.get("segments", [])
        track_dur = 0
        for seg in segments:
            tr = seg.get("target_timerange", {})
            track_dur += tr.get("duration", 0)
        track_dur_sec = track_dur / 1_000_000
        print(f"\n📁 {track_type} 轨道：{len(segments)} 段，总时长 {track_dur_sec:.1f} 秒")
        if abs(track_dur - total_dur * 1_000_000) > 1_000_000:
            issues.append(f"⚠️ {track_type}轨道时长 {track_dur_sec:.1f}s 和总时长 {total_dur:.1f}s 差了 {abs(track_dur_sec - total_dur):.1f}s")

    print(f"\n" + "=" * 60)
    if issues:
        print(f"❌ 发现 {len(issues)} 个问题：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✅ 所有轨道时长一致，没有问题！")
    print("=" * 60)
    return issues


if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_draft(sys.argv[1])
    else:
        drafts = [d for d in os.listdir(DRAFT_DIR) if os.path.isdir(os.path.join(DRAFT_DIR, d))]
        print("本地草稿列表：")
        for i, d in enumerate(drafts, 1):
            print(f"  {i}. {d}")
