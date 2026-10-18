#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 滤镜库
爆款滤镜预设
"""

# 剪映常用爆款滤镜（ID是剪映内部的，后续可以从草稿里提取）
FILTERS = {
    "fresh": {
        "name": "清新",
        "intensity": 0.6,
        "description": "通用清新，适合口播/vlog",
    },
    "warm": {
        "name": "暖阳",
        "intensity": 0.5,
        "description": "温暖治愈，适合情感类",
    },
    "cool": {
        "name": "冷白",
        "intensity": 0.4,
        "description": "干净冷白，适合科技类",
    },
    "vintage": {
        "name": "复古胶片",
        "intensity": 0.5,
        "description": "复古胶片感，适合回忆类",
    },
    "bright": {
        "name": "明亮",
        "intensity": 0.6,
        "description": "提亮画面，适合室内光线暗的素材",
    },
}

# 转场预设
TRANSITIONS = {
    "fade": {
        "name": "叠化",
        "duration": 0.3,
        "description": "最常用，柔和自然",
    },
    "dissolve": {
        "name": "溶解",
        "duration": 0.4,
        "description": "更柔和的过渡",
    },
    "flash": {
        "name": "闪黑",
        "duration": 0.2,
        "description": "节奏快，适合干货类",
    },
    "slide": {
        "name": "滑动",
        "duration": 0.3,
        "description": "左右滑动，动感",
    },
}


def list_filters():
    print("可用滤镜：")
    for key, f in FILTERS.items():
        print(f"  {key}: {f['name']} (强度{f['intensity']}) - {f['description']}")


def list_transitions():
    print("\n可用转场：")
    for key, t in TRANSITIONS.items():
        print(f"  {key}: {t['name']} ({t['duration']}秒) - {t['description']}")


if __name__ == "__main__":
    list_filters()
    list_transitions()
