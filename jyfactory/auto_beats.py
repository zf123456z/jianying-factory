#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动踩点 - 检测BGM节拍点，视频自动跟着节奏切
"""

import subprocess
import re
from typing import List


def detect_beats(bgm_path: str, min_interval_ms: int = 500) -> List[float]:
    """
    检测BGM的节拍点
    返回：节拍时间点列表（秒）
    """
    print("开始检测BGM节拍点...")
    
    # 用ffmpeg的astats滤镜检测音频能量变化
    cmd = [
        "ffmpeg", "-i", bgm_path,
        "-af", "astats=metadata=1:reset=0.2,ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr
    
    # 提取时间戳
    timestamps = re.findall(r"pts_time:([\d.]+)", output)
    levels = re.findall(r"lavfi.astats.Overall.RMS_level=(-?[\d.]+)", output)
    
    # 找能量峰值（节拍点）
    beats = []
    if len(timestamps) > 10:
        # 简单算法：找局部最大值
        prev_level = float(levels[0])
        threshold = -20  # dB
        for i in range(1, len(timestamps)-1):
            current_level = float(levels[i])
            next_level = float(levels[i+1])
            # 如果是局部最大值，且超过阈值，就是节拍点
            if current_level > prev_level and current_level > next_level and current_level > threshold:
                time_sec = float(timestamps[i])
                # 最小间隔限制
                if not beats or (time_sec - beats[-1]) * 1000 > min_interval_ms:
                    beats.append(time_sec)
            prev_level = current_level
    
    print(f"检测到 {len(beats)} 个节拍点")
    return beats


if __name__ == "__main__":
    beats = detect_beats(r"C:\Users\HuaWei\AppData\Local\JianyingPro\User Data\Cache\music\07d8967445d9787434448a1490fa2ff2.mp3")
    print("前10个节拍点：")
    for i, b in enumerate(beats[:10]):
        print(f"  {i+1}. {b:.2f} 秒")
