# -*- coding: utf-8 -*-
"""剪映工厂 v8.0 - 冒烟回归测试（可直接 python tests/smoke_test.py 运行）

覆盖（对齐架构评估报告 P1-2 建议：铁律必须有自动化断言守护）：
  1. 包导入（门面/引擎/云素材）
  2. 服务探活（VectCutAPI localhost:9001）
  3. 建草稿（竖屏 1080x1920）
  4. 加视频（主轨 video + 强制静音 volume=0）
  5. 加配音（audio_main 轨）
  6. 加 BGM（bgm 轨，按配音总时长铺满截断）
  7. 字幕 + 关键词高亮（SRT 时间戳）
  8. 标题（顶部安全线内 + 中文动画枚举）
  9. 保存部署 + 部署完整性（content 可解析 / tracks / materials / 主轨 video）
 10. 素材自包含（assets 目录 + 相对路径）
 11. ★强制静音断言：主轨 video 段 volume == 0（原片杂音清零）
 12. ★分轨断言：audio_main（配音）与 bgm（背景乐）独立成轨，无单轨混音
 13. ★铺满截断断言：BGM 轨时长 == 主视频轨时长（无片尾黑屏/音乐提前结束）
 14. ★时长一致断言：视频/BGM/人声三轨时长一致（±0.15s 容差）
 15. ★local_material_id 非空断言：全部媒体素材 id 非空（防剪映媒体丢失）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = []
FAIL = []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f" | {detail}" if detail and not cond else ""))


def _track_duration(tracks, name, ttype):
    """某轨总时长（微秒）"""
    for tr in tracks:
        if tr.get("name") == name and tr.get("type") == ttype:
            d = 0
            for seg in tr.get("segments", []):
                d = max(d, seg.get("target_timerange", {}).get("duration", 0))
            return d
    return 0


def test_imports():
    from jyfactory import JianyingFactory, JianyingVectcutEngine, CloudManager
    check("包导入", JianyingFactory and JianyingVectcutEngine and CloudManager)


def test_engine_full_flow():
    from jyfactory import JianyingFactory
    jy = JianyingFactory()
    check("服务探活", jy.ensure())
    eng = jy.engine
    draft_id = eng.create_draft(1080, 1920)
    check("建草稿", bool(draft_id), draft_id)

    video = r"E:\张总口播素材\张总形象.mp4"
    voice = r"D:\AI工作区\测试素材\geo_test_voice.wav"
    bgm = r"D:\AI工作区\BGM\默认口播BGM_01.mp3"
    if not os.path.exists(video):
        check("加视频(主轨video)", False, "张总形象素材不存在")
        return
    if not os.path.exists(voice):
        check("加配音(audio_main)", False, "测试配音不存在")
        return

    TOTAL = 3.0
    ok_v = eng.add_video(draft_id, video, volume=0.0, start=0, end=TOTAL,
                         target_start=0, track_name="video")
    check("加视频(主轨video+静音)", ok_v)

    ok_a = eng.add_audio(draft_id, voice, volume=1.0, track_name="audio_main", end=TOTAL)
    check("加配音(audio_main轨)", ok_a)

    if os.path.exists(bgm):
        ok_b = eng.add_audio(draft_id, bgm, volume=0.35, track_name="bgm", end=TOTAL)
        check("加BGM(bgm轨,铺满截断)", ok_b)
    else:
        check("加BGM(bgm轨,铺满截断)", False, "BGM 文件不存在")

    srt = os.path.join(os.path.dirname(__file__), "smoke.srt")
    with open(srt, "w", encoding="utf-8") as f:
        f.write("1\n00:00:00,000 --> 00:00:03,000\nGEO 就是生成式引擎优化，让AI推荐你\n\n")

    check("字幕+关键词高亮", eng.add_subtitle(draft_id, srt, font_size=9.0,
                                            keywords=[{"word": "GEO", "color": "#FF3B30", "bold": True}]))

    check("标题(顶部安全线内)", eng.add_text(draft_id, "AI获客 就三步", 0, TOTAL,
                                        font_size=14.0, transform_y=0.8,
                                        intro_animation="打字机_I"))

    dest = eng.save_and_deploy(draft_id, "smoke_v80_架构回归")
    check("保存部署", bool(dest) and os.path.isdir(dest), dest or "")

    if not dest:
        return

    dc = os.path.join(dest, "draft_content.json")
    if not os.path.exists(dc):
        check("部署完整性: content可解析", False, "draft_content.json 缺失")
        return
    data = json.load(open(dc, encoding="utf-8"))
    tracks = data.get("tracks", [])
    mats = data.get("materials", {})
    check("部署完整性: content可解析", True)
    check("部署完整性: tracks非空", len(tracks) > 0)
    check("部署完整性: materials非空", bool(mats))

    vseg = None
    for tr in tracks:
        if tr.get("name") == "video" and tr.get("type") == "video":
            if tr.get("segments"):
                vseg = tr["segments"][0]
    check("部署完整性: 主轨video", vseg is not None)
    if vseg is not None:
        vol = vseg.get("volume", 1.0) or 0.0
        check("★强制静音(原片volume=0)", abs(vol) < 0.05, f"volume={vol}")

    has_voice = _track_duration(tracks, "audio_main", "audio") > 0
    has_bgm = _track_duration(tracks, "bgm", "audio") > 0
    check("★分轨(配音+BGM独立成轨)", has_voice and has_bgm)

    v_dur = _track_duration(tracks, "video", "video")
    b_dur = _track_duration(tracks, "bgm", "audio")
    check("★BGM铺满(与视频同长)", v_dur > 0 and abs(v_dur - b_dur) < 0.15e6,
          f"video={v_dur/1e6:.2f}s bgm={b_dur/1e6:.2f}s")

    a_dur = _track_duration(tracks, "audio_main", "audio")
    check("★时长一致(三轨对齐)", v_dur > 0 and a_dur > 0 and
          abs(v_dur - a_dur) < 0.15e6 and abs(b_dur - a_dur) < 0.15e6,
          f"video={v_dur/1e6:.2f}s voice={a_dur/1e6:.2f}s bgm={b_dur/1e6:.2f}s")

    bad_ids = []
    for tr in tracks:
        for seg in tr.get("segments", []):
            mid = seg.get("material_id") or seg.get("local_material_id") or ""
            if not mid:
                bad_ids.append(f"{tr.get('name')}:{seg.get('id')}")
    check("★local_material_id非空", not bad_ids, ";".join(bad_ids[:3]) or "全部非空")

    assets = os.path.join(dest, "assets")
    if os.path.isdir(assets) and len(os.listdir(assets)) > 0:
        check("素材自包含(assets目录)", True)
        dc_raw = open(dc, encoding="utf-8").read()
        has_abs = ("D:\\" in dc_raw or "E:\\" in dc_raw or "/mnt/" in dc_raw)
        check("素材自包含(相对路径)", not has_abs, "content 仍含绝对路径" if has_abs else "")
    else:
        check("素材自包含(assets目录)", False, "assets 缺失")


def main():
    test_imports()
    test_engine_full_flow()
    print("=" * 50)
    print(f"通过 {len(PASS)} | 失败 {len(FAIL)}")
    if FAIL:
        print("失败项:", FAIL)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
