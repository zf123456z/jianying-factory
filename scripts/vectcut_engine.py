#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 v7.8 - VectCutAPI 确定性执行内核
=========================================================
【定位】替代 GUI 逐帧操作，成为主执行路径（对齐上游 jianying-editor 已验证路线）
【已验证】2026-09-30：VectCutAPI(jianying_pro_10 profile) 生成的明文草稿，
          剪映专业版 11.5 秒级识别、正常打开（视频/字幕/时长全对）。

流程：create_draft → add_video(素材) → add_audio(配音/BGM) → add_subtitle(SRT)
     → add_text(标题) → add_effect(转场) → save_draft → 部署到剪映草稿目录

用法：
    from vectcut_engine import JianyingVectcutEngine
    eng = JianyingVectcutEngine()
    eng.ensure_server()                      # 确保本地 VectCutAPI 服务在跑
    draft_id = eng.create_draft(1080, 1920)  # 竖屏
    eng.add_video(draft_id, r"E:\素材.mp4", volume=0.1)
    eng.add_audio(draft_id, r"D:\配音.mp3", volume=1.0, track_name="audio_main")
    eng.add_audio(draft_id, r"D:\bgm.wav", volume=0.35, track_name="bgm")
    eng.add_subtitle(draft_id, r"D:\字幕.srt", font_size=9, font_color="#FFD400")
    eng.add_text(draft_id, "爆款标题", 0, 5, font_size=14)
    report = eng.save_and_deploy(draft_id, "项目名")
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

API = "http://127.0.0.1:9001"
VECTCUT_DIR = r"D:\AI工作区\代码\VectCutAPI"
DRAFT_ROOT = r"D:\AI工作区\剪映草稿"


def _post(route: str, payload: dict, timeout: int = 300):
    req = urllib.request.Request(
        f"{API}{route}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class JianyingVectcutEngine:
    """剪映工厂 v7.8 主执行内核（确定性、秒级、无 GUI 依赖）"""

    def __init__(self, draft_root: str = DRAFT_ROOT):
        self.draft_root = draft_root
        self.results = []

    def _log(self, node: str, ok: bool, detail: str = ""):
        self.results.append({"node": node, "ok": ok, "detail": detail})
        print(f"{'✅' if ok else '❌'} [{node}] {detail}")

    def ensure_server(self, wait_s: int = 20) -> bool:
        try:
            _post("/create_draft", {"width": 1080, "height": 1920}, timeout=8)
            self._log("VectCutAPI服务", True, "已运行")
            return True
        except Exception:
            pass
        if not os.path.exists(os.path.join(VECTCUT_DIR, "capcut_server.py")):
            self._log("VectCutAPI服务", False, f"未找到 {VECTCUT_DIR}")
            return False
        subprocess.Popen(
            [sys.executable, "capcut_server.py"],
            cwd=VECTCUT_DIR,
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + wait_s
        while time.time() < deadline:
            try:
                _post("/create_draft", {"width": 1080, "height": 1920}, timeout=8)
                self._log("VectCutAPI服务", True, f"已启动（{VECTCUT_DIR}）")
                return True
            except Exception:
                time.sleep(2)
        self._log("VectCutAPI服务", False, "启动失败")
        return False

    def create_draft(self, width: int = 1080, height: int = 1920) -> str:
        out = _post("/create_draft", {"width": width, "height": height}, timeout=60)
        draft_id = out["output"]["draft_id"]
        self._log("创建草稿", True, f"{draft_id} ({width}x{height})")
        return draft_id

    def add_video(self, draft_id: str, video_path: str,
                  volume: float = 1.0, speed: float = 1.0,
                  start: float = 0, end=None,
                  track_name: str = "main",
                  transition: str = None,
                  transform_y: float = 0, scale: float = 1.0) -> bool:
        out = _post("/add_video", {
            "draft_id": draft_id,
            "video_url": video_path,
            "start": start,
            "end": end,
            "volume": volume,
            "speed": speed,
            "track_name": track_name,
            "transition": transition,
            "transform_y": transform_y,
            "scale_x": scale,
            "scale_y": scale,
        }, timeout=180)
        ok = bool(out.get("success", False))
        self._log("添加视频", ok, os.path.basename(video_path))
        return ok

    def add_audio(self, draft_id: str, audio_path: str,
                  volume: float = 1.0, start: float = 0, end=None,
                  track_name: str = "audio_main") -> bool:
        out = _post("/add_audio", {
            "draft_id": draft_id,
            "audio_url": audio_path,
            "start": start,
            "end": end,
            "volume": volume,
            "track_name": track_name,
        }, timeout=180)
        ok = bool(out.get("success", False))
        self._log("添加音频", ok, f"{os.path.basename(audio_path)} vol={volume} track={track_name}")
        return ok

    def add_subtitle(self, draft_id: str, srt_path: str,
                     font_size: float = 9.0, font_color: str = "#FFD400",
                     background_alpha: float = 0.3, bold: bool = True) -> bool:
        out = _post("/add_subtitle", {
            "draft_id": draft_id,
            "srt": srt_path,
            "font_size": font_size,
            "font_color": font_color,
            "bold": bold,
            "background_alpha": background_alpha,
            "vertical": False,
        }, timeout=180)
        ok = bool(out.get("success", False))
        self._log("添加字幕", ok, f"{os.path.basename(srt_path)} {len(open(srt_path, encoding='utf-8').readlines())//4}条")
        return ok

    def add_text(self, draft_id: str, text: str,
                 start: float, end: float,
                 font_size: float = 12.0, font_color: str = "#FFD400",
                 transform_y: float = -0.85,
                 background_alpha: float = 0.3,
                 border_width: float = 0.6, border_color: str = "#000000") -> bool:
        out = _post("/add_text", {
            "draft_id": draft_id,
            "text": text,
            "start": start,
            "end": end,
            "font_size": font_size,
            "font_color": font_color,
            "transform_y": transform_y,
            "background_alpha": background_alpha,
            "border_width": border_width,
            "border_color": border_color,
        }, timeout=120)
        ok = bool(out.get("success", False))
        self._log("添加标题", ok, text)
        return ok

    def save_and_deploy(self, draft_id: str, project_name: str) -> str:
        out = _post("/save_draft", {
            "draft_id": draft_id,
            "project_name": project_name,
            "auto_deploy": False,
        }, timeout=600)
        local = ""
        if isinstance(out.get("output"), dict):
            local = out["output"].get("draft_url", "")
        if not local or not os.path.isdir(local):
            cand = os.path.join(VECTCUT_DIR, draft_id)
            if os.path.isdir(cand):
                local = cand
        if not local:
            self._log("保存草稿", False, "未找到草稿输出目录")
            return ""
        os.makedirs(self.draft_root, exist_ok=True)
        dest = os.path.join(self.draft_root, project_name)
        try:
            if os.path.exists(dest):
                shutil.rmtree(dest)
        except PermissionError:
            dest = os.path.join(self.draft_root, f"{project_name}_{int(time.time())}")
        shutil.copytree(local, dest)
        lock = os.path.join(dest, ".locked")
        if os.path.exists(lock):
            os.remove(lock)
        self._log("部署草稿", True, f"→ {dest}")
        return dest

    def report(self) -> dict:
        ok_count = sum(1 for r in self.results if r["ok"])
        return {"total": len(self.results), "ok": ok_count,
                "failed": len(self.results) - ok_count, "results": self.results}


if __name__ == "__main__":
    print("剪映工厂 v7.8 VectCutAPI 内核 - 请在其他脚本中调用（勿直接运行）")
