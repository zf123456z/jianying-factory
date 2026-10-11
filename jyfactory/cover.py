#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 自动封面生成
从视频里截一帧，加爆款标题文字，自动生成封面
"""
import os
from . import config
import subprocess
from PIL import Image, ImageDraw, ImageFont


class CoverGenerator:
    """自动封面生成器"""

    def __init__(self, output_dir: str = config.COVER_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_cover(
        self,
        video_path: str,
        title: str,
        output_name: str = None,
        frame_time: float = 1.0,
    ) -> str:
        """从视频里截一帧，加标题文字，生成封面"""
        frame_path = os.path.join(self.output_dir, "temp_frame.jpg")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(frame_time),
            "-i", video_path, "-vframes", "1",
            "-q:v", "2", frame_path
        ], capture_output=True)

        if not os.path.exists(frame_path):
            raise Exception("截帧失败")

        img = Image.open(frame_path)
        draw = ImageDraw.Draw(img)

        font_paths = [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
        ]
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, 80)
                break

        if not font:
            font = ImageFont.load_default()

        lines = []
        current = ""
        for char in title:
            current += char
            if len(current) >= 7:
                lines.append(current)
                current = ""
        if current:
            lines.append(current)

        img_w, img_h = img.size
        line_height = 100
        total_text_height = len(lines) * line_height
        start_y = img_h // 4 - total_text_height // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (img_w - text_w) // 2
            y = start_y + i * line_height

            for dx in [-3, 0, 3]:
                for dy in [-3, 0, 3]:
                    draw.text((x+dx, y+dy), line, font=font, fill=(0, 0, 0))

            draw.text((x, y), line, font=font, fill=(255, 215, 0))

        if not output_name:
            output_name = f"封面_{hash(title) % 10000}.jpg"

        cover_path = os.path.join(self.output_dir, output_name)
        img.save(cover_path, quality=95)

        print(f"✅ 封面生成完成：{cover_path}")
        return cover_path


if __name__ == "__main__":
    gen = CoverGenerator()
    cover = gen.generate_cover(
        video_path=config.DEFAULT_VIDEO_ALT,
        title="GEO获客三步法",
        output_name="GEO封面.jpg"
    )
    print(f"封面路径：{cover}")
