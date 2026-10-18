# 剪映工厂 jyfactory

**剪映的超级操作员** —— 用豆包一句话，自动完成：找热点 → 写爆款文案 → 配音 → 字幕 → 标题花字 → BGM → 转场特效 → 出片到剪映草稿箱。

比人更懂剪映、更快更稳、产出优质成品。所有素材/音乐全部来自剪映官方曲库与用户自有素材，**正版零侵权**。

---

## ✨ 能做什么

| 能力 | 说明 |
|---|---|
| 🎬 口播视频一条龙 | 一句话主题 → 全网热点 → 爆款拆解 → 原创口播稿 →（确认后）配音/字幕/标题/BGM → 草稿箱 |
| 🧠 确定性内核 | VectCutAPI 秒级生成剪映原生明文草稿（视频/配音/BGM/标题多轨一次成型），剪映直接打开 |
| 🎙️ 配音三通道 | 剪映官方克隆音色（你的声音）→ SAMI 官方音色 → edge-tts 自然男声兜底，失败自动降级 |
| ✍️ 字幕精准对齐 | SRT 时间戳与配音逐句对齐；或剪映官方「识别字幕」/「智能包装」自动出字幕+花字+特效 |
| 🎵 正版 BGM | 剪映官方曲库 617+ 首音乐，按人声自动响度平衡（BGM 永远是人声陪衬） |
| 🎨 爆款包装 | 科技风智能包装、标题花字、关键词高亮、转场特效、Ken Burns 运镜 |
| 📦 批量出片 | 一次 10 条不同文案，全部进草稿箱 |
| 📈 蹭热点广告 | 聚蚁AI 双屏常驻模板：热点区+产品区文字动画，无配音拿完播率 |

## 🎬 演示效果

- 口播一条龙成片示例：`examples/demo_talk.mp4`（张总形象口播，配音/字幕/BGM 一次成型）
- 聚蚁双屏热点广告示例：`examples/demo_hotspot_ad.mp4`（纯文字动画 + 产品混剪，无配音）
- 宣传片（本项目能力全景）：见 Releases 附件 `剪映工厂宣传片_何公子复刻版.mp4`

## 💼 典型使用场景

| 场景 | 一句话需求 | 产出 |
|---|---|---|
| 口播带货 | "用我的形象，蹭今天的 AI 热点做条口播" | 45-60s 口播视频进草稿箱 |
| 蹭热点引流 | "按聚蚁的模板做特斯拉火箭车广告" | 14-18s 双屏文字动画广告 |
| 知识分享 | "把这段 300 字文章改成口播" | 自动断句、配音、字幕、标题 |
| 批量起号 | "10 条不同文案一起做" | 10 条草稿一次生成 |
| 账号人设 | "我的口播形象 + 沉稳男声" | 统一形象、统一音色、批量产出 |

## 🖥️ 环境要求

- **Windows 10/11**
- **Python 3.9+**
- **剪映专业版**（https://www.capcut.cn ，11.5 版本实测最优）
- **ffmpeg**（https://ffmpeg.org/download.html ，加入 PATH；缺失只影响预览/抽帧，核心出片不受阻）
- 豆包客户端（使用受控窗口自动化剪映 GUI 能力）

## 🚀 快速安装（3 分钟）

```bash
# 1. 一键安装：检测环境 → 获取内核 → 装依赖 → 生成配置
python install.py

# 2. 环境体检（9 项检查）
python cli.py doctor
```

安装时按提示输入你的口播形象素材路径；之后可在 `<工作区>/config.json` 修改（参考 `config.example.json`）。

## 🎬 快速出片

```bash
# 方式一：命令行
python cli.py produce-tally "你的口播文案" --video 你的素材.mp4 --project 草稿名

# 方式二：豆包技能（推荐）
# 在豆包里说：「帮我做个口播视频，主题是 AI 获客」
# AI 自动找热点 → 写爆款文案 → 等你确认 → 一键出片到草稿箱
```

## 📖 常用命令

```bash
python cli.py doctor          # 环境诊断（只读）
python cli.py ensure          # 启动/探活 VectCutAPI 内核服务
python cli.py sync-music      # 同步剪映缓存正版音乐进曲库
python cli.py templates       # 列出可用模板
python cli.py produce-tally "文案" --video 素材.mp4 --project 草稿名   # 口播一条龙
python cli.py hotspot-ad --title "热点标题" --brand "品牌" --videos a.mp4 b.mp4 --project 草稿名  # 双屏热点广告
```

## ⚙️ 配置

优先级：**环境变量 > `<工作区>/config.json` > 内置默认值**

```bash
# 环境变量示例（Windows）
set JYFACTORY_HOME=D:\MyWorkspace        # 整体重定向工作区
set JYFACTORY_DEFAULT_VIDEO=D:\my\face.mp4  # 口播形象素材
set JYFACTORY_DRAFT_DIR=D:\MyWorkspace\草稿

# config.json（install.py 自动生成，可手改）
# 完整字段见 config.example.json
```

自动探测：剪映安装路径（注册表+常见路径）、ffmpeg（PATH）、剪映缓存音乐目录。

## 🧪 验证

```bash
python tests/smoke_test.py   # 冒烟回归（20 项：导入/内核/建稿/字幕高亮/主轨/静音/BGM铺满/时长一致/部署完整性）
```

## 🏗️ 架构

```
jyfactory/
├── engine.py        草稿引擎（VectCutAPI 确定性内核）
├── media.py         素材与音乐库（云端正版 890 条 + 剪映缓存音乐同步）
├── tts.py           配音（SAMI 官方音色 + edge 兜底 + 克隆音色直传）
├── narrated.py      口播逐句 TTS 对齐（SRT 样本级一致）
├── templates.py     模板管理器（克隆/替换文本素材，保留样式）
├── checks.py        环境诊断（9 项）
├── gui_ops.py       受控窗口 GUI 算子（克隆音色/识别字幕/智能包装）
├── launch.py        剪映启动（受控窗口内）
├── export_gui.py    导出自动化
├── advanced.py      高级算子（Ken Burns/语义匹配/转场/花字）
├── batch.py         批量出片
└── config.py        统一配置（环境变量/JSON/默认值三级）
```

## ❓ 常见问题

**Q：草稿在剪映列表不显示/打不开？**
A：v8 内核生成的是剪映原生明文草稿，剪映 11.5 实测直接打开。若列表不刷新：重启剪映/回首页。老版本（10.9/11.1/11.4）目录无主程序不可用，建议升级 11.5。

**Q：字幕和配音对不齐？**
A：SRT 时间戳严格对齐配音（引擎直接写入），或走剪映官方识别字幕/智能包装。

**Q：原视频有环境杂音？**
A：引擎自动把原片音量设为 0（强制静音铁律）。

**Q：片尾黑屏/BGM 提前结束？**
A：BGM 按配音时长铺满截断，三轨时长一致（回归测试守护）。

**Q：背景音乐会侵权吗？**
A：全部走剪映官方曲库（正版授权），零侵权。

**Q：需要付费吗？**
A：核心流程免费可用；剪映 SVIP 解锁克隆音色/对口型/智能包装等高级能力（由用户自己的剪映账号决定）。

## 📄 License

本项目代码为作者私有（Proprietary）。VectCutAPI 内核为 Apache 2.0（https://github.com/sun-guannan/VectCutAPI ）。
