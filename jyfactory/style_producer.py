#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 通用样式消费函数（P0 高级模板库 · 数据层 → 出片层）
================================================================
【适用场景】
  消费 data/style_templates.json 中的任意模板 code（含 P0 新增 8 条：
  warning-list / side-bigword / card-list / big-block-cover /
  hook-stack-cover / knowledge-card / chapter-flow / jianying-cover-lockup，
  以及既有 8 条口播模板）一键出片：
  竖屏 1080x1920 + 素材等分混剪静音 + 文字按 layers 逐层常驻（只入场不退出）
  + 本地/云 BGM 铺满截断。后续同事只需用本函数即可完成 7 条仅落库模板的出片验证。

【参数说明】
  code        : style_templates.json 的模板 code（必填）
  texts_map   : {role: 文案} dict，role 必须与模板 layers[].role 一一对应。
                文案位即各 layers 的 role 字段（P0 新条目）：
                  warning-list         → 警告标题/清单一/清单二/清单三/清单四/收尾金句/字幕
                  side-bigword         → 主大字/副大字/字幕
                  card-list            → 主标题/要点1/要点2/要点3/要点4/CTA
                  big-block-cover      → 主标题/高亮词/副标题/CTA
                  hook-stack-cover     → 钩子1/钩子2/钩子3/高亮/CTA
                  knowledge-card       → 大字标题/要点卡1/要点卡2/要点卡3/字幕
                  chapter-flow         → 章节徽标/章节标题/章节要点卡/字幕
                  jianying-cover-lockup→ 主标题/副标题/系列标签/底部提示
  videos      : 素材视频绝对路径列表，等分混剪铺满主轨（原片强制静音）
  duration    : 总时长秒（默认 12.0）；所有文字 end=duration，铺满不中途消失
  bgm_keyword : 本地 BGM 缺失时云音乐兜底的关键词（如 "动感"）
  project     : 部署到剪映草稿箱的项目名；缺省自动生成 P0模板_{code}_验证_20261012
  bgm_volume  : BGM 音量（默认 0.35）

【返回】草稿绝对路径（D:/AI工作区/剪映草稿/<project>）

【高亮实现说明】
  层含 highlight_word/highlight_color 时，本函数用 add_text + text_styles
  实现词级高亮（与引擎 add_rich_text 同一机制：把高亮词写成 text_styles
  区间样式），以便 transform_x/bold/background_color/background_round_radius
  等字段全部透传（add_rich_text 不接收这些字段，直接调用会丢背景色块/圆角）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jyfactory import config
from jyfactory.engine import JianyingVectcutEngine
from jyfactory.media import CloudManager
from jyfactory.juyi_template import _pick_bgm, _split_videos

STYLE_TEMPLATES_PATH = os.path.join(config.JYFACTORY_ROOT, "data", "style_templates.json")
LOCAL_BGM = config.DEFAULT_BGM  # D:\AI工作区\BGM\默认口播BGM_01.mp3

# 需要透传给引擎 add_text 的排版字段（层里有才透传，缺省走引擎默认值）
_TEXT_PASSTHROUGH = (
    "font_size", "font_color", "transform_x", "transform_y",
    "border_width", "border_color", "bold",
    "background_alpha", "background_color", "background_round_radius",
)


def _load_style(code: str) -> dict:
    """读取 style_templates.json 并按 code 找到模板条目"""
    data = json.load(open(STYLE_TEMPLATES_PATH, encoding="utf-8"))
    for t in data.get("templates", []):
        if t.get("code") == code:
            return t
    raise ValueError(
        f"style_templates.json 中不存在 code={code}；可选: "
        f"{[x['code'] for x in data.get('templates', [])]}"
    )


def _highlight_styles(text: str, word: str, color: str, font_size: float) -> list:
    """构造词级高亮 text_styles（与引擎 add_rich_text 同一机制）"""
    styles = []
    pos = 0
    while True:
        idx = text.find(word, pos)
        if idx == -1:
            break
        styles.append({
            "start": idx,
            "end": idx + len(word),
            "style": {"size": font_size + 2, "bold": True, "color": color},
        })
        pos = idx + len(word)
    return styles


def produce_style(code: str, texts_map: dict, videos: list,
                  duration: float = 12.0, bgm_keyword: str = None,
                  project: str = None, bgm_volume: float = 0.35) -> str:
    """通用样式消费：按 style_templates.json 的 layers 逐层出片（详见模块 docstring）"""
    tpl = _load_style(code)
    if not videos:
        raise ValueError("videos 素材列表不能为空")

    print(f"\n===== 通用样式消费 · {tpl.get('name', code)} · {duration:.0f}s =====")
    eng = JianyingVectcutEngine()
    if not eng.ensure_server():
        raise RuntimeError("VectCutAPI 服务不可用（ensure_server 失败）")

    draft_id = eng.create_draft(1080, 1920)

    # 1. 视频主轨：素材等分混剪（原片强制静音，复用 juyi_template._split_videos）
    for v, t, seg_dur in _split_videos(videos, duration):
        eng.add_video(draft_id, v, volume=0.0, start=0, end=seg_dur,
                      target_start=t, track_name="video")
        print(f"  └ 素材混剪 {os.path.basename(v)} → {t:.1f}-{t + seg_dur:.1f}s")

    # 2. 文字层：按 role 取文案，字段全部透传，start=delay，end=duration（不中途消失）
    used_tracks = {}
    for layer in tpl.get("layers", []):
        role = layer.get("role", "text")
        text = texts_map.get(role)
        if text is None:
            raise ValueError(f"texts_map 缺少 role={role} 的文案（模板 {code}）")
        n = used_tracks.get(role, 0) + 1
        used_tracks[role] = n
        track_name = f"text_{role}" if n == 1 else f"text_{role}_{n}"

        start = float(layer.get("delay", 0.0))
        end = float(duration)
        kw = {}
        for k in _TEXT_PASSTHROUGH:
            if k in layer:
                kw[k] = layer[k]
        if "intro_animation" in layer:
            kw["intro_animation"] = layer["intro_animation"]
            kw["intro_duration"] = float(layer.get("intro_duration", 0.5))
        word = layer.get("highlight_word")
        color = layer.get("highlight_color")
        if word and color:
            kw["text_styles"] = _highlight_styles(
                str(text), str(word), str(color), float(layer.get("font_size", 12.0)))
        eng.add_text(draft_id, str(text), start, end, track_name=track_name, **kw)
        print(f"  └ [{track_name}] {str(text)[:16]}…  {kw.get('font_size', layer.get('font_size', ''))}号")

    # 3. BGM：本地默认口播 BGM 优先，缺失时云音乐兜底（铺满截断）
    if os.path.isfile(LOCAL_BGM):
        eng.add_audio(draft_id, LOCAL_BGM, volume=bgm_volume,
                      track_name="bgm", start=0, end=duration)
        print(f"  └ BGM 本地 {os.path.basename(LOCAL_BGM)} 铺满 {duration:.0f}s")
    else:
        cm = CloudManager()
        music_id = _pick_bgm(cm, bgm_keyword)
        if music_id:
            eng.add_cloud_music(draft_id, music_id, volume=bgm_volume,
                                track_name="bgm", start=0, end=duration)
            print(f"  └ BGM 云音乐 {music_id} 铺满 {duration:.0f}s")
        else:
            print("  ⚠️ 未匹配到 BGM（可接受）")

    # 4. 部署草稿箱（全新草稿名，绝不覆盖既有草稿）
    dest = eng.save_and_deploy(draft_id, project or f"P0模板_{code}_验证_20261012")
    print(f"✅ 部署完成: {dest}")
    return dest


def self_check(draft_name: str, expected_duration: float = None):
    """P0 出片自查：断言草稿 JSON 的 4 项硬指标

      a) 每条文字 segment 的结束时刻 == 总时长（文字不中途消失）
      b) 视频段 volume == 0（原片强制静音）
      c) bgm 轨时长 == 视频轨时长（±0.15s，铺满截断）
      d) 所有文字 transform_y 在安全线内（字号≤10→|y|≤0.80；11-16→|y|≤0.75；>16→|y|≤0.60；|x|≤0.45）

    返回 (results, all_ok)；同时打印 PASS/FAIL 明细。
    """
    path = os.path.join(config.DRAFT_DIR, draft_name, "draft_content.json")
    results = []
    if not os.path.exists(path):
        print(f"❌ FAIL 草稿不存在: {path}")
        return results, False
    data = json.load(open(path, encoding="utf-8"))
    total_us = data.get("duration", 0)
    total_sec = total_us / 1e6
    if expected_duration is not None and abs(total_sec - expected_duration) > 0.05:
        results.append(("草稿总时长", False, f"{total_sec:.2f}s != 期望 {expected_duration}s"))

    text_mats = {m.get("id"): m for m in data.get("materials", {}).get("texts", [])}

    def _font_size_of(m: dict) -> float:
        """真实字号存在 material.content.styles[0].size（顶层 font_size 为无关默认值）"""
        try:
            content = json.loads(m.get("content", "{}"))
            styles = content.get("styles", [])
            if styles:
                return float(styles[0].get("size", 12.0))
        except Exception:
            pass
        return float(m.get("font_size", 12.0))

    def _limit(fs: float) -> float:
        return 0.80 if fs <= 10 else (0.75 if fs <= 16 else 0.60)

    text_ok, vol_ok, bgm_ok, safe_ok = True, True, True, True
    video_dur_us = 0
    bgm_dur_us = 0
    n_text = 0
    n_video = 0
    n_bgm = 0
    for tr in data.get("tracks", []):
        ttype = tr.get("type")
        tname = tr.get("name")
        for seg in tr.get("segments", []):
            tt = seg.get("target_timerange", {})
            dur_us = tt.get("duration", 0)
            start_us = tt.get("start", 0)
            if ttype == "video":
                n_video += 1
                video_dur_us += dur_us
                vol = seg.get("volume")
                if vol is None or abs(float(vol) - 0.0) > 1e-6:
                    vol_ok = False
            elif ttype == "audio" and tname == "bgm":
                n_bgm += 1
                bgm_dur_us += dur_us
            elif ttype == "text":
                n_text += 1
                end_us = start_us + dur_us
                if abs(end_us - total_us) > 10000:  # ±0.01s
                    text_ok = False
                mid = seg.get("material_id")
                m = text_mats.get(mid, {})
                fs = _font_size_of(m)
                clip = seg.get("clip", {})
                trf = clip.get("transform", {})
                y = float(trf.get("y", 0.0))
                if abs(y) > _limit(fs) + 1e-6:
                    safe_ok = False
                x = float(trf.get("x", 0.0))
                if abs(x) > 0.45 + 1e-6:
                    safe_ok = False

    bgm_dur_s = bgm_dur_us / 1e6
    video_dur_s = video_dur_us / 1e6
    if abs(bgm_dur_s - video_dur_s) > 0.15:
        bgm_ok = False

    results.append(("文字end==总时长(不中途消失)", text_ok, f"{n_text} 条文字"))
    results.append(("video段volume==0", vol_ok, f"{n_video} 段，视频轨 {video_dur_s:.2f}s"))
    results.append(("bgm时长==视频轨时长(±0.15s)", bgm_ok, f"bgm {bgm_dur_s:.2f}s / video {video_dur_s:.2f}s"))
    results.append(("transform_y安全线内", safe_ok, f"{n_text} 条文字按字号档位限幅"))

    for name, ok, detail in results:
        print(f"{'✅ PASS' if ok else '❌ FAIL'} [{name}] {detail}")
    return results, all(ok for _, ok, _ in results)


if __name__ == "__main__":
    # 自测示例：warning-list 全链路出片（原创 GEO/AI获客 主题警告清单文案，非任何爆款原文）
    _dest = produce_style(
        "warning-list",
        texts_map={
            "警告标题": "警告！你的客户正在被AI抢走",
            "清单一": "客户问AI：这家店靠谱吗？搜不到＝直接出局",
            "清单二": "同行已用AI批量获客，你还在等自然流量",
            "清单三": "传统推广成本翻倍，询盘量却越来越少",
            "清单四": "不布局GEO，你的店会在AI推荐里消失",
            "收尾金句": "现在布局AI获客，还来得及",
            "字幕": "评论区打「GEO」，领专属获客诊断方案",
        },
        videos=[
            r"E:\张总口播素材\张总形象.mp4",
            r"E:\张总口播素材\张总视频.mp4",
            r"E:\张总口播素材\12.mp4",
        ],
        duration=12.0, bgm_keyword="动感",
        project="P0模板_warning-list_验证_20261012",
    )
    from jyfactory.draft_checker import check_draft
    check_draft(os.path.basename(_dest))
    self_check(os.path.basename(_dest), 12.0)
    print("RESULT|" + _dest)
