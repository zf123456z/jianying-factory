#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 模板管理器 TemplateManager v1.0（2026-10-08 接入上游模板模式思想）
================================================================================
模板出片核心：把我们的成品**明文草稿**当模板 → 一键克隆 → JSON 级替换文案/素材/配音。
与上游 pyJianYingDraft template_mode 的差异：上游换文本/素材用对象 API（对 VectCutAPI
草稿的关键帧属性名不兼容），我们直接做 JSON 级替换——对 VectCutAPI 明文草稿 100% 兼容，
**完整保留原模板的样式/动画/花字/特效/转场/关键帧字段**，只改内容。

⚠️ 前置条件：模板必须是**明文** draft_content.json（剪映转换过的加密草稿不能用）。
用 list_templates() 只列出可用明文模板。

用法（在任意 Python 环境，不需要 GUI）：
    tm = TemplateManager()
    tm.list_templates()                                  # 列出可用模板
    tm.make_from_template(
        template="GEO口播_最终版v3",
        new_name="新草稿名",
        new_texts={0: "第一句新字幕", 1: "第二句新字幕"},  # 按字幕索引替换（保留样式）
        new_video=config.DEFAULT_VIDEO,         # 换全部视频素材
        new_voice=None,                                   # 换人声配音（wav/mp3）
    )
"""
import os
from . import config
import sys
import json
import shutil
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
try:
    from ._engine_v2_legacy import DRAFT_ROOT, _write_meta_info, safe_draft_dir
except Exception as e:
    DRAFT_ROOT = config.DRAFT_DIR
    def _write_meta_info(draft_dir, duration_us):
        print(f"⚠️ engine_v2 不可用，跳过 meta 回写: {e}")
    def safe_draft_dir(name):
        return os.path.join(DRAFT_ROOT, name)

try:
    from .self_contain import self_contain_draft
except Exception:
    def self_contain_draft(d):
        print("⚠️ self_contain 不可用，跳过素材自包含")


def ff_duration(path: str) -> float:
    """ffprobe 素材时长（秒）"""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", path], capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip() or 0)
    except Exception:
        return 0.0


class TemplateManager:
    SKELETON_SRC = os.path.join(config.DRAFT_DIR, "GEO口播测试_v78")
    SKELETON_FILES = [
        "Resources/.gitkeep",
        "Timelines/project.json",
        "Timelines/project.json.bak",
        "Timelines/91E08AC5-22FB-47e2-9AA0-7DC300FAEA2B/attachment_editing.json",
        "Timelines/91E08AC5-22FB-47e2-9AA0-7DC300FAEA2B/attachment_pc_common.json",
        "Timelines/91E08AC5-22FB-47e2-9AA0-7DC300FAEA2B/common_attachment/attachment_pc_timeline.json",
        "Timelines/91E08AC5-22FB-47e2-9AA0-7DC300FAEA2B/common_attachment/attachment_script_video.json",
        "adjust_mask/.gitkeep",
        "attachment_pc_common.json",
        "common_attachment/attachment_pc_timeline.json",
        "draft_agency_config.json",
        "draft_biz_config.json",
        "draft_settings",
        "draft_virtual_store.json",
        "key_value.json",
        "matting/.gitkeep",
        "performance_opt_info.json",
        "qr_upload/.gitkeep",
        "smart_crop/.gitkeep",
        "subdraft/.gitkeep",
        "timeline_layout.json",
    ]

    def __init__(self, draft_root: str = DRAFT_ROOT):
        self.root = draft_root
        if not os.path.isdir(self.root):
            raise FileNotFoundError(f"草稿根目录不存在: {self.root}")

    def _draft_path(self, name: str) -> str:
        p = os.path.abspath(os.path.join(self.root, name))
        if not p.startswith(os.path.abspath(self.root) + os.sep):
            raise ValueError(f"非法草稿名: {name}")
        return p

    def _content_file(self, draft_dir: str):
        cand = [os.path.join(draft_dir, "draft_content.json")]
        tl = os.path.join(draft_dir, "Timelines")
        if os.path.isdir(tl):
            for sub in os.listdir(tl):
                cand.append(os.path.join(tl, sub, "draft_content.json"))
        for f in cand:
            if os.path.isfile(f) and self._is_plain(f):
                return f
        return None

    @staticmethod
    def _is_plain(f: str) -> bool:
        try:
            with open(f, "rb") as fh:
                head = fh.read(4)
            return head[:1] in (b"{", b"[")
        except Exception:
            return False

    def list_templates(self) -> list:
        ok, bad = [], []
        for name in sorted(os.listdir(self.root)):
            d = os.path.join(self.root, name)
            if not os.path.isdir(d):
                continue
            if self._content_file(d):
                ok.append(name)
            else:
                bad.append(name)
        print(f"✅ 可用模板（明文）{len(ok)} 个 | 加密不可用 {len(bad)} 个（被剪映转换过）")
        for n in ok:
            print("   ·", n)
        return ok

    def clone(self, template_name: str, new_name: str) -> str:
        src = self._draft_path(template_name)
        if not os.path.isdir(src):
            raise FileNotFoundError(f"模板草稿不存在: {template_name}")
        if not self._content_file(src):
            raise ValueError(f"模板已加密（被剪映转换过），无法 JSON 替换: {template_name}")
        dst = safe_draft_dir(new_name)
        if os.path.exists(dst):
            bak = os.path.join(os.path.dirname(dst), f"{new_name}_备份_{int(__import__('time').time())}")
            print(f"⚠️ 目标草稿已存在，先备份旧草稿 → {bak}")
            shutil.move(dst, bak)
        shutil.copytree(src, dst)
        lock = os.path.join(dst, ".locked")
        if os.path.exists(lock):
            os.remove(lock)
        self._ensure_skeleton(dst)
        print(f"✅ 克隆模板成功: {template_name} → {new_name}")
        return dst

    def _ensure_skeleton(self, draft_dir: str) -> None:
        if not os.path.isdir(self.SKELETON_SRC):
            print("⚠️ 骨架源不存在，跳过骨架补全")
            return
        added = 0
        for rel in self.SKELETON_FILES:
            s = os.path.join(self.SKELETON_SRC, rel)
            d = os.path.join(draft_dir, rel)
            if not os.path.exists(s) or os.path.exists(d):
                continue
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            added += 1
        for junk in (".locked", "draft_content.json.bak", "template-2.tmp"):
            jp = os.path.join(draft_dir, junk)
            if os.path.exists(jp) and os.path.isfile(jp):
                try:
                    os.remove(jp)
                except OSError:
                    pass
        tl_dc = os.path.join(draft_dir, "Timelines", "91E08AC5-22FB-47e2-9AA0-7DC300FAEA2B", "draft_content.json")
        top_dc = os.path.join(draft_dir, "draft_content.json")
        if os.path.isdir(os.path.dirname(tl_dc)) and os.path.exists(top_dc):
            shutil.copy2(top_dc, tl_dc)
        if added:
            print(f"✅ 骨架补全 {added} 个文件（剪映列表可见性）")

    def _load(self, draft_dir: str):
        f = self._content_file(draft_dir)
        if not f:
            raise ValueError(f"草稿无明文内容文件: {draft_dir}")
        with open(f, encoding="utf-8") as fh:
            return json.load(fh), f

    def _save(self, j: dict, f: str):
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(j, fh, ensure_ascii=False, indent=2)

    def replace_texts(self, draft_dir: str, text_map: dict) -> int:
        j, f = self._load(draft_dir)
        texts = j.get("materials", {}).get("texts")
        if not isinstance(texts, list):
            print("⚠️ 草稿无 texts 列表，跳过文本替换")
            return 0
        changed = 0
        for key, new_text in text_map.items():
            t = None
            if isinstance(key, int) and 0 <= key < len(texts):
                t = texts[key]
            elif isinstance(key, str):
                t = next((x for x in texts if x.get("id") == key), None)
            if t is None:
                print(f"  ⚠️ 找不到文本 {key}，跳过")
                continue
            content = t.get("content", "")
            try:
                c = json.loads(content) if isinstance(content, str) else content
            except Exception:
                print(f"  ⚠️ 文本 {key} content 解析失败，跳过")
                continue
            c["text"] = new_text
            t["content"] = json.dumps(c, ensure_ascii=False)
            changed += 1
        if changed:
            self._save(j, f)
        print(f"✅ 替换文本 {changed} 段（保留样式/动画/花字）")
        return changed

    def replace_videos(self, draft_dir: str, new_path: str, indices: list = None) -> int:
        if not os.path.isfile(new_path):
            raise FileNotFoundError(f"新视频素材不存在: {new_path}")
        dur_us = int(ff_duration(new_path) * 1e6)
        j, f = self._load(draft_dir)
        videos = j.get("materials", {}).get("videos")
        if not isinstance(videos, list):
            print("⚠️ 草稿无 videos 列表，跳过视频替换")
            return 0
        targets = range(len(videos)) if indices is None else [i for i in indices if 0 <= i < len(videos)]
        changed = 0
        for i in targets:
            v = videos[i]
            v["path"] = new_path
            v["material_name"] = os.path.basename(new_path)
            v["duration"] = dur_us
            v["media_path"] = new_path
            changed += 1
        if changed:
            self._save(j, f)
        print(f"✅ 替换视频素材 {changed} 段 → {os.path.basename(new_path)}（时长 {dur_us/1e6:.1f}s）")
        return changed

    def replace_audios(self, draft_dir: str, new_path: str, name_contains: str = None) -> int:
        if not os.path.isfile(new_path):
            raise FileNotFoundError(f"新音频素材不存在: {new_path}")
        dur_us = int(ff_duration(new_path) * 1e6)
        j, f = self._load(draft_dir)
        audios = j.get("materials", {}).get("audios")
        if not isinstance(audios, list):
            print("⚠️ 草稿无 audios 列表，跳过音频替换")
            return 0
        changed = 0
        for a in audios:
            if name_contains:
                nm = (a.get("name") or "") + (a.get("material_name") or "") + (a.get("path") or "")
                if name_contains not in nm:
                    continue
            a["path"] = new_path
            a["material_name"] = os.path.basename(new_path)
            a["name"] = os.path.basename(new_path)
            a["duration"] = dur_us
            a["media_path"] = new_path
            changed += 1
        if changed:
            self._save(j, f)
        print(f"✅ 替换音频 {changed} 段 → {os.path.basename(new_path)}（{dur_us/1e6:.1f}s）")
        return changed

    def save(self, draft_dir: str, project_name: str = None) -> str:
        j, f = self._load(draft_dir)
        total_us = int(j.get("duration", 0))
        _write_meta_info(draft_dir, total_us)
        try:
            self_contain_draft(draft_dir)
        except Exception as e:
            print(f"⚠️ 素材自包含跳过: {e}")
        print(f"✅ 模板草稿收尾完成: {os.path.basename(draft_dir)}（{total_us/1e6:.1f}s）")
        return draft_dir

    def make_from_template(self, template: str, new_name: str,
                           new_texts: dict = None, new_video: str = None,
                           new_voice: str = None, voice_name_contains: str = "配音") -> str:
        print(f"\n===== 模板出片：{template} → {new_name} =====")
        draft_dir = self.clone(template, new_name)
        if new_texts:
            self.replace_texts(draft_dir, new_texts)
        if new_video:
            self.replace_videos(draft_dir, new_video)
        if new_voice:
            self.replace_audios(draft_dir, new_voice, name_contains=voice_name_contains)
        self.save(draft_dir, new_name)
        return draft_dir


if __name__ == "__main__":
    tm = TemplateManager()
    tm.list_templates()
