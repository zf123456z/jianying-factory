#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 一键安装脚本（对外新用户入口）

用法：
    python install.py            # 全自动安装 + 环境体检
    python install.py --quick    # 跳过交互询问（素材路径用默认值，之后可在 config.json 改）

做的事：
    1. 检测 Python / ffmpeg / 剪映（缺失给明确指引，不中断）
    2. 获取 VectCutAPI 内核（GitHub 下载 zip → 解压 → 装依赖；已存在则跳过）
    3. pip 安装本项目依赖（requirements.txt）
    4. 生成 config.json（工作目录 / 素材路径，--quick 用默认值）
    5. 运行环境体检（cli doctor）并打印体检报告
    6. 提示装进豆包技能的下一步

环境要求：
    - Windows 10/11
    - Python 3.9+
    - 已安装剪映专业版（11.5 实测最优）
    - ffmpeg（加入 PATH；缺失时仅影响预览/转码，核心出片不受阻）
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

PY = sys.executable
ROOT = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ.get("JYFACTORY_HOME") or r"D:\AI工作区"

VECTCUT_URL = "https://github.com/sun-guannan/VectCutAPI/archive/refs/heads/main.zip"
VECTCUT_REQ = ["imageio", "psutil", "flask", "requests", "oss2", "json5"]

QUICK = "--quick" in sys.argv


def step(msg):
    print(f"\n▶ {msg}")


def ok(msg):
    print(f"  ✅ {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def fail(msg):
    print(f"  ❌ {msg}")


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def check_python():
    step("检测 Python")
    v = sys.version_info
    if v.major == 3 and v.minor >= 9:
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    fail(f"Python {v.major}.{v.minor} 过低，需要 3.9+")
    return False


def check_ffmpeg():
    step("检测 ffmpeg")
    ff = shutil.which("ffmpeg")
    if ff:
        ok(f"ffmpeg: {ff}")
        return True
    fail("未找到 ffmpeg。安装后加入 PATH：winget install ffmpeg 或 https://ffmpeg.org/download.html（核心出片不依赖，预览/抽帧/转码需要）")
    return False


def check_jianying():
    step("检测剪映专业版")
    try:
        sys.path.insert(0, ROOT)
        from jyfactory.config import _JIANYING_EXE, JIANYING_BGM_CACHE
    except Exception:
        _JIANYING_EXE, JIANYING_BGM_CACHE = None, None
    if _JIANYING_EXE:
        ok(f"剪映主程序: {_JIANYING_EXE}")
        if os.path.isdir(JIANYING_BGM_CACHE):
            ok(f"剪映缓存音乐目录: {JIANYING_BGM_CACHE}")
        return True
    fail("未探测到剪映专业版。请先安装剪映专业版（https://www.capcut.cn），安装后重跑本脚本")
    return False


def fetch_vectcut(dest):
    """下载并解压 VectCutAPI 到 dest（已存在跳过）"""
    if os.path.isfile(os.path.join(dest, "capcut_server.py")):
        ok(f"VectCutAPI 已存在: {dest}")
        return True
    step("获取 VectCutAPI 内核（剪映草稿确定性生成引擎）")
    os.makedirs(dest, exist_ok=True)
    tmp = os.path.join(tempfile.gettempdir(), "vectcut_main.zip")
    try:
        print(f"  下载 {VECTCUT_URL} ...")
        urllib.request.urlretrieve(VECTCUT_URL, tmp)
        with zipfile.ZipFile(tmp) as z:
            root_dir = z.namelist()[0].split("/")[0]
            z.extractall(dest)
        inner = os.path.join(dest, root_dir)
        for name in os.listdir(inner):
            shutil.move(os.path.join(inner, name), os.path.join(dest, name))
        os.rmdir(inner)
        ok(f"解压完成 → {dest}")
        return True
    except Exception as e:
        fail(f"VectCutAPI 下载/解压失败: {e}（可手动下载 {VECTCUT_URL} 解压到 {dest}）")
        return False


def pip_install_vectcut(dest):
    step("安装 VectCutAPI 依赖")
    req = os.path.join(dest, "requirements.txt")
    pkgs = VECTCUT_REQ
    if os.path.isfile(req):
        r = run(f'"{PY}" -m pip install -r "{req}"')
    else:
        r = run(f'"{PY}" -m pip install {" ".join(pkgs)}')
    if r.returncode == 0:
        ok("VectCutAPI 依赖安装完成")
    else:
        warn(f"pip 安装返回非零（{r.returncode}），请手动执行: {r.args}")


def pip_install_project():
    step("安装本项目依赖")
    req = os.path.join(ROOT, "requirements.txt")
    if not os.path.isfile(req):
        req = "."
    r = run(f'"{PY}" -m pip install -r "{req}"')
    if r.returncode == 0:
        ok("本项目依赖安装完成")
    else:
        warn(f"pip 安装返回非零（{r.returncode}），请手动检查 requirements.txt")


def gen_config():
    """生成 config.json（存在则不覆盖）"""
    cfg_path = os.path.join(HOME, "config.json")
    if os.path.isfile(cfg_path):
        ok(f"config.json 已存在: {cfg_path}（如需修改请直接编辑）")
        return
    step("生成用户配置 config.json")
    print("  请指定你的口播形象素材视频路径（用于 AI 出片的主素材）:")
    video = ""
    if not QUICK:
        try:
            video = input("  → ").strip().strip('"').strip("'")
        except EOFError:
            video = ""
    if not video or not os.path.isfile(video):
        video = r"E:\张总口播素材\张总形象.mp4"
        warn(f"未提供有效路径，使用默认值（之后可在 config.json 修改）: {video}")
    else:
        ok(f"素材: {video}")
    cfg = {
        "DEFAULT_VIDEO": video,
        "DRAFT_DIR": os.path.join(HOME, "剪映草稿"),
        "EXPORT_DIR": os.path.join(HOME, "导出"),
        "MATERIAL_DIR": os.path.join(HOME, "素材"),
        "VOICE_DIR": os.path.join(HOME, "配音"),
    }
    os.makedirs(HOME, exist_ok=True)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    ok(f"已写入: {cfg_path}")


def run_doctor():
    step("环境体检（cli doctor）")
    r = run(f'"{PY}" "{os.path.join(ROOT, "cli.py")}" doctor')
    print(r.stdout[-3000:] if r.stdout else "")
    if r.returncode == 0:
        ok("体检通过")
        return True
    warn("体检有告警项（多为 ffmpeg/剪映路径提示，按提示处理后重跑即可）")
    return False


def main():
    print("=" * 60)
    print("剪映工厂 · 一键安装")
    print("=" * 60)
    print(f"项目根: {ROOT}")
    print(f"工作区: {HOME}（可用环境变量 JYFACTORY_HOME 修改）")

    checks = [check_python(), check_ffmpeg(), check_jianying()]
    if not checks[0]:
        sys.exit(1)

    vectcut_dir = os.path.join(HOME, "代码", "VectCutAPI")
    if fetch_vectcut(vectcut_dir):
        pip_install_vectcut(vectcut_dir)
    pip_install_project()
    gen_config()
    run_doctor()

    print()
    print("=" * 60)
    print("安装完成！下一步：")
    print("  方式A（豆包技能）: 把本目录复制到豆包技能目录后，在豆包里说「帮我做个口播视频」")
    print("  方式B（命令行）  : python cli.py produce-tally \"你的文案\" --video 素材.mp4 --project 草稿名")
    print("  常用命令:")
    print("    python cli.py doctor        # 环境体检")
    print("    python cli.py ensure        # 启动 VectCutAPI 内核服务")
    print("    python cli.py templates     # 列出可用模板")
    print("=" * 60)


if __name__ == "__main__":
    main()
