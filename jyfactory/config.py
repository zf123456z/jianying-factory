#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剪映工厂 - 统一配置（v8.1 三级参数化：环境变量 > config.json > 内置默认）

优先级（高→低）：
  1. 环境变量 JYFACTORY_XXX
  2. <工作区>/config.json（install.py 自动生成）
  3. 内置默认值（作者本机默认，向后兼容）

任一路径均可被环境变量/JSON 覆盖。工作区根 JYFACTORY_HOME 可整体重定向。
"""
import json
import os

# ========== 内置默认（作者本机基线，可全被覆盖） ==========
DEFAULT_HOME = r"D:\AI工作区"
DEFAULT_VIDEO = r"E:\张总口播素材\张总形象.mp4"
DEFAULT_VIDEO_ALT = r"E:\张总口播素材\张总口播素材.mp4"

DRAFT_DIR = os.path.join(DEFAULT_HOME, "剪映草稿")
DRAFT_BACKUP_DIR = os.path.join(DEFAULT_HOME, "剪映草稿_备份")
EXPORT_DIR = os.path.join(DEFAULT_HOME, "导出")
MATERIAL_DIR = os.path.join(DEFAULT_HOME, "素材")
VOICE_DIR = os.path.join(DEFAULT_HOME, "配音")
COVER_DIR = os.path.join(DEFAULT_HOME, "封面")
BGM_DIR = os.path.join(DEFAULT_HOME, "BGM")
CLOUD_CACHE_DIR = os.path.join(DEFAULT_HOME, "cloud_cache")
VECTCUT_DIR = os.path.join(DEFAULT_HOME, "代码", "VectCutAPI")
DATA_DIR = os.path.join(DEFAULT_HOME, "data")

API = "http://127.0.0.1:9001"
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
FPS = 30
VOICE_VOLUME = 1.0
BGM_VOLUME = 0.4          # 铁律 30-40%
ORIGINAL_VIDEO_VOLUME = 0.0  # 铁律 原片静音
SUBTITLE_SIZE = 6.0
SUBTITLE_POS_Y = -0.72
DEFAULT_SUBTITLE_STYLE = "yellow"

_JIANYING_EXE = None
JIANYING_BGM_CACHE = None


def _load_json_cfg(path):
    """读取 JSON 配置，兼容 UTF-8 BOM（记事本 Save-Content 默认带 BOM，json.load 会炸）。"""
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def _find_home() -> str:
    """工作区根：环境变量 > config.json > 内置默认。
    搜索 config.json 顺序：JYFACTORY_HOME → 项目根(技能包根) → 默认 HOME。"""
    env = os.environ.get("JYFACTORY_HOME") or ""
    if env:
        return env.strip().rstrip("\\")
    candidates = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # 项目根（包上一级）
        os.path.dirname(os.path.abspath(__file__)),                  # 包目录
        DEFAULT_HOME,
    ]
    for c in candidates:
        cfg = os.path.join(c, "config.json")
        if os.path.isfile(cfg):
            try:
                data = _load_json_cfg(cfg)
            except Exception:
                continue
            home = data.get("JYFACTORY_HOME") or data.get("_工作区") or ""
            if home:
                return str(home).strip().rstrip("\\")
    return DEFAULT_HOME


def _apply_env(name, default):
    v = os.environ.get("JYFACTORY_" + name)
    if v is None or not str(v).strip():
        return default
    return str(v).strip()


def _init():
    global DEFAULT_VIDEO, DEFAULT_VIDEO_ALT
    global DRAFT_DIR, DRAFT_BACKUP_DIR, EXPORT_DIR, MATERIAL_DIR, VOICE_DIR
    global COVER_DIR, BGM_DIR, CLOUD_CACHE_DIR, VECTCUT_DIR, DATA_DIR, API
    global CANVAS_WIDTH, CANVAS_HEIGHT, FPS, VOICE_VOLUME, BGM_VOLUME
    global ORIGINAL_VIDEO_VOLUME, SUBTITLE_SIZE, SUBTITLE_POS_Y
    global DEFAULT_SUBTITLE_STYLE, _JIANYING_EXE, JIANYING_BGM_CACHE

    home = _find_home()

    # 从用户 config.json 读覆盖（若存在）
    user_cfg = {}
    for c in (os.path.join(home, "config.json"),
              os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"),
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")):
        if os.path.isfile(c):
            try:
                user_cfg = _load_json_cfg(c)
            except Exception:
                pass
            if user_cfg:
                break

    def p(name, default):
        """最终值：环境变量 > config.json > default"""
        if os.environ.get("JYFACTORY_" + name):
            return _apply_env(name, default)
        v = user_cfg.get(name)
        return default if v is None else v

    DEFAULT_VIDEO = p("DEFAULT_VIDEO", DEFAULT_VIDEO)
    DEFAULT_VIDEO_ALT = p("DEFAULT_VIDEO_ALT", DEFAULT_VIDEO_ALT)
    DRAFT_DIR = p("DRAFT_DIR", os.path.join(home, "剪映草稿"))
    DRAFT_BACKUP_DIR = p("DRAFT_BACKUP_DIR", os.path.join(home, "剪映草稿_备份"))
    EXPORT_DIR = p("EXPORT_DIR", os.path.join(home, "导出"))
    MATERIAL_DIR = p("MATERIAL_DIR", os.path.join(home, "素材"))
    VOICE_DIR = p("VOICE_DIR", os.path.join(home, "配音"))
    COVER_DIR = p("COVER_DIR", os.path.join(home, "封面"))
    BGM_DIR = p("BGM_DIR", os.path.join(home, "BGM"))
    CLOUD_CACHE_DIR = p("CLOUD_CACHE_DIR", os.path.join(home, "cloud_cache"))
    VECTCUT_DIR = p("VECTCUT_DIR", os.path.join(home, "代码", "VectCutAPI"))
    DATA_DIR = p("DATA_DIR", os.path.join(home, "data"))
    API = p("API", "http://127.0.0.1:9001")
    CANVAS_WIDTH = int(p("CANVAS_WIDTH", 1080))
    CANVAS_HEIGHT = int(p("CANVAS_HEIGHT", 1920))
    FPS = int(p("FPS", 30))
    VOICE_VOLUME = float(p("VOICE_VOLUME", 1.0))
    BGM_VOLUME = float(p("BGM_VOLUME", 0.4))
    ORIGINAL_VIDEO_VOLUME = float(p("ORIGINAL_VIDEO_VOLUME", 0.0))
    SUBTITLE_SIZE = float(p("SUBTITLE_SIZE", 6.0))
    SUBTITLE_POS_Y = float(p("SUBTITLE_POS_Y", -0.72))
    DEFAULT_SUBTITLE_STYLE = p("DEFAULT_SUBTITLE_STYLE", "yellow")

    # 剪映主程序自动探测（注册表 + 常见路径）
    _JIANYING_EXE = p("JIANYING_EXE", None) or _probe_jianying_exe()
    # 剪映缓存音乐目录自动探测
    JIANYING_BGM_CACHE = p("JIANYING_BGM_CACHE", None) or _probe_jy_bgm_cache()

    # 核心输出目录自动创建
    for d in (DRAFT_DIR, EXPORT_DIR, MATERIAL_DIR, VOICE_DIR, COVER_DIR, BGM_DIR, CLOUD_CACHE_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def _probe_jianying_exe():
    import shutil
    # 注册表
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Uninstall\JianyingPro"),
                          (winreg.HKEY_LOCAL_MACHINE,
                           r"Software\Microsoft\Windows\CurrentVersion\Uninstall\JianyingPro")):
            try:
                with winreg.OpenKey(hive, key) as k:
                    loc, _ = winreg.QueryValueEx(k, "InstallLocation")
                for root in (loc,):
                    exe = os.path.join(root, "JianyingPro.exe")
                    if os.path.isfile(exe):
                        return exe
            except Exception:
                continue
    except Exception:
        pass
    # 常见路径
    import glob
    for pat in (os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\Apps\*"),
                r"C:\Program Files\JianyingPro\Apps\*"):
        for d in sorted(glob.glob(pat), reverse=True):
            exe = os.path.join(d, "JianyingPro.exe")
            if os.path.isfile(exe):
                return exe
    return None


def _probe_jy_bgm_cache():
    import glob
    for pat in (os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Cache\music"),
                os.path.expandvars(r"%APPDATA%\JianyingPro\User Data\Cache\music")):
        if os.path.isdir(pat):
            return pat
    return None


_init()

DRAFT_ROOT = DRAFT_DIR  # 兼容旧引用
