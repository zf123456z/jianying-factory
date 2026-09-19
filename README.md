# 剪映工厂 (JianYing Factory)

> AI驱动的剪映专业版自动化剪辑技能——丢素材进去，出成片。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![CapCut](https://img.shields.io/badge/JianYingPro-10.x%2B-orange.svg)

## 这是什么

剪映工厂是一个开源的AI Agent技能，让AI直接操控你的剪映专业版完成视频剪辑。你不需要学剪映操作，只需要用自然语言说需求，AI全自动完成：

- 🎤 **口播一键成片**：一段文案 → 带字幕配乐的完整视频
- 📦 **批量生产**：一次挂50条文案，夜里自动导出50条
- ✂️ **智能剪辑**：自动去废镜头、AI选B-roll、智能字幕
- 🎨 **模板工厂**：一套模板，批量换N个客户的素材
- 🚀 **无头导出**：命令行直接导出MP4，不需要开界面

## 为什么比其他剪映自动化更强

| 特性 | 其他工具 | 剪映工厂 |
|---|---|---|
| 草稿格式 | 只支持明文JSON | 明文直读 + 加密走GUI双通道 |
| 剪映升级 | 一改格式就崩 | 自动降级，永不卡死 |
| 口播场景 | 通用剪辑 | 专为口播视频优化的完整流水线 |
| 批量能力 | 手动跑脚本 | 队列式夜间批量导出 |
| 使用方式 | 写Python代码 | 自然语言说需求 |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zf123456z/jianying-factory.git

# 2. 放入技能目录
cp -r jianying-factory ~/.agents/skills/

# 3. 重启AI对话，直接说：
# "用剪映工厂帮我做个60秒口播视频，文案如下：..."
```

## 核心能力

### 口播一键成片
```
文案.txt + 素材文件夹 → 完整口播视频.mp4
```
- TTS自动配音
- 自动分镜匹配画面
- 智能字幕（自动识别+错别字修正）
- 自动铺BGM卡点
- 片头片尾自动加

### 批量生产
```python
from voiceover_builder import batch_render

# 一次渲染10条视频
batch_render(
    scripts=["文案1.txt", "文案2.txt", ...],
    assets_dir="./素材/",
    output_dir="./成片/"
)
```

### 无头导出
```bash
# 不打开剪映界面，直接导出
python scripts/auto_exporter.py "项目名" output.mp4 --res 1080 --fps 30
```

## 系统要求

- Windows 10/11
- 剪映专业版 10.x 或 11.x
- Python 3.8+
- 支持桌面自动化的AI环境（豆包/Claude/Coze等）

## 开源协议

MIT License — 免费使用、修改、分发。

## 参与贡献

欢迎提交Issue和PR！特别是：
- 新的剪映版本适配
- 行业模板库（餐饮/服装/教育...）
- 更多导出格式支持

---

Made with 剪映工厂 · 让每个人都能批量生产专业视频
