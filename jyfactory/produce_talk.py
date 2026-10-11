#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 口播视频统一生产模板 v1.0（v8.0 主路径）
================================================================
用法：一句话口播任务 → 本模板 → 剪映草稿箱
流程：文案 → SAMI官方TTS配音(剪映正版音色) → 默认形象循环铺满 → BGM铺满
      → 高亮标题(关键词标红/黄+打字机动画) → 部署草稿箱（不导出）

参数（改 MAIN 区即可）：
  SCRIPT   口播文案全文
  TITLE    爆款标题（支持用 {{高亮词}} 标记要标红的词）
  SPEAKER  sami 音色（默认 zh_male_huoli；克隆音色传 ID）
  HIGHLIGHTS 额外高亮词 [{word,color,bold,size}]
"""
import sys, os, json, subprocess, shutil, glob
from . import config  # 路径单一真源（config.py 为唯一权威）

from .tts import tts_speak
from .engine import JianyingVectcutEngine

# ================= MAIN 区（每次任务改这里） =================
PROJECT_NAME = "口播模板_示例"
SCRIPT = "这是示例文案。AI获客，关键就三步。"
TITLE = "AI获客关键三步"
TITLE_HIGHLIGHTS = [{"word": "GEO", "color": "#FF3B30", "bold": True, "size": 16},
                    {"word": "AI", "color": "#FFD400", "bold": True, "size": 16}]
SPEAKER = "zh_male_huoli"      # 剪映正版音色；克隆音色可传 ID
VIDEO = config.DEFAULT_VIDEO   # 固定素材
BGM_VOL = 0.35                  # 用户铁律：30-40%
BGM_QUERY = "科技"              # 云端音乐关键词（剪映官方曲库，正版零侵权）
VOICE_DIR = config.VOICE_DIR
DRAFT_ROOT = config.DRAFT_DIR
# ============================================================


def pick_bgm():
    """从剪映本地缓存音乐目录挑一首时长合适的正版音乐（无自定义偏好时）"""
    music_dir = os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Cache\music")
    cands = glob.glob(os.path.join(music_dir, "*.mp3")) if os.path.isdir(music_dir) else []
    for c in cands:
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", c], capture_output=True, text=True, timeout=30)
            d = float(r.stdout.strip())
            if 30 <= d <= 600:
                return c
        except Exception:
            continue
    return None


def loop_bgm(bgm, total_dur):
    out = os.path.join(VOICE_DIR, f"{PROJECT_NAME}_bgm_loop.wav")
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", bgm, "-t", f"{total_dur+0.5:.2f}",
                    "-ar", "44100", "-ac", "2", out], check=True, capture_output=True, timeout=300)
    return out


def main():
    eng = JianyingVectcutEngine(draft_root=DRAFT_ROOT)
    if not eng.ensure_server():
        print("❌ VectCutAPI 不可用"); return

    # 1. SAMI 官方配音（剪映正版音色）
    voice = tts_speak(SCRIPT, speaker=SPEAKER,
                      out=os.path.join(VOICE_DIR, f"{PROJECT_NAME}_配音.wav"))
    if not voice:
        print("❌ 配音失败（SAMI与edge都失败）"); return
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", voice], capture_output=True, text=True)
    dur = float(r.stdout.strip())
    print(f"✅ 配音完成: {dur:.1f}s（{SPEAKER}）")

    # 2. 建草稿
    draft_id = eng.create_draft(1080, 1920)
    pos = 0.0
    while pos < dur:
        end = min(60.1, dur - pos)
        eng.add_video(draft_id, VIDEO, volume=0.1, start=0, end=end,
                      target_start=pos, track_name="video")
        pos += end
    eng.add_audio(draft_id, voice, volume=1.0, track_name="audio_main")

    # 3. 云端正版音乐 BGM（按主题词搜索，显式传配音时长铺满截断）
    try:
        eng.add_cloud_music(draft_id, BGM_QUERY, volume=BGM_VOL, end=dur)
    except Exception as e:
        print(f"⚠️ 云端音乐失败({e})，回退本地缓存音乐")
        eng.add_audio(draft_id, loop_bgm(pick_bgm(), dur), volume=BGM_VOL, track_name="bgm")

    # 4. 高亮标题（打字机动画）
    eng.add_rich_text(draft_id, TITLE, TITLE_HIGHLIGHTS,
                      start=0, end=min(6.0, dur),
                      font_size=13.0, transform_y=-0.88,
                      intro_animation="打字机", intro_duration=0.8)

    # 5. 部署
    dest = eng.save_and_deploy(draft_id, PROJECT_NAME)
    print(f"✅ 草稿已部署: {dest}")
    print(f"   时长 {dur:.1f}s | 音色 {SPEAKER} | 标题《{TITLE}》")
    print(eng.report())


if __name__ == "__main__":
    main()
