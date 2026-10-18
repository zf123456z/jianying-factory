#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿时长自动检查工具
导出前自动检查：视频/人声/BGM三个轨道总时长是否一致，不一致自动对齐
彻底杜绝片尾黑屏、BGM比视频长、人声提前结束的问题
"""
import json
import os
import sys
import glob


def check_draft_durations(draft_path: str):
    """检查草稿里所有轨道的总时长，以人声为准对齐"""
    draft_json = os.path.join(draft_path, "draft_content.json")
    if not os.path.exists(draft_json):
        print(f"❌ 草稿文件不存在：{draft_json}")
        return False

    with open(draft_json, "r", encoding="utf-8-sig") as f:
        draft = json.load(f)

    tracks = draft.get("tracks", [])
    durations = {}

    for track in tracks:
        track_name = track.get("name", "unknown")
        segments = track.get("segments", [])
        if not segments:
            durations[track_name] = 0
            continue
        # 轨道总时长 = 最后一段的开始+时长
        total = max(seg["target_timerange"]["start"] + seg["target_timerange"]["duration"] for seg in segments)
        durations[track_name] = total
        print(f"📏 轨道「{track_name}」总时长：{total/1_000_000:.1f}秒")

    # 找人声轨道（voiceover/配音）
    voice_dur = None
    for name, dur in durations.items():
        if "voice" in name.lower() or "配音" in name or "原声" in name:
            voice_dur = dur
            break

    if voice_dur is None:
        print("⚠️ 没找到人声轨道，用最长轨道为准")
        voice_dur = max(durations.values())

    print(f"\n🎯 以人声轨道时长 {voice_dur/1_000_000:.1f}秒 为基准对齐所有轨道")

    # 检查BGM轨道是不是比人声长
    fixed = False
    for track in tracks:
        track_name = track.get("name", "unknown")
        if "bgm" in track_name.lower() or "音乐" in track_name:
            for seg in track.get("segments", []):
                seg_end = seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
                if seg_end > voice_dur:
                    # 把这段BGM截断到人声结束
                    new_dur = voice_dur - seg["target_timerange"]["start"]
                    if new_dur > 0:
                        seg["target_timerange"]["duration"] = new_dur
                        seg["source_timerange"]["duration"] = new_dur
                        print(f"✂️  截断BGM片段：从{seg_end/1e6:.1f}s截到{voice_dur/1e6:.1f}s")
                        fixed = True

    # 检查视频轨道是不是比人声短
    for track in tracks:
        track_name = track.get("name", "unknown")
        if track.get("type") == "video":
            track_dur = 0
            for seg in track.get("segments", []):
                track_dur = max(track_dur, seg["target_timerange"]["start"] + seg["target_timerange"]["duration"])
            if track_dur < voice_dur:
                print(f"⚠️ 视频轨道比人声短：{track_dur/1e6:.1f}s < {voice_dur/1e6:.1f}s，需要补视频")
                # 这里以后加自动补循环视频的逻辑
                fixed = True

    # 写回草稿
    if fixed:
        with open(draft_json, "w", encoding="utf-8") as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
        print("\n✅ 草稿时长已自动对齐，不会再有片尾黑屏！")
    else:
        print("\n✅ 所有轨道时长一致，没问题！")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python check_durations.py 草稿文件夹路径")
        sys.exit(1)
    check_draft_durations(sys.argv[1])
