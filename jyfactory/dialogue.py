#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 多角色对话剪辑支持
支持两个人对话，不同角色不同声音、不同颜色字幕
"""
import json
import os
import uuid
from typing import List, Dict


def gen_id() -> str:
    return uuid.uuid4().hex


class DialogueBuilder:
    """多角色对话生成器"""

    def __init__(self):
        self.roles = {}
        self.lines = []

    def add_role(self, role_name: str, voice: str = "male", subtitle_color: list = None):
        self.roles[role_name] = {
            "voice": voice,
            "subtitle_color": subtitle_color or [1.0, 1.0, 1.0],
            "subtitle_track": None,
        }

    def add_line(self, role: str, text: str, duration: float = 3.0):
        self.lines.append({
            "role": role,
            "text": text,
            "duration": duration,
        })

    def build_tracks(self) -> List[Dict]:
        """构建对话轨道，每个角色一条字幕轨"""
        tracks = []
        for role_name, role_config in self.roles.items():
            role_lines = [l for l in self.lines if l["role"] == role_name]
            if not role_lines:
                continue

            segments = []
            current_time = 0
            for line in role_lines:
                line_start = 0
                for l in self.lines:
                    if l == line:
                        break
                    line_start += l["duration"] * 1_000_000

                text_mat = {
                    "id": gen_id(),
                    "content": json.dumps({"text": line["text"], "styles": [{"fill": {"content": {"solid": {"color": role_config["subtitle_color"]}}}, "range": [0, len(line["text"])]}]}, ensure_ascii=False),
                    "type": "text",
                }

                segments.append({
                    "id": gen_id(),
                    "material_id": text_mat["id"],
                    "target_timerange": {
                        "start": line_start,
                        "duration": int(line["duration"] * 1_000_000),
                    },
                    "clip": {"transform": {"x": 0.0, "y": -0.72}},
                })

            tracks.append({
                "attribute": 0,
                "flag": 0,
                "id": gen_id(),
                "is_default_name": False,
                "name": f"字幕-{role_name}",
                "segments": segments,
                "type": "text",
            })

        return tracks


if __name__ == "__main__":
    builder = DialogueBuilder()
    builder.add_role("张总", voice="male", subtitle_color=[0.98, 0.85, 0.55])
    builder.add_role("李总", voice="female", subtitle_color=[0.95, 0.2, 0.2])

    builder.add_line("张总", "现在GEO真的是新机会！", 3.0)
    builder.add_line("李总", "对啊！比当年抖音还猛！", 3.0)
    builder.add_line("张总", "你现在做还来得及！", 2.5)

    tracks = builder.build_tracks()
    print(f"✅ 生成 {len(tracks)} 条角色字幕轨道")
    for t in tracks:
        print(f"  - {t['name']}: {len(t['segments'])} 句")
