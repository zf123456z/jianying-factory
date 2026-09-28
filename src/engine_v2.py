#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 v7.2 稳定引擎 - 对齐上游jianying-editor的所有稳妥性设计
所有踩过的坑全部堵死，比上游更适合国内用户做口播视频
"""
import os
import re
import hashlib
import shutil
import time
from typing import Optional
import pyJianYingDraft as jy
from pyJianYingDraft import (
    VideoMaterial, VideoSegment, AudioMaterial, AudioSegment,
    trange, TrackType, TrackSpec, DraftFolder
)

# 固定路径配置（可被 factory_config.json / 环境变量覆盖，见 factory_config.py）
import factory_config as _cfg
DRAFT_ROOT = _cfg.get("draft_root") or r"D:\AI工作区\剪映草稿"
EXPORT_ROOT = _cfg.get("export_root") or r"D:\AI工作区\导出"
DEFAULT_VIDEO = _cfg.get("default_video") or r"E:\张总口播素材\张总形象.mp4"
CANVAS_W = int(_cfg.get("canvas_width") or 1080)
CANVAS_H = int(_cfg.get("canvas_height") or 1920)
FPS = int(_cfg.get("fps") or 30)
BACKUP_ROOT = _cfg.get("backup_root") or r"D:\AI工作区\剪映草稿_备份"


def sanitize_project_name(name: str) -> str:
    """过滤文件名非法字符，和上游一致"""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(name)).strip().strip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    while ".." in cleaned:
        cleaned = cleaned.replace("..", "_")
    return cleaned or "未命名草稿"


def safe_draft_dir(name: str) -> str:
    """安全拼草稿路径：校验目标一定在 DRAFT_ROOT 之内，防误删/越界（可靠版安全设计）"""
    target = os.path.abspath(os.path.join(DRAFT_ROOT, name))
    root_abs = os.path.abspath(DRAFT_ROOT)
    if os.path.commonpath([root_abs, target]) != root_abs:
        raise ValueError(f"Unsafe draft path detected: {target}")
    return target


def backup_existing_draft(draft_dir: str) -> str:
    """把已存在草稿移入带毫秒时间戳的备份目录（可靠版 _preserve_existing_draft）。
    备份失败时抛异常中断，绝不继续破坏性重建。"""
    abs_path = os.path.abspath(draft_dir)
    root_abs = os.path.abspath(DRAFT_ROOT)
    if os.path.commonpath([root_abs, abs_path]) != root_abs:
        raise ValueError(f"Refuse to back up path outside drafts root: {abs_path}")
    if not os.path.isdir(abs_path):
        raise FileNotFoundError(abs_path)

    backup_root = os.path.join(os.path.dirname(DRAFT_ROOT), "剪映草稿_备份")
    if _cfg.get("backup_root"):
        backup_root = _cfg.get("backup_root")
    os.makedirs(backup_root, exist_ok=True)
    from datetime import datetime as _dt
    stamp = _dt.now().strftime("%Y%m%d-%H%M%S-%f")  # 毫秒级时间戳，防同一秒内撞名
    target = os.path.join(backup_root, f"{os.path.basename(abs_path)}-{stamp}")
    try:
        shutil.move(abs_path, target)
    except Exception as e:
        raise RuntimeError(f"草稿备份失败，已停止重建以保护原草稿: {e}") from e
    print(f"🛡️ 旧草稿已备份：{target}")
    return target


def stage_material(src_path: str, draft_dir: str) -> str:
    """素材自包含：按MD5复制到草稿materials，和上游一致防重名/防丢失"""
    materials_dir = os.path.join(draft_dir, "materials")
    os.makedirs(materials_dir, exist_ok=True)
    abs_src = os.path.abspath(src_path)
    abs_draft = os.path.abspath(draft_dir)
    try:
        if os.path.commonpath([abs_src, abs_draft]) == abs_draft:
            return abs_src
    except ValueError:
        pass
    md5 = hashlib.md5(abs_src.encode("utf-8")).hexdigest()
    ext = os.path.splitext(abs_src)[1].lower()
    staged = os.path.join(materials_dir, f"{md5}{ext}")
    if not (os.path.exists(staged) and os.path.getsize(staged) == os.path.getsize(abs_src)):
        shutil.copy2(abs_src, staged)
    return staged


# ================= 视频规范化（吸收上游 v1.7 media_normalizer，防画面条纹） =================
# 剪映 5.9+ 对非标准视频（非 h264 / 非 yuv420p / 尺寸非16倍数）解码会出现条纹、花屏。
# 上游做法：ffprobe 探测，不达标就用 ffmpeg 统一转码为 H.264 yuv420p，杜绝条纹。
import json as _json
import subprocess as _subprocess


def _probe_video_for_jianying(video_path: str) -> dict:
    """ffprobe 探测视频编码/尺寸/像素格式"""
    try:
        proc = _subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,width,height,pix_fmt",
             "-of", "json", video_path],
            capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if proc.returncode != 0:
            return {}
        streams = _json.loads(proc.stdout or "{}").get("streams", [])
        return streams[0] if streams else {}
    except Exception:
        return {}


def _norm_output_path(video_path: str, draft_dir: str) -> str:
    """规范化产物放草稿 materials 内（自包含），命名带 __jy_norm__ 防混淆"""
    materials_dir = os.path.join(draft_dir, "materials")
    os.makedirs(materials_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(video_path))[0]
    return os.path.join(materials_dir, f"{stem}.__jy_norm__.mp4")


def normalize_video_for_jianying(video_path: str, draft_dir: str, force: bool = False) -> str:
    """剪映友好化视频：非 h264/yuv420p/非16倍数 时统一转码，防条纹；返回最终可用路径。

    v7.3 修复：转码目标尺寸跟随画布方向（CANVAS_W x CANVAS_H），不再写死横屏 1920x1080。
    竖屏画布(1080x1920)下转码竖屏素材 → 铺满竖屏，方向正确，无两侧黑边。
    """
    info = _probe_video_for_jianying(video_path)
    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    bad = (
        info.get("codec_name") != "h264"
        or info.get("pix_fmt") != "yuv420p"
        or width <= 0 or height <= 0
        or width % 16 != 0 or height % 2 != 0
    )
    if not force and not bad:
        return video_path  # 达标，直接用原片

    print(f"🔄 视频需规范化（codec={info.get('codec_name')}, pix_fmt={info.get('pix_fmt')}, {width}x{height}），转码中...")
    dst = _norm_output_path(video_path, draft_dir)
    # 目标尺寸跟随画布方向（竖屏画布=竖屏转码，横屏画布=横屏转码）
    target_w, target_h = CANVAS_W, CANVAS_H
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", video_path,
        "-map", "0:v:0", "-map", "0:a?",
        "-vf", (f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"),
        "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        dst,
    ]
    try:
        proc = _subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        print("❌ FFmpeg 不可用，无法规范化视频，使用原片")
        return video_path
    except Exception as e:
        print(f"❌ 视频规范化失败（{e}），使用原片")
        return video_path
    if proc.returncode != 0 or not os.path.exists(dst):
        print(f"❌ 视频规范化失败（ffmpeg={proc.returncode}），使用原片")
        return video_path
    print(f"✅ 视频已规范化：{dst}")
    return dst


def make_voiceover_draft(
    name: str,
    script_text: str = "",
    voice: Optional[str] = None,
    video_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    voiceover_path: Optional[str] = None,
    total_duration_s: float = 45.0,
    video_volume: Optional[float] = None,  # ★ 强制静音原片，默认取配置 0.0
    voice_volume: Optional[float] = None,
    bgm_volume: Optional[float] = None,
):
    """一键生成口播草稿，所有稳妥性和上游对齐。

    v7.3 quality 门禁：video/voice/bgm 音量默认从配置读取；显式传入 bgm_volume
    时校验 quality 区间 [bgm_volume_min, bgm_volume_max]，越界钳制并告警。
    """
    name = sanitize_project_name(name)
    voice = voice or _cfg.get("default_voice") or "云希"
    video_path = video_path or DEFAULT_VIDEO
    if video_volume is None:
        video_volume = float(_cfg.get("video_volume") or 0.0)
    if voice_volume is None:
        voice_volume = float(_cfg.get("voice_volume") or 1.0)
    if bgm_volume is None:
        bgm_volume = float(_cfg.get("bgm_volume") or 0.35)
    # quality 门禁：BGM 音量钳制在 [min, max]
    _q = _cfg.get("quality") or {}
    _bmin = float(_q.get("bgm_volume_min") or 0.30)
    _bmax = float(_q.get("bgm_volume_max") or 0.40)
    if bgm_volume < _bmin or bgm_volume > _bmax:
        print(f"⚠️ BGM音量{bgm_volume:.2f}超出质量门禁[{_bmin:.2f},{_bmax:.2f}]，已钳制到{max(_bmin, min(_bmax, bgm_volume)):.2f}")
        bgm_volume = max(_bmin, min(_bmax, bgm_volume))
    print(f"🚀 开始生成草稿：{name}")
    folder = DraftFolder(DRAFT_ROOT)
    draft_dir = safe_draft_dir(name)  # 安全路径，防越界

    # 同名草稿处理：一律先备份（有效或损坏都备份），绝不静默覆盖/直接删除（可靠版安全设计）
    if os.path.exists(draft_dir):
        backup_existing_draft(draft_dir)

    # 创建草稿，带3次重试（处理剪映占用锁）
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

    # 加轨道
    proj.append_track(TrackSpec(TrackType.video, "MainVideo"))
    proj.append_track(TrackSpec(TrackType.audio, "Voice"))
    proj.append_track(TrackSpec(TrackType.audio, "BGM"))

    total_us = int(total_duration_s * 1_000_000)

    def stable_material_id(media_path: str) -> str:
        """上游 v1.7 修复：生成稳定非空的 local_material_id（基于文件名 stem），
        防止剪映 5.9+ 报「检测到媒体丢失，请重新链接后再剪辑」。
        空 local_material_id 是本机 pyJianYingDraft 的已知缺陷，必须在引擎层堵死。"""
        stem = os.path.splitext(os.path.basename(media_path))[0]
        digest = hashlib.md5(stem.encode("utf-8")).hexdigest()[:24]
        return f"lm_{digest}"

    # 1. 主视频：规范化（防条纹）+自包含+强制静音+循环铺满
    print("✅ 1/4 导入主视频（规范化+自包含+强制静音原片）")
    normalized_video = normalize_video_for_jianying(video_path, draft_dir)
    staged_video = stage_material(normalized_video, draft_dir)
    vid_mat = VideoMaterial(staged_video)
    vid_mat.local_material_id = stable_material_id(staged_video)  # ★ v1.7 修复
    start = 0
    loop_count = 0
    while start < total_us:
        seg_len = min(vid_mat.duration, total_us - start)
        vid_seg = VideoSegment(vid_mat, trange(start, seg_len), source_timerange=trange(0, seg_len))
        vid_seg.volume = video_volume
        proj.add_segment(vid_seg, "MainVideo")
        start += seg_len
        loop_count += 1
    if loop_count > 5:
        print(f"⚠️ 时间线审计：单素材循环了{loop_count}次，注意检查画面重复度")

    # 2. 配音轨道
    print("✅ 2/4 导入配音")
    if voiceover_path and os.path.exists(voiceover_path):
        staged_voice = stage_material(voiceover_path, draft_dir)
        voice_mat = AudioMaterial(staged_voice)
        voice_mat.local_material_id = stable_material_id(staged_voice)  # ★ v1.7 修复
        voice_seg = AudioSegment(voice_mat, trange(0, min(total_us, voice_mat.duration)))
        voice_seg.volume = voice_volume
        proj.add_segment(voice_seg, "Voice")

    # 3. BGM自动循环铺满
    print("✅ 3/4 导入BGM（自动铺满全片）")
    if bgm_path and os.path.exists(bgm_path):
        staged_bgm = stage_material(bgm_path, draft_dir)
        bgm_mat = AudioMaterial(staged_bgm)
        bgm_mat.local_material_id = stable_material_id(staged_bgm)  # ★ v1.7 修复
        start = 0
        while start < total_us:
            seg_len = min(bgm_mat.duration, total_us - start)
            bgm_seg = AudioSegment(bgm_mat, trange(start, seg_len), source_timerange=trange(0, seg_len))
            bgm_seg.volume = bgm_volume
            proj.add_segment(bgm_seg, "BGM")
            start += seg_len

    proj.save()
    print(f"✅ 4/4 草稿已保存：{draft_dir}")
    print("👉 打开剪映→字幕→识别字幕→智能包装选科技风→导出")
    return draft_dir
