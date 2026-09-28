#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 统一配置（路径全部参数化，别人安装即用）
读取顺序：环境变量 > factory_config.json > 内置默认值
"""
import os
import json
from pathlib import Path

# 内置默认（可被 factory_config.json / 环境变量覆盖）
DEFAULTS = {
    # 草稿/导出/备份根目录
    "draft_root": r"D:\AI工作区\剪映草稿",
    "export_root": r"D:\AI工作区\导出",
    "backup_root": r"D:\AI工作区\剪映草稿_备份",
    # 默认素材与配音/BGM
    "default_video": r"E:\张总口播素材\张总形象.mp4",
    "voiceover_dir": r"D:\AI工作区\配音",
    "bgm_dir": r"D:\AI工作区\BGM",
    # 出片参数
    "canvas_width": 1080,
    "canvas_height": 1920,
    "fps": 30,
    "video_volume": 0.0,     # 原片强制静音
    "voice_volume": 1.0,
    "bgm_volume": 0.35,      # 30-40% 区间，不抢人声
    "default_voice": "云希",
    # 成品质量门禁
    "quality": {
        "bgm_volume_min": 0.30,
        "bgm_volume_max": 0.40,
        "require_subtitle": True,
        "align_tolerance_ms": 500,
    },
}

_CONFIG = None


def _config_path() -> str:
    """配置文件位置：与脚本同目录的 factory_config.json"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "factory_config.json")


def _merge(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config() -> dict:
    """加载配置：文件 > 内置默认。环境变量按 KEY 覆盖（如 JIANYING_DRAFT_ROOT）"""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    cfg = json.loads(json.dumps(DEFAULTS))  # 深拷贝
    p = _config_path()
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _merge(cfg, user_cfg)
        except Exception as e:
            print(f"⚠️ 配置文件解析失败（{e}），使用内置默认")
    # 环境变量覆盖
    env_map = {
        "JIANYING_DRAFT_ROOT": "draft_root",
        "JIANYING_EXPORT_ROOT": "export_root",
        "JIANYING_BACKUP_ROOT": "backup_root",
        "JIANYING_DEFAULT_VIDEO": "default_video",
        "JIANYING_BGM_VOLUME": "bgm_volume",
    }
    for env, key in env_map.items():
        if os.environ.get(env):
            val = os.environ[env]
            try:
                val = float(val) if key == "bgm_volume" else val
            except ValueError:
                pass
            cfg[key] = val
    _CONFIG = cfg
    return cfg


def ensure_dirs() -> None:
    """确保关键目录存在（全部在配置指定盘符，不占 C 盘）"""
    cfg = load_config()
    for key in ("draft_root", "export_root", "backup_root", "voiceover_dir", "bgm_dir"):
        d = cfg.get(key)
        if d:
            os.makedirs(d, exist_ok=True)


def get(key: str, default=None):
    return load_config().get(key, default)


if __name__ == "__main__":
    cfg = load_config()
    print("当前配置：")
    for k, v in cfg.items():
        if k == "quality":
            print(f"  quality: {json.dumps(v, ensure_ascii=False)}")
        else:
            print(f"  {k}: {v}")
