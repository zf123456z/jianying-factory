#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 聚蚁AI双屏常驻热点广告模板（v1.0 正式模板）
================================================================
【模板类型】无配音 · 纯文字动画 · 热点+产品双屏混剪（对标聚蚁AI打法）
【核心特征】
  1. 上半屏热点区：主标题/副标题/补充句 三行层级，全程常驻（仅入场动画）
  2. 下半屏产品区：品牌/卖点1/卖点2/CTA 四行层级，全程常驻
  3. 每条文字独立文本轨（text_h1..text_p4），互不重叠、不退出
  4. 素材自动混剪铺满 + 原片强制静音
  5. 剪映云音乐正版动感 BGM 自动匹配、铺满截断
【样式搭配】3 档预设（gold 黄金爆款 / tech 蓝科技 / hot 红黑热辣）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jyfactory.engine import JianyingVectcutEngine
from jyfactory.media import CloudManager

DUAL_SCREEN_STYLES = {
    "gold": {
        "name": "黄金爆款档",
        "texts": [
            ("text_h1", "title",    16, "#FFD400", True,  "打字机", 0.75, 0.8, 0.0),
            ("text_h2", "subtitle", 10, "#FFFFFF", False, "渐显",   0.55, 0.6, 0.6),
            ("text_h3", "tagline",  9,  "#FF3B30", True,  "弹入",   0.40, 0.6, 1.2),
            ("text_p1", "brand",    14, "#FFD400", True,  "打字机", -0.40, 0.8, 0.0),
            ("text_p2", "selling_a", 9.5, "#FFFFFF", False, "渐显", -0.58, 0.6, 0.8),
            ("text_p3", "selling_b", 9.5, "#FFFFFF", True, "渐显",  -0.70, 0.6, 1.4),
            ("text_p4", "cta",      9,  "#FF3B30", True,  "弹入",  -0.82, 0.6, 2.0),
        ],
    },
    "tech": {
        "name": "蓝科技档",
        "texts": [
            ("text_h1", "title",    16, "#4FC3F7", True,  "打字机", 0.75, 0.8, 0.0),
            ("text_h2", "subtitle", 10, "#FFFFFF", False, "渐显",   0.55, 0.6, 0.6),
            ("text_h3", "tagline",  9,  "#FFD400", True,  "弹入",   0.40, 0.6, 1.2),
            ("text_p1", "brand",    14, "#4FC3F7", True,  "打字机", -0.40, 0.8, 0.0),
            ("text_p2", "selling_a", 9.5, "#FFFFFF", False, "渐显", -0.58, 0.6, 0.8),
            ("text_p3", "selling_b", 9.5, "#FFFFFF", True, "渐显",  -0.70, 0.6, 1.4),
            ("text_p4", "cta",      9,  "#FF3B30", True,  "弹入",  -0.82, 0.6, 2.0),
        ],
    },
    "hot": {
        "name": "红黑热辣档",
        "texts": [
            ("text_h1", "title",    17, "#FF3B30", True,  "打字机", 0.60, 0.9, 0.0),
            ("text_h2", "subtitle", 10, "#FFFFFF", False, "渐显",   0.45, 0.6, 0.6),
            ("text_h3", "tagline",  9,  "#FFD400", True,  "弹入",   0.32, 0.6, 1.2),
            ("text_p1", "brand",    14, "#FFD400", True,  "打字机", -0.40, 0.8, 0.0),
            ("text_p2", "selling_a", 9.5, "#FFFFFF", False, "渐显", -0.58, 0.6, 0.8),
            ("text_p3", "selling_b", 9.5, "#FFFFFF", True, "渐显",  -0.70, 0.6, 1.4),
            ("text_p4", "cta",      9,  "#FFFFFF", True,  "弹入",  -0.82, 0.7, 2.0),
        ],
    },
}

BGM_KEYWORDS = ["动感", "科技", "燃", "节奏", "电子", "摇滚", "未来"]

PREFERRED_BGM_IDS = [
    "7274070492730329149",  # Cyberpunk Techno Sport Action（赛博动感）
    "7377929381982930955",  # 科技未来运动
    "7376242731608606731",  # 狂野热血激燃电子
]


def _pick_bgm(cm: CloudManager, keyword: str = None) -> str:
    for mid in PREFERRED_BGM_IDS:
        if cm.find_asset(mid):
            return mid
    kws = [keyword] if keyword else BGM_KEYWORDS
    for kw in kws:
        if not kw:
            continue
        hits = cm.search_assets(kw, 12)
        for a in hits:
            dur = a.get("duration_s")
            if dur and dur >= 18.0:
                return a["id"]
    return None


def _split_videos(videos: list, duration: float) -> list:
    n = max(len(videos), 1)
    base = duration / n
    segs = []
    t = 0.0
    for v in videos[:n]:
        segs.append((v, t, base))
        t += base
    return segs


def produce_hotspot_ad(
    title: str,
    subtitle: str,
    tagline: str,
    brand: str,
    selling_a: str,
    selling_b: str,
    cta: str,
    videos: list,
    bgm_keyword: str = None,
    duration: float = 18.0,
    style: str = "gold",
    project: str = "聚蚁模板_热点广告",
    bgm_volume: float = 0.5,
) -> str:
    if style not in DUAL_SCREEN_STYLES:
        raise ValueError(f"未知样式档 {style}，可选: {list(DUAL_SCREEN_STYLES)}")
    if not videos:
        raise ValueError("videos 素材列表不能为空")

    style_cfg = DUAL_SCREEN_STYLES[style]
    texts_map = {
        "title": title, "subtitle": subtitle, "tagline": tagline,
        "brand": brand, "selling_a": selling_a, "selling_b": selling_b, "cta": cta,
    }
    print(f"\n===== 聚蚁AI双屏常驻模板 · 样式档「{style_cfg['name']}」 · {duration:.0f}s =====")

    eng = JianyingVectcutEngine()
    if not eng.ensure_server():
        print("FATAL: VectCutAPI 服务不可用")
        sys.exit(1)

    draft_id = eng.create_draft(1080, 1920)

    segs = _split_videos(videos, duration)
    for v, t, seg_dur in segs:
        eng.add_video(draft_id, v, volume=0.0, start=0, end=seg_dur,
                      target_start=t, track_name="video")
        print(f"  └ 素材混剪 {os.path.basename(v)} → {t:.1f}-{t + seg_dur:.1f}s")

    for track, key, size, color, bold, anim, y, border, delay in style_cfg["texts"]:
        eng.add_text(
            draft_id, texts_map[key], delay, duration,
            font_size=size, font_color=color, bold=bold,
            intro_animation=anim, intro_duration=0.8,
            transform_y=y, border_width=border, track_name=track,
        )
        print(f"  └ [{track}] {texts_map[key][:18]}…  {size}号 {color} {anim}")

    cm = CloudManager()
    music_id = _pick_bgm(cm, bgm_keyword)
    if music_id:
        eng.add_cloud_music(draft_id, music_id, volume=bgm_volume,
                            track_name="bgm", start=0, end=duration)
        print(f"  └ BGM 云音乐 {music_id} 铺满 {duration:.0f}s")
    else:
        print("  ⚠️ 未匹配到 BGM（可接受）")

    dest = eng.save_and_deploy(draft_id, project)
    print(f"✅ 部署完成: {dest}")
    return dest


if __name__ == "__main__":
    dest = produce_hotspot_ad(
        title="GPT-6 免费了！", subtitle="12亿人直接开用",
        tagline="客户都去AI里问了？你的店还搜不到？",
        brand="红鲤AI超级Agent",
        selling_a="一句话，调度所有 AI 员工，跑完整条营销链路",
        selling_b="批量剪视频 · 全网挖客户 · 7×24 自动转化",
        cta="评论区打「GEO」，领 AI 获客方案",
        videos=[
            r"E:\张总口播素材\混剪素材\ae634d2874d0a04cd9fdbf1516fda1fc.mp4",
            r"E:\张总口播素材\混剪素材\微信视频2026-07-21_111028_228.mp4",
            r"E:\张总口播素材\混剪素材\2.mp4",
        ],
        bgm_keyword="动感", duration=18.0, style="gold",
        project="聚蚁模板_GPT6热点_红鲤AI广告",
    )
    print("RESULT|" + dest)
