#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂宣传片 - 设计化图文卡片流（对标 WorkBuddy 技能分享爆款，全面升级）
================================================================
画面实现（比上游强在哪）：
  1. 统一品牌框架：深色科技背景 + 左上角标「剪映工厂 JIANYING FACTORY · 本期主题」
  2. 每段一张"功能演示卡片"（编号+功能名+说明），入场/出场动画错峰
  3. 顶部爆款标题花字（疑问式钩子）+ 底部 SRT 精准字幕（关键词高亮）
  4. 逐句配音（edge 云希自然男声）+ 剪映正版 BGM 自动响度平衡铺满
  5. 全程无录屏、无真人、确定性引擎生成，秒级进草稿箱
"""
import os
import sys

PROJECT_ROOT = r"D:\AI工作区\jianying-factory"
sys.path.insert(0, PROJECT_ROOT)

from jyfactory.engine import JianyingVectcutEngine
from jyfactory.narrated import narrate_script, build_srt

TITLE = "豆包一句话，剪映自己就把视频剪好了？"

SCRIPT = (
    "你知道现在做短视频，能有多快吗？"
    "豆包里有个剪映工厂，你只要说一句话，它自己就把视频剪好了。"
    "01，找热点。它自己去全网搜爆款热点。"
    "02，写文案。爆款公式，原创口播稿，直接给你。"
    "03，配音。克隆你的声音，或者用剪映正版音色。"
    "04，字幕。剪映官方识别字幕，自动对齐。"
    "05，音乐。剪映正版BGM，自动铺满。"
    "06，出片。秒级生成，直接进草稿箱。"
    "不用学剪辑，不用写脚本，你出想法，它出成品。"
    "关注我，解锁更多豆包技能。"
)

CARDS = [
    ("找热点",      "01 · 找热点",   "自动全网搜爆款热点"),
    ("写文案",      "02 · 写文案",   "爆款公式原创口播稿"),
    ("配音",        "03 · 配音",     "克隆你的声音 / 正版音色"),
    ("字幕",        "04 · 字幕",     "官方识别字幕自动对齐"),
    ("音乐",        "05 · 音乐",     "正版BGM 自动铺满"),
    ("出片",        "06 · 出片",     "秒级生成进草稿箱"),
    ("关注我",      "你出想法，它出成品", "关注我，解锁更多豆包技能"),
]

BRAND_BADGE = "剪映工厂 JIANYING FACTORY"
BG_IMAGE = r"D:\AI工作区\素材\剪映工厂_科技背景.png"
SCREEN_REC = r"D:\AI工作区\导出\剪映工厂宣传片_录屏版.mp4"
REC_CLIP_START = 12.0
REC_CLIP_END = 30.0
REC_TIMELINE_AT = 6.0
PROJECT_NAME = "剪映工厂宣传片_图文卡片流"
OUT_VOICE = r"D:\AI工作区\配音\promo_card"
SPEAKER = "zh-CN-YunxiNeural"
BGM_QUERY = "7274070492730329149"
BGM_FALLBACK = "科技"
SUB_KEYWORDS = ["剪映工厂", "豆包", "AI", "BGM"]


def find_card_time(segs, keyword):
    starts, ends = [], []
    for seg in segs:
        if keyword in seg["text"]:
            starts.append(seg["start"])
            ends.append(seg["end"])
    if not starts:
        return None
    return min(starts), max(ends)


def main():
    eng = JianyingVectcutEngine()
    eng.ensure_server()

    voice_wav, segs, total_dur = narrate_script(
        SCRIPT, speaker=SPEAKER, out_dir=OUT_VOICE, prefix="card"
    )
    if not voice_wav or total_dur <= 0:
        print("❌ 配音失败")
        return ""
    print(f"✅ 配音完成 {total_dur:.1f}s  {voice_wav}")

    srt_path = os.path.join(OUT_VOICE, "card.srt")
    build_srt(segs, srt_path)

    draft_id = eng.create_draft(1080, 1920)
    rec_dur = REC_CLIP_END - REC_CLIP_START
    rec_end_tl = REC_TIMELINE_AT + rec_dur
    eng.add_video(draft_id, BG_IMAGE, volume=0.1, start=0, end=REC_TIMELINE_AT,
                  target_start=0, track_name="video")
    eng.add_video(draft_id, SCREEN_REC, volume=0.1, start=REC_CLIP_START, end=REC_CLIP_END,
                  target_start=REC_TIMELINE_AT, track_name="video")
    eng.add_video(draft_id, BG_IMAGE, volume=0.1, start=0, end=max(0.5, total_dur - rec_end_tl),
                  target_start=rec_end_tl, track_name="video")
    eng.add_audio(draft_id, voice_wav, volume=1.0, start=0, end=total_dur,
                  track_name="audio_main")

    eng.add_cloud_music(draft_id, BGM_QUERY, end=total_dur, track_name="bgm",
                        auto_balance=True, voice_path=voice_wav) or \
        eng.add_cloud_music(draft_id, BGM_FALLBACK, end=total_dur, track_name="bgm",
                            auto_balance=True, voice_path=voice_wav)

    eng.add_subtitle(draft_id, srt_path, font_size=9.0, font_color="#FFD400",
                     background_alpha=0.3, bold=True, keywords=SUB_KEYWORDS)

    eng.add_text(draft_id, TITLE, start=0, end=total_dur,
                 font_size=12.0, font_color="#FFFFFF",
                 transform_y=0.8, bold=True,
                 border_width=1.2, border_color="#000000",
                 intro_animation="打字机_I", intro_duration=1.2)

    eng.add_text(draft_id, BRAND_BADGE, start=0, end=total_dur,
                 font_size=5.0, font_color="#FFFFFF",
                 transform_x=-0.8, transform_y=0.72, bold=True,
                 background_alpha=0.35, background_color="#000000",
                 background_round_radius=0.3, intro_animation="渐显", intro_duration=0.5)

    for i, (kw, card_title, card_desc) in enumerate(CARDS):
        t = find_card_time(segs, kw)
        if not t:
            print(f"⚠️ 卡片[{kw}]未匹配到配音句，跳过")
            continue
        start, end = t
        dur = max(0.4, end - start)
        y_main = 0.0 if i < 6 else 0.05
        track_main = f"text_{3 + i * 2}"
        track_sub = f"text_{4 + i * 2}"
        eng.add_rich_text(draft_id, card_title, highlights=[{"word": kw.split(" ")[0], "color": "#FFD400", "bold": True, "size": 14}],
                          start=start, end=end + 0.2, font_size=12.0, font_color="#FFFFFF",
                          transform_y=y_main, border_width=1.0, border_color="#000000",
                          intro_animation="弹入", intro_duration=0.4, track_name=track_main)
        if card_desc:
            eng.add_text(draft_id, card_desc, start=start + 0.25, end=end + 0.2,
                         font_size=9.0, font_color="#D8F0FF",
                         transform_y=y_main + 0.13, background_alpha=0.0,
                         intro_animation="渐显", intro_duration=0.5,
                         track_name=track_sub)

    dest = eng.save_and_deploy(draft_id, PROJECT_NAME)
    if dest:
        print(f"\n✅ 宣传片草稿已部署: {dest}")
        print(f"   总时长 {total_dur:.1f}s | 配音/字幕/卡片/标题/BGM 全轨就绪")
    else:
        print("❌ 部署失败")
    return dest


if __name__ == "__main__":
    main()
