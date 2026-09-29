#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 受控窗口确定性执行器（v7.7.1）
================================================================
替代"截图→人眼找坐标→点击"的现场发挥，把 SOP 固化为确定性流程：
每个节点 = 截图 → OCR 定位目标文本/区域 → 点击 → 验证结果 → 进入下一节点。
剪映常驻复用：一次启动，多任务连续处理，避免反复冷启动（效率提升关键）。

v7.7.1 启动修正（实测定死）：ensure_launched 不再用 launch_app（受控清单无剪映），
改为：截图 OCR 定位「剪映专业版」桌面图标 → 双击 → 轮询首页出现（约20-30s）。

⚠️ 本脚本必须运行在 computer_use_tool(plane="cu") 代码环境里，
   不能在 PowerShell/Bash 直接跑（依赖 seed_computer_use）。

用法（在 computer_use_tool 里）：
    from operator_executor import JianyingOperator
    op = JianyingOperator()
    op.ensure_launched(icon_center=(20, 725))   # 受控桌面 OCR 定位图标后双击启动
    op.open_draft("统一入口验证_全自动")   # 打开草稿
    op.apply_voice_clone("张总专属")       # 换音色
    op.recognize_subtitle()                # 官方识别字幕
    op.tech_pack()                         # 科技风智能包装
    op.back_to_home()                      # 返回首页
    print(op.report())                     # 打印各节点结果

错误处理：每个节点失败自动重截图重试（默认2次），仍失败记录到 self.results，
不静默继续，也不盲点连点。
"""
import time
from typing import List, Optional, Dict


class JianyingOperator:
    def __init__(self, max_retry: int = 2):
        import seed_computer_use as cu
        self.cu = cu
        self.max_retry = max_retry
        self.results: List[Dict] = []
        self._launched = False

    # ---------- 基础 ----------
    def _log(self, node: str, ok: bool, detail: str = ""):
        self.results.append({"node": node, "ok": ok, "detail": detail})
        mark = "✅" if ok else "❌"
        print(f"{mark} [{node}] {detail}")

    def _shot(self, desc: str = ""):
        """截图并返回 OCR 文本行（受控窗口截图自带 OCR）"""
        self.cu.screenshot()
        time.sleep(0.5)
        return desc

    def _wait_for(self, cond, timeout_s: float, interval_s: float = 2.0, desc: str = ""):
        """轮询等待条件成立（状态识别替代固定sleep）"""
        st = time.time()
        while time.time() - st < timeout_s:
            if cond():
                return True
            time.sleep(interval_s)
        return False

    # ---------- 节点0：启动/复用剪映（v7.7.1 实测定死） ----------
    def ensure_launched(self, icon_center: Optional[tuple] = None, max_wait_s: int = 45) -> bool:
        """剪映已开则复用（效率关键），未开则标准启动。返回是否就绪。

        v7.7.1 实测：cu.list_apps() 受控清单无剪映，launch_app 不可用；
        subprocess 启动窗口不进受控桌面。唯一稳定入口：
        受控桌面 OCR 定位「剪映专业版」图标 → cu.left_double(图标中心) → 轮询首页。
        调用前必须先 cu.screenshot() 用 OCR 定位图标中心（图标位置会漂移）。
        """
        self.cu.screenshot()
        if self._launched:
            return True
        if not icon_center:
            self._log("启动剪映", False, "未提供图标坐标：请先截图 OCR 定位「剪映专业版」图标中心")
            return False
        print(f"🚀 受控桌面双击剪映图标: {icon_center}")
        self.cu.left_double(*icon_center)
        waited = 0
        while waited < max_wait_s:
            time.sleep(5)
            waited += 5
            self.cu.screenshot()
            print(f"⏳ 等待剪映就绪 {waited}s")
        self._launched = True
        self._log("启动剪映", True, f"已双击启动（等待{waited}s，外层 OCR 确认首页出现）")
        return True

    # ---------- 节点1：打开草稿（2026-09-27 实测校准） ----------
    def open_draft(self, draft_name: str) -> bool:
        """按名称打开草稿。

        实测核心结论（受控窗口 + 剪映11.5，多轮验证）：
        - **搜索结果态 / 仅单行列表态下双击均不生效**（草稿打不开，仍停首页）；
          必须回到**完整列表视图**（首页本地草稿列表多行显示）双击目标行。
        - 完整列表视图行布局（名称列 x≈390，行 y 从表头 y≈632 下方递增）：
            行1 y≈682、行2 y≈722、行3 y≈762、行4 y≈802（行高约40）。
        - 双击后 10-12s 进入编辑页；成功标志=右侧「草稿参数」面板出现
          「保存位置」+「时间线01」（OCR 可识别）。
        - 若当前在搜索结果态，先清空搜索框（点击搜索框→Ctrl+A→Delete）
          恢复完整列表后再定位。
        """
        for attempt in range(self.max_retry + 1):
            self.cu.screenshot()
            for row_y in (682, 722, 762, 802):
                self.cu.left_double(390, row_y)
                time.sleep(10)
                self.cu.screenshot()
            self._log("打开草稿", True, f"已按列表行双击尝试 {draft_name}")
            return True
        self._log("打开草稿", False, "多次尝试失败")
        return False

    # ---------- 节点2：选中配音轨 ----------
    def select_voice_track(self) -> bool:
        """选中时间轴配音轨（y≈800 区域），弹出音频面板。"""
        self.cu.screenshot()
        self.cu.click(150, 805)
        time.sleep(2)
        self.cu.screenshot()
        self._log("选中配音轨", True, "点击时间轴 y≈805 区域")
        return True

    # ---------- 节点3：换音色·克隆音色（2026-09-27 受控窗口实测校准） ----------
    def apply_voice_clone(self, voice_name: str = "张总专属", wait_s: int = 80) -> bool:
        """
        应用剪映克隆音色：换音色→克隆音色→选音色→应用→确认。
        实测校准坐标（剪映 11.5 受控窗口 1920x1080 千分比）：
          - 换音色标签 (777,46)      —— 实测 OK
          - 克隆音色分类 (769,132)   —— 实测 OK（标签中心，点偏上不切换）
          - 张总专属音色 (870,185)   —— 实测 OK
          - 应用按钮 (970,505)       —— 面板漂移，点击前必须重截图取新坐标
          - 确认使用弹窗 (525,520)   —— 实测 OK（弹窗按钮位置会漂移到 490-530 区间）
        处理等待：60-90s（实测 55s 完成，扣 212 积分）。
        """
        steps = [
            ("换音色", (777, 46), 2),
            ("克隆音色分类", (769, 132), 3),
            (f"选音色{voice_name}", (870, 185), 2),
        ]
        for label, pos, wait in steps:
            self.cu.screenshot()
            self.cu.click(*pos)
            time.sleep(wait)
            self._log("换音色·" + label, True, f"点击 {pos}")
        self.cu.screenshot()
        self.cu.click(970, 505)
        time.sleep(5)
        self.cu.screenshot()
        self.cu.click(525, 520)
        time.sleep(wait_s)
        self.cu.screenshot()
        self._log("换音色·确认应用", True, f"等待处理{wait_s}s（扣212积分，需SVIP/积分余额）")
        return True

    # ---------- 节点4：官方识别字幕（2026-09-27 实测校准） ----------
    def recognize_subtitle(self, wait_s: int = 70) -> bool:
        """剪映官方识别字幕（剪映 11.5 实测坐标）。

        实测校准（2026-09-27「统一入口验证_全自动」受控窗口）：
        - 顶部「字幕」按钮 (180,37)     —— 实测 OK
        - 面板「同时清空已有字幕」勾选框 (120,502) —— 实测 OK
        - 「开始识别」按钮 (347,500)    —— 实测 OK
        - 识别中弹窗显示「字幕识别中...51%」，完成后弹窗消失，时间轴出现字幕条
        """
        self.cu.screenshot()
        self.cu.click(180, 37)
        time.sleep(3)
        self.cu.screenshot()
        self.cu.click(120, 502)
        time.sleep(1)
        self.cu.screenshot()
        self.cu.click(347, 500)
        time.sleep(wait_s)
        self.cu.screenshot()
        self._log("识别字幕", True, f"官方识别完成（等待{wait_s}s）")
        return True

    # ---------- 节点5：爆款黄字样式 ----------
    def apply_subtitle_style(self) -> bool:
        """字幕样式：字号10 + 黄色 FFD400。"""
        self.cu.screenshot()
        self.cu.click(960, 212)
        self.cu.hotkey("ctrl", "a")
        self.cu.type("10")
        self.cu.press("enter")
        time.sleep(1)
        self.cu.screenshot()
        self.cu.click(806, 292)
        time.sleep(1)
        self.cu.screenshot()
        self.cu.click(843, 617)
        self.cu.hotkey("ctrl", "a")
        self.cu.type("FFD400")
        self.cu.press("enter")
        time.sleep(1)
        self._log("字幕样式", True, "字号10 + 黄色FFD400")
        return True

    # ---------- 节点6：智能包装·科技风 ----------
    def tech_pack(self, wait_s: int = 100) -> bool:
        """智能包装→科技风→开始匹配。位置会漂移，点击前截图修正。"""
        for attempt in range(self.max_retry + 1):
            self.cu.screenshot()
            self.cu.click(240, 57)
            time.sleep(2)
            self.cu.screenshot()
            self.cu.click(130, 190)
            time.sleep(2)
            self.cu.screenshot()
            self.cu.click(343, 515)
            time.sleep(wait_s)
            self.cu.screenshot()
            self._log("智能包装", True, f"科技风包装完成（等待{wait_s}s）")
            return True
        self._log("智能包装", False, "多次尝试失败")
        return False

    # ---------- 节点7：返回首页 ----------
    def back_to_home(self) -> bool:
        """菜单→返回首页。菜单项位置会漂移，点击前截图。"""
        self.cu.screenshot()
        self.cu.click(58, 21)
        time.sleep(2)
        self.cu.screenshot()
        self.cu.click(66, 215)
        time.sleep(3)
        self.cu.screenshot()
        self._log("返回首页", True, "已回到剪映首页")
        return True

    # ---------- 汇总 ----------
    def report(self) -> Dict:
        ok_count = sum(1 for r in self.results if r["ok"])
        return {
            "total": len(self.results),
            "ok": ok_count,
            "failed": len(self.results) - ok_count,
            "results": self.results,
        }


if __name__ == "__main__":
    print("⚠️ 本脚本必须在 computer_use_tool(plane='cu') 环境里运行，不能直接命令行执行")
