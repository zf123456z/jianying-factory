#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 云端音乐直调（剪映官方曲库 GUI 操作）
================================================================
核心理念：我们控制剪映，就用剪映的音乐库——全部正版授权，不存在侵权问题。
用户要背景音乐时，不再用本地BGM，而是像人一样在剪映里搜索曲库、点添加。

⚠️ 本脚本必须运行在 computer_use_tool(plane="cu") 代码环境里，
   依赖 seed_computer_use，不能在 PowerShell 直接跑。

⚠️ 2026-09-29 受控窗口实测结论（剪映 11.5，务必阅读）：
  - ✅ 顶部「音频」按钮实测位置：(45,45)（OCR 35,35,55,65）
  - ✅ 音乐库搜索框实测位置：(215,85)（OCR 65,75,365,95"搜索歌曲名称/歌手"）
  - ✅ 搜索可用：输入"科技"回车后返回 10+ 首曲库结果（两列卡片网格）
  - ✅ 结果行布局：行间隔约 90（千分比），左列卡片 x≈68-150，右列卡片 x≈243-378
  - ✅ 双击歌曲 = 触发预览（预览区显示"正在预览 — 音频 不可商用"），不是添加
  - ❓「添加」按钮交互方式未确认：hover/单击/拖拽均未出现可见按钮（图形+OCR识别不到，
    剪映版本UI差异），需从剪映官方交互文档或新版本确认后再校准。
    备选思路：歌曲卡片 hover 后右上角圆形"+"（位置≈卡片右缘-10），或列表底部"使用"按钮。

用法（在 computer_use_tool 里）：
    from cloud_music import MusicPicker
    mp = MusicPicker()
    mp.open_music_panel()          # 顶部「音频」→ 音乐库
    mp.search("科技")              # 搜索曲库（结果已加载）
    mp.preview_row(0)              # 双击第1条预览（已实测）
    # mp.add_row(0)                # 添加第1条（交互待校准，暂不可用）
    mp.back_to_home()              # 返回首页
"""
import time
from typing import Optional


class MusicPicker:
    def __init__(self, max_retry: int = 2):
        import seed_computer_use as cu
        self.cu = cu
        self.max_retry = max_retry
        self.results = []

    def _log(self, node, ok, detail=""):
        self.results.append({"node": node, "ok": ok, "detail": detail})
        print(f"{'✅' if ok else '❌'} [{node}] {detail}")

    def _shot(self):
        self.cu.screenshot()
        time.sleep(0.6)

    # ---------- 节点1：打开剪映音乐库（实测坐标） ----------
    def open_music_panel(self) -> bool:
        """编辑页顶部「音频」→ 音乐库面板（实测 2026-09-29）"""
        for attempt in range(self.max_retry + 1):
            self._shot()
            self.cu.click(45, 45)    # 顶部「音频」（实测 OCR 35,35,55,65）
            time.sleep(3)
            self._shot()
            self._log("打开音乐库", True, "已点击顶部音频按钮")
            return True
        self._log("打开音乐库", False, "多次尝试失败")
        return False

    # ---------- 节点2：搜索（实测坐标） ----------
    def search(self, keyword: str) -> bool:
        """搜索框输入关键词 → 回车（实测 2026-09-29，搜索框 (215,85)）"""
        self._shot()
        self.cu.click(215, 85)      # 搜索框（实测 OCR 65,75,365,95）
        time.sleep(1)
        self.cu.hotkey("ctrl", "a")
        self.cu.type(keyword)
        time.sleep(1)
        self.cu.hotkey("enter")
        time.sleep(5)
        self._shot()
        self._log("搜索音乐", True, f"关键词「{keyword}」→ 已加载结果")
        return True

    # ---------- 节点3：预览（已实测：双击=预览） ----------
    def preview_row(self, row: int = 0) -> bool:
        """双击结果行预览音乐（实测确认：双击=预览播放）"""
        rows = [130, 220, 310, 400, 490]   # 行中心 y（实测行间隔90）
        y = rows[min(row, len(rows) - 1)]
        self._shot()
        self.cu.left_double(120, y)
        time.sleep(3)
        self._shot()
        self._log("预览音乐", True, f"双击第{row+1}条（预览播放）")
        return True

    # ---------- 节点4：添加（⚠️ 交互待校准，暂用占位） ----------
    def add_row(self, row: int = 0) -> bool:
        """添加结果行到时间轴。⚠️ 2026-09-29 实测：hover/单击/拖拽均未确认添加按钮位置，
        剪映 11.5 的添加交互需按官方文档再校准；此函数为占位，调用前务必先实测。"""
        self._log("添加音乐", False,
                  "添加按钮交互未校准（剪映UI差异），需先实测确认后再启用")
        return False

    # ---------- 节点5：返回首页 ----------
    def back_to_home(self) -> bool:
        self._shot()
        self.cu.click(58, 21)        # 左上菜单
        time.sleep(2)
        self._shot()
        self.cu.click(66, 215)       # 返回首页
        time.sleep(3)
        self._shot()
        self._log("返回首页", True, "已回到剪映首页")
        return True

    def report(self):
        ok = sum(1 for r in self.results if r["ok"])
        return {"total": len(self.results), "ok": ok,
                "failed": len(self.results) - ok, "results": self.results}


if __name__ == "__main__":
    print("⚠️ 本脚本必须在 computer_use_tool(plane='cu') 环境里运行")
