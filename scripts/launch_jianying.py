#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 剪映标准启动器（受控窗口内启动，已实测跑通）
============================================================
【重要】必须在 computer_use_tool(plane="cu") 的代码环境里调用，
不能在 PowerShell/Bash 里直接跑本脚本 —— 因为本脚本依赖
seed_computer_use 的 list_apps / launch_app 能力。

正确用法：把下方 LAUNCH() 函数体复制进 computer_use_tool 的 code 参数执行。

为什么必须这样启动（踩坑记录）：
❌ subprocess.Popen 直接启动主程序 -> 剪映进程在后台起来了，但窗口
   不会出现在受控桌面视图里，uiautomation 也找不到主窗口，等于白启动
✅ cu.list_apps() 找到剪映精确名称 -> cu.launch_app(精确名称)
   -> 剪映窗口正确出现在受控桌面里，用户登录态完整保留

常见坑：
- launch_app 只接受 list_apps() 返回的精确 App.name（含 # 后缀唯一ID），
  名称大小写、缺后缀都会被拒绝
- 应用列表里会有「卸载剪映专业版」干扰项，必须过滤掉
- launch_app 返回 accepted_unverified 是正常的（请求已接受、窗口
  还未确认可见），继续轮询截图即可，不要重复 launch
"""
import time


def LAUNCH(max_wait_s: int = 60) -> str:
    """在受控桌面里启动剪映，返回最终状态说明。"""
    import seed_computer_use as cu

    apps = cu.list_apps()
    matches = [
        a for a in apps
        if ("剪映专业版" in a.name and "卸载" not in a.name)
    ]
    if len(matches) != 1:
        return f"ERROR: 剪映匹配项数量异常: {[a.name for a in matches]}"

    name = matches[0].name
    print(f"✅ 找到剪映: {name}")

    result = cu.launch_app(name)
    print(f"🚀 启动结果: {result}")

    waited = 0
    while waited < max_wait_s:
        time.sleep(4)
        waited += 4
        cu.screenshot()
        print(f"⏳ 等待剪映窗口: {waited}s")
    cu.screenshot()
    return "OK: 剪映已在受控桌面打开（已等待窗口出现）"


if __name__ == "__main__":
    print(LAUNCH())
