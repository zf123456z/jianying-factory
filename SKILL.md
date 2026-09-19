---
name: jianying-factory
description: "剪映工厂——AI驱动的剪映专业版自动化剪辑技能。当用户需要用剪映自动剪辑视频、批量成片、口播视频制作、自动加字幕、批量导出、模板替换、AI选B-roll、TTS配音时触发。覆盖场景：口播一键成片（文案进→成片出）、批量视频生产（一次N条）、自动去废镜头+智能字幕、模板克隆批量换素材、无头导出MP4。支持剪映草稿文件直写和GUI双通道操作，兼容加密/明文两种草稿格式。用户提到'剪映工厂''自动剪辑''批量成片''口播视频''自动字幕''一键成片'时必须触发。"
---

# 剪映工厂 (JianYing Factory)

AI驱动的剪映专业版自动化剪辑流水线。丢素材进去，出成片。

## 核心理念

不是教你怎么用剪映，而是让AI替你操作剪映。你说需求，AI全自动完成：
- 启动剪映 → 导入素材 → 剪辑 → 加字幕 → 配乐 → 导出

## 双通道架构（核心优势）

剪映草稿有两种格式，本技能自动选择最佳通道：

| 通道 | 适用场景 | 速度 | 说明 |
|---|---|---|---|
| **草稿文件通道** | 明文草稿（v5.9+ draft_content.json可读） | 极快 | 直接读写JSON，无头操作 |
| **GUI通道** | 加密草稿/任何版本 | 稳定 | 通过桌面控制操作剪映界面 |

自动检测草稿格式，明文走文件通道求快，加密走GUI通道求稳。永不被剪映版本升级卡死。

## 核心能力

### 1. 口播一键成片（主打场景）
输入：一段口播文案 + 素材文件夹
输出：带字幕、配乐、B-roll的完整口播视频

流程：文案→TTS配音→自动分镜→匹配素材→智能字幕→铺BGM→导出

### 2. 批量视频生产
- 一次挂N条文案，自动排队生成
- 夜间批量导出，早上拿成品
- 模板克隆+批量换素材：一套模板，N个客户

### 3. 智能剪辑
- 自动识别废镜头（卡壳/口误/静音段）
- AI选B-roll：根据语义自动匹配画面
- 智能字幕：自动生成+错别字修正
- 自动铺BGM：根据节奏卡点

### 4. 素材管理
- 自动定位剪映安装目录和草稿路径
- 草稿列表查询、项目ID提取
- 素材库索引和搜索

## 使用流程

### 第一步：定位剪映
```bash
python scripts/find_jianying.py
```
自动检测剪映版本、安装路径、草稿目录。

### 第二步：操作草稿
```bash
# 查看草稿列表
python scripts/draft_cli.py list

# 读取草稿信息
python scripts/draft_cli.py info --name "草稿名"

# 无头导出
python scripts/auto_exporter.py "草稿名" output.mp4 --res 1080 --fps 30
```

### 第三步：口播成片
```bash
# 文案→成片（完整流水线）
python scripts/voiceover_builder.py --script "文案.txt" --assets "./素材/" --output "成片.mp4"
```

## 文件结构

```
jianying-factory/
├── SKILL.md                      # 本文件
├── README.md                     # 项目说明（GitHub展示）
├── LICENSE                       # MIT开源协议
├── scripts/
│   ├── find_jianying.py          # 定位剪映安装/草稿
│   ├── draft_cli.py              # 草稿查询与操作
│   ├── auto_exporter.py          # 无头批量导出
│   └── voiceover_builder.py      # 口播一键成片
└── references/
    ├── cli-guide.md              # 剪映官方CLI参考
    ├── ui-guide.md               # GUI操作指南
    └── voiceover-workflow.md     # 口播成片完整工作流
```

## 依赖与要求

- 剪映专业版 Windows（10.x / 11.x）
- Python 3.8+
- 桌面控制能力（用于GUI通道）
- 高级功能（数字人/TTS）需剪映SVIP

## 安装

1. 克隆仓库：`git clone https://github.com/zf123456z/jianying-factory.git`
2. 将 `jianying-factory` 文件夹放入你的技能目录
3. 重启AI对话，技能自动生效
4. 直接说："用剪映工厂帮我做个口播视频"

## 注意事项

- 首次运行自动检测剪映环境
- 操作前自动备份草稿
- 加密草稿自动切换GUI通道
- 导出前确认分辨率/帧率/格式
