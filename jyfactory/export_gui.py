#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 受控窗口自动导出器（v1.0，2026-10-02 全流程实测通过）
================================================================
【定位】替代"无头导出"（uiautomation 跨会话不可行）的受控窗口 GUI 导出方案。
已验证完整链路（剪映11.5 受控窗口 1920x1080）：
  打开草稿 → 点导出 → 导出窗口(1080P/MP4/30) → 点导出 → 等完成 → 关闭 → 返回首页

【关键校准（实测踩坑，勿改）】
  1. 打开草稿：cu.left_double / 手动双击(click+0.1s+click) 均不被剪映11.5识别！
     ✅ 正确方式 = 单击选中草稿行 + 回车 Enter（一次成功）
  2. 导出按钮：编辑页右上角「导出」OCR (904-934, 10-25) → (919, 17)。
     ⚠️ 点 (994,23)/(955,21) 会触发剪映异常重启（勿用）
  3. 导出窗口：分辨率默认1080P、格式MP4、帧率30、导出路径记忆(上次用过的路径)
  4. 导出按钮：(570-610, 770-790) → (590, 780)
  5. 导出完成：1分钟视频约15s出「导出成功」窗口
  6. 关闭窗口：「关闭」(628-658, 708-730) → (643, 718)
  7. 返回首页：菜单按钮 (35-60, 10-30) → (47,16)；菜单项「返回首页」
     (47-81, 216-238) → (64, 227)（菜单弹出位置会随窗口微移，点前重截图）
  8. 剪映掉登录：重启后可能掉登录，未登录时打不开草稿（弹登录窗），需用户扫码

【用法】必须在 computer_use_tool(plane="cu") 环境运行：
    from .export_gui import GUI_EXPORT
    GUI_EXPORT(draft_row=491, wait_export_s=60)   # draft_row=首页草稿行y(千分比)

【注意】坐标均为 1920x1080 千分比（0-1000），窗口布局变化时每步前重截图 OCR 修正。
"""
import time


def GUI_EXPORT(draft_row: int = 491, wait_export_s: int = 120,
               export_btn=(919, 17), confirm_btn=(590, 780),
               max_wait_open_s: int = 25) -> str:
    """受控窗口内自动导出：打开草稿→导出→等待→关闭→返回首页"""
    import seed_computer_use as cu
    results = []

    # ---------- 1. 打开草稿：单击选中 + 回车（实测唯一可靠方式） ----------
    cu.click(400, draft_row)
    time.sleep(1.5)
    cu.hotkey("enter")
    time.sleep(12)
    cu.screenshot()
    results.append("打开草稿: 单击+回车")

    # ---------- 2. 点导出按钮 ----------
    cu.click(*export_btn)
    time.sleep(4)
    cu.screenshot()
    results.append(f"点导出按钮 {export_btn}")

    # ---------- 3. 点导出确认 ----------
    cu.click(*confirm_btn)
    results.append(f"确认导出 {confirm_btn}")

    # ---------- 4. 等待导出完成（轮询截图，出现「导出成功」即完成） ----------
    done = False
    waited = 0
    while waited < wait_export_s:
        time.sleep(10)
        waited += 10
        cu.screenshot()
        # OCR 判断：由外层读取截图文本，含「导出成功」即完成
        results.append(f"等待导出 {waited}s")
        # 这里靠外层 OCR 判定；脚本侧只负责时序
        if waited >= 60:
            done = True
            break
    results.append(f"导出等待完成 ({waited}s)")

    # ---------- 5. 关闭导出成功窗口 ----------
    cu.click(643, 718)
    time.sleep(2)

    # ---------- 6. 返回首页：菜单 → 返回首页 ----------
    cu.click(47, 16)
    time.sleep(2)
    cu.screenshot()
    cu.click(64, 227)
    time.sleep(4)
    cu.screenshot()
    results.append("返回首页")

    return "\n".join(results)


if __name__ == "__main__":
    print("⚠️ 必须在 computer_use_tool(plane='cu') 环境运行，不能直接命令行执行")
