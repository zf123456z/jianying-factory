#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剪映工厂 v7.8 - VectCutAPI 确定性执行内核"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from typing import Dict, List, Optional

from . import config  # noqa: F401,E402
from .config import API, VECTCUT_DIR, DRAFT_ROOT  # noqa: F401,E402


def safe_transform_y(font_size: float, desired: float) -> float:
    if font_size <= 10:
        limit = 0.80
    elif font_size <= 16:
        limit = 0.75
    else:
        limit = 0.60
    return round(max(-limit, min(limit, desired)), 3)


# =====================================================================
# 单行自适应字号（2026-10-13 用户规则：一句话尽量不换行，超宽缩字号）
# =====================================================================
def _text_width_px(text: str, font_size: float, bold: bool = False) -> float:
    """估算整句文字像素宽度（保守口径：中文≈1.15×字号，英文/数字≈0.7×字号，
    空格≈0.4×字号；加粗×1.08）。宁缩不溢——按真实渲染可能更宽的保守值估算。"""
    if not text:
        return 0.0
    w = 0.0
    for ch in text:
        if ch == " ":
            w += font_size * 0.4
        elif ord(ch) > 255:
            w += font_size * 1.15         # 中文/全角（保守，覆盖宽字体）
        else:
            w += font_size * 0.7          # 英文/数字/半角
    if bold:
        w *= 1.08
    return w


def auto_fit_font_size(text: str, font_size: float, canvas_width: int = 1080,
                       max_ratio: float = 0.80, min_size: float = 6.0,
                       bold: bool = False) -> tuple:
    """单行自适应字号：超宽时缩小字号让整句一行放下（尽量不换行）。

    max_ratio: 最大行宽占画布比例（0.80，比服务端 line_max_width=0.82 更保守，
               保证单行放得下、不会触发换行；2026-10-13 用户规则）
    min_size: 字号下限；缩到下限仍超 → 返回下限（由服务端 force_apply 换行兜底，绝不出屏）
    返回 (new_font_size, fitted)；fitted=False 表示已到下限、允许换行兜底
    """
    if not text:
        return font_size, True
    max_px = canvas_width * max_ratio
    w = _text_width_px(text, font_size, bold=bold)
    if w <= max_px:
        return font_size, True
    # 缩小比例 = 最大宽 / 估算宽；0.97 保守系数留误差余量；取整到 0.5 档
    fitted = math.floor(font_size * max_px / w * 0.97 * 2) / 2.0
    if fitted < min_size:
        return min_size, False
    return max(fitted, 1.0), True

TEXT_INTRO_MAP = {
    "打字机": "打字机_I", "随机打字机": "随机打字机", "打字机_I": "打字机_I",
    "卡拉OK": "卡拉OK", "渐显": "渐显", "淡入": "渐显",
    "弹入": "弹入", "弹跳": "弹入跳动", "飞入": "飞入",
    "放大": "放大", "缩小": "缩小", "拉近": "放大", "拉远": "缩小",
    "故障": "乱码故障", "干扰": "乱码故障", "模糊": "模糊", "虚化": "模糊",
    "溶解": "溶解", "叠化": "溶解", "向上滑动": "向上滑动",
    "向下滑动": "向下滑动", "向左滑动": "向左滑动", "向右滑动": "向右滑动",
    "开幕": "开幕", "弹弓": "弹弓", "旋转": "旋入", "螺旋": "螺旋上升",
    "晃动": "闪动", "弹簧": "弹簧", "挤压": "弹性伸缩", "翻折": "折叠",
    "随机弹跳": "随机弹跳", "波浪": "波浪弹入", "漂浮向下": "向下露出",
    "向上露出": "向上露出", "向下露出": "向下露出", "向左露出": "向左露出",
    "向右露出": "向右露出", "翻转": "水平翻转", "日落": "日出",
    "打字机_II": "打字机_II", "打字机_III": "打字机_III", "打字机IV": "打字机IV",
    "居中打字": "居中打字", "复古打字机": "复古打字机", "逐字弹跳": "逐字弹跳",
    "随机飞入": "随机飞入", "随机上升": "随机上升", "随机落下": "随机落下",
}
TEXT_OUTRO_MAP = {
    "渐隐": "渐隐", "淡出": "渐隐", "弹出": "弹出", "溶解": "溶解",
    "模糊": "模糊", "放大": "放大", "缩小": "缩小", "打字机": "打字机_I",
    "向上滑动": "向上滑动", "向下滑动": "向下滑动", "向左滑动": "向左滑动",
    "向右滑动": "向右滑动", "展开": "展开", "飞走": "飞出", "故障": "故障",
    "旋转": "旋出", "翻折": "折叠", "漂浮向上": "向上飞出", "弹弓": "弹弓",
    "日落": "日落", "随机打字机": "随机打字机", "打字机_II": "打字机_II",
    "弹出跳动": "弹出跳动", "向上飞出": "向上飞出", "向下弹出": "向下弹出",
    "炸开": "炸开", "消散": "消散", "闭幕": "闭幕",
}

ANIM_SYNONYMS = {
    "typewriter": ["打字机", "打字机_I", "打字机_II", "打字机_III", "打字机IV", "居中打字", "复古打字机", "typing"],
    "random_typewriter": ["随机打字机"],
    "karaoke": ["卡拉OK"],
    "fade_in": ["渐显", "淡入"],
    "fade_out": ["渐隐", "淡出", "fadeout", "fadeout_2"],
    "fadeout": ["渐隐", "淡出"],
    "pop_up": ["弹入", "弹出"],
    "bounce": ["弹入跳动", "随机弹跳"],
    "fly_in": ["飞入", "随机飞入"],
    "fly_out": ["飞出"],
    "zoom_in": ["放大", "轻微放大"],
    "zoom_out": ["缩小"],
    "glitch": ["乱码故障", "故障", "故障闪动"],
    "blur": ["模糊", "模糊发光"],
    "dissolve": ["溶解"],
    "slide_up": ["向上滑动"],
    "slide_down": ["向下滑动"],
    "slide_left": ["向左滑动"],
    "slide_right": ["向右滑动"],
    "open": ["开幕"],
    "close": ["闭幕"],
    "slingshot": ["弹弓"],
    "spin": ["旋入", "旋出", "旋转缩放"],
    "spring": ["弹簧"],
    "fold": ["折叠"],
    "wave": ["波浪弹入"],
    "flip": ["水平翻转", "翻转"],
}


def _resolve_anim(name, mapping, enum_names=None):
    import difflib
    if not name:
        return None
    if name in mapping:
        return mapping[name]
    low = name.lower()
    for k, v in mapping.items():
        if k.lower() == low:
            return v
    syn_key = low if low in ANIM_SYNONYMS else None
    if syn_key:
        for candidate in ANIM_SYNONYMS[syn_key]:
            if candidate in mapping:
                return mapping[candidate]
            if enum_names and candidate in enum_names:
                return candidate
    if enum_names:
        low_map = {e.lower(): e for e in enum_names}
        if low in low_map:
            return low_map[low]
        match = difflib.get_close_matches(low, [e.lower() for e in enum_names], n=1, cutoff=0.6)
        if match:
            return low_map[match[0]]
    return name

JIANYING_TEXT_INTRO_NAMES = ["乱码故障", "二段缩放", "便利贴", "倒数", "兔子弹跳", "冰雪飘动", "冲屏位移", "卡拉OK", "发光闪入", "变色输入", "叠影并入", "右上弹入", "右下擦开", "向上弹入", "向上擦除", "向上滑动", "向上翻转", "向上重叠", "向上露出", "向下擦除", "向下溶解", "向下滑动", "向下露出", "向下飞入", "向右擦除", "向右模糊_II", "向右滑动", "向右缓入", "向右集合", "向右露出", "向左擦除", "向左模糊", "向左滑动", "向左露出", "吸入", "呐喊声波", "喷绘", "圆形扫描", "圆柱体滚动", "圣诞帽弹跳", "圣诞树弹跳II", "复古打字机", "居中打字", "左上弹入", "左移弹动", "开幕", "弹入", "弹入跳动", "弹弓", "弹性伸缩", "弹性伸缩_II", "弹簧", "彩色映射", "心动瞬间", "慢速放大", "打字光标", "打字机IV", "打字机_I", "打字机_II", "打字机_III", "扭曲模糊", "抖动甩入", "折叠", "拖尾", "描边填充", "收拢", "放大", "放大震动", "故障打字机", "故障闪动", "新年打字机", "旋入", "旋转缩放", "旋转飞入", "日出", "星光闪闪", "星光闪闪_II", "星星弹跳", "晕开", "模糊", "模糊发光", "模糊滚动", "模糊缩小", "水墨晕开", "水平翻转", "汇聚", "波浪弹入", "波浪弹跳", "流光扩散", "渐显", "溶解", "滑动上升", "滚入", "激光雕刻", "爱心弹跳", "玩雪", "环绕滑入", "生长", "生长_II", "甩出", "电光", "电光_II", "碰碰车", "空翻", "站起", "缤纷冲屏", "缩小", "缩小_II", "缩放_III", "羽化向右擦开", "羽化向左擦开", "翻动", "翻页II", "背景滑入", "色散拖影", "螺旋上升", "跃进", "跳跳捣蛋鬼", "跳跳糖", "轻微放大", "辉光", "辉光扫描", "逐字弹跳", "逐字旋入", "逐字旋转", "逐字显影", "逐字翻转", "金粉飘落", "镂空跳入", "闪动", "闪烁集合", "随机上升", "随机弹跳", "随机弹跳_II", "随机打字机", "随机落下", "随机集合", "随机飞入", "雪光模糊", "音符弹跳", "顶出", "预览打字", "飞入", "鼠标点击"]
JIANYING_TEXT_OUTRO_NAMES = ["二段缩放", "发光闪出", "叠影并出", "右上弹出", "右下擦除", "向上擦除", "向上溶解", "向上滑动", "向上飞出", "向下弹出", "向下擦除", "向下滑动", "向下翻转", "向右擦除", "向右滑动", "向右缓出", "向左擦除", "向左模糊", "向左模糊_II", "向左滑动", "向左解散", "吸出", "喷绘", "圆形扫描", "复古打字机", "居中打字", "展开", "左上弹出", "左移弹动", "弹出", "弹出跳动", "弹弓", "弹性伸缩", "弹性伸缩_II", "弹簧", "打字光标", "打字机IV", "打字机_I", "打字机_II", "打字机_III", "扭曲模糊", "折叠", "拖尾", "描边填充", "收缩震动", "放大", "放大_II", "故障", "故障打字机", "故障闪动", "旋出", "旋转缩放", "旋转飞出", "日落", "晕开", "模糊", "模糊发光", "模糊滚动", "水墨晕开", "水平翻转", "波浪弹出", "波浪弹跳", "消散", "渐隐", "溶解", "滑动下落", "滚出", "激光雕刻", "炸开", "炸开_II", "炸开_III", "环绕滑出", "生长", "甩回", "空翻", "缩小", "羽化向右擦除", "羽化向左擦除", "翻动", "螺旋下降", "躺下", "轻微放大", "逐字旋出", "逐字旋转", "逐字翻转", "逐字虚影", "镂空跳出", "闪动", "闪烁散开", "闭幕", "随机弹跳", "随机弹跳_II", "随机打字机", "随机飞出", "顶出", "预览打字", "飞出"]


def safe_tim(inp) -> int:
    if isinstance(inp, int):
        return int(inp)
    if isinstance(inp, float):
        return int(inp * 1000000)
    if isinstance(inp, str) and ":" in inp:
        try:
            parts = inp.split(":")
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return int((h * 3600 + m * 60 + s) * 1000000)
            if len(parts) == 2:
                m, s = map(float, parts)
                return int((m * 60 + s) * 1000000)
        except Exception:
            pass
    if isinstance(inp, str):
        import re
        s = inp.strip()
        unit_pattern = re.compile(r"\s*(\d+(?:\.\d+)?)(ms|us|h|m|s)\s*", re.IGNORECASE)
        unit_scale = {"h": 3600 * 1000000, "m": 60 * 1000000, "s": 1000000, "ms": 1000, "us": 1}
        pos, total = 0, 0.0
        for match in unit_pattern.finditer(s):
            if match.start() != pos:
                break
            total += float(match.group(1)) * unit_scale[match.group(2).lower()]
            pos = match.end()
        if pos == len(s):
            return int(total)
        if s.replace(".", "", 1).isdigit():
            return int(float(s) * 1000000)
    return int(float(inp) * 1000000) if inp else 0


def _post(route: str, payload: dict, timeout: int = 300):
    req = urllib.request.Request(
        f"{API}{route}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class JianyingVectcutEngine:
    def __init__(self, draft_root: str = DRAFT_ROOT):
        self.draft_root = draft_root
        self.results = []
        self._text_slots: Dict[str, list] = {}
        self._slot_by_track: Dict[tuple, list] = {}

    def _log(self, node: str, ok: bool, detail: str = ""):
        self.results.append({"node": node, "ok": ok, "detail": detail})
        print(f"{'✅' if ok else '❌'} [{node}] {detail}")

    def ensure_server(self, wait_s: int = 20) -> bool:
        try:
            _post("/create_draft", {"width": 1080, "height": 1920}, timeout=8)
            self._log("VectCutAPI服务", True, "已运行")
            return True
        except Exception:
            pass
        if not os.path.exists(os.path.join(VECTCUT_DIR, "capcut_server.py")):
            self._log("VectCutAPI服务", False, f"未找到 {VECTCUT_DIR}")
            return False
        subprocess.Popen(
            [sys.executable, "capcut_server.py"],
            cwd=VECTCUT_DIR,
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + wait_s
        while time.time() < deadline:
            try:
                _post("/create_draft", {"width": 1080, "height": 1920}, timeout=8)
                self._log("VectCutAPI服务", True, f"已启动（{VECTCUT_DIR}）")
                return True
            except Exception:
                time.sleep(2)
        self._log("VectCutAPI服务", False, "启动失败")
        return False

    def create_draft(self, width: int = 1080, height: int = 1920) -> str:
        out = _post("/create_draft", {"width": width, "height": height}, timeout=60)
        draft_id = out["output"]["draft_id"]
        self._log("创建草稿", True, f"{draft_id} ({width}x{height})")
        return draft_id

    def add_video(self, draft_id: str, video_path: str,
                  volume: float = 1.0, speed: float = 1.0,
                  start: float = 0, end=None,
                  target_start: float = 0,
                  track_name: str = "video",
                  transition: str = None,
                  transform_y: float = 0, scale: float = 1.0) -> bool:
        if end and video_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")):
            tmp_dir = os.path.join(config.EXPORT_DIR, "_bg_tmp")
            os.makedirs(tmp_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(video_path))[0]
            mp4_path = os.path.join(tmp_dir, f"{base}_{int(round(end))}s.mp4")
            if not os.path.exists(mp4_path) or os.path.getmtime(mp4_path) < os.path.getmtime(video_path):
                r = subprocess.run(
                    ["ffmpeg", "-y", "-loop", "1", "-i", video_path,
                     "-t", f"{end}", "-r", "30", "-pix_fmt", "yuv420p",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", mp4_path],
                    capture_output=True, timeout=300)
                if r.returncode != 0 or not os.path.exists(mp4_path):
                    self._log("添加视频", False, f"图片转视频失败: {video_path}")
                    return False
            video_path = mp4_path
        out = _post("/add_video", {
            "draft_id": draft_id, "video_url": video_path, "start": start,
            "end": end, "target_start": target_start, "volume": volume,
            "speed": speed, "track_name": track_name, "transition": transition,
            "transform_y": transform_y, "scale_x": scale, "scale_y": scale,
        }, timeout=180)
        ok = bool(out.get("success", False))
        self._log("添加视频", ok, os.path.basename(video_path))
        return ok

    def add_audio(self, draft_id: str, audio_path: str,
                  volume: float = 1.0, start: float = 0, end=None,
                  track_name: str = "audio_main") -> bool:
        out = _post("/add_audio", {
            "draft_id": draft_id, "audio_url": audio_path, "start": start,
            "end": end, "volume": volume, "track_name": track_name,
        }, timeout=180)
        ok = bool(out.get("success", False))
        self._log("添加音频", ok, f"{os.path.basename(audio_path)} vol={volume} track={track_name}")
        return ok

    def add_subtitle(self, draft_id: str, srt_path: str,
                     font_size: float = 9.0, font_color: str = "#FFD400",
                     background_alpha: float = 0.3, bold: bool = True,
                     keywords: list = None, auto_fit: bool = True) -> bool:
        # 单行自适应字号：按 SRT 最长一句统一整组字幕字号（2026-10-13 用户规则）
        if auto_fit:
            longest = ""
            try:
                txt = open(srt_path, encoding="utf-8").read()
                for block in re.split(r"\n\s*\n", txt.strip()):
                    lines = block.splitlines()
                    if len(lines) < 2:
                        continue
                    seg = " ".join(x.strip() for x in lines[2:] if x.strip())
                    if len(seg) > len(longest):
                        longest = seg
            except Exception:
                longest = ""
            if longest:
                fs_new, _ = auto_fit_font_size(longest, font_size, bold=bold)
                if abs(fs_new - font_size) > 0.01:
                    font_size = fs_new
        payload = {
            "draft_id": draft_id, "srt": srt_path, "font_size": font_size,
            "font_color": font_color, "bold": bold,
            "background_alpha": background_alpha, "vertical": False,
        }
        if keywords:
            norm = []
            for k in keywords:
                if isinstance(k, str):
                    norm.append({"word": k, "color": "#FF3B30", "bold": True})
                elif isinstance(k, dict) and k.get("word"):
                    norm.append(k)
            if norm:
                payload["keywords"] = norm
        out = _post("/add_subtitle", payload, timeout=180)
        ok = bool(out.get("success", False))
        self._log("添加字幕", ok, f"{os.path.basename(srt_path)} {len(open(srt_path, encoding='utf-8').readlines())//4}条"
                  + (f" 高亮{len(keywords)}词" if keywords else ""))
        return ok

    TEXT_TRACKS = ["text_main", "text_2", "title", "subtitle"]

    def _free_text_track(self, draft_id: str, start: float, end: float) -> str:
        for track in self.TEXT_TRACKS:
            busy = self._slot_by_track.get((draft_id, track), [])
            if all(not (start < e and end > s) for s, e in busy):
                return track
        return "text_main"

    def add_text(self, draft_id: str, text: str, start: float, end: float,
                 font_size: float = 12.0, font_color: str = "#FFD400",
                 transform_x: float = 0.0, transform_y: float = 0.85,
                 font: str = "文轩体", bold: bool = False, italic: bool = False,
                 underline: bool = False, alignment: str = "center",
                 line_spacing: float = 0.25, letter_spacing: float = 0.0,
                 background_alpha: float = 0.3, background_color: str = "#000000",
                 background_round_radius: float = 0.0,
                 border_width: float = 0.6, border_color: str = "#000000",
                 intro_animation: str = None, intro_duration: float = 0.5,
                 outro_animation: str = None, outro_duration: float = 0.5,
                 text_styles: list = None,
                 track_name: str = None, auto_layer: bool = True,
                 auto_fit: bool = True) -> bool:
        if auto_layer and track_name is None:
            track_name = self._free_text_track(draft_id, start, end)
        track_name = track_name or "text_main"
        # 单行自适应字号（2026-10-13 用户规则：先缩字号尽量单行，再按最终字号过安全线）
        fitted_note = ""
        if auto_fit:
            fs_new, fitted = auto_fit_font_size(text, font_size, bold=bold)
            if abs(fs_new - font_size) > 0.01:
                fitted_note = f" [字号{font_size:g}→{fs_new:g} 单行适配]"
                font_size = fs_new
            elif not fitted:
                fitted_note = " [已达最小字号,允许换行兜底]"
        transform_y = safe_transform_y(font_size, transform_y)
        payload = {
            "draft_id": draft_id, "text": text, "start": start, "end": end,
            "font_size": font_size, "font_color": font_color,
            "transform_x": transform_x, "transform_y": transform_y,
            "font": font, "bold": bold, "italic": italic, "underline": underline,
            "alignment": alignment, "line_spacing": line_spacing,
            "letter_spacing": letter_spacing, "background_alpha": background_alpha,
            "background_color": background_color,
            "background_round_radius": background_round_radius,
            "border_width": border_width, "border_color": border_color,
            "track_name": track_name,
        }
        if intro_animation:
            payload["intro_animation"] = _resolve_anim(intro_animation, TEXT_INTRO_MAP, JIANYING_TEXT_INTRO_NAMES)
            payload["intro_duration"] = intro_duration
        if outro_animation:
            payload["outro_animation"] = _resolve_anim(outro_animation, TEXT_OUTRO_MAP, JIANYING_TEXT_OUTRO_NAMES)
            payload["outro_duration"] = outro_duration
        if text_styles:
            payload["text_styles"] = text_styles
        out = _post("/add_text", payload, timeout=120)
        ok = bool(out.get("success", False))
        if ok:
            self._text_slots.setdefault(draft_id, []).append((start, end))
            self._slot_by_track.setdefault((draft_id, track_name), []).append((start, end))
            self._log("添加标题", ok, text + (f" [动画:{intro_animation or ''}]" if intro_animation else "")
                      + fitted_note + f" [轨:{track_name}]")
        else:
            self._log("添加标题", ok, text + " " + str(out.get("error", ""))[:60])
        return ok

    def add_rich_text(self, draft_id: str, text: str, highlights: list,
                      start: float, end: float, font_size: float = 12.0,
                      font_color: str = "#FFD400", transform_y: float = 0.85,
                      background_alpha: float = 0.3, border_width: float = 0.6,
                      border_color: str = "#000000",
                      intro_animation: str = None, intro_duration: float = 0.5,
                      track_name: str = None) -> bool:
        styles = []
        for h in highlights:
            word = h.get("word")
            if not word:
                continue
            pos = 0
            while True:
                idx = text.find(word, pos)
                if idx == -1:
                    break
                style = {"size": h.get("size", font_size + 2), "bold": h.get("bold", True),
                         "italic": h.get("italic", False), "underline": h.get("underline", False),
                         "color": h.get("color", "#FF3B30")}
                styles.append({"start": idx, "end": idx + len(word), "style": style})
                pos = idx + len(word)
        if not styles:
            return self.add_text(draft_id, text, start, end, font_size=font_size,
                                 font_color=font_color, transform_y=transform_y,
                                 background_alpha=background_alpha, border_width=border_width,
                                 border_color=border_color, intro_animation=intro_animation,
                                 intro_duration=intro_duration, track_name=track_name)
        return self.add_text(draft_id, text, start, end, font_size=font_size,
                             font_color=font_color, transform_y=safe_transform_y(font_size, transform_y),
                             background_alpha=background_alpha, border_width=border_width,
                             border_color=border_color, intro_animation=intro_animation,
                             intro_duration=intro_duration, text_styles=styles, track_name=track_name)

    def save_and_deploy(self, draft_id: str, project_name: str) -> str:
        out = _post("/save_draft", {"draft_id": draft_id, "project_name": project_name, "auto_deploy": False}, timeout=600)
        local = ""
        if isinstance(out.get("output"), dict):
            local = out["output"].get("draft_url", "")
        if not local or not os.path.isdir(local):
            cand = os.path.join(VECTCUT_DIR, draft_id)
            if os.path.isdir(cand):
                local = cand
        if not local:
            self._log("保存草稿", False, "未找到草稿输出目录")
            return ""
        os.makedirs(self.draft_root, exist_ok=True)
        dest = os.path.join(self.draft_root, project_name)
        try:
            if os.path.exists(dest):
                shutil.rmtree(dest)
        except PermissionError:
            dest = os.path.join(self.draft_root, f"{project_name}_{int(time.time())}")
        shutil.copytree(local, dest)
        lock = os.path.join(dest, ".locked")
        if os.path.exists(lock):
            os.remove(lock)
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from .self_contain import self_contain_draft
            self_contain_draft(dest)
        except Exception as e:
            print(f"⚠️ 素材自包含跳过: {e}")
        dc = os.path.join(dest, "draft_content.json")
        if not os.path.exists(dc):
            self._log("部署草稿", False, f"完整性校验失败: 缺 draft_content.json（{dest}）")
            return ""
        try:
            data = json.load(open(dc, encoding="utf-8"))
            assert isinstance(data.get("tracks"), list) and data.get("tracks"), "tracks 为空"
            assert isinstance(data.get("materials"), dict) and data.get("materials"), "materials 为空"
        except Exception as e:
            self._log("部署草稿", False, f"完整性校验失败: {e}（{dest}）")
            return ""
        try:
            from collections import Counter
            cnt = Counter()
            for tr in data.get("tracks", []):
                for seg in tr.get("segments", []):
                    path = seg.get("material_id") or seg.get("path") or ""
                    src = seg.get("source_timerange", {}).get("start", 0)
                    if path:
                        cnt[f"{os.path.basename(path)}@{src}"] += 1
            for key, n in cnt.items():
                if n > 5:
                    print(f"⚠️ [素材审计] {key} 重复{n}次——如为短素材循环，请改用播放完/多截一段再循环")
        except Exception:
            pass
        self._log("部署草稿", True, f"→ {dest}")
        return dest

    def _cloud_material(self, query: str):
        from .media import CloudManager
        cm = CloudManager()
        asset = cm.find_asset(query)
        if not asset:
            return None, False
        path = cm.download_asset(query)
        is_audio = asset["source_db"] in {"cloud_music_library.csv", "cloud_sound_effects.csv"}
        return path, is_audio

    def add_cloud_music(self, draft_id: str, query: str, volume: float = 0.35,
                        track_name: str = "bgm", start: float = 0, end: float = None,
                        normalize: bool = True, auto_balance: bool = False,
                        voice_path: str = None) -> Optional[str]:
        from .media import CloudManager
        cm = CloudManager()
        asset = cm.find_asset(query)
        if not asset:
            self._log("云端音乐", False, f"未找到: {query}")
            return None
        path = cm.download_asset(query)
        if not path:
            return None
        work = path
        if path.lower().endswith(".m4a"):
            work = os.path.join(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0] + "_v.wav")
            subprocess.run(["ffmpeg", "-y", "-i", path, "-ar", "44100", "-ac", "2", work],
                           capture_output=True, timeout=300)
            if not os.path.exists(work):
                work = path
        if auto_balance and voice_path and os.path.exists(voice_path):
            try:
                from .audio_balance import auto_bgm_volume
                volume = auto_bgm_volume(voice_path, work, headroom_db=15.0)
            except Exception as e:
                print(f"⚠️ 响度平衡失败({e})，用固定 volume={volume}")
        total = asset.get("duration_s") or 0 if end is None else end
        ok = self.add_audio(draft_id, work, volume=volume, track_name=track_name,
                            start=start, end=total)
        self._log("云端音乐", ok, f"{asset['name']} vol={volume} 铺满{total:.1f}s")
        return work if ok else None

    def add_cloud_media(self, draft_id: str, query: str, volume: float = 1.0,
                        track_name: str = "video", start: float = 0,
                        end: float = None) -> Optional[str]:
        from .media import CloudManager
        cm = CloudManager()
        asset = cm.find_asset(query)
        if not asset:
            self._log("云端素材", False, f"未找到: {query}")
            return None
        path = cm.download_asset(query)
        if not path:
            return None
        is_audio = asset["source_db"] in {"cloud_music_library.csv", "cloud_sound_effects.csv", "jy_cached_audio.csv"}
        if is_audio:
            ok = self.add_audio(draft_id, path, volume=volume, track_name=track_name,
                                start=start, end=end if end else (asset.get("duration_s") or 0))
        else:
            ok = self.add_video(draft_id, path, volume=volume, track_name=track_name,
                                start=start, end=end if end else (asset.get("duration_s") or 0))
        self._log("云端素材", ok, f"{asset['name']} → {track_name}")
        return path if ok else None

    def _draft_duration(self, draft_id: str, base_track: str = "audio_main") -> float:
        import json as _json
        local = os.path.join(VECTCUT_DIR, draft_id)
        dc = os.path.join(local, "draft_content.json")
        if not os.path.exists(dc):
            return 0
        data = _json.load(open(dc, encoding="utf-8"))
        for tr in data.get("tracks", []):
            if tr.get("type") == "audio" and tr.get("name") == base_track:
                for seg in tr.get("segments", []):
                    e = seg.get("target_timerange", {}).get("duration", 0)
                    if e:
                        return e / 1e6
        for tr in data.get("tracks", []):
            if tr.get("type") == "video" and tr.get("name") == "video":
                for seg in tr.get("segments", []):
                    e = seg.get("target_timerange", {}).get("duration", 0)
                    if e:
                        return e / 1e6
        dur = 0.0
        for tr in data.get("tracks", []):
            for seg in tr.get("segments", []):
                e = seg.get("target_timerange", {}).get("duration", 0)
                if e:
                    dur = max(dur, e)
        return dur / 1e6 if dur > 1e5 else dur

    def report(self) -> dict:
        ok_count = sum(1 for r in self.results if r["ok"])
        return {"total": len(self.results), "ok": ok_count,
                "failed": len(self.results) - ok_count, "results": self.results}


if __name__ == "__main__":
    print("剪映工厂 v7.8 VectCutAPI 内核 - 请在其他脚本中调用（勿直接运行）")
