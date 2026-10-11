#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚蚁AI双屏常驻模板 · 生产示例（GPT-6热点+红鲤AI产品）
用法：python examples/聚蚁模板_热点广告.py
等价 CLI：python cli.py hotspot-ad --title "GPT-6 免费了！" ...
"""
import sys

sys.path.insert(0, r"D:\AI工作区\jianying-factory")
from jyfactory.juyi_template import produce_hotspot_ad

dest = produce_hotspot_ad(
    title="GPT-6 免费了！", subtitle="12亿人直接开用",
    tagline="客户都去AI里问了？你的店还搜不到？",
    brand="红鲤AI超级Agent",
    selling_a="一句话，调度所有 AI 员工，跑完整条营销链路",
    selling_b="批量剪视频 · 全网挖客户 · 7×24 自动转化",
    cta="评论区打「GEO」，领 AI 获客方案",
    videos=[
        r"E:\张总口播素材\混剪素材\ae634d2874d0a04cd9fdbf1516fda1fc.mp4",
        r"E:\张总口播素材\混剪素材\微信视频2026-07-21_111028_228.mp4",
        r"E:\张总口播素材\混剪素材\2.mp4",
    ],
    bgm_keyword="动感", duration=18.0, style="gold",
    project="聚蚁模板_GPT6热点_红鲤AI广告_v3_20261009",
)
print("RESULT|" + dest)
