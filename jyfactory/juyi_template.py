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
  每档定义 主标题/副标题/补充句/品牌/卖点/CTA 的字号·颜色·动画·描边层级

用法：
    from jyfactory.juyi_template import produce_hotspot_ad
    dest = produce_hotspot_ad(
        title="GPT-6 免费了！", subtitle="12亿人直接开用",
        tagline="客户都去AI里问了？你的店还搜不到？",
        brand="红鲤AI超级Agent",
        selling_a="一句话，调度所有 AI 员工，跑完整条营销链路",
        selling_b="批量剪视频 · 全网挖客户 · 7×24 自动转化",
        cta="评论区打「GEO」，领 AI 获客方案",
        videos=[m1, m2, m3], bgm_keyword="动感", duration=18.0,
        style="gold", project="聚蚁模板_热点广告",
    )
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jyfactory.engine import JianyingVectcutEngine
from jyfactory.media import CloudManager

# ===================== 样式搭配预设（3 档 · 花样增强版 2026-10-17） =====================
# 每档定义 7 条常驻文字的字号/颜色/动画/描边/安全线内 y 位置
# y 正值=上半屏热点区，负值=下半屏产品区（字号安全线：≤10 → ±0.80；11-16 → ±0.75；>16 → ±0.60）
# 审美规则来源：docs/视频视觉拆解方法论.md（聚蚁AI式双屏广告拆解 + 爆款通用规则）
# ── 用户指正（2026-10-17）：文字花样更丰富 + 主/副标题不换行 ──
#   1. 花样规则：主标题/品牌=高亮暖色大号加粗；副标题=暖白(金白)；补充句/CTA=红强调；
#      卖点1=中性白，卖点2=科技蓝/暖金点缀——同屏≥4 色层次，不单调
#   2. 不换行铁律：一句话一行。先精炼文案（主标题≤12字、副标题≤18字），
#      超宽由引擎 auto_fit 自动缩字号兜底（单行自适应，2026-10-13 规则）
# 字号比例：主标题16=100%基准，副标题10=62%，补充9=56%，品牌14=87%，卖点9.5=59%，CTA9=56%
# 动画：打字机→渐显→弹入 三级错峰（0/0.6/1.2s），全部常驻只入场不退出
DUAL_SCREEN_STYLES = {
    "gold": {  # 档A 黄金爆款（默认，黄主+金白副+红补+金品牌+蓝点缀）
        "name": "黄金爆款档",
        "texts": [
            # (轨道, 文案位, 字号, 颜色, 加粗, 动画, y, 描边, 入场延迟)
            ("text_h1", "title",    16, "#FFD400", True,  "打字机", 0.72, 0.9, 0.0),
            ("text_h2", "subtitle", 10, "#FFE9A8", False, "渐显",   0.52, 0.7, 0.6),
            ("text_h3", "tagline",  9,  "#FF3B30", True,  "弹入",   0.38, 0.6, 1.2),
            ("text_p1", "brand",    14, "#FFD400", True,  "打字机", -0.38, 0.9, 0.0),
            ("text_p2", "selling_a", 9.5, "#FFFFFF", False, "渐显", -0.56, 0.6, 0.8),
            ("text_p3", "selling_b", 9.5, "#7ED4FF", True, "渐显",  -0.68, 0.6, 1.4),
            ("text_p4", "cta",      9,  "#FF3B30", True,  "弹入",  -0.80, 0.7, 2.0),
        ],
    },
    "tech": {  # 档B 蓝科技（科技感，适合AI/数码热点，蓝主+白副+黄补+蓝品牌+暖金点缀）
        "name": "蓝科技档",
        "texts": [
            ("text_h1", "title",    16, "#4FC3F7", True,  "打字机", 0.72, 0.9, 0.0),
            ("text_h2", "subtitle", 10, "#E8F6FF", False, "渐显",   0.52, 0.7, 0.6),
            ("text_h3", "tagline",  9,  "#FFD400", True,  "弹入",   0.38, 0.6, 1.2),
            ("text_p1", "brand",    14, "#4FC3F7", True,  "打字机", -0.38, 0.9, 0.0),
            ("text_p2", "selling_a", 9.5, "#FFFFFF", False, "渐显", -0.56, 0.6, 0.8),
            ("text_p3", "selling_b", 9.5, "#FFE9A8", True, "渐显",  -0.68, 0.6, 1.4),
            ("text_p4", "cta",      9,  "#FF3B30", True,  "弹入",  -0.80, 0.7, 2.0),
        ],
    },
    "hot": {  # 档C 红黑热辣（强冲击，适合争议/惊悚热点，红主+金白副+黄补+红CTA）
        "name": "红黑热辣档",
        "texts": [
            ("text_h1", "title",    17, "#FF3B30", True,  "打字机", 0.58, 1.0, 0.0),
            ("text_h2", "subtitle", 10, "#FFE9A8", False, "渐显",   0.42, 0.7, 0.6),
            ("text_h3", "tagline",  9,  "#FFD400", True,  "弹入",   0.30, 0.6, 1.2),
            ("text_p1", "brand",    14, "#FFD400", True,  "打字机", -0.38, 0.9, 0.0),
            ("text_p2", "selling_a", 9.5, "#FFFFFF", False, "渐显", -0.56, 0.6, 0.8),
            ("text_p3", "selling_b", 9.5, "#FFB3A7", True, "渐显",  -0.68, 0.6, 1.4),
            ("text_p4", "cta",      9,  "#FFFFFF", True,  "弹入",  -0.80, 0.8, 2.0),
        ],
    },
}

# 标题精炼建议阈值（2026-10-17 用户规则：主/副标题禁止换行 → 先精炼文案）
TITLE_TIGHT_COPY = {"title": 12, "subtitle": 18}  # 主标题≤12字、副标题≤18字（超长时打印精炼建议）

# 常用动感 BGM 关键词（剪映云音乐库，命中第一个即用）
BGM_KEYWORDS = ["动感", "科技", "燃", "节奏", "电子", "摇滚", "未来"]

# 已实测认可的动感纯音乐（用户验收过），优先命中
PREFERRED_BGM_IDS = [
    "7274070492730329149",  # 时尚燃烧冲击开幕 - Cyberpunk Techno Sport Action（v3已用，赛博动感）
    "7377929381982930955",  # 科技未来运动 - Energetic Sport Electronic
    "7376242731608606731",  # 狂野热血激燃电子 - I Will Tear You Apart
]


def _pick_bgm(cm: CloudManager, keyword: str = None) -> str:
    """选择 BGM：先查已认可白名单 → 再按关键词在云音乐库匹配动感纯音乐"""
    # 1. 白名单优先（已实测认可）
    for mid in PREFERRED_BGM_IDS:
        if cm.find_asset(mid):
            return mid
    # 2. 关键词搜索（名称模糊匹配，偏好长于18s的纯音乐）
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
    """把素材按总时长等分轮播（每段时长 = duration / len(videos)）"""
    n = max(len(videos), 1)
    base = duration / n
    segs = []
    t = 0.0
    for v in videos[:n]:
        segs.append((v, t, base))
        t += base
    return segs


def _suggest_tight_copy(title: str, subtitle: str) -> None:
    """标题精炼建议（2026-10-17 用户规则：主/副标题禁止换行 → 先精炼文案再缩字号）。
    超长时打印精炼建议（不阻断生成；引擎 auto_fit 仍会缩字号兜底保一行）。"""
    limits = TITLE_TIGHT_COPY
    for key, text in (("title", title), ("subtitle", subtitle)):
        if not text:
            continue
        n = len(text)
        if n > limits[key]:
            print(f"  ⚠️ [{key}] {n}字 超精炼阈值{limits[key]}字 → 建议精炼："
                  f"「{text[:limits[key]]}…」当前由引擎自动缩字号保单行（不换行）")


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
    """全链路生成聚蚁AI双屏常驻热点广告（无配音纯文字动画）

    流程：样式档 → 建草稿 → 素材自动混剪(原片静音) → 双屏常驻文字(独立轨分层)
          → BGM自动匹配铺满 → 部署草稿箱 → 返回草稿路径
    """
    if style not in DUAL_SCREEN_STYLES:
        raise ValueError(f"未知样式档 {style}，可选: {list(DUAL_SCREEN_STYLES)}")
    if not videos:
        raise ValueError("videos 素材列表不能为空")

    style_cfg = DUAL_SCREEN_STYLES[style]
    texts_map = {
        "title": title, "subtitle": subtitle, "tagline": tagline,
        "brand": brand, "selling_a": selling_a, "selling_b": selling_b, "cta": cta,
    }
    _suggest_tight_copy(title, subtitle)  # 主/副标题精炼校验（不换行铁律）
    print(f"\n===== 聚蚁AI双屏常驻模板 · 样式档「{style_cfg['name']}」 · {duration:.0f}s =====")

    eng = JianyingVectcutEngine()
    if not eng.ensure_server():
        print("FATAL: VectCutAPI 服务不可用")
        sys.exit(1)

    draft_id = eng.create_draft(1080, 1920)

    # 1. 视频主轨：素材自动混剪（原片强制静音）
    segs = _split_videos(videos, duration)
    for v, t, seg_dur in segs:
        eng.add_video(draft_id, v, volume=0.0, start=0, end=seg_dur,
                      target_start=t, track_name="video")
        print(f"  └ 素材混剪 {os.path.basename(v)} → {t:.1f}-{t + seg_dur:.1f}s")

    # 2. 双屏常驻文字：7 条独立轨，只入场不退出
    for track, key, size, color, bold, anim, y, border, delay in style_cfg["texts"]:
        eng.add_text(
            draft_id, texts_map[key], delay, duration,
            font_size=size, font_color=color, bold=bold,
            intro_animation=anim, intro_duration=0.8,
            transform_y=y, border_width=border, track_name=track,
        )
        print(f"  └ [{track}] {texts_map[key][:18]}…  {size}号 {color} {anim}")

    # 3. BGM：剪映云音乐自动匹配 + 铺满
    cm = CloudManager()
    music_id = _pick_bgm(cm, bgm_keyword)
    if music_id:
        eng.add_cloud_music(draft_id, music_id, volume=bgm_volume,
                            track_name="bgm", start=0, end=duration)
        print(f"  └ BGM 云音乐 {music_id} 铺满 {duration:.0f}s")
    else:
        print("  ⚠️ 未匹配到 BGM（可接受）")

    # 4. 部署草稿箱
    dest = eng.save_and_deploy(draft_id, project)
    print(f"✅ 部署完成: {dest}")
    return dest


if __name__ == "__main__":
    # 自测：GPT-6 热点示例（与 v3 草稿同构）
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
        project="聚蚁模板_GPT6热点_红鲤AI广告_v3_20261009",
    )
    print("RESULT|" + dest)
