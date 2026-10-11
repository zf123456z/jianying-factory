#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 环境诊断 + 草稿自愈 doctor.py v2.0（适配 VectCutAPI 引擎）
================================================================
用途：生成草稿前/排障"打不开/丢素材"时先跑一次。**只读诊断为主，
      自愈动作仅限安全项：清 .locked / JSON可解析检查 / 素材存在性校验。

用法：
  python doctor.py                  # 人读摘要（退出码 0=OK 1=warning 2=致命）
  python doctor.py --json           # 机器可读
  python doctor.py --heal <草稿目录> # 对单个草稿执行自愈（清locked+校验素材）
"""
import argparse
from . import config  # T8: 路径单一真源（config.py 为唯一权威）
import json
import os
import shutil
import subprocess
import sys

DRAFT_ROOT = config.DRAFT_DIR
EXPORT_ROOT = config.EXPORT_DIR
VOICE_DIR = config.VOICE_DIR
DEFAULT_VIDEO = config.DEFAULT_VIDEO
VECTCUT_DIR = config.VECTCUT_DIR
API = "http://127.0.0.1:9001"


def _check_env() -> dict:
    """只读环境检查"""
    checks = []
    # 1. Python
    checks.append(("python", sys.executable, True, ""))
    # 2. ffmpeg/ffprobe
    ff = shutil.which("ffmpeg")
    fp = shutil.which("ffprobe")
    checks.append(("ffmpeg/ffprobe", "可用" if ff and fp else "缺失",
                   bool(ff and fp), f"ffmpeg={ff} ffprobe={fp}"))
    # 3. 剪映版本（注册表）
    ver = "未知"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\JianyingPro") as k:
            ver, _ = winreg.QueryValueEx(k, "DisplayVersion")
    except Exception:
        pass
    checks.append(("剪映版本", ver, bool(ver and ver != "未知"), ""))
    # 4. 关键目录
    for name, p in (("草稿根", DRAFT_ROOT), ("导出", EXPORT_ROOT),
                    ("配音", VOICE_DIR), ("VectCutAPI", VECTCUT_DIR)):
        checks.append((name, p, os.path.isdir(p), "存在" if os.path.isdir(p) else "缺失"))
    # 5. 固定素材
    ok_v = os.path.exists(DEFAULT_VIDEO)
    checks.append(("固定素材", DEFAULT_VIDEO, ok_v, "存在" if ok_v else "缺失"))
    # 6. VectCutAPI 服务
    up = False
    try:
        import urllib.request
        req = urllib.request.Request(API + "/create_draft",
                                     data=b'{"width":1080,"height":1920}',
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=8)
        up = True
    except Exception:
        pass
    checks.append(("VectCutAPI服务(9001)", API, up, "运行中" if up else "未运行"))
    return checks


def heal_draft(draft_dir: str) -> dict:
    """草稿自愈：JSON可解析 + 清.locked + 素材路径存在性校验（缺失不删）"""
    report = {"dir": draft_dir, "ok": True, "issues": []}
    dc = os.path.join(draft_dir, "draft_content.json")
    if not os.path.exists(dc):
        report.update({"ok": False, "issues": ["draft_content.json 不存在"]})
        return report
    # 1. JSON 可解析（损坏则备份，不覆盖）
    try:
        data = json.load(open(dc, encoding="utf-8"))
    except Exception as e:
        import time
        bak = dc + f".corrupt_{int(time.time())}"
        shutil.copy2(dc, bak)
        report["issues"].append(f"JSON损坏已备份到 {os.path.basename(bak)}: {e}")
        report["ok"] = False
        return report
    # 2. 清 .locked
    lock = os.path.join(draft_dir, ".locked")
    if os.path.exists(lock):
        os.remove(lock)
        report["issues"].append("已清除 .locked")
    # 3. 素材 path 存在性
    mats = data.get("materials", {})
    missing = []
    for mtype in ("videos", "audios", "images"):
        for m in mats.get(mtype, []):
            path = m.get("path", "")
            if not path:
                continue
            if path.startswith("assets/"):
                full = os.path.join(draft_dir, path)
            elif os.path.isabs(path):
                full = path
            else:
                full = os.path.join(draft_dir, path)
            if not os.path.exists(full):
                missing.append(f"{mtype}: {path}")
    if missing:
        report["issues"] += [f"素材缺失({len(missing)}): " + "; ".join(missing[:5])]
        report["ok"] = False
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--heal", metavar="DRAFT_DIR", default=None)
    args = ap.parse_args()

    if args.heal:
        r = heal_draft(args.heal)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 自愈完成: {r['dir']} | 问题: {len(r['issues'])}" if r["ok"] else
                  f"⚠️ 存在{len(r['issues'])}个问题: " + "; ".join(r["issues"]))
        sys.exit(0 if r["ok"] else 2)

    checks = _check_env()
    fatal = [c for c in checks if not c[3] and c[0] in ("固定素材", "VectCutAPI服务(9001)", "ffmpeg/ffprobe")]
    warn = [c for c in checks if not c[3] and c not in fatal]
    if args.json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
    else:
        for name, val, ok, detail in checks:
            mark = "✅" if ok else ("⚠️" if detail and detail in ("存在", "运行中") else "❌")
            print(f"{mark} {name}: {val} {detail if not ok else ''}")
        print(f"\n结论: {'✅ 环境就绪' if not fatal else '❌ 有致命缺失'}")
    sys.exit(2 if fatal else (1 if warn else 0))


if __name__ == "__main__":
    main()
