#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 核心回归测试（export_precheck 导出预检）
覆盖预检三态：明文草稿 / 加密草稿降级 / 草稿不存在。
运行：python -m unittest tests.test_export_precheck -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# export_precheck.py 位于技能 scripts/ 目录
_SKILL_SCRIPTS = os.path.join(
    os.environ.get("USERPROFILE", r"C:\Users\HuaWei"),
    "AppData", "Local", "Doubao", "User Data", "Default", ".doubao", "agent_mode",
    "workspace", ".user_skills", "jianying-factory", "scripts",
)
sys.path.insert(0, _SKILL_SCRIPTS)

import export_precheck  # noqa: E402

TEST_ROOT = tempfile.mkdtemp(prefix="jy_test_precheck_")


def _write_plain_draft(name: str, with_bgm_fill: bool = True) -> str:
    draft_dir = os.path.join(TEST_ROOT, name)
    os.makedirs(os.path.join(draft_dir, "materials"), exist_ok=True)
    for f in ("vid.mp4", "voc.m4a", "bgm.mp3"):
        with open(os.path.join(draft_dir, "materials", f), "wb") as fp:
            fp.write(b"\x00" * 16)
    total_us = 2_000_000
    tracks = [
        {"type": "video", "name": "MainVideo",
         "segments": [{"material_id": "m_video",
                        "target_timerange": {"start": 0, "duration": total_us}}]},
        {"type": "audio", "name": "Voice",
         "segments": [{"material_id": "m_voice",
                        "target_timerange": {"start": 0, "duration": total_us}}]},
    ]
    if with_bgm_fill:
        tracks.append({"type": "audio", "name": "BGM",
                        "segments": [{"material_id": "m_bgm",
                                       "target_timerange": {"start": 0, "duration": total_us}}]})
    draft = {
        "duration": total_us,
        "tracks": tracks,
        "materials": {
            "videos": [{"id": "m_video", "local_material_id": "lm_video",
                         "path": "jym://materials/vid.mp4", "duration": total_us}],
            "audios": [
                {"id": "m_voice", "local_material_id": "lm_voice",
                 "path": "jym://materials/voc.m4a", "duration": total_us},
                {"id": "m_bgm", "local_material_id": "lm_bgm",
                 "path": "jym://materials/bgm.mp3", "duration": total_us},
            ],
        },
    }
    with open(os.path.join(draft_dir, "draft_content.json"), "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False)
    return draft_dir


def _write_encrypted_draft(name: str) -> str:
    import base64
    draft_dir = os.path.join(TEST_ROOT, name)
    os.makedirs(draft_dir, exist_ok=True)
    cipher = base64.b64encode(bytes(range(256)) * 8).decode("ascii")
    with open(os.path.join(draft_dir, "draft_content.json"), "w", encoding="utf-8") as f:
        f.write(cipher)
    return draft_dir


class TestExportPrecheck(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def test_01_plain_draft_passes(self):
        _write_plain_draft("明文草稿A")
        export_precheck.DRAFT_ROOT = TEST_ROOT
        result = export_precheck.export_precheck("明文草稿A")
        self.assertTrue(result["ok"])
        self.assertNotIn("无法解析", " ".join(result["errors"]))

    def test_02_plain_draft_checks_bgm_fill(self):
        _write_plain_draft("明文缺BGM", with_bgm_fill=False)
        export_precheck.DRAFT_ROOT = TEST_ROOT
        result = export_precheck.export_precheck("明文缺BGM")
        self.assertNotEqual(result["code"], "fatal")

    def test_03_encrypted_draft_degrades_to_warning(self):
        _write_encrypted_draft("加密草稿B")
        export_precheck.DRAFT_ROOT = TEST_ROOT
        result = export_precheck.export_precheck("加密草稿B")
        self.assertTrue(result["ok"], msg=f"加密草稿不应 fatal: {result['errors']}")
        self.assertEqual(result["code"], "warning")
        self.assertTrue(any("加密" in w for w in result["warnings"]), msg="应提示草稿已加密")

    def test_04_missing_draft_fatal(self):
        export_precheck.DRAFT_ROOT = TEST_ROOT
        result = export_precheck.export_precheck("完全不存在的草稿XYZ")
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "fatal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
