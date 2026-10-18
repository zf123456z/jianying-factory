#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能剪口播 - 自动剪掉无效停顿
"""

import subprocess
import re
from typing import List, Tuple


def detect_silences(audio_path: str, silence_db: int = -25, min_silence_ms: int = 200) -> List[Tuple[float, float]]:
    """检测音频里的静音段"""
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-af", f"silencedetect=noise={silence_db}dB:d={min_silence_ms/1000}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr
    
    silences = []
    silence_starts = re.findall(r"silence_start: ([\d.]+)", output)
    silence_ends = re.findall(r"silence_end: ([\d.]+)", output)
    
    for s, e in zip(silence_starts, silence_ends):
        silences.append((float(s), float(e)))
    
    return silences


def smart_cut_voiceover(audio_path: str, output_path: str, keep_silence_ms: int = 200):
    """
    智能剪口播：自动剪掉过长的停顿，保留短停顿
    keep_silence_ms: 保留多长的停顿（毫秒），超过的剪掉
    """
    print("开始智能剪口播...")
    
    # 1. 检测所有静音段
    silences = detect_silences(audio_path)
    print(f"检测到 {len(silences)} 个静音段")
    
    # 2. 计算要剪掉的部分
    # 每个静音段，只保留中间keep_silence_ms的长度，前后都剪掉
    segments_to_keep = []
    current_pos = 0.0
    
    for s, e in silences:
        silence_dur = e - s
        # 保留中间的keep_silence_ms
        keep_start = s + (silence_dur - keep_silence_ms/1000) / 2
        keep_end = keep_start + keep_silence_ms/1000
        
        # 保留静音段之前的部分
        if keep_start > current_pos:
            segments_to_keep.append((current_pos, keep_start))
        
        current_pos = keep_end
    
    # 保留最后一段
    # 获取音频总时长
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    total_duration = float(result.stdout.strip())
    
    if total_duration > current_pos:
        segments_to_keep.append((current_pos, total_duration))
    
    print(f"剪成 {len(segments_to_keep)} 段")
    
    # 3. 用ffmpeg拼接
    # 先把每段剪出来，再拼接
    temp_files = []
    for i, (start, end) in enumerate(segments_to_keep):
        temp_file = output_path.replace(".wav", f"_temp_{i}.wav")
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-ss", str(start),
            "-to", str(end),
            "-c", "copy",
            temp_file
        ]
        subprocess.run(cmd, capture_output=True)
        temp_files.append(temp_file)
    
    # 生成concat列表
    list_file = output_path.replace(".wav", "_list.txt")
    with open(list_file, "w") as f:
        for tf in temp_files:
            f.write(f"file '{tf}'\n")
    
    # 拼接
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, capture_output=True)
    
    # 清理临时文件
    import os
    for tf in temp_files:
        if os.path.exists(tf):
            os.remove(tf)
    if os.path.exists(list_file):
        os.remove(list_file)
    
    # 计算节省了多少时间
    new_result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", output_path],
        capture_output=True, text=True
    )
    new_duration = float(new_result.stdout.strip())
    saved = total_duration - new_duration
    print(f"✅ 智能剪口播完成：节省了 {saved:.1f} 秒")
    print(f"   原时长：{total_duration:.1f} 秒 → 新时长：{new_duration:.1f} 秒")


if __name__ == "__main__":
    smart_cut_voiceover(
        audio_path=r"D:\AI工作区\素材\GEO口播_张总声音版v3.wav",
        output_path=r"D:\AI工作区\素材\GEO口播_智能剪版.wav"
    )
