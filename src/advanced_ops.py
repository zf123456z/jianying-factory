#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 v7.7 高级算子（对齐并超越上游 jianying-editor）
================================================================
8 大能力，全部遵循项目铁律：
  - 音频一律预混【单音轨】（剪映11.5打不开多音频轨草稿，v7.6实测钉死）
  - 素材自包含 + local_material_id 稳定非空（防媒体丢失）
  - 视频规范化（防条纹）+ 竖屏画布 1080x1920
  - 草稿放 D 盘草稿箱，同名先备份

功能清单：
  1. add_ken_burns           关键帧运镜（缩放/位移/旋转/透明度，Ken Burns 预设）
  2. narrated_draft          引擎内置 TTS + 逐句字幕同步（edge-tts，单音轨）
  3. clone_draft             模板克隆批量生产（安全克隆+替换物料/文案）
  4. match_assets_by_script  语义素材匹配（按文案句子语义匹配 B-roll）
  5. build_cloud_text_styles / add_styled_text  花字样式（挖掘剪映花字ID + 注入）
  6. web_to_video            Web-to-Video（Playwright 录 HTML 动效 → 视频素材）
  7. record_screen / apply_zoom_draft  录屏 + 智能变焦（点击处缩放关键帧）
  8. movie_commentary_draft  影视解说模板（分镜裁剪 + 逐镜解说 + 字幕合成）
  9. add_scene_transition / add_scene_effect / add_effect_track  转场+特效轨道算子
  10. apply_flower_text / add_flower_title  花字引擎级应用（513 官方花字 ID）

依赖：edge-tts（TTS）、playwright（Web-to-Video）、pynput（录屏事件）
"""
import os
import re
import json
import shutil
import hashlib
import random
import subprocess
import time
from typing import Optional, List, Dict, Union

import pyJianYingDraft as jy
from pyJianYingDraft import (
    VideoMaterial, VideoSegment, AudioMaterial, AudioSegment, TextSegment,
    TextStyle, ClipSettings, trange, TrackType, TrackSpec, DraftFolder,
    KeyframeProperty as KP,
)


def _resolve_bgm(bgm_path: Optional[str], max_dur: Optional[float] = None) -> Optional[str]:
    """BGM 来源解析（v7.7 新增）：
    优先使用显式 bgm_path；为 None 时自动从剪映官方曲库本地缓存选歌
    （剪映曲库音乐全部正版授权，下载后落盘 Cache\\music\\，引擎直接混音）。
    """
    if bgm_path and os.path.exists(bgm_path):
        return bgm_path
    try:
        from jianying_music_bridge import JianyingMusicBridge
        song = JianyingMusicBridge().pick(max_duration_s=max_dur)
        if song:
            print(f"🎵 剪映曲库BGM（正版）：{song['duration_s']}s "
                  f"{os.path.basename(song['path'])}")
            return song["path"]
    except Exception as e:
        print(f"⚠️ 曲库BGM不可用，改无BGM：{e}")
    return None

import engine_v2 as E
from engine_v2 import (
    DRAFT_ROOT, CANVAS_W, CANVAS_H, FPS,
    sanitize_project_name, safe_draft_dir, backup_existing_draft,
    stage_material, normalize_video_for_jianying, probe_duration_s,
    _mix_voice_bgm, _write_meta_info,
)

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


# =====================================================================
# 1. 关键帧运镜（Ken Burns）—— 对齐上游 keyframes.md，直接可用
# =====================================================================
KEN_BURNS_PRESETS = {
    "zoom_in_slow":   [(KP.uniform_scale, 1.00, 1.30)],
    "zoom_out_slow":  [(KP.uniform_scale, 1.30, 1.00)],
    "pan_left":       [(KP.uniform_scale, 1.20, 1.20), (KP.position_x, 0.30, -0.30)],
    "pan_right":      [(KP.uniform_scale, 1.20, 1.20), (KP.position_x, -0.30, 0.30)],
    "zoom_in_center": [(KP.uniform_scale, 1.00, 1.45)],
    "fade_in":        [(KP.alpha, 0.00, 1.00)],
    "fade_out":       [(KP.alpha, 1.00, 0.00)],
    "rotate_pulse":   [(KP.rotation, 0.0, 1.5), (KP.uniform_scale, 1.00, 1.15)],
}


def add_ken_burns(segment, start_us: int, dur_us: int, style: str = "zoom_in_slow",
                  ease: Optional[Dict] = None) -> object:
    """给视频/图片段加 Ken Burns 运镜关键帧。
    style 支持：zoom_in_slow / zoom_out_slow / pan_left / pan_right /
               zoom_in_center / fade_in / fade_out / rotate_pulse
    关键帧时间用绝对时间线微秒（对齐上游约束）。"""
    if style not in KEN_BURNS_PRESETS:
        style = "zoom_in_slow"
    t0, t1 = int(start_us), int(start_us + dur_us)
    for prop, v0, v1 in KEN_BURNS_PRESETS[style]:
        segment.add_keyframe(prop, t0, v0)
        segment.add_keyframe(prop, t1, v1)
    return segment


# =====================================================================
# 1b. 转场 + 特效轨道（对齐上游 vfx_ops.add_transition_simple / add_effect_simple）
#     实测 pyJianYingDraft：TransitionType 500+ 转场、VideoSceneEffectType 1000+ 特效，
#     段方法 add_transition(type, duration=秒) / add_effect(type)。
# =====================================================================
# 常用转场白名单（按短视频风格推荐，保证稳定可打开）
TRANSITION_SAFE = ["叠化", "闪白", "闪黑", "水墨", "翻页", "模糊", "滑动",
                   "推近", "拉开", "旋转", "故障", "闪白_II", "闪黑_II"]
# 常用特效白名单（运镜/氛围类，避免纯装饰性特效）
EFFECT_SAFE = ["S形运镜", "变焦推镜", "推拉跟随", "动感运镜", "丝滑运镜",
               "跟随运镜", "缩放运镜", "广角", "电影感", "老电影", "胶片"]


def add_scene_transition(segment, transition_name: str = "叠化",
                         duration_s: float = 0.5) -> object:
    """给视频段尾部挂转场（衔接下一段），剪映官方转场ID（正版）。
    transition_name 支持 500+ 种（pyJianYingDraft.TransitionType），
    不在白名单也直接透传（库负责校验）；建议用白名单内的稳定风格。"""
    try:
        seg = segment.add_transition(jy.TransitionType[transition_name],
                                     duration=f"{duration_s:.2f}s")
        return seg
    except Exception as e:
        print(f"⚠️ 转场 {transition_name} 不可用（{e}），跳过")
        return segment


def add_scene_effect(segment, effect_name: str = "电影感") -> object:
    """给视频段加场景特效（运镜/氛围/滤镜），剪映官方特效ID（正版）。"""
    try:
        return segment.add_effect(jy.VideoSceneEffectType[effect_name])
    except Exception as e:
        print(f"⚠️ 特效 {effect_name} 不可用（{e}），跳过")
        return segment


def add_effect_track(proj, effect_name: str = "电影感",
                     start_us: int = 0, dur_us: Optional[int] = None) -> object:
    """特效轨道算子（对齐上游 vfx_ops.add_effect_simple）：
    建独立特效轨 + EffectSegment，可指定时间范围，作用于覆盖区间画面。
    实测：video_effects 写入 type=video_effect + effect_id。"""
    try:
        proj.append_track(jy.TrackSpec(jy.TrackType.effect))
        proj.add_effect(jy.VideoSceneEffectType[effect_name],
                        jy.trange(int(start_us), int(dur_us or 3_000_000)))
    except Exception as e:
        print(f"⚠️ 特效轨 {effect_name} 不可用（{e}），跳过")
    return proj


def apply_flower_text(segment, style_id) -> object:
    """给文本段应用剪映官方花字样式（引擎级，无需GUI）。

    花字ID来源：`data/cloud_text_styles.csv`（513个，build_cloud_text_styles_library 挖掘）。
    实测（v7.7.1）：513个ID全部可写入，JSON落点 materials.filters →
    type=text_effect（effect_id=resource_id=花字ID），剪映正版花字。
    示例（爆款黄字描边）：6740498118342611464 / 6895924568708467981。"""
    try:
        return segment.add_effect(str(style_id))
    except Exception as e:
        print(f"⚠️ 花字 {style_id} 不可用（{e}），跳过")
        return segment


def add_flower_title(proj, text: str, start_us: int = 0, dur_us: int = 2_000_000,
                     style_id: str = "6740498118342611464") -> object:
    """在指定时间加一条花字标题文本（爆款标题样式），引擎级写入。

    用于热点混剪上部标题 / 口播强调句：一行调用生成花字标题段。"""
    tseg = jy.TextSegment(text, jy.trange(int(start_us), int(dur_us)))
    apply_flower_text(tseg, style_id)
    proj.add_segment(tseg, "text")
    return proj


# =====================================================================
# 2. 引擎内置 TTS + 逐句字幕同步（单音轨）—— 对齐上游 add_narrated_subtitles
# =====================================================================
TTS_VOICES = {
    "云希": "zh-CN-YunxiNeural",      # 年轻男声
    "云健": "zh-CN-YunjianNeural",    # 沉稳男声
    "晓晓": "zh-CN-XiaoxiaoNeural",   # 甜美女声
    "晓伊": "zh-CN-XiaoyiNeural",     # 温柔女声
    "沉稳男": "zh-CN-YunjianNeural",
    "活力男": "zh-CN-YunxiNeural",
    "磁性男": "zh-CN-YunjianNeural",
}


def split_sentences(text: str) -> List[str]:
    """按中文标点/换行拆句（保留标点）"""
    parts = re.split(r"([。！？；\n]+)", text)
    sents = []
    for i in range(0, len(parts) - 1, 2):
        s = (parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")).strip()
        if s:
            sents.append(s)
    if parts:
        tail = parts[-1].strip()
        if tail and (not sents or sents[-1] != tail):
            sents.append(tail)
    return [s for s in sents if s]


def tts_sentence(text: str, out_path: str, voice: str = "zh-CN-YunxiNeural",
                 rate: str = "+0%") -> Optional[str]:
    """edge-tts 合成单句语音；成功返回路径，失败返回 None"""
    try:
        import edge_tts
        import asyncio

        async def _run():
            c = edge_tts.Communicate(text, voice=voice, rate=rate)
            await c.save(out_path)

        asyncio.run(_run())
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path
    except Exception as e:
        print(f"⚠️ TTS失败({text[:12]}...): {e}")
    return None


def _wav_std(src: str, dst: str) -> bool:
    """统一转 44.1k/双声道/pcm_s16le，供 concat 拼接"""
    r = subprocess.run(
        [FFMPEG, "-y", "-i", src, "-ar", "44100", "-ac", "2",
         "-c:a", "pcm_s16le", dst],
        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return r.returncode == 0 and os.path.exists(dst)


def _concat_audios(paths: List[str], out_path: str) -> Optional[str]:
    """多段音频无损拼接为单条 wav（单音轨铁律：多句 TTS 合并成 1 条音轨）"""
    if not paths:
        return None
    stds = []
    for i, p in enumerate(paths):
        w = f"{out_path}.std{i}.wav"
        if not _wav_std(p, w):
            for x in stds:
                try: os.remove(x)
                except OSError: pass
            return None
        stds.append(w)
    lst = out_path + ".lst.txt"
    try:
        with open(lst, "w", encoding="utf-8") as f:
            for w in stds:
                f.write(f"file '{w.replace(os.sep, '/')}'\n")
        r = subprocess.run(
            [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", out_path],
            capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if r.returncode != 0 or not os.path.exists(out_path):
            return None
        return out_path
    finally:
        for w in stds:
            try: os.remove(w)
            except OSError: pass
        try: os.remove(lst)
        except OSError: pass


def _stable_material_id(media_path: str) -> str:
    stem = os.path.splitext(os.path.basename(media_path))[0]
    return f"lm_{hashlib.md5(stem.encode('utf-8')).hexdigest()[:24]}"


def narrated_draft(
    name: str,
    script_text: str,
    video_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    voice: str = "云健",
    rate: str = "+0%",
    total_duration_s: Optional[float] = None,
    bgm_volume: float = 0.35,
    video_volume: float = 0.0,
    ken_burns: str = "zoom_in_slow",
    subtitle_size: float = 5.0,
    subtitle_y: float = -0.8,
) -> str:
    """引擎内置 TTS + 逐句字幕同步 + 单音轨混音（口播全自动）。

    流程：文案拆句 → 逐句 TTS → 累计时长排字幕 → 拼接单音轨 → BGM 混音
    → 视频铺满(Ken Burns 运镜) → 字幕逐句对齐 → 保存草稿。
    单条音频轨铁律：所有 TTS 句拼接为一条 wav 再与 BGM 预混，剪映 100% 能打开。
    """
    name = sanitize_project_name(name)
    video_path = video_path or E.DEFAULT_VIDEO
    voice_key = TTS_VOICES.get(voice, voice)  # 支持中文别名或直接 edge-tts voice 名

    sents = split_sentences(script_text)
    if not sents:
        raise ValueError("文案为空，无法生成配音")

    print(f"🚀 内置TTS口播草稿：{name}（{len(sents)}句，音色={voice_key}）")
    folder = DraftFolder(DRAFT_ROOT)
    draft_dir = safe_draft_dir(name)
    if os.path.exists(draft_dir):
        backup_existing_draft(draft_dir)

    proj = None
    for attempt in range(3):
        try:
            proj = folder.create_draft(name, width=CANVAS_W, height=CANVAS_H,
                                       fps=FPS, allow_replace=True)
            break
        except PermissionError:
            print(f"⚠️ 草稿被剪映占用，2秒后重试（第{attempt+1}次）")
            time.sleep(2)
    if not proj:
        raise Exception("草稿创建失败，请先关闭剪映中正在编辑的同名草稿")

    proj.append_track(TrackSpec(TrackType.video, "MainVideo"))
    proj.append_track(TrackSpec(TrackType.audio, "AudioMix"))
    proj.append_track(TrackSpec(TrackType.text, "Subtitles"))

    # ---- 1. 逐句 TTS ----
    print(f"✅ 1/5 逐句TTS合成（{len(sents)}句）")
    tmp_dir = os.path.join(draft_dir, "materials", "tts_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    sent_audios, sent_durs = [], []
    for i, s in enumerate(sents):
        p = os.path.join(tmp_dir, f"s{i:03d}.mp3")
        if not tts_sentence(s, p, voice=voice_key, rate=rate):
            raise RuntimeError(f"第{i+1}句TTS失败：{s[:20]}...（请检查网络或改用剪映GUI换音色）")
        d = probe_duration_s(p)
        sent_audios.append(p)
        sent_durs.append(d if d > 0 else 0.0)
        print(f"   ↳ [{i+1}] {d:.1f}s {s[:24]}{'...' if len(s)>24 else ''}")

    # ---- 2. 拼接单音轨 ----
    print("✅ 2/5 拼接单音轨")
    voice_combined = os.path.join(draft_dir, "materials", "voice_combined.wav")
    if not _concat_audios(sent_audios, voice_combined):
        raise RuntimeError("TTS拼接失败")
    vo_s = probe_duration_s(voice_combined)
    total_us = int((total_duration_s or vo_s) * 1_000_000)

    # 字幕时间（累计）
    sub_times = []
    acc = 0.0
    for d in sent_durs:
        sub_times.append((acc, acc + d))
        acc += d

    # ---- 3. BGM 混音单轨（人声段闪避）----
    print("✅ 3/5 音频混音（单音轨：人声满音量 + BGM闪避铺满）")
    bgm_path = _resolve_bgm(bgm_path, max_dur=total_us / 1e6)
    staged_voice = stage_material(voice_combined, draft_dir)
    if bgm_path and os.path.exists(bgm_path):
        mix_out = os.path.join(draft_dir, "materials", "audio_mix.wav")
        mix_dur = _mix_voice_bgm(voice_combined, bgm_path, mix_out,
                                 total_us / 1e6, voice_volume=1.0,
                                 bgm_volume=bgm_volume, duck_volume=0.15)
        if mix_dur and mix_dur > 0:
            staged_mix = stage_material(mix_out, draft_dir)
            mat = AudioMaterial(staged_mix)
            mat.local_material_id = _stable_material_id(staged_mix)
            seg = AudioSegment(mat, trange(0, min(total_us, mat.duration)),
                               source_timerange=trange(0, min(total_us, mat.duration)))
            seg.volume = 1.0
            proj.add_segment(seg, "AudioMix")
        else:
            print("⚠️ 混音失败，仅铺配音轨（无BGM）")
            mat = AudioMaterial(staged_voice)
            mat.local_material_id = _stable_material_id(staged_voice)
            seg = AudioSegment(mat, trange(0, min(total_us, mat.duration)))
            seg.volume = 1.0
            proj.add_segment(seg, "AudioMix")
    else:
        mat = AudioMaterial(staged_voice)
        mat.local_material_id = _stable_material_id(staged_voice)
        seg = AudioSegment(mat, trange(0, min(total_us, mat.duration)))
        seg.volume = 1.0
        proj.add_segment(seg, "AudioMix")

    # ---- 4. 视频铺满 + Ken Burns ----
    print(f"✅ 4/5 视频铺满（Ken Burns: {ken_burns}）")
    norm_video = normalize_video_for_jianying(video_path, draft_dir)
    staged_video = stage_material(norm_video, draft_dir)
    vid_mat = VideoMaterial(staged_video)
    vid_mat.local_material_id = _stable_material_id(staged_video)
    start = 0
    while start < total_us:
        seg_len = min(vid_mat.duration, total_us - start)
        vseg = VideoSegment(vid_mat, trange(start, seg_len),
                            source_timerange=trange(0, seg_len))
        vseg.volume = video_volume
        add_ken_burns(vseg, start, seg_len, ken_burns)
        # 循环段衔接处自动加官方转场（v7.7.1）
        if start > 0:
            add_scene_transition(vseg, "叠化", 0.4)
        proj.add_segment(vseg, "MainVideo")
        start += seg_len

    # ---- 5. 逐句字幕 ----
    print(f"✅ 5/5 字幕逐句对齐（{len(sents)}条）")
    style = TextStyle(size=subtitle_size, bold=True, color=(1.0, 1.0, 1.0), align=2)
    border = jy.TextBorder(color=(0.0, 0.0, 0.0), alpha=1.0, width=40.0)
    for i, s in enumerate(sents):
        st, en = sub_times[i]
        s_us = int(st * 1e6)
        d_us = max(int((en - st) * 1e6), 300_000)
        if s_us >= total_us:
            break
        d_us = min(d_us, total_us - s_us)
        clip = ClipSettings(transform_y=subtitle_y)
        tseg = TextSegment(s, trange(s_us, d_us), style=style,
                           border=border, clip_settings=clip)
        proj.add_segment(tseg, "Subtitles")
        print(f"   ↳ [{st:.1f}s-{en:.1f}s] {s[:24]}{'...' if len(s)>24 else ''}")

    proj.save()
    _write_meta_info(draft_dir, total_us)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"✅ 草稿已保存：{draft_dir}（音频单轨 {vo_s:.1f}s 配音 + 字幕{len(sents)}条）")
    return draft_dir


# =====================================================================
# 3. 模板克隆批量生产（对齐上游 from_template，安全克隆不碰原模板）
# =====================================================================
def clone_draft(
    template_name: str,
    new_name: str,
    video_replace: Optional[str] = None,
    text_replace: Optional[Dict[str, str]] = None,
) -> str:
    """安全克隆模板草稿 → 新草稿，可替换主视频素材与文案。

    - 只克隆【未在剪映打开过的明文草稿】（打开过的被加密无法改，会明确报错）
    - 绝不修改原模板（copy 到新目录后改副本）
    - 素材替换：新视频规范化+自包含进副本 materials，替换 material 引用
    - 文本替换：对草稿内所有文本内容做 dict 替换
    """
    src = safe_draft_dir(template_name)
    if not os.path.isdir(src):
        raise FileNotFoundError(f"模板草稿不存在：{src}")
    new_name = sanitize_project_name(new_name)
    dst = safe_draft_dir(new_name)
    if os.path.exists(dst):
        backup_existing_draft(dst)

    # 明文检测（只读 src，绝不写入 src）
    src_content = os.path.join(src, "draft_content.json")
    src_info = os.path.join(src, "draft_info.json")
    src_json = src_content if os.path.exists(src_content) else src_info
    if not os.path.exists(src_json):
        raise RuntimeError(f"模板草稿缺少JSON：{template_name}")

    raw = open(src_json, encoding="utf-8-sig").read()
    # 剪映加密草稿的 draft_content.json 是密文（base64/加密块），明文草稿应含 "tracks" 关键词
    if '"tracks"' not in raw and '"materials"' not in raw:
        raise RuntimeError(
            f"模板草稿 {template_name} 已被剪映打开过（JSON已加密），无法克隆。"
            "请用未在剪映打开的明文草稿做模板（例如引擎刚生成、未双击打开过的草稿）")

    shutil.copytree(src, dst)

    # 之后所有 JSON 读写一律针对副本 dst，原模板 src 只读不写
    dst_content = os.path.join(dst, "draft_content.json")
    dst_info = os.path.join(dst, "draft_info.json")
    dst_json = dst_content if os.path.exists(dst_content) else dst_info
    if not os.path.exists(dst_json):
        raise RuntimeError("副本缺少JSON，克隆中断")

    # ---- 素材替换 ----
    if video_replace and os.path.exists(video_replace):
        norm_video = normalize_video_for_jianying(video_replace, dst)
        staged = stage_material(norm_video, dst)
        mat = VideoMaterial(staged)
        mat.local_material_id = _stable_material_id(staged)

        with open(dst_json, encoding="utf-8-sig") as f:
            data = json.load(f)
        # 找到原主视频 material（path 含 mp4/mov 的第一个 video material）
        mats = data.get("materials", {}).get("videos", [])
        new_id = getattr(mat, "material_id", None) or _stable_material_id(staged)
        for m in mats:
            m["path"] = staged.replace(os.sep, "/")
            m["local_material_id"] = mat.local_material_id
            m["material_id"] = new_id
            m["name"] = os.path.basename(staged)
        old_ids = [m.get("material_id") for m in mats]
        for tr in data.get("tracks", []):
            for seg in tr.get("segments", []):
                if seg.get("material_id") in old_ids:
                    seg["material_id"] = new_id
        with open(dst_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"   ↳ 素材已替换：{os.path.basename(video_replace)}")

    # ---- 文本替换（JSON级：改 materials.texts[].content.text，兼顾转义安全）----
    if text_replace:
        with open(dst_json, encoding="utf-8-sig") as f:
            data = json.load(f)
        changed = 0
        for t in data.get("materials", {}).get("texts", []):
            try:
                c = json.loads(t.get("content", "{}"))
            except Exception:
                continue
            if "text" in c:
                old_text = c["text"]
                for k, v in text_replace.items():
                    if k in old_text:
                        c["text"] = old_text.replace(k, v)
                if c["text"] != old_text:
                    t["content"] = json.dumps(c, ensure_ascii=False)
                    changed += 1
        with open(dst_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"   ↳ 文本替换完成（{len(text_replace)}组，命中{changed}条字幕）")

    # 更新 meta 大小
    dur_us = 0
    if video_replace and os.path.exists(video_replace):
        d = E.probe_duration_s(staged)
        dur_us = int(d * 1e6) if d > 0 else 0
    _write_meta_info(dst, dur_us)
    print(f"✅ 克隆完成：{dst}")
    return dst


# =====================================================================
# 4. 语义素材匹配（对齐上游 video_transcribe_and_match：按台词语义选 B-roll）
# =====================================================================
STOP_WORDS = set("的了和与或在把被让给对从向于是一就有也不都还才很更最只又再这那我你他她它们这个那个一个一些什么怎么为什么因为所以但是然而如果那么")


def _keywords_of(sentence: str) -> List[str]:
    """无分词依赖的中文关键词提取：过滤停用词/符号后的 2-6 字词块 + 整句切片"""
    clean = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", sentence)
    kws = set()
    for n in (6, 5, 4, 3, 2):
        for i in range(0, max(0, len(clean) - n + 1)):
            w = clean[i:i + n]
            if len(w) == n and not all(ch in STOP_WORDS for ch in w):
                kws.add(w)
    if clean:
        kws.add(clean)  # 整句词块（长匹配优先）
    return list(kws)


def index_asset_dir(asset_dir: str) -> List[Dict]:
    """索引素材目录：文件名 + 目录名作为标签（用户可维护更细的标签 CSV）"""
    items = []
    for root, _, files in os.walk(asset_dir):
        for fn in files:
            if fn.lower().endswith((".mp4", ".mov", ".webm", ".jpg", ".png", ".jpeg")):
                rel = os.path.relpath(os.path.join(root, fn), asset_dir)
                tags = re.split(r"[_\-.\(\)（）\s]+", os.path.splitext(fn)[0])
                tags += [os.path.basename(root)]
                items.append({
                    "path": os.path.join(root, fn),
                    "tags": [t for t in tags if t and not t.isdigit()],
                    "rel": rel,
                })
    return items


def match_assets_by_script(
    script_text: str,
    asset_dir: str,
    items: Optional[List[Dict]] = None,
    top_k: int = 1,
) -> List[Dict]:
    """按文案句子语义匹配 B-roll 素材。
    返回 [{"sentence": 句, "assets": [匹配素材路径...]}, ...]
    """
    items = items or index_asset_dir(asset_dir)
    sents = split_sentences(script_text)
    results = []
    for s in sents:
        kws = _keywords_of(s)
        scored = []
        for it in items:
            tags = " ".join(it["tags"])
            score = sum(1 for kw in kws if kw in tags or tags.find(kw[:min(3, len(kw))]) >= 0)
            scored.append((score, it["path"]))
        scored.sort(key=lambda x: -x[0])
        top = [p for sc, p in scored[:top_k] if sc > 0]
        results.append({"sentence": s, "assets": top or [scored[0][1]]})
    return results


# =====================================================================
# 5. 花字样式（挖掘剪映缓存花字 ID + 注入草稿）
# =====================================================================
def _jianying_cache_root() -> Optional[str]:
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data"),
        os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def build_cloud_text_styles_library(out_csv: Optional[str] = None) -> List[Dict]:
    """扫描剪映缓存中的 artistEffect 花字资源，生成花字 ID 清单（对齐上游 build_cloud_text_styles_library）"""
    styles = []
    root = _jianying_cache_root()
    if root:
        for dirpath, dirnames, _ in os.walk(root):
            if os.path.basename(dirpath) == "artistEffect":
                for d in dirnames:
                    if re.fullmatch(r"\d{10,}", d):
                        name_hint = d
                        cfg = os.path.join(dirpath, d, "config.json")
                        if os.path.exists(cfg):
                            try:
                                with open(cfg, encoding="utf-8") as f:
                                    c = json.load(f)
                                name_hint = c.get("name", c.get("displayName", d))
                            except Exception:
                                pass
                        styles.append({"style_id": d, "name": str(name_hint)})
                break
    out_csv = out_csv or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "data", "cloud_text_styles.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        f.write("style_id,name_hint\n")
        for s in styles:
            f.write(f"{s['style_id']},{s['name']}\n")
    print(f"✅ 花字库已生成：{out_csv}（{len(styles)}个）")
    return styles


# =====================================================================
# 6. Web-to-Video（Playwright 录 HTML/JS/CSS 动效 → 视频素材）
# =====================================================================
def web_to_video(
    html_path: str,
    out_mp4: str,
    duration_s: float = 5.0,
    wait_animation: bool = True,
    width: int = 1080,
    height: int = 1920,
) -> Optional[str]:
    """录制本地 HTML 动画为视频（对齐上游 web-vfx：window.animationFinished 契约）。
    输出 H.264 yuv420p（防条纹），可直接作为剪映素材。
    """
    if not os.path.exists(html_path):
        raise FileNotFoundError(html_path)
    tmp_dir = os.path.join(os.path.dirname(out_mp4), "_webvfx_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("请先安装 playwright：python -m pip install playwright && python -m playwright install chromium")
    with sync_playwright() as p:
        # 优先用系统自带 Edge（免下载 chromium，国内网络友好）；失败回退默认 chromium
        browser = None
        for channel in ("msedge", "chrome", None):
            try:
                kwargs = {"args": ["--autoplay-policy=no-user-gesture-required"]}
                if channel:
                    kwargs["channel"] = channel
                browser = p.chromium.launch(**kwargs)
                print(f"   ↳ 浏览器引擎: {channel or 'chromium-default'}")
                break
            except Exception as e:
                print(f"⚠️ {channel or 'chromium'} 启动失败: {str(e)[:80]}")
        if browser is None:
            raise RuntimeError("无可用浏览器引擎（请安装 Edge 或运行 python -m playwright install chromium）")
        ctx = browser.new_context(record_video_dir=tmp_dir,
                                  viewport={"width": width, "height": height})
        page = ctx.new_page()
        page.goto(f"file:///{html_path.replace(os.sep, '/')}")
        if wait_animation:
            try:
                page.wait_for_function("window.animationFinished === true", timeout=30000)
            except Exception:
                print("⚠️ 未等到 animationFinished，按 duration_s 录制")
                page.wait_for_timeout(int(duration_s * 1000))
        else:
            page.wait_for_timeout(int(duration_s * 1000))
        video_path = page.video.path() if page.video else None
        ctx.close()
        browser.close()
    if not video_path or not os.path.exists(video_path):
        raise RuntimeError("Playwright 未生成录屏视频")
    # webm → mp4 (H.264/yuv420p 防条纹)
    r = subprocess.run(
        [FFMPEG, "-y", "-i", video_path, "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
         "-crf", "18", "-movflags", "+faststart", out_mp4],
        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    if r.returncode != 0 or not os.path.exists(out_mp4):
        raise RuntimeError(f"Web视频转码失败：{r.stderr[-300:]}")
    print(f"✅ Web-to-Video 完成：{out_mp4}（{probe_duration_s(out_mp4):.1f}s）")
    return out_mp4


# =====================================================================
# 7. 录屏 + 智能变焦（对齐上游 recording：点击处自动缩放关键帧）
# =====================================================================
def record_screen(out_mp4: str, duration_s: float = 10.0,
                  events_json: Optional[str] = None) -> Optional[str]:
    """录屏（ffmpeg gdigrab）+ 记录鼠标点击事件（pynput）。
    events_json：录屏期间鼠标 click 事件 [{t:秒, x:0-1, y:0-1}]，供智能变焦。
    """
    try:
        from pynput import mouse
    except ImportError:
        raise RuntimeError("请先安装 pynput：python -m pip install pynput")
    events = []

    def _on_click(x, y, button, pressed):
        if pressed:
            events.append({"t": time.time() - t0, "x": x, "y": y})

    t0 = time.time()
    listener = mouse.Listener(on_click=_on_click)
    listener.start()
    r = subprocess.run(
        [FFMPEG, "-y", "-f", "gdigrab", "-framerate", "30", "-video_size", "1920x1080",
         "-i", "desktop", "-t", f"{duration_s:.1f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
         "-crf", "20", "-movflags", "+faststart", out_mp4],
        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    listener.stop()
    if r.returncode != 0 or not os.path.exists(out_mp4):
        print(f"❌ 录屏失败：{r.stderr[-300:]}")
        return None
    if events_json:
        with open(events_json, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False)
        print(f"   ↳ 事件已保存：{events_json}（{len(events)}次点击）")
    print(f"✅ 录屏完成：{out_mp4}（{duration_s}s）")
    return out_mp4


def apply_zoom_draft(
    name: str,
    video_path: str,
    events: Optional[List[Dict]] = None,
    events_json: Optional[str] = None,
    zoom_scale: float = 1.5,
    bgm_path: Optional[str] = None,
) -> str:
    """智能变焦草稿：在每次鼠标点击处插入「放大-停留-恢复」缩放关键帧（对齐上游 apply-zoom）。"""
    if events is None and events_json and os.path.exists(events_json):
        with open(events_json, encoding="utf-8") as f:
            events = json.load(f)
    events = events or []
    name = sanitize_project_name(name)
    folder = DraftFolder(DRAFT_ROOT)
    draft_dir = safe_draft_dir(name)
    if os.path.exists(draft_dir):
        backup_existing_draft(draft_dir)
    proj = folder.create_draft(name, width=CANVAS_W, height=CANVAS_H, fps=FPS, allow_replace=True)
    proj.append_track(TrackSpec(TrackType.video, "MainVideo"))
    proj.append_track(TrackSpec(TrackType.audio, "AudioMix"))

    norm_video = normalize_video_for_jianying(video_path, draft_dir)
    staged = stage_material(norm_video, draft_dir)
    mat = VideoMaterial(staged)
    mat.local_material_id = _stable_material_id(staged)
    total_us = int(mat.duration)

    vseg = VideoSegment(mat, trange(0, total_us), source_timerange=trange(0, total_us))
    vseg.volume = 0.0
    # 智能变焦关键帧：点击时刻 1.0→zoom_scale→1.0（每次点击持续1.2s）
    added = 0
    for ev in events:
        t = float(ev.get("t", 0)) * 1e6
        if t <= 0 or t >= total_us:
            continue
        t = int(t)
        dur = int(0.6 * 1e6)
        vseg.add_keyframe(KP.uniform_scale, t, 1.0)
        vseg.add_keyframe(KP.uniform_scale, t + dur, zoom_scale)
        vseg.add_keyframe(KP.uniform_scale, t + 2 * dur, 1.0)
        added += 1
    proj.add_segment(vseg, "MainVideo")

    bgm_path = _resolve_bgm(bgm_path, max_dur=total_us / 1e6)
    if bgm_path and os.path.exists(bgm_path):
        bgm = stage_material(bgm_path, draft_dir)
        bmat = AudioMaterial(bgm)
        bmat.local_material_id = _stable_material_id(bgm)
        bseg = AudioSegment(bmat, trange(0, total_us), source_timerange=trange(0, min(total_us, bmat.duration)))
        bseg.volume = 0.35
        proj.add_segment(bseg, "AudioMix")

    proj.save()
    _write_meta_info(draft_dir, total_us)
    print(f"✅ 智能变焦草稿：{draft_dir}（{added}次点击缩放）")
    return draft_dir


# =====================================================================
# 8. 影视解说模板（对齐上游 movie_commentary_builder：分镜→解说→合成）
# =====================================================================
def movie_commentary_draft(
    name: str,
    video_path: str,
    storyboard: List[Dict],
    voice: str = "云健",
    bgm_path: Optional[str] = None,
    subtitle_y: float = -0.8,
) -> str:
    """影视解说草稿：按分镜裁剪主视频 + 逐镜 TTS 解说 + 字幕 + 单音轨。

    storyboard: [{"start_s": 0, "dur_s": 8, "narration": "这句解说..."}, ...]
    """
    name = sanitize_project_name(name)
    folder = DraftFolder(DRAFT_ROOT)
    draft_dir = safe_draft_dir(name)
    if os.path.exists(draft_dir):
        backup_existing_draft(draft_dir)
    proj = folder.create_draft(name, width=CANVAS_W, height=CANVAS_H, fps=FPS, allow_replace=True)
    proj.append_track(TrackSpec(TrackType.video, "MainVideo"))
    proj.append_track(TrackSpec(TrackType.audio, "AudioMix"))
    proj.append_track(TrackSpec(TrackType.text, "Subtitles"))

    norm_video = normalize_video_for_jianying(video_path, draft_dir)
    staged = stage_material(norm_video, draft_dir)
    mat = VideoMaterial(staged)
    mat.local_material_id = _stable_material_id(staged)

    voice_key = TTS_VOICES.get(voice, voice)
    tmp_dir = os.path.join(draft_dir, "materials", "tts_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    total_us = 0
    audios, subs = [], []
    for i, shot in enumerate(storyboard):
        st = float(shot.get("start_s", 0))
        du = float(shot.get("dur_s", 5))
        narr = str(shot.get("narration", "")).strip()
        # 视频裁剪段
        seg_len_us = int(du * 1e6)
        vseg = VideoSegment(mat, trange(total_us, seg_len_us),
                            source_timerange=trange(int(st * 1e6), seg_len_us))
        vseg.volume = 0.0
        add_ken_burns(vseg, total_us, seg_len_us, "zoom_in_slow")
        # 段落间自动加官方转场（v7.7.1：镜头衔接更专业，非最后一镜才挂）
        if i < len(storyboard) - 1:
            add_scene_transition(vseg, "叠化", 0.5)
        proj.add_segment(vseg, "MainVideo")
        # 解说
        if narr:
            ap = os.path.join(tmp_dir, f"n{i:03d}.mp3")
            if tts_sentence(narr, ap, voice=voice_key):
                audios.append(ap)
                d = probe_duration_s(ap)
                subs.append((narr, total_us / 1e6, (total_us + d * 1e6) / 1e6))
                if d * 1e6 > seg_len_us:
                    print(f"⚠️ 镜{i+1}解说{d:.1f}s > 镜头{du}s，字幕会延出（建议调快语速或加长镜头）")
        total_us += seg_len_us

    # 配音拼接单音轨
    if audios:
        voice_combined = os.path.join(draft_dir, "materials", "voice_combined.wav")
        if _concat_audios(audios, voice_combined):
            staged_voice = stage_material(voice_combined, draft_dir)
            bgm_path = _resolve_bgm(bgm_path, max_dur=total_us / 1e6)
            if bgm_path and os.path.exists(bgm_path):
                mix_out = os.path.join(draft_dir, "materials", "audio_mix.wav")
                _mix_voice_bgm(voice_combined, bgm_path, mix_out, total_us / 1e6,
                               voice_volume=1.0, bgm_volume=0.35, duck_volume=0.15)
                if os.path.exists(mix_out):
                    voice_combined = mix_out
            amat = AudioMaterial(stage_material(voice_combined, draft_dir))
            amat.local_material_id = _stable_material_id(stage_material(voice_combined, draft_dir))
            aseg = AudioSegment(amat, trange(0, total_us),
                                source_timerange=trange(0, min(total_us, amat.duration)))
            aseg.volume = 1.0
            proj.add_segment(aseg, "AudioMix")

    # 字幕
    style = TextStyle(size=5.0, bold=True, color=(1.0, 1.0, 1.0), align=2)
    border = jy.TextBorder(color=(0.0, 0.0, 0.0), alpha=1.0, width=40.0)
    for narr, st, en in subs:
        s_us = int(st * 1e6)
        d_us = max(int((en - st) * 1e6), 300_000)
        d_us = min(d_us, total_us - s_us)
        if d_us <= 0:
            continue
        tseg = TextSegment(narr, trange(s_us, d_us), style=style,
                           border=border, clip_settings=ClipSettings(transform_y=subtitle_y))
        proj.add_segment(tseg, "Subtitles")

    proj.save()
    _write_meta_info(draft_dir, total_us)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"✅ 影视解说草稿：{draft_dir}（{len(storyboard)}镜，{total_us/1e6:.0f}s）")
    return draft_dir


if __name__ == "__main__":
    print("剪映工厂 v7.7 高级算子已加载")
    print("可用：add_ken_burns / narrated_draft / clone_draft / match_assets_by_script")
    print("      build_cloud_text_styles_library / web_to_video / record_screen / apply_zoom_draft / movie_commentary_draft")
