#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂宣传片 - 何公子复刻版（1:1 复刻 WorkBuddy 保姆级教程爆款骨架）
================================================================
复刻何公子画面骨架（逐层对应）：
  1. 深绿渐变+网格暗底（背景图贯穿全片）
  2. 左上角「剪映工厂」品牌白字 + 「本期主题」绿色胶囊按钮
  3. 英文标识区：每主题换（SOLO CREATOR SYSTEM / RESULT GALLERY / ...）
  4. 主标题（大白字）+ 副标题（小字），逐段换内容
  5. 中部"模拟界面"功能卡片：编号+状态（已生成/正在展示/DONE）+功能名+一句话说明
  6. 右下角张总圆形头像（透明覆盖层，全程常驻）
  7. 底部口播字幕条（SRT 黄字+关键词高亮）
  8. 逐段文字动画（打字机/弹入/渐显错峰）+ 剪映正版 BGM + edge 云希口播
结尾：YOUR NEXT STEP → 评论区扣「剪映工厂」→ 关注解锁更多豆包技能
"""
import os
import sys

PROJECT_ROOT = r"D:\AI工作区\jianying-factory"
sys.path.insert(0, PROJECT_ROOT)

from jyfactory.engine import JianyingVectcutEngine
from jyfactory.narrated import narrate_script, build_srt

# ---------- 1. 口播文案（短句、口语化，按 [，。！？] 自动断句） ----------
SCRIPT = (
    "装好了剪映，还在自己一帧一帧地剪？"
    "素材不会找，文案不会写，剪辑太费时。其实它一句话就能搞定。"
    "第一步，找热点。全网热点秒抓，爆款逻辑自动拆解。"
    "第二步，写文案。钩子、干货、转化，原创改写不洗稿。"
    "第三步，配音加字幕。你的声音克隆配音，官方识别字幕逐句对齐。"
    "第四步，音乐加特效。剪映正版曲库BGM，智能包装自动加花字和转场。"
    "第五步，一键成片。秒出草稿，自动导出。"
    "你出想法，它出成品。关注我，解锁更多豆包技能。"
)

# 段落定义：句索引区间(含引导句+说明句,消除空档) → (英文标识, 主标题, 副标题)
# segs 句序: 0装好了/1素材不会找/2一句话就能搞定/3第一步找热点/4全网热点秒抓/
#           5第二步写文案/6钩子干货转化/7第三步配音/8你的声音克隆配音/9第四步音乐/
#           10剪映正版曲库BGM/11第五步一键成片/12秒出草稿/13你出想法/14关注我
SECTIONS = [
    (0, 0,  "SOLO CREATOR SYSTEM", "装好了剪映，还在自己一帧一帧剪？", None),
    (1, 2,  "SOLO CREATOR SYSTEM", "其实它一句话就能搞定", "素材不会找 · 文案不会写 · 剪辑太费时"),
    (3, 4,  "RESULT GALLERY",       "全网热点",       "AI热点秒抓 · 爆款逻辑自动拆解"),
    (5, 6,  "CONTENT LAB",          "爆款口播稿",     "钩子干货转化 · 原创不洗稿"),
    (7, 8,  "VOICE & CAPTION",      "克隆声音+识别字幕", "你的声音配音 · 字幕逐句对齐"),
    (9, 10, "STYLE ENGINE",         "正版BGM+智能包装", "剪映曲库音乐 · 自动花字转场"),
    (11, 12,"EXECUTION LOG",        "秒出草稿 自动导出", "一句话，剪映自己把视频剪好"),
    (13, 14,"YOUR NEXT STEP",       "完整演示等你解锁", "评论区扣「剪映工厂」"),
]

# 中部模拟界面功能卡片：句索引 → (编号+状态, 功能名, 说明)
CARDS = [
    (3, 4,   "01 · 已生成",     "找热点",   "AI热点秒抓 爆款逻辑自动拆解"),
    (5, 6,   "02 · 已生成",     "写文案",   "钩子干货转化 原创不洗稿"),
    (7, 8,   "03 · 正在展示",   "配音字幕", "克隆声音 识别字幕逐句对齐"),
    (9, 10,  "04 · 已生成",     "音乐特效", "正版BGM 智能包装花字转场"),
    (11, 12, "05 · DONE",      "一键成片", "秒出草稿 自动导出"),
]

# ---------- 2. 素材与配置 ----------
BG_IMAGE = r"D:\AI工作区\素材\剪映工厂_何公子风背景_带头像.png"  # 深绿渐变网格背景（头像已合成进背景，避免透明层转码丢alpha变黑底）
OUT_VOICE = r"D:\AI工作区\配音\promo_hegongzi"
PROJECT_NAME = "剪映工厂宣传片_何公子复刻版"
SPEAKER = "zh-CN-YunxiNeural"          # edge 云希自然男声
BGM_QUERY = "7274070492730329149"      # 剪映白名单动感科技纯音乐（Cyberpunk）
BGM_FALLBACK = "科技"
SUB_KEYWORDS = ["剪映工厂", "豆包", "AI", "BGM", "克隆", "字幕"]


def find_range(segs, seg_span):
    """按句索引区间取时间窗（含引导句+说明句，消除段落空档）"""
    i0, i1 = seg_span
    i0 = max(0, min(i0, len(segs) - 1))
    i1 = max(i0, min(i1, len(segs) - 1))
    return segs[i0]["start"], segs[i1]["end"]


def main():
    eng = JianyingVectcutEngine()
    eng.ensure_server()

    # 1) 配音（逐句 TTS + 真实静音拼接，SRT 样本级一致）
    voice_wav, segs, total_dur = narrate_script(
        SCRIPT, speaker=SPEAKER, out_dir=OUT_VOICE, prefix="hgz"
    )
    if not voice_wav or total_dur <= 0:
        print("❌ 配音失败")
        return ""
    print(f"✅ 配音完成 {total_dur:.1f}s  {voice_wav}")

    # 2) SRT 字幕（时间戳与配音严格对齐）
    srt_path = os.path.join(OUT_VOICE, "hgz.srt")
    build_srt(segs, srt_path)

    # 3) 建草稿：背景(主视频轨，含头像) + 配音 + BGM
    draft_id = eng.create_draft(1080, 1920)
    eng.add_video(draft_id, BG_IMAGE, volume=0.1, start=0, end=total_dur,
                  target_start=0, track_name="video")
    eng.add_audio(draft_id, voice_wav, volume=1.0, start=0, end=total_dur,
                  track_name="audio_main")
    eng.add_cloud_music(draft_id, BGM_QUERY, end=total_dur, track_name="bgm",
                        auto_balance=True, voice_path=voice_wav) or \
        eng.add_cloud_music(draft_id, BGM_FALLBACK, end=total_dur, track_name="bgm",
                            auto_balance=True, voice_path=voice_wav)

    # 4) 底部字幕（黄字 + 关键词高亮）
    eng.add_subtitle(draft_id, srt_path, font_size=9.0, font_color="#FFD400",
                     background_alpha=0.3, bold=True, keywords=SUB_KEYWORDS)

    # 5) 左上品牌 + 本期主题胶囊（全程常驻）
    eng.add_text(draft_id, "剪映工厂", start=0, end=total_dur,
                 font_size=5.0, font_color="#FFFFFF",
                 transform_x=-0.78, transform_y=0.86, bold=True,
                 intro_animation="渐显", intro_duration=0.5)
    eng.add_text(draft_id, "本期主题", start=0, end=total_dur,
                 font_size=4.0, font_color="#4CAF50",
                 transform_x=-0.70, transform_y=0.77, bold=True,
                 background_alpha=0.45, background_color="#000000",
                 background_round_radius=0.5,
                 intro_animation="渐显", intro_duration=0.5)

    # 6) 分段落：英文标识 / 主标题 / 副标题（逐段替换，打字机+弹入+渐显错峰）
    for i, (si0, si1, eng_label, h1, h2) in enumerate(SECTIONS):
        t_start, t_end = find_range(segs, (si0, si1))
        t_end += 0.2
        dur = max(0.5, t_end - t_start)
        # 英文标识
        eng.add_text(draft_id, eng_label, start=t_start, end=t_end,
                     font_size=3.5, font_color="#B8FFD8",
                     transform_x=-0.62, transform_y=0.63,
                     intro_animation="渐显", intro_duration=0.4,
                     track_name=f"eng_{i}")
        # 主标题（大白字，打字机；超长自动拆两行+居中，防出屏）
        h1_lines = h1 if "\n" in h1 else (h1[:len(h1)//2] + "\n" + h1[len(h1)//2:] if len(h1) > 9 else h1)
        eng.add_text(draft_id, h1_lines, start=t_start, end=t_end,
                     font_size=16.0 if len(h1) <= 9 else 14.0, font_color="#FFFFFF",
                     transform_x=0.0, transform_y=0.58, bold=True,
                     border_width=1.0, border_color="#000000",
                     intro_animation="打字机_I", intro_duration=0.6,
                     track_name=f"h1_{i}")
        # 副标题（小字渐显，晚 0.3s，与主标题拉开间距防重叠）
        if h2:
            eng.add_text(draft_id, h2, start=t_start + 0.3, end=t_end,
                         font_size=7.5, font_color="#A8E6C8",
                         transform_x=0.0, transform_y=0.40,
                         intro_animation="渐显", intro_duration=0.5,
                         track_name=f"h2_{i}")

    # 7) 中部模拟界面功能卡片（编号+状态 / 功能名 / 说明，弹入+渐显）
    for i, (si0, si1, badge, card_name, card_desc) in enumerate(CARDS):
        start, end = find_range(segs, (si0, si1))
        end += 0.2
        # 编号+状态（小胶囊，黄色）
        eng.add_text(draft_id, badge, start=start, end=end,
                     font_size=5.0, font_color="#FFD400",
                     transform_x=-0.30, transform_y=0.18, bold=True,
                     intro_animation="弹入", intro_duration=0.35,
                     track_name=f"cb_{i}")
        # 功能名（白字）
        eng.add_text(draft_id, card_name, start=start + 0.15, end=end,
                     font_size=11.0, font_color="#FFFFFF",
                     transform_x=-0.30, transform_y=0.12, bold=True,
                     intro_animation="弹入", intro_duration=0.4,
                     track_name=f"cn_{i}")
        # 说明（浅色小字）
        eng.add_text(draft_id, card_desc, start=start + 0.35, end=end,
                     font_size=8.0, font_color="#D8F0FF",
                     transform_x=-0.30, transform_y=0.04,
                     intro_animation="渐显", intro_duration=0.5,
                     track_name=f"cd_{i}")

    # 8) 结尾大 CTA（关注我，解锁更多豆包技能）
    start, end = find_range(segs, (13, 14))
    end += 0.2
    eng.add_text(draft_id, "关注我，解锁更多豆包技能", start=start, end=end,
                 font_size=13.0, font_color="#FFD400",
                 transform_x=0.0, transform_y=0.24, bold=True,
                 border_width=1.0, border_color="#000000",
                 intro_animation="弹入", intro_duration=0.5,
                 track_name="cta_end")

    # 9) 保存部署 → 剪映草稿箱
    dest = eng.save_and_deploy(draft_id, PROJECT_NAME)
    if dest:
        print(f"\n✅ 何公子复刻版草稿已部署: {dest}")
        print(f"   总时长 {total_dur:.1f}s | 品牌/英文/主副标题/卡片/头像/字幕/配音/BGM 全轨就绪")
    else:
        print("❌ 部署失败")
    return dest


if __name__ == "__main__":
    main()
