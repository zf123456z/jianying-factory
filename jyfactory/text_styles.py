#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 字幕动画预设库
爆款字幕样式 + 打字机/弹入/浮现等动画效果
+ 字幕字号/位置实测标定公式
"""

SUBTITLE_STYLES = {
    "yellow": {
        "name": "黄字黑边爆款款",
        "color": [0.98, 0.85, 0.55],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "typewriter",
    },
    "white": {
        "name": "白字黑边专业款",
        "color": [1.0, 1.0, 1.0],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "pop",
    },
    "red": {
        "name": "红字重点强调款",
        "color": [0.95, 0.2, 0.2],
        "size": 6.5,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "shake",
    },
    "blue": {
        "name": "蓝色科技感款",
        "color": [0.3, 0.6, 1.0],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "fade",
    },
    "green": {
        "name": "绿色正能量款",
        "color": [0.2, 0.9, 0.4],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "slide_up",
    },
}

SUBTITLE_ANIMATIONS = {
    "typewriter": {"id": "a1b2c3d4e5f6789012345678abcdef01", "duration": 0.5},
    "pop": {"id": "b2c3d4e5f6789012345678abcdef012", "duration": 0.3},
    "shake": {"id": "c3d4e5f6789012345678abcdef0123", "duration": 0.5},
    "fade": {"id": "d4e5f6789012345678abcdef012345", "duration": 0.3},
    "slide_up": {"id": "e5f6789012345678abcdef01234567", "duration": 0.3},
}


def text_height_px(size: float) -> float:
    """实测标定：白字高(px) = 7.5 + 2.4 × size（1080x1920 画布，Poppins_Bold）"""
    return 7.5 + 2.4 * size


def vertical_position_pct(transform_y: float) -> float:
    """实测标定：画面高度百分比 = 49.76 − 49.8 × transform_y"""
    return 49.76 - 49.8 * transform_y


def recommend_size(voiceover_duration_s: float) -> float:
    """按配音时长推荐爆款字幕字号"""
    if voiceover_duration_s < 60:
        return 10.0
    elif voiceover_duration_s <= 120:
        return 8.0
    return 7.0


def get_style(style_name: str = "yellow") -> dict:
    return SUBTITLE_STYLES.get(style_name, SUBTITLE_STYLES["yellow"])


def list_styles():
    print("📝 可用字幕样式：")
    for key, style in SUBTITLE_STYLES.items():
        print(f"  {key}: {style['name']} (动画：{style['animation']})")


if __name__ == "__main__":
    list_styles()
