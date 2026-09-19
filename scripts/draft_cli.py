"""剪映工厂 - 草稿操作CLI"""
import os, json, argparse
from find_jianying import list_drafts, get_draft_path, find_latest_version, find_jianying_root

def get_project_id(draft_name):
    """提取草稿的项目ID，兼容加密/明文两种格式"""
    draft_path = get_draft_path()
    draft_dir = os.path.join(draft_path, draft_name)
    if not os.path.isdir(draft_dir):
        return None
    # 尝试明文格式
    drc = os.path.join(draft_dir, "draft_content.json")
    if os.path.exists(drc):
        try:
            with open(drc, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("id")
        except:
            pass
    # 尝试加密格式
    vsc = os.path.join(draft_dir, "draft_virtual_store.json")
    if os.path.exists(vsc):
        try:
            with open(vsc, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("child_id") or data.get("id")
        except:
            pass
    return None

def draft_info(draft_name):
    """读取草稿基本信息"""
    draft_path = get_draft_path()
    draft_dir = os.path.join(draft_path, draft_name)
    drc = os.path.join(draft_dir, "draft_content.json")
    if not os.path.exists(drc):
        return {"error": "草稿内容不可读（可能为加密格式）"}
    try:
        with open(drc, encoding="utf-8") as f:
            data = json.load(f)
        duration = data.get("duration", 0) / 1_000_000  # 微秒转秒
        fps = data.get("fps", 30)
        width = data.get("canvas_config", {}).get("width", 1920)
        height = data.get("canvas_config", {}).get("height", 1080)
        tracks = len(data.get("tracks", []))
        clips = sum(len(t.get("segments", [])) for t in data.get("tracks", []))
        return {
            "name": draft_name,
            "project_id": data.get("id"),
            "duration_sec": round(duration, 1),
            "fps": fps,
            "resolution": f"{width}x{height}",
            "tracks": tracks,
            "clips": clips,
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="剪映工厂 - 草稿操作")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("list", help="列出草稿")
    pid = sub.add_parser("project-id", help="获取项目ID")
    pid.add_argument("name")
    info = sub.add_parser("info", help="读取草稿信息")
    info.add_argument("name")
    args = p.parse_args()
    if args.cmd == "list":
        for d in list_drafts():
            print(d["name"])
    elif args.cmd == "project-id":
        print(get_project_id(args.name))
    elif args.cmd == "info":
        print(json.dumps(draft_info(args.name), ensure_ascii=False, indent=2))
