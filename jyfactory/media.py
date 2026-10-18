#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - 云端素材管理器 v1.0（对齐上游 cloud_manager.py，适配本地）
================================================================
【价值】用剪映官方素材 API 按 ID/关键词解析并下载正版云端素材
       （音乐库617首/视频素材234个/音效43个），零侵权。

用法：
    from .media import CloudManager
    cm = CloudManager()
    path = cm.download_asset("科技")        # 按名称模糊搜索第一个匹配
    path = cm.download_asset("7176685873453500417")  # 按ID精确
"""
import csv
from . import config  # T8: 路径单一真源（config.py 为唯一权威）
import ipaddress
import json
import os
import re
import urllib.request
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_ROOT, "data")
CACHE_DIR = config.CLOUD_CACHE_DIR
# 剪映缓存正版音乐同步目录（物理文件必须在 D 盘——用户铁律：不占 C 盘）
JY_CACHED_DIR = config.JY_CACHED_DIR
JY_CACHED_INDEX = config.JY_CACHED_INDEX
MAX_DOWNLOAD_BYTES = 300 * 1024 * 1024  # 300MB 上限

# 剪映官方素材解析 API（上游已验证）
JY_MGET_ITEM_URL = (
    "https://lv-api-sinfonlinea.ulikecam.com/artist/v1/effect/mget_item"
    "?effect_sdk_version=16.4.0"
    "&channel=jianyingpro_0"
    "&aid=3704"
    "&opengl_version=3.3"
    "&device_id=1053764930506284"
    "&cpu=12th%20Gen%20Intel(R)%20Core(TM)%20i5-12400F"
    "&version_name=5.9.0"
    "&language=zh-Hans"
    "&region=CN"
    "&version_code=5.9.0"
    "&device_platform=windows"
    "&biz_id=2"
    "&subdivision_id="
    "&gpu=NVIDIA%20GeForce%20RTX%203060"
    "&version_code_num=329984"
    "&device_type=x86_64"
)
JY_API_HEADERS = {
    "User-Agent": "JianyingPro/5.9.0.11632 (Windows 10.0.19045; app_id:3704)",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


class CloudManager:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.assets: Dict[str, dict] = {}
        self._load_database()

    def _load_database(self):
        db_files = ["cloud_music_library.csv", "cloud_video_assets.csv", "cloud_sound_effects.csv"]
        # 剪映缓存正版音乐索引（D 盘，sync_jy_cached_music 增量生成）
        if os.path.exists(JY_CACHED_INDEX):
            db_files.append(JY_CACHED_INDEX)
        for db_name in db_files:
            # 绝对路径（D 盘索引）直接用；相对文件名基于 DATA_DIR
            path = db_name if os.path.isabs(db_name) else os.path.join(DATA_DIR, db_name)
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = [ln for ln in f.readlines() if not ln.startswith("#")]
                reader = csv.DictReader(lines)
                for row in reader:
                    eid = (row.get("music_id") or row.get("id") or row.get("effect_id") or "").strip()
                    if not eid:
                        continue
                    name = (row.get("title") or row.get("name") or row.get("id") or "").strip()
                    dur = row.get("duration_s") or row.get("duration")
                    self.assets[str(eid)] = {
                        "id": str(eid),
                        "name": name,
                        "url": (row.get("url") or "").strip(),
                        "duration_s": float(dur) if dur and str(dur).replace(".", "", 1).isdigit() else None,
                        "source_db": os.path.basename(db_name),  # 只存文件名，供音频/视频类型判断
                    }
            except Exception as e:
                print(f"⚠️ 加载 {db_name} 失败: {e}")
        print(f"📦 云端素材索引: {len(self.assets)} 条（音乐/视频/音效）")

    # ---------- 查找 ----------
    def find_asset(self, query: str) -> Optional[dict]:
        """按 ID 精确 / 名称模糊查找"""
        q = str(query).strip()
        if q in self.assets:
            return self.assets[q]
        ql = q.lower()
        for asset in self.assets.values():
            if ql and ql in str(asset.get("name", "")).lower():
                return asset
        return None

    def search_assets(self, query: str, limit: int = 10) -> list:
        """按名称关键词搜索全部匹配（返回列表）"""
        ql = str(query).strip().lower()
        hits = []
        for asset in self.assets.values():
            name = str(asset.get("name", "")).lower()
            if ql and ql in name:
                hits.append(asset)
        return hits[:limit]

    # ---------- URL 解析 ----------
    def _extract_urls(self, data) -> list:
        urls = []

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "item_urls" and isinstance(v, list):
                        urls.extend(str(x) for x in v if isinstance(x, str))
                    elif k in {"url", "video_url", "download_url"} and isinstance(v, str):
                        urls.append(v)
                    else:
                        walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        return [u.replace("\\u0026", "&").replace("\\/", "/") for u in urls if u.startswith("http")]

    def _resolve_url_by_id(self, eid: str) -> Optional[str]:
        bodies = [
            {"items": [{"id": eid, "effect_type": 4, "source": 3}]},
            {"items": [{"id": eid, "effect_type": 4}]},
            {"items": [{"effect_id": eid, "effect_type": 4, "source": 3}]},
            {"items": [{"effect_id": eid, "effect_type": 4}]},
        ]
        for body in bodies:
            try:
                req = urllib.request.Request(
                    JY_MGET_ITEM_URL,
                    data=json.dumps(body).encode("utf-8"),
                    headers=JY_API_HEADERS,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                for url in self._extract_urls(data):
                    if self._is_safe_url(url):
                        return url
            except Exception:
                continue
        return None

    def _is_safe_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme.lower() not in {"http", "https"}:
                return False
            host = (parsed.hostname or "").strip().lower()
            if not host or host in {"localhost", "127.0.0.1", "::1"}:
                return False
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                pass
            return True
        except Exception:
            return False

    # ---------- 下载 ----------
    AUDIO_DBS = {"cloud_music_library.csv", "cloud_sound_effects.csv", "jy_cached_audio.csv"}

    def _infer_ext(self, asset: dict, url: str) -> str:
        is_audio = asset["source_db"] in self.AUDIO_DBS
        q = (urlparse(url).query or "")
        if "audio" in q or is_audio:
            return ".m4a"
        return ".mp4"

    def download_asset(self, query: str, force: bool = False) -> Optional[str]:
        """按 ID/名称下载云端素材到缓存，返回本地路径"""
        asset = self.find_asset(query)
        if not asset:
            print(f"❌ 云端素材未找到: {query}")
            return None
        eid = asset["id"]
        # 本地正版素材（剪映缓存同步来的）——URL 字段是本地文件路径，直接命中
        local_ref = asset.get("url") or ""
        if local_ref and os.path.exists(local_ref):
            print(f"✅ 命中本地正版素材: {os.path.basename(local_ref)}")
            return local_ref
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", asset["name"])[:40]
        ext = self._infer_ext(asset, asset.get("url") or "")
        local_path = os.path.join(self.cache_dir, f"{eid}_{safe_name}{ext}")
        if not force and os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
            print(f"✅ 云端素材命中缓存: {os.path.basename(local_path)}")
            return local_path

        # 解析 URL：优先 API 实时解析（新鲜签名），CSV 旧链接仅备选（可能已过期403）
        url = self._resolve_url_by_id(eid) or asset.get("url")
        if not url:
            print(f"❌ 无法解析素材 URL: {query} ({eid})")
            return None
        if not self._is_safe_url(url):
            print(f"❌ URL 不安全，已拦截: {query}")
            return None

        print(f"⬇️ 下载云端素材: {asset['name']}（{eid}）")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": JY_API_HEADERS["User-Agent"]})
            with urllib.request.urlopen(req, timeout=120) as resp:
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if content_type.startswith("text/html") or content_type.startswith("application/json"):
                    print(f"❌ 下载被拦截（Content-Type={content_type}）")
                    return None
                total = 0
                with open(local_path + ".part", "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_DOWNLOAD_BYTES:
                            raise ValueError("超过大小上限")
                        f.write(chunk)
                os.replace(local_path + ".part", local_path)
            print(f"✅ 下载完成: {os.path.basename(local_path)}（{total/1024/1024:.1f}MB）")
            return local_path
        except Exception as e:
            part = local_path + ".part"
            if os.path.exists(part):
                try:
                    os.remove(part)
                except Exception:
                    pass
            print(f"❌ 下载失败: {e}")
            return None

    def get_asset_duration(self, query: str) -> Optional[float]:
        asset = self.find_asset(query)
        return asset.get("duration_s") if asset else None

    # ---------- 剪映缓存正版音乐同步（2026-10-09 吸收上游 sync_jy_assets） ----------
    def sync_jy_cached_music(self) -> int:
        """把剪映本地缓存的正版音乐（播放/收藏过的）同步进音乐库，增量执行。

        来源：%LOCALAPPDATA%\\JianyingPro\\User Data\\Cache\\music\\downLoadcfg
        （剪映下载缓存清单，物理 mp3 在 Cache\\music 下）
        物理文件复制到 D 盘（JY_CACHED_DIR），索引写 D:\\AI工作区\\data\\jy_cached_audio.csv，
        供 add_cloud_music("歌名") 直接搜索使用——正版、零侵权、无需 API 解析。
        """
        import shutil
        import subprocess
        jy_user_data = os.path.join(os.environ.get("LOCALAPPDATA", ""), "JianyingPro", "User Data")
        jy_cache_music = os.path.join(jy_user_data, "Cache", "music")
        cfg_path = os.path.join(jy_cache_music, "downLoadcfg")
        if not os.path.exists(cfg_path):
            print("❌ 未找到 downLoadcfg——请先在剪映里播放/收藏过音乐再同步")
            return 0
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                file_list = json.load(f).get("list", [])
        except Exception as e:
            print(f"❌ 解析 downLoadcfg 失败: {e}")
            return 0
        if not file_list:
            print("downLoadcfg 无缓存音乐记录")
            return 0
        # 元数据（best effort：读剪映 rp.db 拿歌名/作者）
        db_map = {}
        db_root = os.path.join(jy_user_data, "Cache", "ressdk_db")
        if os.path.exists(db_root):
            import sqlite3
            for root, dirs, files in os.walk(db_root):
                if "rp.db" in files:
                    try:
                        conn = sqlite3.connect(os.path.join(root, "rp.db"))
                        try:
                            for mid, title, author in conn.execute("SELECT id, title, author FROM music"):
                                db_map[str(mid)] = (title or "", author or "")
                        except Exception:
                            pass
                        conn.close()
                    except Exception:
                        pass
        # 增量：读现有索引
        existing = set()
        items = []
        if os.path.exists(JY_CACHED_INDEX):
            try:
                with open(JY_CACHED_INDEX, "r", encoding="utf-8", newline="") as f:
                    lines = [ln for ln in f.readlines() if not ln.startswith("#")]
                if lines:
                    for row in csv.DictReader(lines):
                        items.append(row)
                        existing.add(row.get("id", ""))
            except Exception as e:
                print(f"⚠️ 读索引失败: {e}")
        # 同步
        os.makedirs(JY_CACHED_DIR, exist_ok=True)
        new_count = 0
        print(f"📂 剪映缓存音乐 {len(file_list)} 条 | 已同步 {len(existing)} 条")
        for item in file_list:
            mid_hex = str(item.get("hex", ""))
            file_name = item.get("path", "")
            src = os.path.join(jy_cache_music, file_name)
            if not os.path.exists(src):
                continue
            title, author = db_map.get(mid_hex, ("", ""))
            display = title or f"JY缓存_{mid_hex[:6]}"
            if display in existing:
                continue
            safe = "".join(c for c in display if c.isalnum() or c in (" ", "_", "-")).strip()
            if not safe:
                safe = f"Music_{mid_hex[:6]}"
            dest = os.path.join(JY_CACHED_DIR, f"{safe}.mp3")
            try:
                shutil.copy2(src, dest)
                dur = 0.0
                try:
                    r = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "csv=p=0", dest],
                        capture_output=True, text=True, timeout=20)
                    dur = round(float(r.stdout.strip() or 0), 2)
                except Exception:
                    pass
                items.append({"id": display, "author": author, "duration": str(dur),
                              "url": dest, "source_db": "jy_cached_audio.csv"})
                existing.add(display)
                new_count += 1
                print(f"   + {display}（{dur}s）")
            except Exception as e:
                print(f"   ⚠ 复制失败 {file_name}: {e}")
        # 写索引（保留引导注释）
        os.makedirs(os.path.dirname(JY_CACHED_INDEX), exist_ok=True)
        with open(JY_CACHED_INDEX, "w", encoding="utf-8", newline="") as f:
            f.write("# 剪映缓存正版音乐索引（sync_jy_cached_music 增量生成，物理文件在 D 盘）\n")
            f.write("# AI: 直接 add_cloud_music(\"歌名\") 即可使用，无需 API 解析\n")
            writer = csv.DictWriter(f, fieldnames=["id", "author", "duration", "url", "source_db"])
            writer.writeheader()
            writer.writerows(items)
        # 重新加载索引
        self.assets = {}
        self._load_database()
        print(f"🎉 同步完成: 新增 {new_count} 条 | 音乐库合计 {sum(1 for a in self.assets.values() if a.get('source_db') == 'jy_cached_audio.csv')} 条剪映缓存")
        return new_count


if __name__ == "__main__":
    import sys
    cm = CloudManager()
    if len(sys.argv) > 1:
        p = cm.download_asset(sys.argv[1])
        print("RESULT_PATH|" + (p or ""))
    else:
        # 自检：列出几个可用素材
        for q in ("科技", "温馨", "vlog"):
            hits = cm.search_assets(q, 3)
            print(f"搜索「{q}」: {[(a['id'], a['name']) for a in hits]}")
