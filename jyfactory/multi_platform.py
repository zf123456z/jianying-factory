#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台适配 - 一个视频自动生成不同平台版本
"""

import subprocess
from . import config  # T8: 路径单一真源（config.py 为唯一权威）
import os


PLATFORMS = {
    "douyin": {  # 抖音/视频号
        "width": 1080,
        "height": 1920,
        "ratio": "9:16",
        "name": "抖音竖屏"
    },
    "xiaohongshu": {  # 小红书
        "width": 1080,
        "height": 1440,
        "ratio": "3:4",
        "name": "小红书竖屏"
    },
    "bilibili": {  # B站/YouTube
        "width": 1920,
        "height": 1080,
        "ratio": "16:9",
        "name": "横屏"
    },
}


def export_multi_platform(input_video: str, output_dir: str):
    """
    自动导出多平台版本
    """
    print("开始导出多平台版本...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for platform, config in PLATFORMS.items():
        output_path = os.path.join(
            output_dir,
            f"{os.path.basename(input_video).replace('.mp4', '')}_{platform}.mp4"
        )
        
        # 用ffmpeg转比例：缩放+黑边填充
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf",
            f"scale={config['width']}:{config['height']}:force_original_aspect_ratio=decrease,"
            f"pad={config['width']}:{config['height']}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "copy",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"✅ {config['name']}版：{output_path}")


if __name__ == "__main__":
    export_multi_platform(
        input_video=os.path.join(config.EXPORT_DIR, "测试导出.mp4"),
        output_dir=os.path.join(config.EXPORT_DIR, "多平台版本")
    )
