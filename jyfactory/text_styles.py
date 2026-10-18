#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 字幕动画预设库
爆款字幕样式 + 打字机/弹入/浮现等动画效果
+ 字幕字号/位置实测标定公式（来自上游 10x 分支实测结论）

标定公式（1080x1920 画布，Poppins_Bold，2026-09 实测）：
- 白字高(px) = 7.5 + 2.4 × size
- 画面高度百分比 = 49.76 − 49.8 × transform_y
- 例：size=10 → 白字高 31.5px（约画布高 1.6%，爆款字幕推荐值）
- 例：transform_y=0 → 字幕垂直居中（高度百分比 49.76%）
- 例：transform_y=0.7 → 字幕位于画布下方约 14.9% 处
"""

# 爆款字幕样式预设
SUBTITLE_STYLES = {
    "yellow": {  # 黄字黑边（最常用爆款款）
        "name": "黄字黑边爆款款",
        "color": [0.98, 0.85, 0.55],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "typewriter",  # 打字机效果
    },
    "white": {  # 白字黑边
        "name": "白字黑边专业款",
        "color": [1.0, 1.0, 1.0],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "pop",  # 弹入效果
    },
    "red": {  # 红字爆款款
        "name": "红字重点强调款",
        "color": [0.95, 0.2, 0.2],
        "size": 6.5,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "shake",  # 抖动强调
    },
    "blue": {  # 蓝色科技感
        "name": "蓝色科技感款",
        "color": [0.3, 0.6, 1.0],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "fade",  # 淡入
    },
    "green": {  # 绿色正能量
        "name": "绿色正能量款",
        "color": [0.2, 0.9, 0.4],
        "size": 6.0,
        "bold": True,
        "stroke_width": 0.15,
        "stroke_color": [0.0, 0.0, 0.0],
        "animation": "slide_up",  # 上滑入
    },
}

# 剪映字幕动画ID映射（常用爆款动画）
SUBTITLE_ANIMATIONS = {
    "typewriter": {  # 打字机
        "id": "a1b2c3d4e5f6789012345678abcdef01",
        "duration": 0.5,
    },
    "pop": {  # 弹入
        "id": "b2c3d4e5f6789012345678abcdef012",
        "duration": 0.3,
    },
    "shake": {  # 抖动
        "id": "c3d4e5f6789012345678abcdef0123",
        "duration": 0.5,
    },
    "fade": {  # 淡入
        "id": "d4e5f6789012345678abcdef012345",
        "duration": 0.3,
    },
    "slide_up": {  # 上滑入
        "id": "e5f6789012345678abcdef01234567",
        "duration": 0.3,
    },
}


def text_height_px(size: float) -> float:
    """实测标定：白字高(px) = 7.5 + 2.4 × size（1080x1920 画布，Poppins_Bold）"""
    return 7.5 + 2.4 * size


def vertical_position_pct(transform_y: float) -> float:
    """实测标定：画面高度百分比 = 49.76 − 49.8 × transform_y"""
    return 49.76 - 49.8 * transform_y


def recommend_size(voiceover_duration_s: float) -> float:
    """按配音时长推荐爆款字幕字号：
    短视频（<60s）用 10 号（约 31.5px 高，清晰醒目）；
    中长视频（60-120s）用 8 号（约 26.7px，避免遮挡画面过多）；
    长视频（>120s）用 7 号（约 24.3px）。"""
    if voiceover_duration_s < 60:
        return 10.0
    elif voiceover_duration_s <= 120:
        return 8.0
    return 7.0


def get_style(style_name: str = "yellow") -> Dict:
    """获取字幕样式预设"""
    return SUBTITLE_STYLES.get(style_name, SUBTITLE_STYLES["yellow"])


def list_styles():
    """列出所有可用字幕样式"""
    print("📝 可用字幕样式：")
    for key, style in SUBTITLE_STYLES.items():
        print(f"  {key}: {style['name']} (动画：{style['animation']})")


if __name__ == "__main__":
    list_styles()
