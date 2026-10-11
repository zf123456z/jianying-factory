#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 导出预检 export_precheck.py（吸收 reliable 分支 auto_exporter 预检思路）
============================================================
在导出前对草稿做一次完整预检，把"导出后才发现问题"变成"导出前就拦截"。

检查项：
1. 草稿存在性与结构完整性（draft_info.json / draft_content.json）
2. 素材自包含：materials/ 目录存在、素材文件在位、local_material_id 非空
3. 轨道时长对齐：视频 / 人声 / BGM 三个轨道总时长一致（人声为准），杜绝片尾黑屏
4. 剪映版本预检：>5.9 自动导出不可用 → 提示走受控窗口 GUI 导出

用法：
  python export_precheck.py <草稿名>
  python export_precheck.py --json <草稿名>
退出码：0=通过可导出，1=有 warning，2=有致命问题
"""
import argparse
from . import config
import json
import os
import re
import sys
import subprocess

DRAFT_ROOT = config.DRAFT_DIR
DRAFT_BACKUP = config.DRAFT_BACKUP_DIR

QUALITY = {
    "bgm_volume_min": 0.30,
    "bgm_volume_max": 0.40,
    "require_subtitle": True,
    "align_tolerance_ms": 500,
}


def _find_draft(draft_name: str):
    target = os.path.abspath(os.path.join(DRAFT_ROOT, draft_name))
    if os.path.commonpath([os.path.abspath(DRAFT_ROOT), target]) != os.path.abspath(DRAFT_ROOT):
        return None
    if os.path.isdir(target):
        return target
    if os.path.isdir(DRAFT_ROOT):
        for d in os.listdir(DRAFT_ROOT):
            if draft_name.lower() in d.lower():
                return os.path.join(DRAFT_ROOT, d)
    return None


_B64_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/= \r\n\t")


def _is_encrypted_draft(p: str) -> bool:
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
    except OSError:
        return False
    compact = head.strip()
    if not compact:
        return False
    if compact[0] in "{[":
        return False
    return all(c in _B64_CHARS for c in compact)


def _load_draft(draft_path: str):
    for fname in ("draft_content.json", "draft_info.json"):
        p = os.path.join(draft_path, fname)
        if os.path.isfile(p):
            if _is_encrypted_draft(p):
                return None, fname, True
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    return json.load(f), fname, False
            except Exception:
                continue
    return None, None, False


_EMBEDDED_CATS = {
    "texts", "stickers", "effects", "video_effects", "plugin_effects",
    "material_animations", "material_colors", "text_templates",
    "shapes", "handwrites", "flowers", "beats", "time_marks",
    "audio_effects", "audio_balances", "audio_fades", "audio_track_indexes",
    "sound_channel_mappings", "transitions", "speeds", "masks",
    "smart_crops", "smart_relights", "realtime_denoises", "vocal_beautifys",
    "vocal_separations", "primary_color_wheels", "log_color_wheels",
    "color_curves", "hsl", "loudnesses", "canvases", "chromas",
    "digital_humans", "drafts", "multi_language_refs", "placeholders",
    "green_screens", "tail_leaders", "video_trackings", "manual_deformations",
}


def _iter_material_dicts(draft, media_only: bool = False):
    materials = draft.get("materials", {})
    if isinstance(materials, dict):
        for key, items in materials.items():
            if media_only and key in _EMBEDDED_CATS:
                continue
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        yield item
            elif isinstance(items, dict):
                yield items
    elif isinstance(materials, list):
        for item in materials:
            if isinstance(item, dict):
                yield item


def _check_asset_self_contained(draft, draft_path: str, errors: list, warnings: list):
    materials_dir = os.path.join(draft_path, "materials")
    if not os.path.isdir(materials_dir):
        warnings.append("materials/ 目录缺失（素材未自包含，剪映 5.9+ 可能报媒体丢失）")
        return

    all_mats = list(_iter_material_dicts(draft, media_only=True))

    used_mids = set()
    for track in draft.get("tracks", []):
        for seg in track.get("segments", []):
            mid = seg.get("material_id")
            if mid:
                used_mids.add(mid)

    id_map = {}
    for mat in all_mats:
        mid = mat.get("id") or mat.get("material_id")
        if mid:
            id_map[mid] = mat

    empty_count = 0
    missing_files = []
    checked = set()
    for mid in used_mids:
        if mid in checked:
            continue
        checked.add(mid)
        mat = id_map.get(mid)
        if mat is None:
            continue
        lid = mat.get("local_material_id") or ""
        if not lid:
            empty_count += 1
        path = mat.get("path") or mat.get("media_path") or ""
        if path:
            base = os.path.basename(path)
            staged = os.path.join(materials_dir, base)
            if not os.path.isfile(staged):
                missing_files.append(base)

    for mat in all_mats:
        path = mat.get("path") or mat.get("media_path") or ""
        if not path:
            continue
        base = os.path.basename(path)
        staged = os.path.join(materials_dir, base)
        if not os.path.isfile(staged):
            missing_files.append(base)

    if empty_count:
        errors.append(f"{empty_count} 个被引用素材 local_material_id 为空（剪映会报媒体丢失）")
    if missing_files:
        errors.append(f"{len(missing_files)} 个素材文件不在 materials/ 内（引用外部路径，有丢失风险）")


def _check_track_durations(draft, errors: list, warnings: list):
    tracks = draft.get("tracks", [])
    durations = {}
    for track in tracks:
        name = track.get("name", "unknown")
        segments = track.get("segments", [])
        if not segments:
            durations[name] = 0
            continue
        total = max(
            seg["target_timerange"]["start"] + seg["target_timerange"]["duration"]
            for seg in segments if "target_timerange" in seg
        )
        durations[name] = total

    if not durations:
        errors.append("草稿无任何轨道")
        return

    voice_dur = None
    for name, dur in durations.items():
        if "voice" in name.lower() or "配音" in name or "人声" in name:
            voice_dur = dur
            break
    if voice_dur is None:
        warnings.append("未识别到人声轨道，以最长轨道为基准")
        voice_dur = max(durations.values())

    for name, dur in durations.items():
        if "bgm" in name.lower() or "音乐" in name:
            if dur < voice_dur:
                warnings.append(f"BGM 轨道({name}) {dur/1e6:.1f}s < 人声 {voice_dur/1e6:.1f}s，片尾可能黑屏/无声")
    for track in tracks:
        if track.get("type") == "video":
            segs = track.get("segments", [])
            track_end = max(
                (s["target_timerange"]["start"] + s["target_timerange"]["duration"] for s in segs
                 if "target_timerange" in s), default=0)
            if track_end < voice_dur:
                warnings.append(f"视频轨道 {track_end/1e6:.1f}s < 人声 {voice_dur/1e6:.1f}s，视频未铺满")

    return voice_dur / 1_000_000 if voice_dur else None


def _detect_jianying_version():
    if sys.platform != "win32":
        return None, False
    version = None
    try:
        import winreg
        roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
        uninstall_paths = (
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
            r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        )
        for root in roots:
            for up in uninstall_paths:
                try:
                    with winreg.OpenKey(root, up) as parent:
                        for i in range(winreg.QueryInfoKey(parent)[0]):
                            try:
                                with winreg.OpenKey(parent, winreg.EnumKey(parent, i)) as item:
                                    name = str(winreg.QueryValueEx(item, "DisplayName")[0])
                                    if "剪映" not in name and "jianying" not in name.lower():
                                        continue
                                    try:
                                        version = str(winreg.QueryValueEx(item, "DisplayVersion")[0])
                                    except OSError:
                                        pass
                            except OSError:
                                continue
                except OSError:
                    continue
    except ImportError:
        pass
    if not version:
        return None, False
    try:
        major, minor = [int(p) for p in version.split(".")[:2]]
    except (ValueError, TypeError):
        major, minor = None, None
    supported = major is not None and (major < 5 or (major == 5 and (minor or 0) <= 9))
    return version, supported


def _check_quality_gates(draft, errors: list, warnings: list):
    qmin = float(QUALITY["bgm_volume_min"])
    qmax = float(QUALITY["bgm_volume_max"])
    tol_us = int(QUALITY["align_tolerance_ms"]) * 1000

    tracks = draft.get("tracks", [])
    voice_end = 0
    total_us = draft.get("duration", 0)

    for track in tracks:
        name = track.get("name", "unknown")
        segs = track.get("segments", [])
        is_bgm = "bgm" in name.lower() or "音乐" in name
        is_voice = "voice" in name.lower() or "配音" in name or "人声" in name
        for seg in segs:
            tr = seg.get("target_timerange", {})
            end = tr.get("start", 0) + tr.get("duration", 0)
            if is_voice:
                voice_end = max(voice_end, end)
            if is_bgm:
                vol = seg.get("volume")
                if vol is not None:
                    if vol < qmin:
                        warnings.append(f"BGM 音量 {vol:.2f} 低于门禁下限 {qmin:.2f}（太小声）")
                    elif vol > qmax:
                        warnings.append(f"BGM 音量 {vol:.2f} 高于门禁上限 {qmax:.2f}（压过人声）")

    if voice_end and total_us and abs(total_us - voice_end) > tol_us:
        warnings.append(
            f"人声结束 {voice_end/1e6:.1f}s 与总时长 {total_us/1e6:.1f}s 偏差"
            f" {abs(total_us-voice_end)/1e6:.2f}s > 容差 {QUALITY['align_tolerance_ms']}ms，建议人工检查片尾对齐")

    if QUALITY["require_subtitle"]:
        texts = draft.get("materials", {}).get("texts", [])
        has_text_track = any(
            t.get("type") in ("text", "subtitle") or "字幕" in t.get("name", "")
            for t in tracks)
        if not texts and not has_text_track:
            warnings.append("未检测到字幕素材/字幕轨道（质量门禁 require_subtitle），建议在剪映中执行官方识别字幕")


def export_precheck(draft_name: str) -> dict:
    errors, warnings = [], []

    draft_path = _find_draft(draft_name)
    if not draft_path:
        return {
            "ok": False, "code": "fatal", "draft": draft_name,
            "errors": [f"草稿不存在（{DRAFT_ROOT} 下未找到）"], "warnings": [],
            "voice_duration_s": None, "jianying_version": None, "export_path": "GUI",
        }

    draft, fname, encrypted = _load_draft(draft_path)
    if encrypted:
        warnings.append(
            "草稿已被剪映GUI加密保存（剪映11.5正常现象），跳过代码层内容审计；请人工在剪映中确认画面/字幕/音频时长后导出")
    elif draft is None:
        errors.append(f"草稿 JSON 无法解析（{draft_path}）")
    else:
        _check_asset_self_contained(draft, draft_path, errors, warnings)
        voice_dur = _check_track_durations(draft, errors, warnings)
        _check_quality_gates(draft, errors, warnings)

    version, auto_ok = _detect_jianying_version()
    if version and not auto_ok:
        warnings.append(f"剪映 {version}：自动导出不可用（仅验证到 5.9），请走受控窗口 GUI 导出")

    return {
        "ok": not errors,
        "code": "fatal" if errors else ("warning" if warnings else "ok"),
        "draft": draft_name,
        "draft_path": draft_path,
        "voice_duration_s": voice_dur if draft else None,
        "jianying_version": version,
        "auto_export_supported": auto_ok,
        "errors": errors,
        "warnings": warnings,
        "export_path": "GUI" if (version and not auto_ok) else "unknown",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="剪映工厂导出预检")
    parser.add_argument("draft_name", help="草稿名（支持模糊匹配）")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    result = export_precheck(args.draft_name)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 55)
        print(f"🔍 导出预检：{result['draft']}")
        print("=" * 55)
        if result.get("draft_path"):
            print(f"草稿路径: {result['draft_path']}")
        if result.get("voice_duration_s"):
            print(f"人声时长: {result['voice_duration_s']:.1f}s")
        print(f"剪映版本: {result['jianying_version'] or '未检测到'} | 导出方式: {result['export_path']}")
        if result['warnings']:
            print(f"\n⚠️ 警告 {len(result['warnings'])} 项（可导出但注意）：")
            for w in result['warnings']:
                print(f"  - {w}")
        if result['errors']:
            print(f"\n❌ 致命问题 {len(result['errors'])} 项（禁止导出）：")
            for e in result['errors']:
                print(f"  - {e}")
        print(f"\n结论: {'✅ 预检通过，可以导出' if result['ok'] else '❌ 存在致命问题，先修复再导出'}")
    return 0 if result["ok"] else (1 if result["code"] == "warning" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
