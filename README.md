# 剪映工厂 (JianYing Factory)

> AI 驱动的剪映专业版超级操作员——丢素材进去，出成片。
> 我们不替剪映干活，只做最懂剪映、操作最快最稳的 AI。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![JianYingPro](https://img.shields.io/badge/JianYingPro-11.x-orange.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)

## 这是什么

剪映工厂是一个开源的 AI Agent 技能：用成熟开源库 **pyJianYingDraft** 直写剪映草稿，再配合受控窗口驱动**剪映官方功能**（识别字幕 / 克隆音色 / 智能包装 / 对口型），一条命令产出爆款口播短视频。

**核心理念：不替剪映干活，只做比人更懂剪映、更会用剪映、更快更准的 AI。**
所有历史踩过的坑（画面条纹 / 片尾黑屏 / 原片杂音 / 字幕错位 / 素材丢失 / 加密草稿误报）全部在代码层堵死。

## 为什么比别的剪映自动化强

| 维度 | 普通方案 | 剪映工厂 v7.3 |
|---|---|---|
| 草稿生成 | 手写裸 JSON，剪映升级就崩 | pyJianYingDraft 成熟引擎，字段库自动校验 |
| 字幕 | 自写对齐算法，永远对不准 | **剪映官方识别字幕**，100% 同步 |
| 画面条纹 | 解码花屏/倒置 | ffprobe 探测 + 自动转码 H.264 yuv420p 竖屏 1080x1920 |
| 原片杂音 | 漏静音 | 引擎强制原片音量=0 |
| 片尾黑屏 | BGM 提前结束 | BGM 自动循环铺满总时长 |
| 素材丢失 | 剪映 5.9+ 报"媒体丢失" | local_material_id 稳定非空 + 素材 MD5 自包含 |
| 剪映 11.5 加密草稿 | 预检误报"致命错误" | **识别加密 → 降级提示**，不再误判 |
| 质量门禁 | 无 | BGM 音量 0.30-0.40 / 字幕存在性 / 对齐容差 500ms 自动检查 |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zf123456z/jianying-factory.git

# 2. 安装依赖
pip install pyJianYingDraft

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

- 🎤 **口播一键成片**：文案/主题 → 草稿（视频+配音+BGM 三轨，全部对齐铺满）
- 📝 **剪映官方识别字幕**：打开草稿 → 识别字幕 → 爆款黄字样式，100% 同步
- 🗣️ **克隆音色**：剪映「换音色 → 克隆音色 → 张总专属」（用户已克隆）
- 🎨 **智能包装**：剪映官方科技风智能包装（花字/特效/音效自动匹配）
- 📦 **批量生产**：一次 N 条文案 → N 个独立草稿（9.9 批量版核心）
- 🔒 **质量门禁**：BGM 音量区间 / 字幕存在性 / 对齐容差自动检查
- 🩺 **只读诊断 + 导出预检**：doctor / export_precheck，导出前拦截问题

## 使用方式（傻瓜式）

> **"帮我做个口播视频，主题是 XXX，素材用 XXX"**

豆包自动完成：写文案 → 生成配音 → 引擎写草稿 → 受控窗口开剪映 → 官方识别字幕 → 爆款样式 → 智能包装 → 放草稿箱/导出。

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
├── src/                  # 统一入口 + 引擎 + 配置（核心，路径全参数化）
│   ├── factory.py        #    CLI 门面：produce/precheck/doctor/drafts/config
│   ├── engine_v2.py      #    引擎：pyJianYingDraft 写草稿 + 全部稳妥性设计
│   ├── factory_config.py #    配置加载（默认值→JSON→环境变量）
│   └── factory_config.json
├── scripts/              # 技能脚本（GUI 操作 / 预检 / 诊断 / 批量）
│   ├── export_precheck.py  #  导出预检（加密降级 + 质量门禁）
│   ├── doctor.py           #  只读环境诊断
│   ├── operator_executor.py#  受控窗口确定性执行器（剪映GUI节点）
│   ├── batch_generator.py  #  批量生成器
│   └── ...
├── references/           # 方法论 / 剪映 GUI 节点 SOP
├── tests/                # 回归测试（13 项，覆盖引擎+预检）
└── README.md / SKILL.md / LICENSE
```

## 开源协议

MIT License — 免费使用、修改、分发。商业使用请支持正版剪映。

---

Made with 剪映工厂 · 让每个人都能批量生产专业视频
