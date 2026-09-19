"""剪映工厂 - 定位剪映安装目录和草稿路径"""
import os, glob, json

def find_jianying_root():
    """定位剪映专业版安装根目录"""
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro"),
        r"C:\Program Files\JianyingPro",
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None

def find_latest_version(root):
    """找到最新版本目录"""
    apps_dir = os.path.join(root, "Apps")
    if not os.path.isdir(apps_dir):
        return None
    versions = [d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d))]
    versions.sort(reverse=True)
    return os.path.join(apps_dir, versions[0]) if versions else None

def get_draft_path():
    """读取当前草稿路径（从globalSetting）"""
    root = find_jianying_root()
    if not root:
        return None
    cfg = os.path.join(root, "User Data", "Config", "globalSetting")
    if os.path.exists(cfg):
        with open(cfg, encoding="utf-8") as f:
            for line in f:
                if line.startswith("currentCustomDraftPath="):
                    return line.split("=",1)[1].strip()
    return os.path.join(root, "User Data", "Projects", "com.lveditor.draft")

def list_drafts():
    """列出所有草稿"""
    draft_path = get_draft_path()
    if not draft_path or not os.path.isdir(draft_path):
        return []
    drafts = []
    for d in os.listdir(draft_path):
        full = os.path.join(draft_path, d)
        if os.path.isdir(full):
            drafts.append({"name": d, "path": full})
    return drafts

if __name__ == "__main__":
    root = find_jianying_root()
    ver = find_latest_version(root) if root else None
    draft = get_draft_path()
    print(f"剪映根目录: {root}")
    print(f"最新版本: {ver}")
    print(f"草稿路径: {draft}")
    print(f"草稿数量: {len(list_drafts())}")
    for d in list_drafts()[:5]:
        print(f"  - {d['name']}")
