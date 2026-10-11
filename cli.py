# -*- coding: utf-8 -*-
"""剪映工厂 CLI - 统一命令行入口（v8.0）
用法：
    python cli.py doctor / ensure / sync-music / templates / produce-tally / hotspot-ad
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_doctor(_a):
    from jyfactory.checks import _check_env
    checks = _check_env()
    fatal = [c for c in checks if not c[3] and c[0] in ("固定素材张总形象", "VectCutAPI服务(9001)", "ffmpeg/ffprobe")]
    for name, val, ok, detail in checks:
        mark = "✅" if ok else ("⚠️" if detail in ("存在", "运行中") else "❌")
        print(f"{mark} {name}: {val}" + ("" if ok else f" {detail}"))
    print(f"\n结论: {'✅ 环境就绪' if not fatal else '❌ 有致命缺失'}")
    return 2 if fatal else (1 if [c for c in checks if not c[3] and c not in fatal] else 0)


def cmd_ensure(_a):
    from jyfactory import JianyingFactory
    jy = JianyingFactory()
    ok = jy.ensure()
    print("服务就绪" if ok else "服务启动失败")
    return 0 if ok else 1


def cmd_sync_music(_a):
    from jyfactory import JianyingFactory
    jy = JianyingFactory()
    n = jy.sync_music()
    print(f"同步完成，新增 {n} 条")
    return 0


def cmd_produce_talk(a):
    from jyfactory import JianyingFactory
    jy = JianyingFactory()
    dest = jy.produce_talk(
        script=a.script, video=a.video, project_name=a.project,
        speaker=a.speaker, bgm=a.bgm, title=a.title, keywords=a.keywords or None,
    )
    if dest:
        print(f"✅ 草稿已部署: {dest}")
        return 0
    print("❌ 生产失败，详见上方日志")
    return 1


def cmd_templates(_a):
    from jyfactory.templates import TemplateManager
    tm = TemplateManager()
    ok = tm.list_templates()
    return 0


def cmd_hotspot_ad(a):
    from jyfactory.juyi_template import produce_hotspot_ad
    dest = produce_hotspot_ad(
        title=a.title, subtitle=a.subtitle, tagline=a.tagline,
        brand=a.brand, selling_a=a.selling_a, selling_b=a.selling_b, cta=a.cta,
        videos=list(a.videos) or None, bgm_keyword=a.bgm,
        duration=a.duration, style=a.style, project=a.project, bgm_volume=a.bgm_volume,
    )
    if dest:
        print(f"✅ 草稿已部署: {dest}")
        return 0
    print("❌ 生产失败，详见上方日志")
    return 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="jyfactory", description="剪映工厂 CLI v8.0")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="环境诊断（只读）").set_defaults(fn=cmd_doctor)
    sub.add_parser("ensure", help="启动/探活 VectCutAPI 服务").set_defaults(fn=cmd_ensure)
    sub.add_parser("sync-music", help="同步剪映缓存正版音乐").set_defaults(fn=cmd_sync_music)
    sub.add_parser("templates", help="列出可用模板").set_defaults(fn=cmd_templates)
    pt = sub.add_parser("produce-tally", help="口播视频一条龙 → 草稿箱")
    pt.set_defaults(fn=cmd_produce_talk)
    pt.add_argument("script", help="口播文案")
    pt.add_argument("--video", required=True, help="视频素材路径")
    pt.add_argument("--project", required=True, help="草稿项目名")
    pt.add_argument("--speaker", default="zh-CN-YunxiNeural", help="音色（默认云希男声）")
    pt.add_argument("--bgm", default=None, help="BGM 关键词（剪映官方/缓存音乐库）")
    pt.add_argument("--title", default=None, help="爆款标题（顶部安全线内）")
    pt.add_argument("--keywords", nargs="*", default=None, help="字幕高亮关键词")
    ha = sub.add_parser("hotspot-ad", help="聚蚁AI双屏常驻热点广告 → 草稿箱")
    ha.set_defaults(fn=cmd_hotspot_ad)
    ha.add_argument("--title", required=True, help="热点主标题")
    ha.add_argument("--subtitle", default="", help="热点副标题")
    ha.add_argument("--tagline", default="", help="热点补充句")
    ha.add_argument("--brand", required=True, help="产品品牌名")
    ha.add_argument("--selling-a", default="", help="产品卖点1")
    ha.add_argument("--selling-b", default="", help="产品卖点2")
    ha.add_argument("--cta", default="", help="收口引导语")
    ha.add_argument("--videos", nargs="+", required=True, help="素材路径（自动混剪铺满）")
    ha.add_argument("--bgm", default=None, help="BGM 关键词（默认自动匹配动感纯音乐）")
    ha.add_argument("--duration", type=float, default=18.0, help="总时长秒数（默认18）")
    ha.add_argument("--style", default="gold", choices=["gold", "tech", "hot"], help="样式档 gold/tech/hot")
    ha.add_argument("--project", required=True, help="草稿项目名")
    ha.add_argument("--bgm-volume", type=float, default=0.5, help="BGM 音量（默认0.5）")
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
