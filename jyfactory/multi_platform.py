#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台适配 - 一个视频自动生成不同平台版本
"""

import subprocess
from . import config
import os


PLATFORMS = {
    "douyin": {
        "width": 1080, "height": 1920, "ratio": "9:16", "name": "抖音竖屏"
    },
    "xiaohongshu": {
        "width": 1080, "height": 1440, "ratio": "3:4", "name": "小红书竖屏"
    },
    "bilibili": {
        "width": 1920, "height": 1080, "ratio": "16:9", "name": "横屏"
    },
}


def export_multi_platform(input_video: str, output_dir: str):
    """自动导出多平台版本"""
    print("开始导出多平台版本...")

    os.makedirs(output_dir, exist_ok=True)

    for platform, cfg in PLATFORMS.items():
        output_path = os.path.join(
            output_dir,
            f"{os.path.basename(input_video).replace('.mp4', '')}_{platform}.mp4"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf",
            f"scale={cfg['width']}:{cfg['height']}:force_original_aspect_ratio=decrease,"
            f"pad={cfg['width']}:{cfg['height']}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "copy",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"✅ {cfg['name']}版：{output_path}")


if __name__ == "__main__":
    export_multi_platform(
        input_video=os.path.join(config.EXPORT_DIR, "测试导出.mp4"),
        output_dir=os.path.join(config.EXPORT_DIR, "多平台版本")
    )
