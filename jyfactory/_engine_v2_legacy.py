#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 v7.2 稳定引擎 - 对齐上游jianying-editor的所有稳妥性设计
所有踩过的坑全部堵死（v8 起主执行路径为 VectCutAPI 确定性内核 jyfactory/engine.py，
本模块仅 advanced 等 legacy 依赖内部使用，勿外扩）
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

from . import _factory_config_legacy as _cfg
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


def _write_meta_info(draft_dir: str, duration_us: int) -> None:
    """回写 draft_meta_info.json 的素材总大小与时长字段，保证剪映首页列表显示正确"""
    meta_path = os.path.join(draft_dir, "draft_meta_info.json")
    if not os.path.exists(meta_path):
        return
    try:
        import json
        with open(meta_path, "r", encoding="utf-8-sig") as f:
            meta = json.load(f)
        mats_dir = os.path.join(draft_dir, "materials")
        total = 0
        if os.path.isdir(mats_dir):
            for root, _, files in os.walk(mats_dir):
                for fn in files:
                    try:
                        total += os.path.getsize(os.path.join(root, fn))
                    except OSError:
                        pass
        meta["draft_timeline_materials_size_"] = total
        meta["tm_duration"] = duration_us
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        print(f"✅ meta回写：素材大小={total}字节，时长={duration_us/1e6:.0f}s")
    except Exception as e:
        print(f"⚠️ meta回写失败（不影响草稿本体）：{e}")


def safe_draft_dir(name: str) -> str:
    """安全拼草稿路径：校验目标一定在 DRAFT_ROOT 之内，防误删/越界"""
    target = os.path.abspath(os.path.join(DRAFT_ROOT, name))
    root_abs = os.path.abspath(DRAFT_ROOT)
    if os.path.commonpath([root_abs, target]) != root_abs:
        raise ValueError(f"Unsafe draft path detected: {target}")
    return target


def backup_existing_draft(draft_dir: str) -> str:
    """把已存在草稿移入带毫秒时间戳的备份目录，绝不静默覆盖/直接删除"""
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
    stamp = _dt.now().strftime("%Y%m%d-%H%M%S-%f")
    target = os.path.join(backup_root, f"{os.path.basename(abs_path)}-{stamp}")
    try:
        shutil.move(abs_path, target)
    except Exception as e:
        raise RuntimeError(f"草稿备份失败，已停止重建以保护原草稿: {e}") from e
    print(f"🛡️ 旧草稿已备份：{target}")
    return target


def stage_material(src_path: str, draft_dir: str) -> str:
    """素材自包含：按MD5复制到草稿materials，防重名/防丢失"""
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
    materials_dir = os.path.join(draft_dir, "materials")
    os.makedirs(materials_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(video_path))[0]
    return os.path.join(materials_dir, f"{stem}.__jy_norm__.mp4")


def normalize_video_for_jianying(video_path: str, draft_dir: str, force: bool = False) -> str:
    """剪映友好化视频：非 h264/yuv420p/非16倍数 时统一转码，防条纹；返回最终可用路径"""
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
        return video_path

    print(f"🔄 视频需规范化（codec={info.get('codec_name')}, pix_fmt={info.get('pix_fmt')}, {width}x{height}），转码中...")
    dst = _norm_output_path(video_path, draft_dir)
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


def probe_duration_s(path: str) -> float:
    """用 ffprobe 读取媒体时长（秒），失败返回 0.0"""
    try:
        r = _subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        if r.returncode == 0:
            return float(_json.loads(r.stdout)["format"]["duration"])
    except Exception:
        pass
    return 0.0


def _mix_voice_bgm(voice_path: str, bgm_path: str, out_path: str,
                   total_s: float, voice_volume: float = 1.0,
                   bgm_volume: float = 0.35, duck_volume: float = 0.15) -> Optional[float]:
    """把配音/画外音与 BGM 预混成单条音轨（v7.6 修复：剪映打不开多音轨草稿）"""
    try:
        vo_s = probe_duration_s(voice_path)
        bgm_s = probe_duration_s(bgm_path)
        if vo_s <= 0:
            vo_s = total_s
        bgm_use = bgm_path
        tmp_loop = None
        if bgm_s < total_s - 0.05:
            tmp_loop = out_path + ".bgm_loop.wav"
            r = _subprocess.run(
                ["ffmpeg", "-y", "-stream_loop", "2000", "-i", bgm_path,
                 "-t", f"{total_s:.3f}", "-ar", "44100", "-ac", "2",
                 "-c:a", "pcm_s16le", tmp_loop],
                capture_output=True, text=True, encoding="utf-8", timeout=300)
            if r.returncode == 0:
                bgm_use = tmp_loop
            else:
                print(f"⚠️ BGM循环失败，直接使用原BGM：{bgm_path}")
        fc = (
            f"[0:a]volume={voice_volume}[a0];"
            f"[1:a]volume='if(lt(t,{vo_s:.3f}),{duck_volume},{bgm_volume})':eval=frame[a1];"
            f"[a0][a1]amix=inputs=2:duration=longest:normalize=0:dropout_transition=0[out]"
        )
        r = _subprocess.run(
            ["ffmpeg", "-y", "-i", voice_path, "-i", bgm_use,
             "-filter_complex", fc, "-map", "[out]",
             "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", out_path],
            capture_output=True, text=True, encoding="utf-8", timeout=300)
        if tmp_loop and os.path.exists(tmp_loop):
            try:
                os.remove(tmp_loop)
            except OSError:
                pass
        if r.returncode != 0:
            print(f"❌ 混音失败：{r.stderr[-400:]}")
            return None
        return probe_duration_s(out_path)
    except Exception as e:
        print(f"⚠️ 混音异常：{e}")
        return None


def _fallback_dual_audio(proj, voice_path, bgm_path, draft_dir, stable_material_id,
                         total_us, voice_volume, bgm_volume):
    """混音失败时的回退：配音、BGM 分别铺入同一条 AudioMix 轨（两段不同时间位置）"""
    try:
        from pyJianYingDraft import trange as _tr
        if voice_path and os.path.exists(voice_path):
            staged_voice = stage_material(voice_path, draft_dir)
            voice_mat = AudioMaterial(staged_voice)
            voice_mat.local_material_id = stable_material_id(staged_voice)
            vlen = min(int(voice_mat.duration), total_us)
            vseg = AudioSegment(voice_mat, _tr(0, vlen), source_timerange=_tr(0, vlen))
            vseg.volume = voice_volume
            proj.add_segment(vseg, "AudioMix")
        if bgm_path and os.path.exists(bgm_path):
            staged_bgm = stage_material(bgm_path, draft_dir)
            bgm_mat = AudioMaterial(staged_bgm)
            bgm_mat.local_material_id = stable_material_id(staged_bgm)
            start = 0
            while start < total_us:
                seg_len = min(bgm_mat.duration, total_us - start)
                bgm_seg = AudioSegment(bgm_mat, _tr(start, seg_len), source_timerange=_tr(0, seg_len))
                bgm_seg.volume = bgm_volume
                proj.add_segment(bgm_seg, "AudioMix")
                start += seg_len
        print("   ↳ 回退成功：配音+BGM 同轨铺入（同轨多段剪映可正常打开）")
    except Exception as e:
        print(f"⚠️ 回退铺音失败：{e}")


def make_voiceover_draft(
    name: str,
    script_text: str = "",
    voice: Optional[str] = None,
    video_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    voiceover_path: Optional[str] = None,
    total_duration_s: float = 45.0,
    video_volume: Optional[float] = None,
    voice_volume: Optional[float] = None,
    bgm_volume: Optional[float] = None,
):
    """一键生成口播草稿，所有稳妥性和上游对齐"""
    name = sanitize_project_name(name)
    voice = voice or _cfg.get("default_voice") or "云希"
    video_path = video_path or DEFAULT_VIDEO
    if video_volume is None:
        video_volume = float(_cfg.get("video_volume") or 0.0)
    if voice_volume is None:
        voice_volume = float(_cfg.get("voice_volume") or 1.0)
    if bgm_volume is None:
        bgm_volume = float(_cfg.get("bgm_volume") or 0.35)
    _q = _cfg.get("quality") or {}
    _bmin = float(_q.get("bgm_volume_min") or 0.30)
    _bmax = float(_q.get("bgm_volume_max") or 0.40)
    if bgm_volume < _bmin or bgm_volume > _bmax:
        print(f"⚠️ BGM音量{bgm_volume:.2f}超出质量门禁[{_bmin:.2f},{_bmax:.2f}]，已钳制到{max(_bmin, min(_bmax, bgm_volume)):.2f}")
        bgm_volume = max(_bmin, min(_bmax, bgm_volume))
    print(f"🚀 开始生成草稿：{name}")
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
    proj.append_track(TrackSpec(TrackType.audio, "AudioMix"))

    total_us = int(total_duration_s * 1_000_000)

    def stable_material_id(media_path: str) -> str:
        """生成稳定非空的 local_material_id，防止剪映 5.9+ 报媒体丢失"""
        stem = os.path.splitext(os.path.basename(media_path))[0]
        digest = hashlib.md5(stem.encode("utf-8")).hexdigest()[:24]
        return f"lm_{digest}"

    print("✅ 1/4 导入主视频（规范化+自包含+强制静音原片）")
    normalized_video = normalize_video_for_jianying(video_path, draft_dir)
    staged_video = stage_material(normalized_video, draft_dir)
    vid_mat = VideoMaterial(staged_video)
    vid_mat.local_material_id = stable_material_id(staged_video)
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

    print("✅ 2/4 导入配音 + BGM（预混单音轨：人声满音量，BGM人声段自动闪避、铺满全片）")
    if voiceover_path and os.path.exists(voiceover_path) and bgm_path and os.path.exists(bgm_path):
        mix_out = os.path.join(draft_dir, "materials", "audio_mix.wav")
        mix_dur = _mix_voice_bgm(voiceover_path, bgm_path, mix_out, total_duration_s,
                                 voice_volume=voice_volume, bgm_volume=bgm_volume, duck_volume=0.15)
        if mix_dur and mix_dur > 0:
            staged_mix = stage_material(mix_out, draft_dir)
            mix_mat = AudioMaterial(staged_mix)
            mix_mat.local_material_id = stable_material_id(staged_mix)
            mix_seg = AudioSegment(mix_mat, trange(0, min(total_us, mix_mat.duration)),
                                   source_timerange=trange(0, min(total_us, mix_mat.duration)))
            mix_seg.volume = 1.0
            proj.add_segment(mix_seg, "AudioMix")
            print(f"   ↳ 混音轨 {mix_dur:.1f}s 已铺满全片")
        else:
            print("⚠️ 混音失败，退回：配音与BGM分别独立铺入（不推荐）")
            _fallback_dual_audio(proj, voiceover_path, bgm_path, draft_dir,
                                 stable_material_id, total_us, voice_volume, bgm_volume)
    elif voiceover_path and os.path.exists(voiceover_path):
        staged_voice = stage_material(voiceover_path, draft_dir)
        voice_mat = AudioMaterial(staged_voice)
        voice_mat.local_material_id = stable_material_id(staged_voice)
        voice_seg = AudioSegment(voice_mat, trange(0, min(total_us, voice_mat.duration)))
        voice_seg.volume = voice_volume
        proj.add_segment(voice_seg, "AudioMix")
        print("   ↳ 无BGM，仅配音轨")
    elif bgm_path and os.path.exists(bgm_path):
        staged_bgm = stage_material(bgm_path, draft_dir)
        bgm_mat = AudioMaterial(staged_bgm)
        bgm_mat.local_material_id = stable_material_id(staged_bgm)
        start = 0
        while start < total_us:
            seg_len = min(bgm_mat.duration, total_us - start)
            bgm_seg = AudioSegment(bgm_mat, trange(start, seg_len), source_timerange=trange(0, seg_len))
            bgm_seg.volume = bgm_volume
            proj.add_segment(bgm_seg, "AudioMix")
            start += seg_len
        print("   ↳ 无配音，仅BGM铺满")
    else:
        print("   ↳ 无配音无BGM，跳过音频")

    proj.save()
    _write_meta_info(draft_dir, total_us)
    print(f"✅ 4/4 草稿已保存：{draft_dir}")
    print("👉 打开剪映→字幕→识别字幕→智能包装选科技风→导出")
    return draft_dir
