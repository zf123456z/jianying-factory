#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 首批落库 · 出片验证脚本（2026-10-12）
================================================================
负责 3 条验证草稿：
  1. P0模板_warning-list_验证_20261012   —— 由 jyfactory/style_producer.produce_style 渲染
     （也可直接运行 `python -m jyfactory.style_producer` 重新渲染）
  2. P0模板_contrast_验证_20261012       —— produce_hotspot_ad(style="contrast")
  3. P0模板_headline-top_验证_20261012   —— produce_hotspot_ad(style="headline-top")

每条约跑 jyfactory/draft_checker.check_draft + style_producer.self_check，
最后输出统一 PASS/FAIL 清单。

文案全部为原创（GEO/AI获客主题），未照搬任何爆款具体文案。
videos 取自 E:\\张总口播素材（张总形象.mp4 / 张总视频.mp4 / 12.mp4），duration=18.0。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jyfactory.juyi_template import produce_hotspot_ad
from jyfactory.draft_checker import check_draft
from jyfactory.style_producer import self_check

VIDEOS = [
    r"E:\张总口播素材\张总形象.mp4",
    r"E:\张总口播素材\张总视频.mp4",
    r"E:\张总口播素材\12.mp4",
]

CONTRAST_DRAFT = "P0模板_contrast_验证_20261012"
HEADLINE_DRAFT = "P0模板_headline-top_验证_20261012"
WARNING_DRAFT = "P0模板_warning-list_验证_20261012"


def render_contrast():
    """样式档 contrast：红黄对比双屏（痛点红/优势黄）· 原创 GEO 获客文案"""
    return produce_hotspot_ad(
        title="传统推广，客户正在流失",
        subtitle="AI时代，获客方式已经变了",
        tagline="你的店还在AI搜索里隐身？",
        brand="红鲤AI超级Agent",
        selling_a="传统方式：人工跟单、成本高、漏客率高",
        selling_b="AI方式：7×24自动获客、批量转化",
        cta="评论区打「GEO」，领AI获客方案",
        videos=VIDEOS, bgm_keyword="动感", duration=18.0,
        style="contrast", project=CONTRAST_DRAFT, bgm_volume=0.35,
    )


def render_headline_top():
    """样式档 headline-top：贴顶头条（白字粗描边）· 原创 GEO 获客文案"""
    return produce_hotspot_ad(
        title="AI获客进入爆发期",
        subtitle="今天不布局，明天更难追",
        tagline="流量正在流向AI搜索入口",
        brand="红鲤AI超级Agent",
        selling_a="AI自动写文案、批量发内容、全天候跟进",
        selling_b="一次搭建，全年自动获客",
        cta="评论区扣「GEO」，免费领诊断",
        videos=VIDEOS, bgm_keyword="动感", duration=18.0,
        style="headline-top", project=HEADLINE_DRAFT, bgm_volume=0.35,
    )


def main():
    print("\n############ P0 出片验证 ############")
    # 1. contrast
    print("\n---- 渲染 contrast ----")
    dest1 = render_contrast()
    print("RESULT|" + dest1)
    # 2. headline-top
    print("\n---- 渲染 headline-top ----")
    dest2 = render_headline_top()
    print("RESULT|" + dest2)
    # 3. warning-list 已由 style_producer.__main__ 渲染；此处仅复检
    print("\n---- warning-list（由 style_producer.__main__ 渲染，此处复检）----")

    print("\n\n############ draft_checker 输出 ############")
    for name in (WARNING_DRAFT, CONTRAST_DRAFT, HEADLINE_DRAFT):
        print(f"\n=== draft_checker: {name} ===")
        check_draft(name)

    print("\n\n############ 自查断言（self_check）############")
    overall = []
    for name, dur in ((WARNING_DRAFT, 12.0), (CONTRAST_DRAFT, 18.0), (HEADLINE_DRAFT, 18.0)):
        print(f"\n=== self_check: {name} ===")
        results, ok = self_check(name, dur)
        overall.append((name, results, ok))

    print("\n\n############ PASS/FAIL 汇总 ############")
    all_ok = True
    for name, results, ok in overall:
        fails = [r for r in results if not r[1]]
        status = "✅ 全部 PASS" if ok else f"❌ {len(fails)} 项 FAIL"
        print(f"{status}  {name}")
        for r in fails:
            print(f"    ❌ FAIL [{r[0]}] {r[2]}")
        all_ok = all_ok and ok
    print("=" * 60)
    print("总体结论:", "✅ 全部 PASS" if all_ok else "❌ 存在 FAIL，请排查")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
