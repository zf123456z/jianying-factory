#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 统一命令行入口（v7.2.1）

一句话成片：
    python factory.py produce "文案或主题" --video E:\\张总口播素材\\张总形象.mp4 \\
        --voiceover D:\\配音\\配音.wav --bgm D:\\BGM\\bgm.mp3 --name 草稿名 --duration 60

常用子命令：
    produce    ★ 一条命令：生成草稿 + 导出预检（核心入口）
    precheck   对已有草稿跑导出预检（防媒体丢失/片尾黑屏）
    doctor     环境诊断（只读）
    drafts     列出草稿
    config     打印当前配置

所有输出 JSON 信封 {ok, code, reason, data}，退出码 0=成功 / 1=业务失败 / 2=用法错。
"""
import argparse
import json
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factory_config as cfg
from engine_v2 import make_voiceover_draft

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _skill_scripts_dir() -> Optional[str]:
    """技能脚本目录（配置项 skill_scripts_dir），含 export_precheck.py / doctor.py"""
    d = cfg.get("skill_scripts_dir")
    if d and os.path.isdir(d):
        return d
    return None


def _precheck_path() -> Optional[str]:
    d = _skill_scripts_dir()
    if not d:
        return None
    p = os.path.join(d, "export_precheck.py")
    return p if os.path.isfile(p) else None


def _out(ok: bool, code: str, reason: str, data=None) -> dict:
    return {"ok": ok, "code": code, "reason": reason, "data": data or {}}


def _find_voiceover(voiceover_dir: str, name_hint: Optional[str] = None) -> Optional[str]:
    """在配音目录找配音文件：优先精确匹配 name_hint，否则取最新的 wav/mp3"""
    if not os.path.isdir(voiceover_dir):
        return None
    exts = (".wav", ".mp3", ".m4a", ".aac")
    candidates = [f for f in os.listdir(voiceover_dir)
                  if f.lower().endswith(exts)]
    if not candidates:
        return None
    if name_hint:
        exact = [f for f in candidates if name_hint.lower() in f.lower()]
        if exact:
            return os.path.join(voiceover_dir, exact[0])
    full = [os.path.join(voiceover_dir, f) for f in candidates]
    return max(full, key=os.path.getmtime)


def _find_bgm(bgm_dir: str) -> Optional[str]:
    """在 BGM 目录找纯音乐：优先最近添加的 mp3/wav（纯音乐目录由用户维护）"""
    if not os.path.isdir(bgm_dir):
        return None
    exts = (".mp3", ".wav", ".m4a", ".flac")
    candidates = [os.path.join(bgm_dir, f) for f in os.listdir(bgm_dir)
                  if f.lower().endswith(exts)]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def cmd_produce(args) -> dict:
    """一条命令：确认素材 → 生成草稿 → 导出预检"""
    c = cfg.load_config()
    cfg.ensure_dirs()

    # 1. 素材解析
    video = args.video or c.get("default_video")
    if not video or not os.path.isfile(video):
        return _out(False, "video_missing", f"主视频素材不存在: {video}")

    voiceover = args.voiceover or _find_voiceover(c.get("voiceover_dir"), args.name)
    bgm = args.bgm or _find_bgm(c.get("bgm_dir"))

    duration = args.duration or 45.0

    # 2. 时长兜底：有配音则用配音真实时长（ffprobe），确保人声为准
    if voiceover and not args.duration:
        import subprocess
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", voiceover],
            capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                duration = float(proc.stdout.strip())
            except ValueError:
                pass

    # 3. 生成草稿（引擎：规范化防条纹 + 自包含 + 强制静音 + 铺满 + 备份）
    try:
        draft_dir = make_voiceover_draft(
            name=args.name,
            script_text=args.script or "",
            voice=c.get("default_voice"),
            video_path=video,
            bgm_path=bgm,
            voiceover_path=voiceover,
            total_duration_s=float(duration),
            video_volume=c.get("video_volume", 0.0),
            voice_volume=c.get("voice_volume", 1.0),
            bgm_volume=c.get("bgm_volume", 0.35),
        )
    except Exception as e:
        return _out(False, "draft_failed", f"草稿生成失败: {e}")

    data = {
        "draft_name": args.name,
        "draft_dir": draft_dir,
        "duration_s": round(float(duration), 1),
        "video": video,
        "voiceover": voiceover,
        "bgm": bgm,
    }

    # 4. 导出预检（拦截媒体丢失/片尾黑屏/未铺满）
    precheck_ok = True
    precheck_msg = "未执行预检（脚本不存在）"
    precheck_path = _precheck_path()
    if os.path.isfile(precheck_path):
        try:
            import subprocess
            proc = subprocess.run(
                [sys.executable, precheck_path, args.name, "--json"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore")
            if proc.returncode in (0, 1, 2) and proc.stdout:
                res = json.loads(proc.stdout[proc.stdout.find("{"):proc.stdout.rfind("}") + 1])
                precheck_ok = res.get("ok", True)
                precheck_msg = res.get("reason", "")
                data["precheck"] = res
            else:
                precheck_msg = f"预检脚本异常（退出码 {proc.returncode}）"
        except Exception as e:
            precheck_msg = f"预检执行失败: {e}"
    else:
        precheck_msg = "预检脚本不存在，请先同步 scripts/export_precheck.py"

    # 预检失败时也返回草稿（GUI 前能人工看原因），但标记 not_ok
    if not precheck_ok:
        return _out(False, "precheck_failed", f"草稿已生成但预检未通过: {precheck_msg}", data)

    print(f"\n✅ 成片草稿已就绪：{draft_dir}")
    print("👉 下一步：受控窗口打开剪映 → 开草稿 → 换音色 → 识别字幕 → 智能包装 → 返回首页")
    return _out(True, "ok", "草稿生成并通过预检", data)


def cmd_precheck(args) -> dict:
    """对已有草稿跑导出预检"""
    if not args.name:
        return _out(False, "usage", "用法: factory.py precheck <草稿名>")
    precheck_path = _precheck_path()
    if not precheck_path:
        return _out(False, "missing_script", "export_precheck.py 不存在（检查配置 skill_scripts_dir）")
    import subprocess
    proc = subprocess.run(
        [sys.executable, precheck_path, args.name, "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if proc.returncode not in (0, 1, 2):
        return _out(False, "precheck_crash", proc.stderr[-500:] if proc.stderr else "无输出")
    try:
        res = json.loads(proc.stdout[proc.stdout.find("{"):proc.stdout.rfind("}") + 1])
    except Exception:
        return _out(False, "precheck_parse", proc.stdout[-500:])
    return res


def cmd_doctor(args) -> dict:
    """环境诊断（复用 scripts/doctor.py）"""
    d = _skill_scripts_dir()
    doctor_path = os.path.join(d, "doctor.py") if d else None
    if not doctor_path or not os.path.isfile(doctor_path):
        return _out(False, "missing_script", "doctor.py 不存在（检查配置 skill_scripts_dir）")
    import subprocess
    proc = subprocess.run([sys.executable, doctor_path, "--json"],
                          capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if proc.returncode not in (0, 2):
        return _out(False, "doctor_crash", proc.stderr[-500:] if proc.stderr else "无输出")
    try:
        res = json.loads(proc.stdout[proc.stdout.find("{"):proc.stdout.rfind("}") + 1])
    except Exception:
        return _out(False, "doctor_parse", proc.stdout[-500:])
    return res


def cmd_drafts(args) -> dict:
    """列出草稿（过滤剪映缓存目录，如 .cache_voice / .recycle_bin / __pycache__）"""
    root = cfg.get("draft_root")
    if not os.path.isdir(root):
        return _out(False, "no_draft_root", f"草稿目录不存在: {root}")
    _CACHE_DIRS = {".cache_voice", ".recycle_bin", ".cloud_cache", "__pycache__", ".cache"}
    names = sorted(
        d for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d)) and d not in _CACHE_DIRS and not d.startswith(".")
    )
    return _out(True, "ok", f"{len(names)} 个草稿", {"drafts": names})


def cmd_config(args) -> dict:
    return _out(True, "ok", "当前配置", cfg.load_config())


def main():
    parser = argparse.ArgumentParser(description="剪映工厂统一入口")
    parser.add_argument("--json", action="store_true", help="输出 JSON 信封")
    sub = parser.add_subparsers(dest="cmd")

    p_produce = sub.add_parser("produce", help="★ 一条命令成片（草稿+预检）")
    p_produce.add_argument("script", nargs="?", default=None, help="口播文案（可选，有配音则可省略）")
    p_produce.add_argument("--name", required=True, help="草稿名")
    p_produce.add_argument("--video", default=None, help="主视频素材路径（默认用配置 default_video）")
    p_produce.add_argument("--voiceover", default=None, help="配音文件路径（默认取配音目录最新）")
    p_produce.add_argument("--bgm", default=None, help="BGM 路径（默认取 BGM 目录最新）")
    p_produce.add_argument("--duration", type=float, default=None, help="总时长秒（默认用配音真实时长）")

    p_pre = sub.add_parser("precheck", help="对已有草稿跑导出预检")
    p_pre.add_argument("name", help="草稿名")

    sub.add_parser("doctor", help="环境诊断（只读）")
    sub.add_parser("drafts", help="列出草稿")
    sub.add_parser("config", help="打印配置")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(2)

    if args.cmd == "produce":
        result = cmd_produce(args)
    elif args.cmd == "precheck":
        result = cmd_precheck(args)
    elif args.cmd == "doctor":
        result = cmd_doctor(args)
    elif args.cmd == "drafts":
        result = cmd_drafts(args)
    elif args.cmd == "config":
        result = cmd_config(args)
    else:
        parser.print_help()
        sys.exit(2)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))

    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
