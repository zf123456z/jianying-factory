#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 逐句TTS + 字幕精准对齐 v1.0（对齐上游 add_narrated_subtitles）
================================================================
【价值】口播视频字幕与配音逐句严格对齐：每句独立TTS→实测时长→
        SRT时间轴（句间100ms间隔）→ 配音整轨 + 字幕轨。

用法：
    from .narrated import narrate_script, build_srt
    voice, srt_path, total_dur = narrate_script(
        "第一句。第二句。第三句！", speaker="zh_male_huoli",
        out_dir=config.VOICE_DIR, prefix="我的口播")
"""
import os
from . import config  # T8: 路径单一真源（config.py 为唯一权威）
import re
import subprocess

sys_path = __file__ and os.path.dirname(os.path.abspath(__file__))
if sys_path:
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)

from .tts import tts_speak

SENT_GAP_MS = 100          # 句间间隔（与上游一致）
MAX_SENT_CHARS = 180       # 单句上限（SAMI 安全长度）


def split_script(script: str) -> list:
    """按中文句读标点分句，保持句子完整"""
    raw = re.split(r"(?<=[。！？；])|(?<=[.!?;])", script.replace("\n", ""))
    out = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        # 超长句继续按逗号拆
        while len(s) > MAX_SENT_CHARS:
            cut = s.rfind("，", 0, MAX_SENT_CHARS)
            if cut == -1 or cut < MAX_SENT_CHARS // 2:
                cut = MAX_SENT_CHARS
            out.append(s[: cut + 1].strip())
            s = s[cut + 1:].strip()
        if s:
            out.append(s)
    return out


def ff_duration(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, timeout=60)
    return float(r.stdout.strip() or 0)


def narrate_script(script: str, speaker: str, out_dir: str, prefix: str = "narration",
                   backend: str = None):
    """逐句 TTS → 每句wav+时长 → concat整轨 → 返回(voice_wav, segs, total_dur)
    segs: [{text, wav, start, end, dur}]（start/end 为秒，含句间间隔）
    backend: None=SAMI优先 / "edge"=强制微软云希（更自然沉稳）"""
    os.makedirs(out_dir, exist_ok=True)
    sentences = split_script(script)
    if not sentences:
        raise ValueError("文案为空")
    segs = []
    t = 0.0
    for i, sent in enumerate(sentences):
        wav = os.path.join(out_dir, f"{prefix}_seg{i:03d}.wav")
        ok = tts_speak(sent, speaker=speaker, out=wav, backend=backend)
        if not ok:
            print(f"⚠️ 第{i+1}句TTS失败，跳过: {sent[:20]}")
            continue
        # 统一转 44100/双声道 wav（SAMI ogg 与 edge mp3 混用前 concat filter 必须同格式）
        wav_u = os.path.join(out_dir, f"{prefix}_seg{i:03d}_u.wav")
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-ar", "44100", "-ac", "2", wav_u],
                       check=True, capture_output=True, timeout=120)
        wav = wav_u
        dur = ff_duration(wav)
        if dur <= 0:
            continue
        segs.append({"text": sent, "wav": wav, "dur": dur,
                     "start": t, "end": t + dur})
        t += dur + SENT_GAP_MS / 1000.0
    if not segs:
        raise RuntimeError("全部句子TTS失败")
    # 拼接整轨：句间插入真实静音（与 SRT 时间轴 100ms 间隔严格一致，
    # 否则音频比字幕短，片尾出现"字幕没播完/黑屏"——历史踩坑）
    # ⚠️ concat demuxer 对 wav 会丢帧（实测丢0.2s）→ 必须用 concat filter（样本级精确）
    silence = os.path.join(out_dir, f"{prefix}_silence.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", f"{SENT_GAP_MS / 1000:.3f}", silence],
                   check=True, capture_output=True, timeout=60)
    voice = os.path.join(out_dir, f"{prefix}_voice.wav")
    inputs = []
    for seg in segs:
        inputs += ["-i", seg["wav"]]
    inputs += ["-i", silence]
    sil_idx = len(segs)  # 静音输入索引
    labels = []
    for i in range(len(segs)):
        labels.append(f"[{i}:a]")
        if i < len(segs) - 1:
            labels.append(f"[{sil_idx}:a]")
    n = len(segs) * 2 - 1
    filter_complex = "".join(labels) + f"concat=n={n}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y"] + inputs +
                   ["-filter_complex", filter_complex, "-map", "[out]",
                    "-ar", "44100", "-ac", "2", voice],
                   check=True, capture_output=True, timeout=600)
    total = ff_duration(voice)
    # 人声响度归一化：推到口播标准平均 -16dB（SAMI 原始约 -21dB，成片偏弱；
    # 归一化后人声清晰、BGM 也有稳定参照=BGM-15dB）
    try:
        from .audio_balance import normalize_voice
        voice = normalize_voice(voice, target_mean_db=-16.0)
    except Exception as e:
        print(f"⚠️ 人声归一化跳过({e})")
    # 整轨时长（归一化不改变时长，用 ffprobe 实测更准）
    total = ff_duration(voice)
    print(f"✅ 逐句配音完成: {len(segs)}句 / 整轨{total:.1f}s")
    return voice, segs, total


def build_srt(segs: list, srt_path: str) -> str:
    """按每句实际时长生成 SRT（句间100ms间隔已并入 start/end）"""
    def ts(sec):
        ms = int(round(sec * 1000))
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    lines = []
    for i, seg in enumerate(segs, 1):
        lines += [str(i), f"{ts(seg['start'])} --> {ts(seg['end'])}", seg["text"], ""]
    srt = "\n".join(lines)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt)
    print(f"✅ SRT 已生成: {len(segs)}条 → {srt_path}")
    return srt_path


if __name__ == "__main__":
    demo = "AI获客，关键就三步。第一步，反向问AI，让AI把高流量关键词挖出来。第二步，锁定AI的参考源。第三步，按AI的审美发内容。记住：人在哪儿，生意就在哪儿。"
    voice, segs, total = narrate_script(demo, "zh_male_huoli",
                                        config.VOICE_DIR, "narration_demo")
    srt = build_srt(segs, os.path.join(config.VOICE_DIR, "narration_demo.srt"))
    print("首3句时间轴:")
    for s in segs[:3]:
        print(f"  {s['start']:.2f}-{s['end']:.2f}s [{s['text'][:20]}]")
