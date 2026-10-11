#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 剪映标准启动器（受控窗口内启动，v7.7.2 实测定死）
================================================================
【重要】必须在 computer_use_tool(plane="cu") 的代码环境里调用，
不能在 PowerShell/Bash 里直接跑本脚本 —— 本脚本依赖 seed_computer_use。

正确用法（在 computer_use_tool 里）：
    from .launch import LAUNCH
    LAUNCH(mode="search", max_wait_s=45)     # 首选：任务栏搜索启动
    LAUNCH(mode="icon", icon_center=(x, y))  # 备选：桌面图标双击

为什么必须这样启动（踩坑记录，v7.7.2 重新定死）：
❌ subprocess.Popen 直接启动主程序 -> 剪映进程在后台起来了，但窗口
   不会出现在受控桌面视图里（uiautomation 找得到窗口、截图却看不到），白启动
❌ cu.list_apps() + launch_app -> 受控窗口应用清单实测无剪映（官方安装版
   未注册进受控应用目录），launch_app 拒绝
✅【首选·v7.7.2 实测】任务栏搜索启动：点任务栏搜索框 → 输入"剪映" →
   点搜索结果「剪映专业版」-> 30s 内首页出现（2026-09-30 实测两次成功）
   ⚠️ 踩坑补充（2026-09-30 实测）：搜索结果带右键菜单时，点左侧列表项
   (62-81, 262) 可能落空；此时直接点右侧菜单「打开」(262, 402) 一次成功。
✅【备选】受控桌面 OCR 定位「剪映专业版」桌面图标 -> cu.left_double(图标中心)
   -> 剪映窗口出现在受控桌面视图（2026-09-29 实测双击后约25s首页出现）
✅ 复用：若截图已见剪映首页/编辑页，直接复用不重复启动（效率关键）
"""
import time


def SEARCH_LAUNCH(max_wait_s: int = 45) -> str:
    """任务栏搜索启动剪映（v7.7.2 首选，2026-09-30 实测一次成功）。"""
    import seed_computer_use as cu
    print("🔍 任务栏搜索启动剪映")
    cu.click(80, 982)          # 任务栏搜索框（实测 1920x1080）
    time.sleep(2)
    cu.type("剪映")
    time.sleep(2)
    cu.screenshot()
    cu.click(81, 263)
    time.sleep(3)
    cu.screenshot()
    cu.click(262, 402)         # 兜底：右键菜单「打开」
    waited = 0
    while waited < max_wait_s:
        time.sleep(5)
        waited += 5
        cu.screenshot()
        print(f"⏳ 等待剪映就绪: {waited}s")
    cu.screenshot()
    return f"OK: 已通过任务栏搜索启动剪映（等待{waited}s，外层 OCR 确认首页/草稿列表出现）"


def ICON_LAUNCH(icon_center: tuple = (48, 650), max_wait_s: int = 45) -> str:
    """受控桌面双击剪映图标启动（v7.7.2 备选）。"""
    import seed_computer_use as cu
    print(f"🎯 双击受控桌面剪映图标: {icon_center}")
    cu.left_double(*icon_center)
    waited = 0
    while waited < max_wait_s:
        time.sleep(5)
        waited += 5
        cu.screenshot()
        print(f"⏳ 等待剪映就绪: {waited}s")
    cu.screenshot()
    return f"OK: 已双击启动剪映（等待{waited}s，请外层 OCR 确认首页/草稿列表出现）"


def LAUNCH(mode: str = "search", icon_center: tuple = (48, 650), max_wait_s: int = 45) -> str:
    """统一启动入口：mode=search 任务栏搜索（首选）/ mode=icon 桌面图标（备选）。"""
    if mode == "icon":
        return ICON_LAUNCH(icon_center=icon_center, max_wait_s=max_wait_s)
    return SEARCH_LAUNCH(max_wait_s=max_wait_s)


if __name__ == "__main__":
    print(LAUNCH())
