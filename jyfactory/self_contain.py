#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 素材自包含 v1.0（对齐上游 _stage_local_asset）
================================================================
【价值】剪映草稿引用素材改为草稿内相对路径（assets/<type>/<name>），
        素材随草稿走——服务端草稿被清理/移动/换机都不丢素材。

用法：
    from .self_contain import self_contain_draft
    fixed = self_contain_draft(r"D:/AI工作区/剪映草稿/我的草稿")
"""
import json
import os
import shutil

TYPE_DIR = {"video": "video", "audio": "audio", "image": "image"}


def self_contain_draft(draft_dir: str, dry_run: bool = False) -> dict:
    dc = os.path.join(draft_dir, "draft_content.json")
    if not os.path.exists(dc):
        return {"fixed": 0, "missing": [], "ok": False, "reason": "draft_content.json 不存在"}
    data = json.load(open(dc, encoding="utf-8"))
    mats = data.get("materials", {})
    fixed, missing = 0, []

    for mtype in ("videos", "audios", "images"):
        sub = TYPE_DIR.get(mtype.rstrip("s"), mtype)
        for m in mats.get(mtype, []):
            path = m.get("path", "")
            if not path:
                continue
            if path.startswith("assets/") or path.startswith("assets\\"):
                continue
            src = path
            if not os.path.isabs(src):
                src = os.path.join(draft_dir, src)
            if not os.path.exists(src):
                missing.append({"type": mtype, "path": path})
                continue
            dest_dir = os.path.join(draft_dir, "assets", sub)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, os.path.basename(src))
            if not dry_run and (not os.path.exists(dest) or os.path.getsize(dest) != os.path.getsize(src)):
                shutil.copy2(src, dest)
            rel = f"assets/{sub}/{os.path.basename(dest)}"
            if not dry_run:
                m["path"] = rel
            fixed += 1
            print(f"📦 [{mtype}] {os.path.basename(src)} → {rel}")

    remote_cleared = 0
    for mtype in ("videos", "audios", "images"):
        for m in mats.get(mtype, []):
            if m.get("remote_url"):
                if not dry_run:
                    m["remote_url"] = ""
                remote_cleared += 1

    if not dry_run:
        json.dump(data, open(dc, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 素材自包含完成: 修复{fixed}个 | remote_url清理{remote_cleared}个 | 缺失{len(missing)}个")
    for x in missing:
        print(f"  ⚠️ 缺失: {x['type']} {x['path']}")
    return {"fixed": fixed, "missing": missing, "ok": len(missing) == 0, "reason": ""}


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else r"D:\AI工作区\剪映草稿\一指哥_30秒懂GEO"
    self_contain_draft(d)
