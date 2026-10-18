# -*- coding: utf-8 -*-
"""
剪映工厂 jyfactory 包 - 产品级架构（v8.1 对外交付友好版）
=============================================================
【定位】剪映的超级操作员内核。单一真源：D:\\AI工作区\\jianying-factory
【分层】
  engine.py          草稿引擎（VectCutAPI 确定性内核，建草稿/素材/音频/字幕/标题/部署）
  media.py           素材与音乐库（云端正版素材 + 剪映缓存正版音乐同步 + 本地自包含）
  tts.py             配音（SAMI 剪映官方音色 + edge 兜底 + 克隆音色直传）
  narrated.py        口播逐句 TTS 对齐（SRT 时间轴与音频样本级一致）
  text_styles.py     字幕/标题样式预设（爆款黄字/打字机/动画/字号标定公式）
  keywords.py        爆款关键词自动提取（供字幕高亮）
  resources.py       剪映官方资源库查询（滤镜/转场/特效/动画/音色 CSV）
  templates.py       模板管理器（克隆/JSON 替换文本/素材/音频/保存）
  checks.py          只读环境诊断
  export_precheck.py 导出前预检（时长对齐/轨道/素材完整性）
  gui_ops.py         GUI 节点执行器（受控窗口内操作剪映）
  launch.py          剪映启动（受控窗口内，任务栏搜索启动）
  batch.py           批量出片（多文案一次生成，放草稿箱）
  hotspot_mix.py     热点混剪（热点视频 + 广告文字）
  smart_cut.py       智能粗剪
  config.py          全局配置
  paths.py           剪映安装/草稿路径探测
【铁律】见 SKILL.md（安全线/动画中文枚举/响度平衡/轨道名/受控窗口/不占C盘）
"""
from .engine import JianyingVectcutEngine
from .media import CloudManager

__version__ = "8.1.0"
__all__ = ["JianyingVectcutEngine", "CloudManager", "JianyingFactory"]


class JianyingFactory:
    """剪映工厂门面：把引擎 + 素材库 + 生产流程收敛成几个高层动作。

    用法：
        from jyfactory import JianyingFactory
        jy = JianyingFactory()
        report = jy.produce_talk(
            script="口播文案...", video="E:\\素材.mp4",
            speaker="zh_male_huoli", project_name="我的口播",
        )
    """

    def __init__(self, draft_root: str = None):
        from .config import DRAFT_ROOT
        self.engine = JianyingVectcutEngine(draft_root or DRAFT_ROOT)
        self.media = CloudManager()
        self.results = []

    def ensure(self) -> bool:
        """服务保障：确保 VectCutAPI 在跑。"""
        return self.engine.ensure_server()

    def produce_talk(self, script: str, video: str, project_name: str,
                     speaker: str = "zh-CN-YunxiNeural", bgm: str = None,
                     bgm_volume: float = 0.3, title: str = None,
                     keywords: list = None, deploy_only: bool = True) -> str:
        """口播短视频一条龙：配音 → 字幕(SRT精准对齐+关键词高亮) → 素材主轨 →
        BGM 铺满截断 → 部署到剪映草稿箱。

        返回草稿目录路径；失败返回空字符串。
        """
        import os
        import subprocess
        eng = self.engine
        eng.ensure_server()
        draft_id = eng.create_draft(1080, 1920)

        # 1. 配音（逐句 TTS，返回整轨 + 分段时间轴）
        from .narrated import narrate_script, build_srt
        from .config import VOICE_DIR
        work = os.path.join(VOICE_DIR, "work_voice")
        voice_wav, segs, total_dur = narrate_script(
            script, speaker=speaker, out_dir=work, prefix="talk")
        if not voice_wav or total_dur <= 0:
            eng._log("配音", False, "TTS 失败")
            return ""

        # 2. 视频素材（单素材不够时长循环铺满：播放完→再截取补足，防切痕；volume=0 强制静音）
        def _probe_dur(path):
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", path], capture_output=True, text=True, timeout=60)
            try:
                return float(r.stdout.strip() or 0)
            except ValueError:
                return 0
        mat_dur = _probe_dur(video)
        if mat_dur <= 0:
            eng.add_video(draft_id, video, volume=0.0, track_name="video")
        else:
            pos = 0.0
            seg_i = 0
            while pos < total_dur - 0.1:
                need = total_dur - pos
                # 素材比剩余需求长→截取 need；素材不够→整段循环（防切痕）
                src_end = need if mat_dur >= need else mat_dur
                ok = eng.add_video(draft_id, video, volume=0.0, start=0, end=src_end,
                                   target_start=pos, track_name="video")
                if not ok:
                    eng._log("循环视频", False, f"第{seg_i + 1}段失败")
                    break
                pos += (mat_dur if src_end is None else src_end)
                seg_i += 1
            eng._log("循环视频", True, f"素材{mat_dur:.1f}s × 铺满到{total_dur:.1f}s（{seg_i}段）")

        # 3. 配音轨（整轨）+ 4. 字幕 SRT（对齐配音，样本级一致）
        srt = os.path.join(work, "talk.srt")
        build_srt(segs, srt)
        eng.add_audio(draft_id, voice_wav, volume=1.0, track_name="audio_main")
        eng.add_subtitle(draft_id, srt, font_size=9.0, font_color="#FFD400",
                         bold=True, keywords=keywords or [])

        # 5. 标题（顶部安全线内）
        if title:
            eng.add_text(draft_id, title, 0, total_dur, font_size=14.0,
                         transform_y=0.8, intro_animation="打字机_I")

        # 6. BGM（铺满总时长 + 自动响度平衡到人声-15dB）
        if bgm:
            eng.add_cloud_music(draft_id, bgm, volume=bgm_volume,
                                track_name="bgm", end=total_dur,
                                auto_balance=True, voice_path=voice_wav)

        # 7. 保存部署
        dest = eng.save_and_deploy(draft_id, project_name)
        self.results = eng.results
        return dest

    def sync_music(self) -> int:
        """同步剪映缓存正版音乐到音乐库（增量）。"""
        return self.media.sync_jy_cached_music()

    def report(self) -> dict:
        return {"results": self.results,
                "ok": sum(1 for r in self.results if r.get("ok")),
                "total": len(self.results)}

