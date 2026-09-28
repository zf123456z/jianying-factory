#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 只读环境诊断 doctor.py（v7.3）
============================================================
检查剪映工厂运行环境是否就绪，只读不写，绝不创建/修改/删除任何草稿。

检查项：
1. Python 版本与可执行路径
2. ffmpeg / ffprobe 是否可用
3. pyJianYingDraft 是否安装及版本（importlib.metadata 读真实版本，修复 unknown）
4. 剪映安装版本（Windows 注册表，>5.9 自动导出不可用）
5. 草稿根/备份根/配音/导出目录是否存在
6. 固定素材是否存在
7. 引擎 engine_v2.py 是否就位

用法：
  python doctor.py            # 人读摘要
  python doctor.py --json     # 机器可读 JSON
退出码：0=就绪，1=有 warning（不阻塞），2=有致命缺失（阻塞）
"""
import argparse
import json
import os
import platform
import shutil
import sys

DRAFT_ROOT = os.environ.get("JIANYING_DRAFT_ROOT", r"D:\AI工作区\剪映草稿")
EXPORT_ROOT = os.environ.get("JIANYING_EXPORT_ROOT", r"D:\AI工作区\导出")
VOICE_DIR = os.environ.get("JIANYING_VOICE_DIR", r"D:\AI工作区\配音")
BACKUP_ROOT = os.environ.get("JIANYING_BACKUP_ROOT", r"D:\AI工作区\剪映草稿_备份")
DEFAULT_VIDEO = os.environ.get("JIANYING_DEFAULT_VIDEO", r"E:\张总口播素材\张总形象.mp4")
ENGINE_PATH = r"D:\AI工作区\代码\engine_v2.py"


def _which(cmd: str):
    return shutil.which(cmd)


def _detect_jianying_version() -> dict:
    """Windows 注册表读取剪映安装版本"""
    if sys.platform != "win32":
        return {"installed": None, "version": None, "executable": None}
    candidates = []
    version = None
    try:
        import winreg
        roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
        uninstall_paths = (
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
            r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        )
        for root in roots:
            for uninstall_path in uninstall_paths:
                try:
                    with winreg.OpenKey(root, uninstall_path) as parent:
                        for index in range(winreg.QueryInfoKey(parent)[0]):
                            try:
                                with winreg.OpenKey(parent, winreg.EnumKey(parent, index)) as item:
                                    name = str(winreg.QueryValueEx(item, "DisplayName")[0])
                                    if "剪映" not in name and "jianying" not in name.lower():
                                        continue
                                    try:
                                        version = str(winreg.QueryValueEx(item, "DisplayVersion")[0])
                                    except OSError:
                                        pass
                                    for value_name in ("InstallLocation", "DisplayIcon"):
                                        try:
                                            value = str(winreg.QueryValueEx(item, value_name)[0]).strip('"')
                                            if value:
                                                candidates.append(value)
                                        except OSError:
                                            pass
                            except OSError:
                                continue
                except OSError:
                    continue
    except ImportError:
        pass

    local_app_data = os.getenv("LOCALAPPDATA", "")
    if local_app_data:
        candidates.extend([
            os.path.join(local_app_data, "JianyingPro", "Apps", "JianyingPro.exe"),
            os.path.join(local_app_data, "JianyingPro", "JianyingPro.exe"),
        ])

    expanded = []
    for candidate in candidates:
        candidate = candidate.split(",", 1)[0]
        expanded.append(candidate)
        if os.path.isfile(candidate):
            expanded.append(os.path.join(os.path.dirname(candidate), "JianyingPro.exe"))
        elif os.path.isdir(candidate):
            expanded.append(os.path.join(candidate, "JianyingPro.exe"))

    executable = next(
        (os.path.abspath(p) for p in expanded if os.path.isfile(p) and os.path.basename(p).lower() == "jianyingpro.exe"),
        None,
    )
    return {"installed": bool(executable or version), "version": version, "executable": executable}


def _pyjy_version() -> str:
    """v7.3：importlib.metadata 读真实安装版本，修复旧版 unknown"""
    try:
        from importlib import metadata
        return metadata.version("pyJianYingDraft")
    except Exception:
        try:
            import pyJianYingDraft as jy
            return getattr(jy, "__version__", "unknown")
        except Exception:
            return None


def collect_diagnostics() -> dict:
    """收集诊断信息（只读，无任何副作用）"""
    warnings = []
    errors = []

    py_ver = platform.python_version()
    py_exe = sys.executable

    ffmpeg = _which("ffmpeg")
    ffprobe = _which("ffprobe")
    if not ffmpeg:
        errors.append("ffmpeg_missing（转码/静音检测依赖，必须安装并加入 PATH）")
    if not ffprobe:
        errors.append("ffprobe_missing（时长探测依赖）")

    pyjy = _pyjy_version()
    if not pyjy:
        errors.append("pyJianYingDraft_missing（核心草稿引擎，pip install pyJianYingDraft）")

    jianying = _detect_jianying_version()
    version = jianying.get("version") or ""
    try:
        major, minor = [int(p) for p in version.split(".")[:2]]
    except (ValueError, TypeError):
        major, minor = None, None
    auto_export_supported = (
        sys.platform == "win32" and major is not None and (major < 5 or (major == 5 and (minor or 0) <= 9))
    )
    if sys.platform == "win32" and major is not None and not auto_export_supported:
        warnings.append(f"auto_export_unverified（检测到剪映 {version}，UIA 自动导出仅验证到 5.9；请走受控窗口 GUI 导出）")

    for label, path in [("drafts_root", DRAFT_ROOT), ("export_root", EXPORT_ROOT),
                        ("voice_dir", VOICE_DIR), ("backup_root", BACKUP_ROOT)]:
        if not os.path.isdir(path):
            warnings.append(f"{label}_missing（{path} 不存在，首次生成时自动创建）")

    if not os.path.isfile(DEFAULT_VIDEO):
        errors.append(f"default_video_missing（{DEFAULT_VIDEO} 不存在，请检查素材路径）")

    if not os.path.isfile(ENGINE_PATH):
        errors.append(f"engine_missing（{ENGINE_PATH} 不存在）")

    return {
        "ok": not errors,
        "code": "ok" if not errors else "fatal",
        "read_only": True,
        "platform": platform.platform(),
        "python": {"version": py_ver, "executable": py_exe},
        "commands": {"ffmpeg": ffmpeg, "ffprobe": ffprobe},
        "pyJianYingDraft": pyjy,
        "jianying": {**jianying, "auto_export_supported": auto_export_supported},
        "paths": {
            "drafts_root": DRAFT_ROOT,
            "export_root": EXPORT_ROOT,
            "voice_dir": VOICE_DIR,
            "backup_root": BACKUP_ROOT,
            "default_video": DEFAULT_VIDEO,
            "engine": ENGINE_PATH,
        },
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="剪映工厂只读环境诊断")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()
    result = collect_diagnostics()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 50)
        print("🔍 剪映工厂环境诊断（只读，不修改任何文件）")
        print("=" * 50)
        print(f"Python: {result['python']['version']}")
        print(f"ffmpeg: {'✅' if result['commands']['ffmpeg'] else '❌'} | ffprobe: {'✅' if result['commands']['ffprobe'] else '❌'}")
        print(f"pyJianYingDraft: {result['pyJianYingDraft'] or '❌ 未安装'}")
        jy = result['jianying']
        print(f"剪映: {'✅ v' + (jy['version'] or '?') if jy.get('installed') else '⚠️ 未检测到'}"
              f"{'（自动导出:' + ('✅' if jy.get('auto_export_supported') else '❌ 走GUI') + '）' if jy.get('installed') else ''}")
        print(f"草稿根: {result['paths']['drafts_root']}")
        if result['warnings']:
            print(f"\n⚠️ 警告 {len(result['warnings'])} 项（不阻塞）：")
            for w in result['warnings']:
                print(f"  - {w}")
        if result['errors']:
            print(f"\n❌ 致命问题 {len(result['errors'])} 项（阻塞）：")
            for e in result['errors']:
                print(f"  - {e}")
        print(f"\n结论: {'✅ 环境就绪，可以生成草稿' if result['ok'] else '❌ 存在致命缺失，先修复再生成'}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
