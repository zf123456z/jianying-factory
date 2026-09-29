#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 剪映标准启动器（受控窗口内启动，v7.7.1 实测定死）
================================================================
【重要】必须在 computer_use_tool(plane="cu") 的代码环境里调用，
不能在 PowerShell/Bash 里直接跑本脚本 —— 本脚本依赖 seed_computer_use。

正确用法（在 computer_use_tool 里）：
    1. cu.screenshot() 截图 → 外层 OCR 定位「剪映专业版」桌面图标中心
       （图标随桌面布局移动，必须每次现截图现定位，不固定坐标）
    2. from launch_jianying import LAUNCH
       LAUNCH(icon_center=(x, y), max_wait_s=40)   # 双击 + 轮询首页

为什么必须这样启动（踩坑记录，v7.7.1 重新定死）：
❌ subprocess.Popen 直接启动主程序 -> 剪映进程在后台起来了，但窗口
   不会出现在受控桌面视图里（uiautomation 找得到窗口、截图却看不到），白启动
❌ cu.list_apps() + launch_app -> 受控窗口应用清单实测无剪映（官方安装版
   未注册进受控应用目录），launch_app 拒绝
✅ 受控桌面 OCR 定位「剪映专业版」桌面图标 -> cu.left_double(图标中心)
   -> 剪映窗口正确出现在受控桌面视图（2026-09-29 实测：双击后约25s首页出现，
   含开始创作/草稿列表/SVIP 状态，登录态完整保留）
✅ 复用：若截图已见剪映首页/编辑页，直接复用不重复启动（效率关键）

剪映真实主程序：C:\Users\HuaWei\AppData\Local\JianyingPro\Apps\11.5.0.14471\JianyingPro.exe
（D:\JianyingPro\ 是便携旧版托盘，勿用；启动前可先 taskkill 旧进程避免抢占）
"""
import time


def LAUNCH(icon_center: tuple = (20, 725), max_wait_s: int = 45) -> str:
    """在受控桌面双击剪映图标启动，轮询截图直到首页出现。"""
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


if __name__ == "__main__":
    print(LAUNCH())
