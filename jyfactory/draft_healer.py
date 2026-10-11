#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 工程自修复工具
自动检测损坏的剪映草稿，修复缺失字段，防止剪映打开崩溃
"""
import json
import os
import argparse


def auto_heal_draft(draft_path: str) -> bool:
    """自动修复损坏的剪映草稿"""
    content_file = os.path.join(draft_path, "draft_content.json")
    if not os.path.exists(content_file):
        print(f"❌ 找不到 {content_file}")
        return False

    try:
        with open(content_file, "r", encoding="utf-8") as f:
            draft = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ JSON损坏，无法修复")
        return False

    fixed = []

    required_materials = [
        "ai_translates", "audio_balances", "audio_effects", "audio_fades",
        "audio_track_indexes", "audios", "beats", "canvases", "chromas",
        "color_curves", "digital_humans", "drafts", "effects", "flowers",
        "green_screens", "handwrites", "hsl", "images", "log_color_wheels",
        "loudnesses", "manual_deformations", "masks", "material_animations",
        "material_colors", "multi_language_refs", "placeholders", "plugin_effects",
        "primary_color_wheels", "realtime_denoises", "shapes", "smart_crops",
        "smart_relights", "sound_channel_mappings", "speeds", "stickers",
        "tail_leaders", "text_templates", "texts", "time_marks", "transitions",
        "video_effects", "video_trackings", "videos", "vocal_beautifys", "vocal_separations"
    ]
    if "materials" not in draft:
        draft["materials"] = {}
        fixed.append("materials")

    for mat in required_materials:
        if mat not in draft["materials"]:
            draft["materials"][mat] = []
            fixed.append(f"materials.{mat}")

    required_config = [
        "adjust_max_index", "attachment_info", "combination_max_index",
        "export_range", "extract_audio_last_index", "lyrics_recognition_id",
        "lyrics_sync", "lyrics_taskinfo", "maintrack_adsorb", "material_save_mode",
        "multi_language_current", "multi_language_list", "multi_language_main",
        "multi_language_mode", "original_sound_last_index", "record_audio_last_index",
        "sticker_max_index", "subtitle_keywords_config", "subtitle_recognition_id",
        "subtitle_sync", "subtitle_taskinfo", "system_font_list", "video_mute", "zoom_info_params"
    ]
    if "config" not in draft:
        draft["config"] = {}
        fixed.append("config")

    for cfg in required_config:
        if cfg not in draft["config"]:
            draft["config"][cfg] = None
            fixed.append(f"config.{cfg}")

    if "tracks" not in draft:
        draft["tracks"] = []
        fixed.append("tracks")

    if "duration" not in draft:
        draft["duration"] = 60 * 1_000_000
        fixed.append("duration")

    if "canvas_config" not in draft:
        draft["canvas_config"] = {"width": 1080, "height": 1920, "ratio": "9:16"}
        fixed.append("canvas_config")

    if "platform" not in draft:
        draft["platform"] = {"app_id": 3704, "app_source": "lv", "app_version": "11.5.0", "os": "windows"}
        fixed.append("platform")

    if "last_modified_platform" not in draft:
        draft["last_modified_platform"] = {"app_id": 3704, "app_source": "lv", "app_version": "11.5.0", "os": "windows"}
        fixed.append("last_modified_platform")

    with open(content_file, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)

    if fixed:
        print(f"✅ 修复了 {len(fixed)} 个字段：")
        for f in fixed[:10]:
            print(f"  - {f}")
        if len(fixed) > 10:
            print(f"  ... 还有 {len(fixed)-10} 个")
    else:
        print("✅ 草稿结构完整，无需修复")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="剪映草稿自修复工具")
    parser.add_argument("draft_path", help="草稿目录路径")
    args = parser.parse_args()
    auto_heal_draft(args.draft_path)
