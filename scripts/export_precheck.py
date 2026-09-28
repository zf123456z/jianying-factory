#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 导出预检 export_precheck.py（v7.3：加密降级 + 质量门禁）
============================================================
在导出前对草稿做一次完整预检，把"导出后才发现问题"变成"导出前就拦截"。

检查项：
1. 草稿存在性与结构完整性（draft_info.json / draft_content.json）
2. 素材自包含：materials/ 目录存在、素材文件在位、local_material_id 非空（v1.7 修复项）
3. 轨道时长对齐：视频 / 人声 / BGM 三个轨道总时长一致（人声为准），杜绝片尾黑屏
4. 剪映版本预检：>5.9 自动导出不可用 → 提示走受控窗口 GUI 导出
5. 质量门禁（v7.3）：BGM 音量区间 / 字幕存在性 / 人声对齐容差

用法：
  python export_precheck.py <草稿名>
  python export_precheck.py --json <草稿名>    # 机器可读
退出码：0=通过可导出，1=有 warning（可导出但注意），2=有致命问题（禁止导出）
"""
import argparse
import json
import os
import sys

DRAFT_ROOT = os.environ.get("JIANYING_DRAFT_ROOT", r"D:\AI工作区\剪映草稿")
DRAFT_BACKUP = os.environ.get("JIANYING_BACKUP_ROOT", r"D:\AI工作区\剪映草稿_备份")

# 成品质量门禁（与 factory_config.json quality 对齐）
QUALITY = {
    "bgm_volume_min": 0.30,
    "bgm_volume_max": 0.40,
    "require_subtitle": True,
    "align_tolerance_ms": 500,
}


def _find_draft(draft_name: str):
    """在草稿根找草稿目录，返回绝对路径或 None"""
    target = os.path.abspath(os.path.join(DRAFT_ROOT, draft_name))
    if os.path.commonpath([os.path.abspath(DRAFT_ROOT), target]) != os.path.abspath(DRAFT_ROOT):
        return None
    if os.path.isdir(target):
        return target
    # 支持模糊匹配
    if os.path.isdir(DRAFT_ROOT):
        for d in os.listdir(DRAFT_ROOT):
            if draft_name.lower() in d.lower():
                return os.path.join(DRAFT_ROOT, d)
    return None


_B64_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/= \r\n\t")


def _is_encrypted_draft(p: str) -> bool:
    """检测剪映 GUI 加密草稿（v7.3）。

    剪映 11.5 在 GUI 里打开并保存过的草稿，draft_content.json 会被加密成
    Base64 包裹的密文（已实测：文件头 `J107qtr4DF27...`，base64 解码后为随机
    字节，非 zlib/gzip/明文，无法在代码层解密）。此时代码层内容审计必然失败，
    应降级为提示而非误报"致命错误"。
    检测：读前 4KB，去空白后首字符不是 { / [，且剩余字符全在 Base64 字符集内。
    """
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
    """加载草稿 JSON，返回 (dict|None, 文件名, 是否加密)"""
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


def _iter_material_dicts(draft):
    """遍历草稿中所有素材 dict（适配真实结构：materials 是 dict，子键是分类列表）"""
    materials = draft.get("materials", {})
    if isinstance(materials, dict):
        for key, items in materials.items():
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
    """素材自包含检查：local_material_id 非空 + 引用素材文件在位"""
    materials_dir = os.path.join(draft_path, "materials")
    if not os.path.isdir(materials_dir):
        warnings.append("materials/ 目录缺失（素材未自包含，剪映 5.9+ 可能报媒体丢失）")
        return

    all_mats = list(_iter_material_dicts(draft))

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
        errors.append(f"{empty_count} 个被引用素材 local_material_id 为空（v1.7 修复未生效，剪映会报媒体丢失）")
    if missing_files:
        errors.append(f"{len(missing_files)} 个素材文件不在 materials/ 内（引用外部路径，有丢失风险）")


def _check_track_durations(draft, errors: list, warnings: list):
    """轨道时长对齐检查：以人声为准，视频/BGM 必须铺满"""
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
        return None

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


def _check_quality_gates(draft, warnings: list):
    """成品质量门禁（v7.3）：BGM音量区间 / 字幕存在性 / 人声对齐容差"""
    # 1. BGM 音量区间
    for track in draft.get("tracks", []):
        name = track.get("name", "")
        if "bgm" not in name.lower() and "音乐" not in name:
            continue
        for seg in track.get("segments", []):
            vol = seg.get("volume")
            if vol is None:
                continue
            if vol < QUALITY["bgm_volume_min"] or vol > QUALITY["bgm_volume_max"]:
                warnings.append(
                    f"BGM音量 {vol:.2f} 超出质量门禁 [{QUALITY['bgm_volume_min']:.2f},{QUALITY['bgm_volume_max']:.2f}]，"
                    f"建议 0.30-0.40 不抢人声")
    # 2. 字幕存在性
    if QUALITY.get("require_subtitle"):
        has_sub = False
        for track in draft.get("tracks", []):
            if "字幕" in track.get("name", "") or track.get("type") == "subtitle":
                has_sub = True
                break
        if not has_sub:
            warnings.append("未检测到字幕轨道——口播视频建议用剪映官方识别字幕后导出")
    # 3. 人声对齐容差（配音轨首段起点 >500ms 则提示）
    for track in draft.get("tracks", []):
        name = track.get("name", "")
        if "voice" not in name.lower() and "配音" not in name:
            continue
        for seg in track.get("segments", []):
            start = seg.get("target_timerange", {}).get("start", 0)
            if start > QUALITY["align_tolerance_ms"] * 1000:
                warnings.append(f"配音轨道起点 {start/1e6:.2f}s 超过对齐容差 {QUALITY['align_tolerance_ms']}ms，注意音画同步")


def _detect_jianying_version():
    """剪映版本预检（doctor 同款逻辑）"""
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


def export_precheck(draft_name: str) -> dict:
    """执行导出预检，返回结构化结果"""
    errors, warnings = [], []

    draft_path = _find_draft(draft_name)
    if not draft_path:
        return {
            "ok": False,
            "code": "fatal",
            "draft": draft_name,
            "errors": [f"草稿不存在（{DRAFT_ROOT} 下未找到）"],
            "warnings": [],
            "voice_duration_s": None,
            "jianying_version": None,
            "export_path": "GUI",
        }

    draft, fname, encrypted = _load_draft(draft_path)
    if encrypted:
        warnings.append(
            "草稿已被剪映GUI加密保存（剪映11.5正常现象），跳过代码层内容审计；"
            "请人工在剪映中确认画面/字幕/音频时长后导出"
        )
    elif draft is None:
        errors.append(f"草稿 JSON 无法解析（{draft_path}）")
    else:
        _check_asset_self_contained(draft, draft_path, errors, warnings)
        voice_dur = _check_track_durations(draft, errors, warnings)
        _check_quality_gates(draft, warnings)

    version, auto_ok = _detect_jianying_version()
    if version and not auto_ok:
        warnings.append(f"剪映 {version}：自动导出不可用（仅验证到 5.9），请走受控窗口 GUI 导出")

    return {
        "ok": not errors,
        "code": "fatal" if errors else ("warning" if warnings else "ok"),
        "draft": draft_name,
        "draft_path": draft_path,
        "voice_duration_s": (draft_path and not encrypted and (_check_track_durations(draft, [], []) if draft else None)),
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
