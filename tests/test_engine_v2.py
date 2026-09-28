#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 核心回归测试（engine_v2 草稿生成）
运行：python -m unittest tests.test_engine_v2 -v
"""
import os
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

TEST_ROOT = tempfile.mkdtemp(prefix="jy_test_engine_")
os.environ["JIANYING_DRAFT_ROOT"] = os.path.join(TEST_ROOT, "drafts")
os.environ["JIANYING_EXPORT_ROOT"] = os.path.join(TEST_ROOT, "export")
os.environ["JIANYING_BACKUP_ROOT"] = os.path.join(TEST_ROOT, "drafts_backup")
os.environ["JIANYING_DEFAULT_VIDEO"] = os.path.join(TEST_ROOT, "media", "test_video.mp4")
os.environ["JIANYING_BGM_VOLUME"] = "0.35"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_v2  # noqa: E402

MEDIA_DIR = os.path.join(TEST_ROOT, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.environ["JIANYING_DRAFT_ROOT"], exist_ok=True)


def _ffmpeg(args: list) -> bool:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args,
                          capture_output=True, text=True)
    return proc.returncode == 0


def _make_test_assets() -> dict:
    video = os.path.join(MEDIA_DIR, "test_video.mp4")
    voice = os.path.join(MEDIA_DIR, "test_voice.m4a")
    bgm = os.path.join(MEDIA_DIR, "test_bgm.m4a")
    assert _ffmpeg(["-f", "lavfi", "-i", "color=c=blue:s=320x640:d=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", video]), "生成测试视频失败"
    assert _ffmpeg(["-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-c:a", "aac", voice]), "生成人声失败"
    assert _ffmpeg(["-f", "lavfi", "-i", "sine=frequency=220:duration=1", "-c:a", "aac", bgm]), "生成BGM失败"
    return {"video": video, "voice": voice, "bgm": bgm}


class TestEngineV2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assets = _make_test_assets()
        cls.draft_name = "回归测试_草稿A"
        cls.draft_dir = engine_v2.make_voiceover_draft(
            name=cls.draft_name,
            script_text="这是一条用于回归测试的口播文案，验证引擎稳妥性设计。",
            video_path=cls.assets["video"],
            voiceover_path=cls.assets["voice"],
            bgm_path=cls.assets["bgm"],
            total_duration_s=2.0,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def test_01_draft_exists(self):
        self.assertTrue(os.path.isdir(self.draft_dir))
        self.assertTrue(os.path.isfile(os.path.join(self.draft_dir, "draft_content.json")))

    def test_02_json_parseable(self):
        with open(os.path.join(self.draft_dir, "draft_content.json"), "r", encoding="utf-8-sig") as f:
            draft = json.load(f)
        self.assertIn("tracks", draft)

    def test_03_three_tracks(self):
        with open(os.path.join(self.draft_dir, "draft_content.json"), "r", encoding="utf-8-sig") as f:
            draft = json.load(f)
        names = [t.get("name", "") for t in draft.get("tracks", [])]
        self.assertIn("MainVideo", names)
        self.assertIn("Voice", names)
        self.assertIn("BGM", names)

    def test_04_video_muted(self):
        with open(os.path.join(self.draft_dir, "draft_content.json"), "r", encoding="utf-8-sig") as f:
            draft = json.load(f)
        for track in draft.get("tracks", []):
            if track.get("name") == "MainVideo":
                for seg in track.get("segments", []):
                    self.assertEqual(seg.get("volume", 0.0), 0.0, msg="视频段未强制静音")

    def test_05_bgm_fills_duration(self):
        with open(os.path.join(self.draft_dir, "draft_content.json"), "r", encoding="utf-8-sig") as f:
            draft = json.load(f)
        total_us = draft.get("duration", 0)
        bgm_end = 0
        for track in draft.get("tracks", []):
            if track.get("name") == "BGM":
                for seg in track.get("segments", []):
                    tr = seg.get("target_timerange", {})
                    bgm_end = max(bgm_end, tr.get("start", 0) + tr.get("duration", 0))
        self.assertGreaterEqual(bgm_end, total_us - 1000, msg=f"BGM 未铺满（{bgm_end/1e6:.2f}s < {total_us/1e6:.2f}s）")

    def test_06_local_material_id_nonempty(self):
        with open(os.path.join(self.draft_dir, "draft_content.json"), "r", encoding="utf-8-sig") as f:
            draft = json.load(f)
        mats = draft.get("materials", {})
        count = 0
        for key in ("videos", "audios"):
            items = mats.get(key, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and item.get("id"):
                    count += 1
                    self.assertTrue(item.get("local_material_id"),
                                    msg=f"素材 {item.get('id')} 的 local_material_id 为空（{key}）")
        self.assertGreater(count, 0, msg="未找到任何真实素材条目")

    def test_07_materials_self_contained(self):
        materials_dir = os.path.join(self.draft_dir, "materials")
        self.assertTrue(os.path.isdir(materials_dir))
        files = [f for f in os.listdir(materials_dir) if os.path.isfile(os.path.join(materials_dir, f))]
        self.assertGreater(len(files), 0, msg="materials/ 内没有素材文件")

    def test_08_same_name_backup(self):
        backup_root = engine_v2.BACKUP_ROOT
        engine_v2.make_voiceover_draft(
            name=self.draft_name,
            video_path=self.assets["video"],
            voiceover_path=self.assets["voice"],
            bgm_path=self.assets["bgm"],
            total_duration_s=2.0,
        )
        backups = [d for d in os.listdir(backup_root) if self.draft_name in d] if os.path.isdir(backup_root) else []
        self.assertGreater(len(backups), 0, msg="同名草稿未触发备份")

    def test_09_vertical_normalize_direction(self):
        src = os.path.join(MEDIA_DIR, "src_vertical_322.mp4")
        assert _ffmpeg(["-f", "lavfi", "-i", "color=c=blue:s=322x640:d=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", src]), "生成不达标竖屏素材失败"
        draft_dir = os.path.join(os.environ["JIANYING_DRAFT_ROOT"], "v_竖屏方向草稿")
        os.makedirs(os.path.join(draft_dir, "materials"), exist_ok=True)
        out = engine_v2.normalize_video_for_jianying(src, draft_dir)
        self.assertNotEqual(os.path.basename(out), os.path.basename(src), msg="不达标素材应触发转码")
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,codec_name,pix_fmt",
             "-of", "json", out], capture_output=True, text=True)
        info = json.loads(proc.stdout)["streams"][0]
        self.assertEqual((int(info["width"]), int(info["height"])), (1080, 1920),
                         msg=f"竖屏方向错误: {info['width']}x{info['height']}")
        self.assertEqual(info["pix_fmt"], "yuv420p")


if __name__ == "__main__":
    unittest.main(verbosity=2)
