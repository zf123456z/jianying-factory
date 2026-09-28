#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 批量生成器 v2（引擎 v7.2 稳定版）
一次输入多条文案，自动生成多个剪映草稿（放草稿箱，不导出）
这是9.9元批量版的核心功能

架构说明（2026-09-27 重构）：
- 旧版依赖 voiceover_builder_v5（手写JSON） + auto_export（UIA导出，剪映10.x不可用）
- v2 统一走稳定引擎 engine_v2.make_voiceover_draft：
  * 素材自包含 + local_material_id 稳定化（上游 v1.7 修复，防媒体丢失）
  * 原视频强制静音、BGM自动铺满
  * 竖屏1080x1920/30fps
- 批量生产的配音由调用方准备（豆包 TTS / 剪映官方克隆音色），本脚本只负责草稿生成
"""
import os
import sys
import time
import argparse
from typing import List, Optional

# 引擎定位：优先仓库内 src/（发布友好），兼容本地 D:\AI工作区\代码
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, "..", "src"), r"D:\AI工作区\代码"):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from engine_v2 import make_voiceover_draft, DRAFT_ROOT, DEFAULT_VIDEO


class BatchGenerator:
    """批量生成器：一次出N条口播草稿（放剪映草稿箱）"""

    def __init__(self, video_source: str = DEFAULT_VIDEO, bgm_path: Optional[str] = None):
        self.video_source = video_source
        self.bgm_path = bgm_path
        self.results = []

    def generate_batch(
        self,
        scripts: List[str],
        voiceover_paths: List[str] = None,
        voiceover_durations: List[float] = None,
        bgm_path: Optional[str] = None,
    ):
        """
        批量生成多条草稿（放草稿箱，不导出）
        :param scripts: 文案列表
        :param voiceover_paths: 配音路径列表（对应每条文案，长度可与scripts相同或留空）
        :param voiceover_durations: 配音时长列表（秒，用于铺满视频/BGM；缺省按配音实际时长）
        :param bgm_path: 统一BGM路径（覆盖实例默认）
        """
        total = len(scripts)
        print("=" * 60)
        print(f"🚀 剪映工厂 - 批量生成 {total} 条草稿（v7.2 稳定引擎）")
        print("=" * 60)

        for i, script in enumerate(scripts):
            print(f"\n📝 正在生成第 {i+1}/{total} 条...")

            draft_name = f"批量_{i+1:02d}_{time.strftime('%H%M%S')}"
            voiceover = voiceover_paths[i] if voiceover_paths and i < len(voiceover_paths) else None
            duration = voiceover_durations[i] if voiceover_durations and i < len(voiceover_durations) else None

            try:
                if duration is None and voiceover:
                    try:
                        import subprocess, json as _json
                        r = subprocess.run(
                            ["ffprobe", "-v", "quiet", "-print_format", "json",
                             "-show_format", voiceover],
                            capture_output=True, text=True, encoding="utf-8")
                        if r.returncode == 0:
                            duration = float(_json.loads(r.stdout)["format"]["duration"])
                    except Exception:
                        duration = None
                if duration is None:
                    duration = 45.0  # 兜底

                draft_path = make_voiceover_draft(
                    name=draft_name,
                    script_text=script,
                    video_path=self.video_source,
                    bgm_path=bgm_path or self.bgm_path,
                    voiceover_path=voiceover,
                    total_duration_s=duration,
                )

                self.results.append({
                    "index": i + 1,
                    "script": script[:30] + ("..." if len(script) > 30 else ""),
                    "draft_name": draft_name,
                    "draft_path": draft_path,
                    "status": "draft_ok",
                })
                print(f"✅ 第{i+1}条完成：{draft_name}")

            except Exception as e:
                print(f"❌ 第{i+1}条失败：{e}")
                self.results.append({
                    "index": i + 1,
                    "script": script[:30] + ("..." if len(script) > 30 else ""),
                    "status": "failed",
                    "error": str(e),
                })

        ok = sum(1 for r in self.results if r["status"] == "draft_ok")
        print("\n" + "=" * 60)
        print(f"📊 批量生成完成！成功 {ok}/{total}，草稿均在剪映草稿箱：{DRAFT_ROOT}")
        print("=" * 60)
        for r in self.results:
            print(f"  {r['index']}. {r['status']:10} | {r['script']}")
        return self.results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="剪映工厂批量生成草稿")
    parser.add_argument("--scripts-file", help="文案文件（每行一条），不传则用内置示例")
    parser.add_argument("--video", default=DEFAULT_VIDEO, help="主素材视频路径（默认张总形象）")
    parser.add_argument("--bgm", default=None, help="BGM路径（可选）")
    parser.add_argument("--voiceovers", nargs="*", default=[], help="配音路径列表（可选）")
    args = parser.parse_args()

    if args.scripts_file and os.path.exists(args.scripts_file):
        with open(args.scripts_file, "r", encoding="utf-8") as f:
            scripts = [line.strip() for line in f if line.strip()]
    else:
        scripts = [
            "大家好，今天给大家讲三个副业赚钱的小思路，第一个就是短视频带货，第二个是知识付费，第三个是本地生活服务。",
            "为什么你做短视频总是起不来号？因为你踩了这三个坑：第一个是内容没有价值，第二个是没有持续更新，第三个是没有引导转化。",
            "普通人最值得做的三个副业，第一个是AI工具代运营，第二个是企业GEO优化，第三个是短视频矩阵。",
        ]

    gen = BatchGenerator(video_source=args.video, bgm_path=args.bgm)
    gen.generate_batch(scripts, voiceover_paths=args.voiceovers or None)
