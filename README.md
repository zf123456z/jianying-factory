# 剪映工厂 (JianYing Factory)

> AI 驱动的剪映专业版超级操作员——丢素材进去，出成片。
> 我们不替剪映干活，只做最懂剪映、操作最快最稳的 AI。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![JianYingPro](https://img.shields.io/badge/JianYingPro-11.x-orange.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)
![Version](https://img.shields.io/badge/version-v7.7.1-brightgreen.svg)

## 这是什么

剪映工厂是一个开源的 AI Agent 技能：用成熟开源库 **pyJianYingDraft** 直写剪映草稿，再配合受控窗口驱动**剪映官方功能**（识别字幕 / 克隆音色 / 智能包装 / 对口型 / 云端正版曲库），一条命令产出爆款口播短视频。

**核心理念：不替剪映干活，只做比人更懂剪映、更会用剪映、更快更准的 AI。**
所有历史踩过的坑（画面条纹 / 片尾黑屏 / 原片杂音 / 字幕错位 / 素材丢失 / 多音轨草稿打不开）全部在代码层堵死。

## v7.7.1 最新能力（10/10 实测通过）

| 能力 | 说明 |
|---|---|
| 🔟 转场+特效轨道算子 | `TransitionType` 500+ 转场、`VideoSceneEffectType` 1000+ 特效，自动注册 materials.transitions / video_effects（对齐上游 vfx_ops） |
| ⑥ 花字样式（引擎级） | **513 个剪映官方花字 ID 全部可直接写入草稿 JSON**（无需 GUI），`add_flower_title()` 一行加爆款花字标题 |
| ⑧ 录屏智能变焦 | record_screen（ffmpeg gdigrab 无需授权）+ 点击处 1.0→1.5→1.0 缩放脉冲 |
| ① 云端正版音乐 | 剪映曲库缓存桥接：BGM 留空自动选最近下载的曲库歌混音，正版零侵权、不依赖 GUI 按钮 |
| ② Ken Burns 运镜 | 8 预设关键帧运镜（zoom_in_slow / pan_left / fade_in …） |
| ③ 内置 TTS+逐句字幕 | edge-tts 拆句合成 → 累计时长排字幕 → 单音轨混音，无需剪映 GUI |
| ④ 模板克隆批量 | 草稿 JSON 级克隆：素材替换 + 文本替换，原模板零污染 |
| ⑤ 语义素材匹配 | 中文关键词 n-gram + 素材标签打分，按文案语义自动匹配画面 |
| ⑦ Web 动效录屏 | Playwright 优先系统 Edge，录 HTML 动效 → H.264 竖屏 |
| ⑨ 影视解说 | 分镜裁剪 + 逐镜 TTS + 字幕 + 段间自动叠化转场 |

**v7.6 核心铁律（单音轨混音）**：配音/BGM 由引擎 ffmpeg 预混成**单条音轨**（人声时段 BGM 自动闪避 0.15、之后恢复 0.35），剪映 11.5 实测 ≥2 条 audio 轨的草稿一律打不开，单音轨 100% 打开。

## 爆款文案前期（v7.4 青出于蓝）

用户只说一句话（如"找今天的 AI 热点"），AI 自动完成：
1. **全网找热点**（今日头条/36氪/量子位/抖音热榜）
2. **五维评估**（新鲜度/情绪值/利益相关度/可跟风度/争议度，≥32 才做）
3. **爆款拆解**（钩子 0-3s → 冲突 → 转折 → 干货 → 行动）
4. **原创改写**（换主角 + 加数字 + 加案例 + 留钩子，绝不洗稿）
5. **用户确认文案后才开剪**（不返工）

完整方法论见 `references/爆款文案工作流.md`。

## 为什么比别的剪映自动化强

| 维度 | 普通方案 | 剪映工厂 v7.7.1 |
|---|---|---|
| 文案前期 | 无/手写 | **一句话→热点→爆款拆解→原创文案→用户确认** |
| 草稿生成 | 手写裸 JSON，剪映升级就崩 | pyJianYingDraft 成熟引擎，字段库自动校验 |
| 字幕 | 自写对齐算法，永远对不准 | **剪映官方识别字幕**，100% 同步 |
| 画面条纹 | 解码花屏/倒置 | ffprobe 探测 + 自动转码 H.264 yuv420p 竖屏 1080x1920 |
| 原片杂音 | 漏静音 | 引擎强制原片音量=0 |
| 片尾黑屏 | BGM 提前结束 | BGM 自动循环铺满总时长 |
| 素材丢失 | 剪映 5.9+ 报"媒体丢失" | local_material_id 稳定非空 + 素材 MD5 自包含 |
| 草稿打不开 | 双音轨/裸 JSON | 单音轨混音铁律 + 库校验 |
| 花字 | 只能 GUI 手点 | **513 个官方花字 ID 引擎级直写** |
| 音乐版权 | 网上下载可能侵权 | **剪映曲库缓存桥接，全部正版授权** |

## 快速开始

```bash
# 1. 克隆仓库
 git clone https://github.com/zf123456z/jianying-factory.git

# 2. 安装依赖
 pip install pyJianYingDraft edge-tts pynput playwright

# 3. 配置路径（src/factory_config.json，或用环境变量覆盖）
#    JIANYING_DRAFT_ROOT / JIANYING_EXPORT_ROOT / JIANYING_BACKUP_ROOT
#    JIANYING_DEFAULT_VIDEO / JIANYING_BGM_VOLUME

# 4. 一条命令成片（草稿进剪映草稿箱）
 python src/factory.py produce "文案或主题" --name 我的草稿 \
     --video E:\素材\形象.mp4 --voiceover D:\配音\配音.wav --bgm D:\BGM\bgm.mp3

# 5. 跑回归测试
 python -m unittest discover tests -v
```

## 核心能力

- 🎤 **口播一键成片**：文案/主题 → 草稿（视频+配音+BGM 全对齐铺满）
- 🔥 **爆款文案前期**：一句话 → 热点 → 拆解 → 原创文案 → 用户确认
- 📝 **剪映官方识别字幕**：识别字幕 → 爆款黄字样式，100% 同步
- 🗣️ **克隆音色**：剪映「换音色 → 克隆音色」，用户自克隆声音
- 🎨 **智能包装**：剪映官方科技风智能包装（花字/特效/音效自动匹配）
- ✨ **花字引擎级**：513 个官方花字 ID 直写草稿 JSON，爆款标题一行生成
- 🎵 **云端正版音乐**：曲库缓存桥接，BGM 正版零侵权
- 🎬 **转场+特效轨道**：500+ 转场 / 1000+ 特效，段间自动叠化
- 📦 **批量生产**：一次 N 条文案 → N 个独立草稿（9.9 批量版核心）
- 🔒 **质量门禁**：BGM 音量区间 / 字幕存在性 / 对齐容差自动检查
- 🩺 **只读诊断 + 导出预检**：doctor / export_precheck，导出前拦截问题

## 使用方式（傻瓜式）

> **"帮我做个口播视频，主题是 XXX，素材用 XXX"**

AI 自动完成：找热点 → 写爆款文案 → **用户确认** → 生成配音 → 引擎写草稿 → 受控窗口开剪映 → 官方识别字幕 → 爆款样式 → 智能包装 → 放草稿箱/导出。

## 版本与价格

| 版本 | 价格 | 内容 |
|---|---|---|
| 基础版 | 1.9 元 | 单条口播视频（文案 + 素材 → 草稿） |
| 批量版 | 9.9 元 | 批量生产 + 声音克隆 + 关键词高亮 + 多角色对话 |

## 系统要求

- Windows 10/11
- 剪映专业版 10.x / 11.x（11.5 实测通过）
- Python 3.10+
- ffmpeg / ffprobe（加入 PATH）
- 支持桌面自动化的 AI 环境（豆包等）

## 目录结构

```
jianying-factory/
├── src/                  # 引擎 + 高级算子 + CLI（核心）
│   ├── factory.py        #    CLI 门面：produce/precheck/doctor/drafts/config
│   ├── engine_v2.py      #    引擎：pyJianYingDraft 写草稿 + 单音轨混音 + 防条纹/防黑屏
│   ├── advanced_ops.py   #    高级算子：Ken Burns / TTS / 花字 / 转场特效 / 录屏变焦 / 影视解说
│   └── factory_config.py / jianying_music_bridge.py / factory_config.json
├── scripts/              # 技能脚本（GUI 操作 / 预检 / 诊断 / 批量 / 枚举库）
├── references/           # 方法论 / 爆款文案工作流 / 剪映 GUI 节点 SOP / 代码卫生
├── data/                 # 花字 513 ID / 曲库搜索词 / 素材语义标签
├── tests/                # 回归测试
└── README.md / SKILL.md / LICENSE
```

## 开源协议

MIT License — 免费使用、修改、分发。商业使用请支持正版剪映。

---

Made with 剪映工厂 · 让每个人都能批量生产专业视频