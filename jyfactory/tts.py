#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剪映工厂 - 剪映官方TTS直调（SAMI协议）v1.0（对齐上游 universal_tts.py）"""
import asyncio
import json
import os
import re
import ssl
import sys
import time
from typing import Optional, Tuple

try:
    import websockets
except ImportError:
    websockets = None

APP_KEY = "IZjhUeAYwP"
APP_ID = "3704"
DEFAULT_DEVICE_ID = "1053764930506284"
DEFAULT_IID = "2314914062247833"


def get_jy_local_config() -> Tuple[str, str]:
    defaults = (DEFAULT_DEVICE_ID, DEFAULT_IID)
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if not local_app_data:
        return defaults
    jy_user_data = os.path.join(local_app_data, "JianyingPro", "User Data")
    cfg = {"device_id": defaults[0], "iid": defaults[1]}
    ttnet_path = os.path.join(jy_user_data, "TTNet", "tt_net_config.config")
    if os.path.exists(ttnet_path):
        try:
            with open(ttnet_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            m = re.search(r"device_id&#\*(\d+)", content)
            if m:
                cfg["device_id"] = m.group(1)
        except Exception:
            pass
    log_dir = os.path.join(jy_user_data, "Log")
    if os.path.exists(log_dir):
        logs = sorted([os.path.join(log_dir, x) for x in os.listdir(log_dir) if x.endswith(".log")],
                      key=os.path.getmtime, reverse=True)
        for p in logs[:5]:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    chunk = f.read(1_000_000)
                m = re.search(r"iid=(\d+)", chunk)
                if m:
                    cfg["iid"] = m.group(1)
                    break
            except Exception:
                continue
    return cfg["device_id"], cfg["iid"]


def _build_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


async def _run_sami_tts(text: str, speaker: str, output_file: str,
                        dev_id: str, iid: str) -> Tuple[bool, str]:
    ws_url = f"wss://sami.bytedance.com/internal/api/v2/ws?device_id={dev_id}&iid={iid}"
    headers = {
        "User-Agent": f"JianyingPro/5.9.0.11632 (Windows 10.0.19045; app_id:3704; device_id:{dev_id})"
    }
    ssl_context = _build_ssl_context()
    try:
        async with websockets.connect(ws_url, additional_headers=headers, ssl=ssl_context, open_timeout=20) as ws:
            task_id = f"ai_gen_{os.urandom(4).hex()}"
            start_msg = {
                "app_id": APP_ID,
                "appkey": APP_KEY,
                "event": "StartTask",
                "namespace": "TTS",
                "task_id": task_id,
                "message_id": task_id + "_0",
                "payload": json.dumps({"text": text, "speaker": speaker,
                                        "audio_config": {"format": "ogg_opus", "sample_rate": 24000, "bit_rate": 64000}},
                                       ensure_ascii=False, separators=(",", ":")),
            }
            await ws.send(json.dumps(start_msg, ensure_ascii=False, separators=(",", ":")))
            await ws.send(json.dumps({"appkey": APP_KEY, "event": "FinishTask", "namespace": "TTS"}))
            audio_data = bytearray()
            while True:
                try:
                    resp_raw = await asyncio.wait_for(ws.recv(), timeout=20)
                except asyncio.TimeoutError:
                    return False, "SAMI Timeout"
                if isinstance(resp_raw, str):
                    resp = json.loads(resp_raw)
                    event = resp.get("event")
                    if event == "TaskFailed":
                        return False, f"SAMI Error: {resp.get('status_text')} (Code: {resp.get('status_code')})"
                    if event == "TaskFinished":
                        break
                else:
                    audio_data.extend(resp_raw)
            if audio_data:
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                return True, output_file
            return False, "No audio"
    except Exception as e:
        return False, str(e)


async def _run_edge_tts(text: str, output_file: str, speaker: str = "zh_male_huoli") -> Tuple[bool, str]:
    try:
        import edge_tts
        voice = "zh-CN-YunxiNeural" if "male" in speaker else "zh-CN-XiaoxiaoNeural"
        actual_path = output_file if output_file.endswith(".mp3") else output_file.rsplit(".", 1)[0] + ".mp3"
        communicate = edge_tts.Communicate(text, voice, rate="+10%")
        await communicate.save(actual_path)
        return True, actual_path
    except Exception as e:
        return False, f"Edge-TTS Error: {str(e)}"


async def generate_voice_with_meta(text: str, output_path: str, speaker: str = "zh_male_huoli", *,
                                   backend: Optional[str] = None, allow_fallback: bool = True,
                                   sami_retries: int = 1) -> Tuple[Optional[str], Optional[str]]:
    if websockets is None:
        backend = "edge"
    dev_id, iid = get_jy_local_config()
    force_sami = backend == "sami"
    force_edge = backend == "edge"
    if not force_edge:
        for i in range(max(1, int(sami_retries))):
            ok, res = await _run_sami_tts(text, speaker, output_path, dev_id, iid)
            if ok:
                print(f"[+] SAMI Success: {res}")
                return res, "sami"
            print(f"[!] SAMI Failed (attempt {i + 1}): {res}")
            if i + 1 < max(1, int(sami_retries)):
                await asyncio.sleep(0.35)
        if force_sami or not allow_fallback:
            return None, None
    ok_edge, res_edge = await _run_edge_tts(text, output_path, speaker)
    if ok_edge:
        print(f"[+] Edge-TTS Success: {res_edge}")
        return res_edge, "edge"
    return None, None


def tts_speak(text: str, speaker: str = "zh_male_huoli", out: str = "",
              backend: Optional[str] = None, allow_fallback: bool = True) -> Optional[str]:
    if not out:
        out = os.path.join(os.getcwd(), f"tts_{int(time.time())}.wav")
    parts = re.split(r"(?<=[。？！])", text)
    parts = [p.strip() for p in parts if p.strip()]
    seg_files = []
    buf = ""
    idx = 0

    def synth(text_seg: str, out_seg: str) -> Optional[str]:
        path, _ = asyncio.run(generate_voice_with_meta(text_seg, out_seg, speaker,
                                                       backend=backend, allow_fallback=allow_fallback))
        return path

    tmp_dir = os.path.join(os.path.dirname(out) or ".", "_sami_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    for p in parts:
        if len(buf) + len(p) > 180 and buf:
            seg_out = os.path.join(tmp_dir, f"seg_{idx}.ogg")
            r = synth(buf, seg_out)
            if r:
                seg_files.append((r, buf))
            idx += 1
            buf = ""
        buf += p
    if buf:
        seg_out = os.path.join(tmp_dir, f"seg_{idx}.ogg")
        r = synth(buf, seg_out)
        if r:
            seg_files.append((r, buf))
    if not seg_files:
        print("❌ 全部 TTS 分段失败")
        return None
    import subprocess
    listf = os.path.join(tmp_dir, "list.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for path, _ in seg_files:
            f.write(f"file '{path}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                    "-ar", "44100", "-ac", "2", out],
                   check=True, capture_output=True)
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"✅ TTS 完成: {out}（{len(seg_files)}段）")
    return out


if __name__ == "__main__":
    import sys as _sys
    text = _sys.argv[1] if len(_sys.argv) > 1 else "你好，这是剪映官方配音测试。"
    speaker = _sys.argv[2] if len(_sys.argv) > 2 else "zh_male_huoli"
    out = _sys.argv[3] if len(_sys.argv) > 3 else r"D:\AI工作区\配音\sami_test.wav"
    tts_speak(text, speaker, out)
