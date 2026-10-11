#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 热点引流混剪引擎（v7.5 新模板）
================================================================
做抖音「热点引流 + 项目广告」混剪短视频：
  上部：热点话题标题文字（逐条出现，黄字黑边爆款款）
  中部：多个视频素材混剪（全网热点素材 + 公司/项目素材）
  下部：公司/项目广告文字（常驻全片）
  音频：BGM 铺满（可选配音）

版式（竖屏 1080x1920）：
  - 上部标题区  transform_y ≈ -0.60（上 1/4，不挡人脸）
  - 下部广告区  transform_y ≈ +0.60 ~ +0.85（下 1/4，常驻）
  - 中部素材区  0.25 ~ 0.75 画面（素材全屏，标题/广告浮于其上）

横屏素材自动竖屏化（scale 放大 + 中心裁剪），杜绝黑边/变形/条纹。
"""
import os
from . import config
import re
import sys
import time
import hashlib
import shutil
import json
import subprocess
from typing import List, Optional, Tuple

ENGINE_DIR = r"D:\AI工作区\代码"
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
from ._engine_v2_legacy import (
    sanitize_project_name, safe_draft_dir, backup_existing_draft,
    stage_material, normalize_video_for_jianying,
    DRAFT_ROOT, CANVAS_W, CANVAS_H, FPS,
)
import pyJianYingDraft as jy
from pyJianYingDraft import (
    DraftFolder, TrackSpec, TrackType,
    VideoMaterial, VideoSegment, AudioMaterial, AudioSegment,
    TextSegment, TextStyle, TextBorder, TextBackground, ClipSettings,
    trange,
)


def stable_material_id_public(media_path: str) -> str:
    stem = os.path.splitext(os.path.basename(media_path))[0]
    digest = hashlib.md5(stem.encode("utf-8")).hexdigest()[:24]
    return f"lm_{digest}"


def portraitize_video(video_path: str, draft_dir: str) -> str:
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", video_path],
            capture_output=True, text=True, encoding="utf-8", errors="ignore")
        streams = json.loads(proc.stdout or "{}").get("streams", [])
        w, h = int(streams[0]["width"]), int(streams[0]["height"])
    except Exception:
        w, h = 0, 0
    if h >= w:
        return normalize_video_for_jianying(video_path, draft_dir)

    materials_dir = os.path.join(draft_dir, "materials")
    os.makedirs(materials_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(video_path))[0]
    dst = os.path.join(materials_dir, f"{stem}.__jy_portrait__.mp4")
    if os.path.exists(dst):
        return dst
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", video_path,
        "-map", "0:v:0", "-map", "0:a?",
        "-vf", (f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
                f"crop={CANVAS_W}:{CANVAS_H}"),
        "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        dst,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"❌ 竖屏化失败（{e}），用原片")
        return video_path
    if proc.returncode != 0 or not os.path.exists(dst):
        print(f"❌ 竖屏化失败（ffmpeg={proc.returncode}），用原片")
        return video_path
    print(f"✅ 横屏素材已竖屏化：{dst}")
    return dst


def probe_duration(path: str) -> float:
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return float(proc.stdout.strip())
    except Exception:
        return 0.0


def make_hotspot_mix_draft(
    name: str,
    video_list: List[str],
    title_lines: List[str],
    ad_lines: List[str],
    bgm_path: Optional[str] = None,
    total_duration_s: float = 40.0,
    title_seconds: float = 4.0,
    bgm_volume: Optional[float] = None,
    voiceover_path: Optional[str] = None,
):
    name = sanitize_project_name(name)
    if bgm_volume is None:
        bgm_volume = 0.35

    print(f"🚀 热点引流混剪开始：{name}（{total_duration_s:.0f}s，{len(video_list)}段素材，{len(title_lines)}条标题）")
    folder = DraftFolder(DRAFT_ROOT)
    draft_dir = safe_draft_dir(name)
    if os.path.exists(draft_dir):
        backup_existing_draft(draft_dir)

    proj = None
    for attempt in range(3):
        try:
            proj = folder.create_draft(name, width=CANVAS_W, height=CANVAS_H, fps=FPS, allow_replace=True)
            break
        except PermissionError:
            print(f"⚠️ 草稿被剪映占用，2秒后重试（第{attempt+1}次）")
            time.sleep(2)
    if not proj:
        raise Exception("草稿创建失败，请先关闭剪映中正在编辑的同名草稿")

    proj.append_track(TrackSpec(TrackType.video, "MainVideo"))
    proj.append_track(TrackSpec(TrackType.text, "TextTitle"))
    proj.append_track(TrackSpec(TrackType.text, "TextAd"))
    proj.append_track(TrackSpec(TrackType.audio, "Voice"))
    proj.append_track(TrackSpec(TrackType.audio, "BGM"))

    total_us = int(total_duration_s * 1_000_000)

    print("✅ 1/4 混剪素材（竖屏化+自包含+强制静音原片）")
    seg_plan: List[Tuple[str, float]] = []
    remain = total_duration_s
    for vp in video_list:
        if not vp or not os.path.exists(vp):
            print(f"⚠️ 素材不存在，跳过：{vp}")
            continue
        vp_ok = portraitize_video(vp, draft_dir)
        dur = probe_duration(vp_ok) or 0.0
        take = min(dur, remain) if remain > 0 else 0.0
        if take > 0.5:
            seg_plan.append((vp_ok, take))
            remain -= take
        if remain <= 0:
            break
    if not seg_plan:
        raise Exception("没有任何可用素材")
    if remain > 0:
        print(f"⚠️ 素材总长不足，循环补足剩余 {remain:.1f}s")
        while remain > 0:
            for vp_ok, dur in [(p, probe_duration(p)) for p, _ in seg_plan]:
                take = min(dur, remain)
                if take > 0.5:
                    seg_plan.append((vp_ok, take))
                    remain -= take
                if remain <= 0:
                    break

    start = 0
    for idx, (vp_ok, take) in enumerate(seg_plan):
        seg_us = int(take * 1_000_000)
        staged = stage_material(vp_ok, draft_dir)
        mat = VideoMaterial(staged)
        mat.local_material_id = stable_material_id_public(staged)
        max_us = mat.duration - 1000
        src_us = min(seg_us, max_us)
        vs = VideoSegment(mat, trange(start, seg_us), source_timerange=trange(0, src_us))
        vs.volume = 0.0
        proj.add_segment(vs, "MainVideo")
        start += seg_us
        print(f"   └ 片段{idx+1}: {os.path.basename(vp_ok)} → {take:.1f}s")
    print(f"✅ 素材轨铺满：{start/1e6:.1f}s / 目标 {total_duration_s:.1f}s")

    print(f"✅ 2/4 上部标题区（{len(title_lines)}条，每条{title_seconds}s）")
    t_start = 0
    for i, line in enumerate(title_lines):
        t_us = int(title_seconds * 1_000_000)
        if t_start + t_us > total_us:
            t_us = max(0, total_us - t_start)
        if t_us <= 0:
            break
        seg = TextSegment(
            line,
            trange(t_start, t_us),
            style=TextStyle(size=7.5, bold=True, color=(1.0, 0.82, 0.30),
                            align=1, auto_wrapping=True, max_line_width=0.9),
            border=TextBorder(color=(0.0, 0.0, 0.0), width=30.0),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=-0.58),
        )
        proj.add_segment(seg, "TextTitle")
        t_start += t_us
        print(f"   └ 标题{i+1}: {line}")
    if title_lines and t_start < total_us:
        seg = TextSegment(
            title_lines[-1],
            trange(t_start, total_us - t_start),
            style=TextStyle(size=7.5, bold=True, color=(1.0, 0.82, 0.30),
                            align=1, auto_wrapping=True, max_line_width=0.9),
            border=TextBorder(color=(0.0, 0.0, 0.0), width=30.0),
            clip_settings=ClipSettings(transform_x=0.0, transform_y=-0.58),
        )
        proj.add_segment(seg, "TextTitle")

    print(f"✅ 3/4 下部广告区（{len(ad_lines)}行，常驻全片）")
    ad_lines_use = ad_lines[:3]
    ad_text = "\n".join(ad_lines_use)
    seg_ad = TextSegment(
        ad_text,
        trange(0, total_us),
        style=TextStyle(size=4.5, bold=True, color=(1.0, 1.0, 1.0),
                        align=1, line_spacing=12, auto_wrapping=True, max_line_width=0.92),
        border=TextBorder(color=(0.0, 0.0, 0.0), width=20.0),
        clip_settings=ClipSettings(transform_x=0.0, transform_y=0.78),
    )
    proj.add_segment(seg_ad, "TextAd")
    for i, line in enumerate(ad_lines_use):
        print(f"   └ 广告{i+1}: {line}")

    print("✅ 4/4 导入配音(可选)+BGM铺满")
    if voiceover_path and os.path.exists(voiceover_path):
        staged_v = stage_material(voiceover_path, draft_dir)
        v_mat = AudioMaterial(staged_v)
        v_mat.local_material_id = stable_material_id_public(staged_v)
        v_seg = AudioSegment(v_mat, trange(0, min(total_us, v_mat.duration)))
        v_seg.volume = 1.0
        proj.add_segment(v_seg, "Voice")

    if bgm_path and os.path.exists(bgm_path):
        staged_b = stage_material(bgm_path, draft_dir)
        b_mat = AudioMaterial(staged_b)
        b_mat.local_material_id = stable_material_id_public(staged_b)
        start = 0
        while start < total_us:
            seg_len = min(b_mat.duration, total_us - start)
            b_seg = AudioSegment(b_mat, trange(start, seg_len), source_timerange=trange(0, seg_len))
            b_seg.volume = bgm_volume
            proj.add_segment(b_seg, "BGM")
            start += seg_len

    proj.save()
    print(f"✅ 草稿已保存：{draft_dir}")
    return draft_dir


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="热点引流混剪")
    parser.add_argument("--name", default="热点引流_红鲤AI")
    parser.add_argument("--video", nargs="+", default=[
        r"E:\张总口播素材\混剪素材\2.mp4",
        r"E:\张总口播素材\混剪素材\ae634d2874d0a04cd9fdbf1516fda1fc.mp4",
        r"E:\张总口播素材\混剪素材\微信视频2026-07-21_111022_046.mp4",
        r"E:\张总口播素材\混剪素材\微信视频2026-07-21_111028_228.mp4",
    ])
    parser.add_argument("--title", nargs="+", default=[
        "AI员工，正在取代重复性工作",
        "一个人干三个人的活，正在成为过去",
        "中小企业获客难，AI正在改写规则",
        "一句话，调度整个AI团队",
    ])
    parser.add_argument("--ad", nargs="+", default=[
        "红鲤AI超级Agent · AI获客全流程自动化",
        "做内容 → GEO优化 → 找客户 → 转化，全链路自动",
        "真实设备执行 · 7×24小时自动获客 · 有电脑即可装",
    ])
    parser.add_argument("--bgm", default=config.DEFAULT_BGM)
    parser.add_argument("--duration", type=float, default=40.0)
    parser.add_argument("--voiceover", default=None)
    args = parser.parse_args()
    make_hotspot_mix_draft(
        name=args.name, video_list=args.video, title_lines=args.title,
        ad_lines=args.ad, bgm_path=args.bgm,
        total_duration_s=args.duration, voiceover_path=args.voiceover,
    )
