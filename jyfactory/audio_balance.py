#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剪映工厂 - BGM/人声响度自动平衡（专业级规则）"""
import os
import re
import subprocess


def measure_mean_volume(wav: str) -> float:
    null = "NUL" if os.name == "nt" else "/dev/null"
    r = subprocess.run(["ffmpeg", "-i", wav, "-af", "volumedetect", "-f", "null", null],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", r.stderr or "")
    return float(m.group(1)) if m else -20.0


def auto_bgm_volume(voice_wav: str, bgm_wav: str,
                    headroom_db: float = 15.0,
                    min_vol: float = 0.03, max_vol: float = 0.9) -> float:
    v = measure_mean_volume(voice_wav)
    b = measure_mean_volume(bgm_wav)
    target = v - headroom_db
    delta = target - b
    vol = 10 ** (delta / 20.0)
    vol = max(min_vol, min(max_vol, vol))
    print(f"🎚 响度平衡: 人声{v:.1f}dB / BGM原{b:.1f}dB → 目标{target:.1f}dB (低{headroom_db:.0f}dB, 需调{delta:+.1f}dB) → volume={vol:.2f}")
    return vol


def normalize_voice(voice_wav: str, target_mean_db: float = -16.0,
                    out_path: str = None) -> str:
    v = measure_mean_volume(voice_wav)
    delta = target_mean_db - v
    if abs(delta) < 1.0:
        print(f"🎚 人声响度: {v:.1f}dB 已达标（目标{target_mean_db:.0f}dB），无需归一化")
        return voice_wav
    out = out_path or (os.path.splitext(voice_wav)[0] + "_norm.wav")
    gain = 10 ** (delta / 20.0)
    subprocess.run(["ffmpeg", "-y", "-i", voice_wav, "-af", f"volume={gain:.4f}",
                    "-ar", "44100", "-ac", "2", out],
                   capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if os.path.exists(out):
        print(f"🎚 人声归一化: {v:.1f}dB → {measure_mean_volume(out):.1f}dB (增益{gain:.2f}x) → {os.path.basename(out)}")
        return out
    print("⚠️ 人声归一化失败，用原始 wav")
    return voice_wav
