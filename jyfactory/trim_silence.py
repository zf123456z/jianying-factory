#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频静音智能裁剪（剪映工厂 · 智能剪口播）
1. 自动剪掉开头结尾的静音，一开口就有声音
2. 自动压缩中间过长停顿（>0.8s 压缩到 0.25s），口播节奏更紧凑，不拖沓
3. 保留短停顿和语义停顿，不破坏语音自然度
（吸收 YGtemple/talking-head 智能剪口播思路）
"""
import subprocess
import os
import json
import tempfile


def detect_silence(audio_path: str, noise_db: int = -30, min_silence_ms: int = 300):
    """用ffmpeg silencedetect检测音频里的静音段"""
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_silence_ms/1000}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    stderr = result.stderr

    silences = []
    for line in stderr.split("\n"):
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].strip())
        if "silence_end:" in line:
            end = float(line.split("silence_end:")[1].split("|")[0].strip())
            silences.append((start, end))

    # 音频总时长
    cmd2 = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    total = float(subprocess.run(cmd2, capture_output=True, text=True).stdout.strip())
    return silences, total


def _compile_keep_segments(silences, total, head_silence_ms=200, tail_silence_ms=200,
                           mid_max_ms=800, mid_target_ms=250):
    """计算要保留的音频段（去首尾 + 压缩中间长停顿）"""
    keep = []  # (start, end) 保留段列表

    start = 0.0
    if silences and silences[0][0] < 0.1:  # 开头有静音
        start = max(0.0, silences[0][1] - head_silence_ms / 1000)

    for i, (s, e) in enumerate(silences):
        if s < start + 0.05:
            continue  # 与当前起点重叠的静音跳过
        # 中间长停顿压缩：>mid_max_ms 的静音，保留前 mid_target_ms 作为语义缓冲
        dur = (e - s) * 1000
        if 0.1 < s and e < total - 0.1 and dur > mid_max_ms:
            # 长停顿：压缩到 mid_target_ms
            keep.append((start, s + mid_target_ms / 1000))
            start = e
        else:
            # 短停顿（≤800ms）：完整保留，不打断语义节奏
            keep.append((start, e))
            start = e

    # 结尾
    end = total
    if silences and silences[-1][1] > total - 0.1:  # 结尾有静音
        end = silences[-1][0] + tail_silence_ms / 1000
        end = min(total, end)
    if start < end - 0.05:
        keep.append((start, end))

    return keep


def trim_silence(audio_path: str, output_path: str = None, head_silence_ms: int = 200,
                 tail_silence_ms: int = 200, mid_max_ms: int = 800, mid_target_ms: int = 250):
    """
    智能剪口播：去首尾静音 + 压缩中间过长停顿
    :param mid_max_ms: 超过该时长的中间静音视为"过长停顿"
    :param mid_target_ms: 过长停顿压缩后的目标长度
    """
    if output_path is None:
        base, ext = os.path.splitext(audio_path)
        output_path = base + "_trimmed" + ext

    silences, total = detect_silence(audio_path)
    if not silences:
        print("✅ 没有检测到明显静音，直接复制原文件")
        import shutil
        shutil.copy(audio_path, output_path)
        return output_path, 0.0, total

    keep = _compile_keep_segments(silences, total, head_silence_ms, tail_silence_ms, mid_max_ms, mid_target_ms)
    if not keep:
        print("✅ 无可裁剪内容，直接复制原文件")
        import shutil
        shutil.copy(audio_path, output_path)
        return output_path, 0.0, total

    # 合并相邻保留段（间隔<50ms视为连续）
    merged = []
    for seg in keep:
        if merged and seg[0] - merged[-1][1] < 0.05:
            merged[-1] = (merged[-1][0], seg[1])
        else:
            merged.append(seg)

    # 统计
    orig_voice = sum(e - s for s, e in merged if not (silences and silences[0][0] < 0.1 and s < 0.1))
    total_keep = sum(e - s for s, e in merged)
    print(f"🔇 原时长：{total:.1f}s → 处理后：{total_keep:.1f}s（省 {total-total_keep:.1f}s，{100*(total-total_keep)/total:.0f}%）")
    for i, (s, e) in enumerate(merged):
        print(f"   保留段{i+1}: {s:.2f}s ~ {e:.2f}s（{e-s:.2f}s）")

    # 用 ffmpeg filter 拼接保留段（concat filter 避免中间转码质量损失）
    if len(merged) == 1:
        cmd = [
            "ffmpeg", "-y", "-ss", str(merged[0][0]), "-i", audio_path,
            "-t", str(merged[0][1] - merged[0][0]),
            "-c:a", "libmp3lame", "-q:a", "2", output_path
        ]
    else:
        parts = []
        for s, e in merged:
            parts.extend(["-ss", f"{s:.3f}", "-t", f"{e-s:.3f}", "-i", audio_path])
        # 用 filter_complex 做 concat
        inputs = [str(i) for i in range(len(merged))]
        filter_complex = "".join(f"[{i}:a]atrim=0:{merged[i][1]-merged[i][0]:.3f},asetpts=PTS-STARTPTS[a{i}];" for i in range(len(merged)))
        filter_complex += "".join(f"[a{i}]" for i in range(len(merged))) + f"concat=n={len(merged)}:v=0:a=1[outa]"
        cmd = [
            "ffmpeg", "-y", *parts,
            "-filter_complex", filter_complex,
            "-map", "[outa]", "-c:a", "libmp3lame", "-q:a", "2", output_path
        ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        print(f"⚠️ 智能裁剪失败（{result.stderr[-200:]}），回退只剪首尾")
        # 回退：只剪首尾静音
        cmd2 = [
            "ffmpeg", "-y", "-ss", str(keep[0][0]), "-i", audio_path,
            "-t", str(keep[-1][1] - keep[0][0]),
            "-c:a", "libmp3lame", "-q:a", "2", output_path
        ]
        subprocess.run(cmd2, capture_output=True)
    print(f"✅ 智能剪口播完成：{output_path}")
    return output_path, keep[0][0], keep[-1][1]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法：python trim_silence.py 配音文件.mp3")
        sys.exit(1)
    inp = sys.argv[1]
    out, s, e = trim_silence(inp)
    print(f"输出：{out}")
