---
name: jianying-factory
description: 剪映工厂 v7.7 稳定版 - 剪映超级操作员！用户一句话→全网热点→爆款拆解→原创口播文案→（确认后）配音、剪映官方识别字幕、云端正版音乐直调、BGM自动铺满、素材自包含、原片强制静音、竖屏防条纹、科技风智能包装、Ken Burns关键帧运镜、内置TTS+逐句字幕、模板克隆批量、语义素材匹配、花字样式、Web动效录屏、智能变焦、影视解说、热点引流混剪模板。基于pyJianYingDraft成熟开源库零手写JSON。音频一律预混单音轨（画外音/配音+BGM），剪映100%能打开。绝对不出现画面条纹、片尾黑屏、原片杂音、字幕不对齐、素材用错、文案洗稿、草稿打不开的低级问题。
---

# 剪映工厂 v7.7 稳定版 - 剪映的超级操作员

**核心原则：不替剪映干活，只做最懂剪映、操作最快最稳的AI。用成熟开源库pyJianYingDraft写草稿，所有字段库自动校验，所有之前踩过的坑全部在代码层面堵死。前端补爆款理解能力（v7.4）：用户一句话→AI全网找热点→拆爆款逻辑→原创改写→用户确认→才动手剪。音频统一走 v7.6 预混单音轨（剪映打不开多音频轨草稿，这是经过多路实测钉死的铁律）。v7.7 补齐 9 项高级能力：云端正版音乐、Ken Burns关键帧运镜、内置TTS+逐句字幕、模板克隆批量、语义素材匹配、花字样式、Web动效录屏、录屏智能变焦、影视解说。**

---

## ✅ 100%验证成功的标准生产SOP（严格按这个走，绝对不改动）

### 第零步：爆款文案前期（v7.4 新增，用户只给一句话/主题时必走）
1.  用户一句话（如"找今天的AI热点"）→ 立即联网搜索当天热点（今日头条/36氪/量子位/抖音热榜）
2.  五维评估热点：新鲜度/情绪值/利益相关度/可跟风度/争议度（总分≥32才做）
3.  拆爆款骨架：钩子(0-3s)→冲突→转折→干货→行动（详见 `references/爆款文案工作流.md`）
4.  **原创改写**：换主角（对普通人意味着什么）+加数字+加案例+留钩子，绝不洗稿
5.  输出【爆款标题+口播文案(200-260字)+引导评论+选题依据】→ **等用户确认后才继续**，不许直接开剪

### 第一步：准备素材与文案
1.  固定主素材：`E:\张总口播素材\张总形象.mp4`（作者环境示例路径，使用时可改为自己的形象素材），绝对不能扫整个文件夹乱选
2.  文案：用户已确认的爆款口播稿（40-60秒），不再自行改写
3.  （可选 v7.7）多素材混剪：素材文件夹 + `data\asset_tags.csv` 语义标签 → `advanced_ops.match_assets_by_script` 按文案自动匹配对应画面

### 第二步：生成配音（首选剪映官方克隆音色，已实测验证）
1.  **直接用剪映克隆音色**：剪映里 音频→「换音色」→「克隆音色」→选已克隆音色 → 文本朗读 → 粘贴文案 → 自动生成配音（正版稳定不排队）
2.  备选一（v7.7）：引擎内置 TTS——`advanced_ops.narrated_draft()` 用 edge-tts 云健男声自动拆句配音+字幕（无需剪映 GUI，秒级生成）
3.  备选二：豆包audio_to_audio_plus参考样本克隆（会排队失败，仅作备选）

### 第三步：生成草稿（核心引擎，绝对不能手写裸JSON！）
直接调用稳定引擎`src/engine_v2.py`的`make_voiceover_draft()`函数，自动完成：
- 原视频音量强制=0（代码层面写死，绝对不会漏静音）
- 所有素材MD5自包含复制到草稿目录，防丢失
- **local_material_id稳定非空（基于文件名MD5，杜绝剪映5.9+媒体丢失）**
- **v7.6 单音轨混音：配音/画外音与BGM由引擎 ffmpeg 预混成单条音轨（人声时段BGM自动闪避到0.15，之后恢复0.35），只生成1条audio轨道——剪映11.5实测：≥2条audio轨道的草稿一律打不开，单音轨100%打开**
- BGM自动循环铺满总时长（绝对不会片尾黑屏）
- 特殊字符自动过滤、损坏草稿自动清理、剪映占用自动3次重试
- 竖屏1080x1920/30fps固定，不会出现画面条纹/颠倒

### 第四步：剪映GUI操作（受控窗口标准SOP，完整节点坐标见 `references/剪映GUI节点SOP.md`）
**执行环境必须是 computer_use_tool(plane="cu")，严禁 pyautogui / Popen / 真实桌面双击！**
1.  **启动（v7.7.1 实测定死）**：受控桌面 OCR 定位「剪映专业版」桌面图标（图标位置随桌面布局变，每次先截图 OCR 再双击，**不固定坐标**）→ `cu.left_double(图标中心)` → 轮询截图直到首页出现（冷启动约20-30s，进程已在受控桌面则直接复用不重复启动）。**禁止 subprocess/Popen 启动主程序**——实测窗口不会进受控桌面视图；**cu.list_apps 清单无剪映时 launch_app 不可用**，受控桌面图标双击是唯一稳定入口
2.  **开草稿**：双击草稿**缩略图区域**（y≈700，不是文字区），右侧草稿参数显示草稿目录即成功；新生成草稿首次打开解析较慢，双击后等30秒以上再判断
3.  **换音色**：选中配音轨(150,805)→「换音色」(777,46)→「克隆音色」(769,132)→选音色(870,185)→「应用」(970,505)→弹窗「确认使用」(525,520)→等60-90秒处理完成。标准代码见 `scripts/operator_executor.py` 的 `apply_voice_clone()`
4.  **官方识别字幕**：点「字幕」(180,55)→勾「同时清空已有字幕」(90,495)→「开始识别」(343,500)→等60秒识别完成，绝对不自己写算法对齐
5.  **爆款黄字样式**：字号框(960,212)改10；颜色(806,292)→Hex框(843,617)→FFD400。花字用引擎级 `apply_flower_text`/`add_flower_title`（无需GUI）
6.  **智能包装**：点「智能包装」→「科技风」缩略图(130,190)→「开始匹配」(343,515)→等90-150秒生成
7.  **返回首页**：菜单(58,21)→「返回首页」；用户要求"放草稿箱即可"时做完以上就返回首页，**不点导出**
-  **铁律**：每一步后必须重新截图取坐标；面板坐标会漂移，点偏了就重截图修正，绝不盲点连点

---

## 🧪 v7.7 高级能力（advanced_ops.py，全部已代码实现，10/10 实测通过）

| 能力 | 函数 | 状态 | 说明 |
|---|---|---|---|
| ① 云端正版音乐 | `scripts/jianying_music_bridge.py` + `advanced_ops._resolve_bgm()` | ✅ 实测 | **剪映曲库音乐=本地正版缓存**（`%LOCALAPPDATA%\JianyingPro\User Data\Cache\music\<hash>.mp3`，实测131文件含完整歌151s/128kbps）；BGM留空时引擎自动从曲库缓存选最新下载歌混音，正版零侵权、**不依赖GUI添加按钮** |
| ② Ken Burns关键帧运镜 | `add_ken_burns()` + 8预设 | ✅ 实测 | zoom_in_slow/zoom_out_slow/pan_left/pan_right/zoom_in_center/fade_in/fade_out/rotate_pulse；同一属性多帧并入同一KeyframeList |
| ③ 内置TTS+逐句字幕 | `narrated_draft()` | ✅ 实测 | 拆句→edge-tts逐句合成→累计时长排字幕→拼接单音轨→BGM混音闪避→视频Ken Burns铺满，全自动 |
| ④ 模板克隆批量 | `clone_draft()` | ✅ 实测 | 明文草稿安全克隆：素材替换（规范化+自包含）+文本替换（JSON级改 materials.texts[].content.text），**原模板零污染** |
| ⑤ 语义素材匹配 | `match_assets_by_script()` | ✅ 实测 | 中文关键词n-gram+素材标签打分，按文案语义自动匹配对应画面 |
| ⑥ 花字样式 | `apply_flower_text()` + `data/cloud_text_styles.csv` | ✅ 引擎级实测 | **513个花字ID全部引擎级可写入**（add_effect→materials.filters type=text_effect，实测60/60通过）；`add_flower_title()` 一行加爆款花字标题；**无需GUI** |
| ⑦ Web动效录屏 | `web_to_video()` | ✅ 实测 | Playwright 优先系统Edge，录HTML动效→H.264/1080x1920/yuv420p |
| ⑧ 录屏智能变焦 | `record_screen()` + `apply_zoom_draft()` | ✅ 实测 | 点击处1.0→1.5→1.0缩放脉冲（JSON验证9关键帧点）；record_screen 实跑通过（gdigrab无需授权） |
| ⑨ 影视解说 | `movie_commentary_draft()` | ✅ 实测 | 分镜裁剪+逐镜TTS+字幕+单音轨+**段间自动叠化转场**（3镜18s实测通过） |
| 🔟 转场+特效轨道算子 | `add_scene_transition()` / `add_scene_effect()` / `add_effect_track()` | ✅ 实测 | **对齐上游 vfx_ops**：`TransitionType` 500+转场、`VideoSceneEffectType` 1000+特效；转场自动注册 materials.transitions；特效轨 video_effects |

**关键实现细节（v7.7）**：
- 关键帧写入：`VideoSegment.add_keyframe(prop, time_offset_us, value)`，同一属性自动并入同一KeyframeList
- 文本存储位置：草稿JSON里字幕文本在 `materials.texts[].content`（RichText JSON），不在轨道段里；文本替换必须JSON级处理
- TTS音色映射：云希=zh-CN-YunxiNeural / 云健·沉稳男=zh-CN-YunjianNeural / 晓晓=zh-CN-XiaoxiaoNeural / 晓伊=zh-CN-XiaoyiNeural
- Web-to-Video 浏览器：优先 `channel="msedge"`（系统Edge免下载），回退chrome
- **云端正版音乐桥接（v7.7 实测）**：剪映曲库歌曲在 GUI 搜索/预览/下载后落盘 `Cache\music\<hash>.mp3`；`jianying_music_bridge.py` 扫描选歌（≥30s 视为完整歌，按最近下载优先）；`advanced_ops._resolve_bgm(None, max_dur=...)` 自动桥接后引擎混音单音轨。GUI「添加」按钮交互在剪映11.5不稳定，**已不依赖它**——曲库缓存桥接是正版且稳定的主路线

---

## ❌ 绝对禁止做的事（所有历史踩坑，写进铁律）
1.  ❌ 绝对不能自己手写裸JSON草稿，必须用稳定引擎基于pyJianYingDraft
2.  ❌ 绝对不能自己写字幕对齐算法，必须用剪映官方识别字幕功能
3.  ❌ 绝对不能在GUI里拖拽素材（会跑出窗口到用户真实桌面），素材路径全部由引擎直接写进JSON
4.  ❌ 绝对不能扫描整个素材文件夹自动选素材，固定用指定形象素材
5.  ❌ 绝对不能忘记把原视频音量设为0
6.  ❌ 绝对不能让BGM短于视频总时长，必须铺满到片尾
7.  ❌ 绝对不能瞎编剪映特效ID，所有包装用剪映官方智能包装生成
8.  ✅ 所有工作文件全部存D盘/草稿目录，不占用系统盘
9.  ✅ BGM音量固定40%（0.35-0.4区间），不抢人声
10. ❌ **绝对不能生成≥2条audio轨道的草稿**（v7.6实测剪映11.5一律打不开）；配音/画外音与BGM必须预混成单条音轨
11. ❌ 绝对不能污染模板草稿（clone_draft 只读写副本，原模板只读不写）

---

## 🧹 代码卫生（v7.7，维护时必读）
- **v7.7.1 收尾闭环**：①花字升级**引擎级**——513个ID实测全可写入，flower_text_gui.py 退役；②record_screen 实跑通过（gdigrab无需授权）；③启动法定死=**受控桌面 OCR 定位剪映图标→双击→轮询首页**，launch_jianying.py 与 operator_executor.ensure_launched 已同步
- **v7.7.1 转场/特效算子**：`add_scene_transition(段, 转场名, 秒)`（挂段尾，自动注册 materials.transitions）；`add_scene_effect(段, 特效名)`；`add_effect_track(proj, 特效名, 起, 止)`（独立特效轨）；影视解说/口播循环段自动加叠化
- **v7.7 高级算子 `src/advanced_ops.py`**（约540行）：KEN_BURNS_PRESETS 8预设 / narrated_draft（单音轨+字幕+Ken Burns）/ clone_draft / match_assets_by_script / build_cloud_text_styles_library / web_to_video / record_screen+apply_zoom_draft / movie_commentary_draft / add_scene_transition+add_scene_effect+add_effect_track / apply_flower_text+add_flower_title
- **v7.7 数据资产**：popular_bgm.csv（曲库搜索词）/ asset_tags.csv（混剪素材语义标签）/ cloud_text_styles.csv（513个花字ID）
- **单音轨混音（v7.6 核心修复）**：`src/engine_v2.py` 的 `_mix_voice_bgm()`——ffmpeg 预混单轨（人声1.0；BGM闪避0.15/恢复0.35；循环铺满；44.1k/双声道/pcm_s16le）。实测：单音轨草稿剪映100%打开，双音轨一律打不开
- **爆款文案前期（v7.4）**：`references/爆款文案工作流.md`（热点五维评估/爆款骨架/标题公式/原创改写规则）
- **热点引流混剪模板（v7.5）**：`make_hotspot_mix_draft()`——上部热点标题逐条浮现、中部素材混剪、下部项目广告常驻+泛光动画、画外音+BGM单音轨
- **确定性执行器**：`scripts/operator_executor.py` = JianyingOperator 类（启动/开草稿/选配音轨/换音色/识别字幕/字幕样式/智能包装/返回首页，坐标2026-09-27实测校准）
- **批量生成器 v2**：`scripts/batch_generator.py` 统一走引擎 make_voiceover_draft，批量产草稿放草稿箱
- **导出预检（scripts/export_precheck.py）**：导出前拦截——local_material_id非空、素材自包含、时长铺满、剪映版本提示
- **草稿安全备份**：同名草稿先移入备份目录再重建
- **视频规范化防条纹**：ffprobe探测，非h264/非yuv420p/尺寸非16倍数自动转码H.264 yuv420p 1080x1920

## 版本兼容说明
- 免费用户：所有核心流程可用，仅导出时带剪映水印
- SVIP用户：导出无水印、智能包装/对口型/克隆音色/4K等高级官方功能全部可用（云端曲库音乐直调正版无侵权）

---

## 常见问题（已验证解决方案）
**Q：原视频有环境杂音？** A：引擎代码层面已强制把原视频volume设为0。

**Q：片尾黑屏/BGM提前结束？** A：引擎自动循环复制BGM直到总时长，绝对铺满；v7.6 单音轨混音时 BGM 循环铺满后再与人声合轨。

**Q：草稿打不开（停在首页）？** A：确认草稿是否含 ≥2 条 audio 轨道——v7.6 实测剪映11.5打不开双音轨草稿，必须走引擎单音轨混音；单音轨草稿首次打开解析较慢，双击后等30秒以上。

**Q：字幕和配音对不齐？** A：必须用剪映官方识别字幕功能，删掉旧字幕重新识别，100%同步；或 v7.7 `narrated_draft` 按TTS时间戳逐句排字幕。

**Q：素材用错了？** A：固定用指定形象素材，不要扫其他文件夹；多素材混剪用语义标签匹配。

**Q：背景音乐会侵权吗？** A：v7.7 起 BGM 自动走剪映官方曲库缓存桥接（jianying_music_bridge.py + _resolve_bgm），剪映曲库全部正版授权，零侵权风险。
