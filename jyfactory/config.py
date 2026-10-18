#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 统一配置（v8.1 对外可配置版）

配置优先级（高→低）：
  1. 环境变量  JYFACTORY_XXX（如 JYFACTORY_DRAFT_DIR、JYFACTORY_HOME、JYFACTORY_DEFAULT_VIDEO）
  2. 用户配置  <JYFACTORY_HOME>/config.json 或 技能包根目录 config.json（首次 install/setup 自动生成）
  3. 内置默认  （默认值为作者本机路径，未配置时保持原行为，向后兼容）

工作区根：
  - 环境变量 JYFACTORY_HOME 可整体重定向（默认 D:\\AI工作区）
  - 所有子目录（草稿/导出/素材/配音/缓存…）相对工作区根自动派生，
    也可在 config.json / 环境变量中单独覆盖

剪映与 ffmpeg：
  - JIANYING_EXE：自动探测注册表 + 常见路径；config.json 可手写覆盖
  - ffmpeg：shutil.which 探测 PATH；缺失时 checks.doctor 会明确提示
"""

import json
import os
import shutil
import sys
import winreg
from pathlib import Path

# ========== 0. 工作区根（唯一顶层锚点） ==========
_HOME = os.environ.get("JYFACTORY_HOME") or r"D:\AI工作区"
_HOME = _HOME.rstrip("\\/")

# ========== 1. 用户配置文件加载 ==========
def _load_user_config():
    """读取用户配置 JSON（不存在返回空 dict）"""
    candidates = [
        os.environ.get("JYFACTORY_CONFIG"),
        os.path.join(_HOME, "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
    ]
    for path in candidates:
        if not path:
            continue
        if os.path.isfile(path):
            try:
                # utf-8-sig 兼容记事本等工具保存的带 BOM 文件
                with open(path, "r", encoding="utf-8-sig") as f:
                    return json.load(f) or {}
            except Exception as e:
                print(f"⚠️ 读取用户配置失败（{path}）：{e}")
                return {}
    return {}


USER_CFG = _load_user_config()


def _env(key):
    """环境变量读取，key = JYFACTORY_XXX"""
    return os.environ.get(f"JYFACTORY_{key}")


def _resolve(key, default):
    """三级解析：环境变量 > config.json > 默认值"""
    v = _env(key)
    if v:
        return v
    if key in USER_CFG and USER_CFG[key]:
        return str(USER_CFG[key])
    return default


def _resolve_dir(key, default):
    """目录三级解析（展开环境变量）"""
    v = _resolve(key, default)
    return os.path.expandvars(v)


# ========== 2. 自动探测剪映安装路径 ==========
def _detect_jianying():
    """探测剪映专业版主程序路径：注册表 > 常见安装路径"""
    # 注册表：JianyingPro 的 uninstall / App Paths
    reg_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    try:
        for hive, sub in reg_keys:
            try:
                with winreg.OpenKey(hive, sub) as key:
                    i = 0
                    while True:
                        try:
                            name = winreg.EnumKey(key, i)
                            i += 1
                            try:
                                with winreg.OpenKey(key, name) as k:
                                    try:
                                        val, _ = winreg.QueryValueEx(k, None)
                                    except OSError:
                                        continue
                                    if val and isinstance(val, str) and ("Jianying" in val or "JianyingPro" in val) and val.lower().endswith(".exe"):
                                        return val
                                    try:
                                        disp, _ = winreg.QueryValueEx(k, "DisplayName")
                                        if disp and "剪映" in str(disp):
                                            loc, _ = winreg.QueryValueEx(k, "InstallLocation")
                                            if loc:
                                                cand = os.path.join(loc, "JianyingPro.exe")
                                                if os.path.isfile(cand):
                                                    return cand
                                    except OSError:
                                        pass
                            except OSError:
                                continue
                        except OSError:
                            break
            except OSError:
                continue
    except Exception:
        pass
    # 常见路径（按版本号通配）
    base = os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\Apps")
    if os.path.isdir(base):
        for ver in sorted(os.listdir(base), reverse=True):
            cand = os.path.join(base, ver, "JianyingPro.exe")
            if os.path.isfile(cand):
                return cand
    return None


_JIANYING_EXE = _resolve("JIANYING_EXE", "") or _detect_jianying() or ""

# 剪映缓存音乐目录（探测主程序同级的 User Data）
if _JIANYING_EXE:
    _jy_base = os.path.dirname(os.path.dirname(_JIANYING_EXE))
    _jy_userdata = os.path.join(os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Cache\music"))
else:
    _jy_userdata = r"C:\Users\HuaWei\AppData\Local\JianyingPro\User Data\Cache\music"

# ========== 3. ffmpeg 探测 ==========
FFMPEG = shutil.which("ffmpeg") or (os.path.isfile(r"C:\ffmpeg\bin\ffmpeg.exe") and r"C:\ffmpeg\bin\ffmpeg.exe") or ""
FFPROBE = shutil.which("ffprobe") or (os.path.isfile(r"C:\ffmpeg\bin\ffprobe.exe") and r"C:\ffmpeg\bin\ffprobe.exe") or ""

# ========== 4. 路径配置（全部可覆盖） ==========
DRAFT_DIR = _resolve_dir("DRAFT_DIR", os.path.join(_HOME, "剪映草稿"))
DRAFT_BACKUP_DIR = _resolve_dir("DRAFT_BACKUP_DIR", os.path.join(_HOME, "剪映草稿_备份"))
EXPORT_DIR = _resolve_dir("EXPORT_DIR", os.path.join(_HOME, "导出"))
CODE_DIR = _resolve_dir("CODE_DIR", os.path.join(_HOME, "代码"))
MATERIAL_DIR = _resolve_dir("MATERIAL_DIR", os.path.join(_HOME, "素材"))
VOICE_DIR = _resolve_dir("VOICE_DIR", os.path.join(_HOME, "配音"))
COVER_DIR = _resolve_dir("COVER_DIR", os.path.join(_HOME, "封面"))
BGM_DIR = _resolve_dir("BGM_DIR", os.path.join(_HOME, "BGM"))
CLOUD_CACHE_DIR = _resolve_dir("CLOUD_CACHE_DIR", os.path.join(_HOME, "cloud_cache"))
JY_CACHED_DIR = _resolve_dir("JY_CACHED_DIR", os.path.join(CLOUD_CACHE_DIR, "jy_cached"))
JY_CACHED_INDEX = _resolve_dir("JY_CACHED_INDEX", os.path.join(_HOME, "data", "jy_cached_audio.csv"))
JYFACTORY_ROOT = _resolve_dir("JYFACTORY_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VECTCUT_DIR = _resolve_dir("VECTCUT_DIR", os.path.join(CODE_DIR, "VectCutAPI"))
API = _env("API") or str(USER_CFG.get("API", "http://127.0.0.1:9001"))
DRAFT_ROOT = DRAFT_DIR

# ========== 5. 固定素材（用户配置，首次 setup 引导；兼容原默认值） ==========
DEFAULT_VIDEO = _resolve("DEFAULT_VIDEO", r"E:\张总口播素材\张总形象.mp4")
DEFAULT_VIDEO_ALT = _resolve("DEFAULT_VIDEO_ALT", r"E:\张总口播素材\张总视频.mp4")
DEFAULT_BGM = _resolve("DEFAULT_BGM", os.path.join(BGM_DIR, "默认口播BGM_01.mp3"))

# 剪映缓存音乐目录
JIANYING_BGM_CACHE = _resolve("JIANYING_BGM_CACHE", _jy_userdata)

# ========== 6. 视频尺寸 ==========
CANVAS_WIDTH = int(_resolve("CANVAS_WIDTH", "1080"))
CANVAS_HEIGHT = int(_resolve("CANVAS_HEIGHT", "1920"))
FPS = int(_resolve("FPS", "30"))
RATIO = _resolve("RATIO", "9:16")

# ========== 7. 音频音量（0-1） ==========
VOICE_VOLUME = float(_resolve("VOICE_VOLUME", "1.0"))
BGM_VOLUME = float(_resolve("BGM_VOLUME", "0.4"))
ORIGINAL_VIDEO_VOLUME = float(_resolve("ORIGINAL_VIDEO_VOLUME", "0.0"))

# ========== 8. BGM配置 ==========
BGM_FADE_IN = float(_resolve("BGM_FADE_IN", "0.5"))
BGM_FADE_OUT = float(_resolve("BGM_FADE_OUT", "0.5"))

# ========== 9. 字幕配置 ==========
SUBTITLE_SIZE = float(_resolve("SUBTITLE_SIZE", "6.0"))
SUBTITLE_POS_Y = float(_resolve("SUBTITLE_POS_Y", "-0.72"))
SUBTITLE_STROKE_WIDTH = float(_resolve("SUBTITLE_STROKE_WIDTH", "0.15"))

# ========== 10. 视频循环配置 ==========
MAX_SEGMENT_DUR = int(_resolve("MAX_SEGMENT_DUR", "10"))
SEGMENT_OFFSET = int(_resolve("SEGMENT_OFFSET", "2"))

# ========== 11. 默认值 ==========
DEFAULT_SUBTITLE_STYLE = _resolve("DEFAULT_SUBTITLE_STYLE", "yellow")
DEFAULT_TRANSITION = _resolve("DEFAULT_TRANSITION", "fade")

# ========== 12. 开机自检（仅打印关键信息，不中断） ==========
def _ensure_dirs():
    """核心输出目录自动创建（草稿/导出/素材/配音/封面/BGM/缓存）"""
    for d in (DRAFT_DIR, EXPORT_DIR, MATERIAL_DIR, VOICE_DIR, COVER_DIR, BGM_DIR, CLOUD_CACHE_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass


_ensure_dirs()

if not os.environ.get("JYFACTORY_QUIET"):
    print("✅ 配置加载完成")
    print(f"   工作区：{_HOME}")
    print(f"   草稿目录：{DRAFT_DIR}")
    print(f"   导出目录：{EXPORT_DIR}")
    print(f"   剪映主程序：{_JIANYING_EXE or '未探测到（可配置 JYFACTORY_JIANYING_EXE 或 config.json）'}")
    print(f"   ffmpeg：{FFMPEG or '未找到（安装 ffmpeg 并加入 PATH）'}")
    print(f"   人声音量：{VOICE_VOLUME*100}%")
    print(f"   BGM音量：{BGM_VOLUME*100}%")
