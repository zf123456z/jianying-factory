#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 受控窗口确定性执行器（v1.0）
================================================================
替代"截图→人眼找坐标→点击"的现场发挥，把 SOP 固化为确定性流程：
每个节点 = 截图 → OCR 定位目标文本/区域 → 点击 → 验证结果 → 进入下一节点。
剪映常驻复用：一次启动，多任务连续处理，避免反复冷启动（效率提升关键）。

⚠️ 本脚本必须运行在 computer_use_tool(plane="cu") 代码环境里，
   不能在 PowerShell/Bash 直接跑（依赖 seed_computer_use）。

用法（在 computer_use_tool 里）：
    from operator_executor import JianyingOperator
    op = JianyingOperator()
    op.ensure_launched()          # 剪映已开则复用，未开则启动
    op.open_draft("统一入口验证_全自动")   # 打开草稿
    op.apply_voice_clone("张总专属")       # 换音色
    op.recognize_subtitle()                # 官方识别字幕
    op.tech_pack()                         # 科技风智能包装
    op.back_to_home()                      # 返回首页
    print(op.report())                     # 打印各节点结果
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

    def _log(self, node: str, ok: bool, detail: str = ""):
        self.results.append({"node": node, "ok": ok, "detail": detail})
        mark = "✅" if ok else "❌"
        print(f"{mark} [{node}] {detail}")

    def _shot(self, desc: str = ""):
        self.cu.screenshot()
        time.sleep(0.5)
        return desc

    def _wait_for(self, cond, timeout_s: float, interval_s: float = 2.0, desc: str = ""):
        st = time.time()
        while time.time() - st < timeout_s:
            if cond():
                return True
            time.sleep(interval_s)
        return False

    # ---------- 节点0：启动/复用剪映 ----------
    def ensure_launched(self, max_wait_s: int = 45) -> bool:
        """剪映已开则复用（效率关键），未开则标准启动。"""
        self.cu.screenshot()
        if self._launched:
            return True
        apps = self.cu.list_apps()
        matches = [a for a in apps if ("剪映专业版" in a.name and "卸载" not in a.name)]
        if len(matches) != 1:
            self._log("启动剪映", False, f"匹配项异常: {[a.name for a in matches]}")
            return False
        name = matches[0].name
        result = self.cu.launch_app(name)
        print(f"🚀 启动/激活剪映: {name} → {result}")
        waited = 0
        while waited < max_wait_s:
            time.sleep(4)
            waited += 4
            self.cu.screenshot()
            print(f"⏳ 等待剪映就绪 {waited}s")
        self._launched = True
        self._log("启动剪映", True, f"剪映已就绪（等待{waited}s）")
        return True

    # ---------- 节点1：打开草稿（2026-09-27 实测校准） ----------
    def open_draft(self, draft_name: str) -> bool:
        """按名称打开草稿（完整列表视图双击行；搜索态/单行态双击不生效）。"""
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
        """应用剪映克隆音色：换音色→克隆音色→选音色→应用→确认。
        实测校准：换音色(777,46) → 克隆音色(769,132) → 张总专属(870,185) →
        应用(970,505 漂移区940-990,490-520) → 确认弹窗(525,520 漂移区490-530)。
        处理等待 60-90s（实测 55s 完成，扣 212 积分）。"""
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
        字幕(180,37) → 同时清空已有字幕(120,502) → 开始识别(347,500) → 等60s。"""
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
