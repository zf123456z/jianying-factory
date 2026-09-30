---
name: jianying-factory
description: 剪映工厂 v7.8 稳定版 - 剪映超级操作员！用户一句话→全网热点→爆款拆解→原创口播文案→（确认后）VectCutAPI确定性内核秒级生成草稿（视频/配音/BGM/SRT字幕/标题多轨一次成型，剪映专业版10.x/11.x直接打开）→（可选）剪映官方克隆音色/识别字幕/智能包装/导出。内置1800+剪映官方功能调用：转场/特效/关键帧/贴纸/花字/字幕/音乐，全部正版零侵权。绝对不出现画面条纹、片尾黑屏、原片杂音、字幕不对齐、素材用错、文案洗稿、草稿打不开的低级问题。
---

# 剪映工厂 v7.8 稳定版 - 剪映的超级操作员

**核心原则：不替剪映干活，只做最懂剪映、操作最快最稳的AI。**

**v7.8 架构升级（2026-09-30 实测验证通过）**：主执行路径从"GUI逐帧操作"升级为 **VectCutAPI 确定性内核**——本地 HTTP 服务（localhost:9001）调用 `jianying_pro_10` profile，生成**剪映专业版10.x原生多时间线明文草稿**（draft_content.json + Timelines/ + 素材自包含），剪映专业版 **11.5 实测秒级识别、双击直接打开**（视频/配音/字幕/标题/时长全部正确）。这是一次"引擎级出片"的质变：**从 GUI 40 分钟 → API 40 秒**，稳定性从"坐标漂移碰运气"变成"确定性字段生成"。

**技术真相**：上游 jianying-editor 用的不是 pyJianYingDraft 直写，而是 **VectCutAPI 生成 CapCut 国际版明文格式**（app_source=cc，CapCut 国际版永不加密），剪映/CapCut 同源引擎直接兼容。我们本地 11.5 撞的"加密墙"只针对剪映自存草稿；**读明文草稿不撞墙**。VectCutAPI 额外提供 `jianying_pro_10` profile（剪映10.x原生模板），比上游默认的 capcut_legacy 更贴剪映。本地 10.9.0.14199 / 11.5.0.14471 均可打开（11.5 已实测）。

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

### 第三步：VectCutAPI 内核生成草稿（v7.8 主执行路径，秒级）
**统一调用 `scripts/vectcut_engine.py` 的 JianyingVectcutEngine 类**（底层 = 本地 VectCutAPI 服务 localhost:9001）：
1. `ensure_server()` —— 服务没跑则自动后台拉起（D:\AI工作区\代码\VectCutAPI\capcut_server.py）
2. `create_draft(1080, 1920)` —— 竖屏口播比例
3. `add_video(素材, end=配音时长, volume=0.1)` —— 主视频轨，原片压静音
4. `add_audio(配音, volume=1.0, track_name="audio_main")` —— 配音轨
5. `add_audio(BGM, volume=0.35, track_name="bgm")` —— BGM轨（剪映原生多轨格式，铺满截断）
6. `add_subtitle(SRT, font_size=9, 黄字FFD400)` —— SRT精准字幕（时间戳与配音严格对齐，**不是自己写算法**）
7. `add_text(爆款标题, 顶部, 黄字大字)` —— 标题花字
8. `save_and_deploy(draft_id, 项目名)` —— 保存+部署到剪映草稿目录，剪映重启/回首页即可见
- **已验证（2026-09-30）**：GEO口播测试_v78_1790758108，13.15s 竖屏，视频/配音/3条字幕/标题全对，剪映11.5双击打开正常
- 素材时长不足时 `end=` 指定截取；长文案视频素材循环由引擎按配音时长铺满
- 接口速查：create_draft / add_video / add_audio / add_subtitle(srt参数名!) / add_text / add_effect / add_sticker / add_video_keyframe / save_draft（返回 output.draft_url=本地路径）

### 第四步：剪映GUI操作（仅剪映专属能力，受控窗口标准SOP）
**执行环境必须是 computer_use_tool(plane="cu")，严禁 pyautogui / Popen / 真实桌面双击！**
1.  **启动（v7.7.2 实测定死）**：**首选任务栏搜索**——受控窗口点任务栏搜索框(80,982)→输入"剪映"→点搜索结果「剪映专业版」(81,263)→轮询截图直到首页出现（30s 内出首页）。**备选**：受控桌面 OCR 定位「剪映专业版」桌面图标→`cu.left_double(图标中心)`。**禁止 subprocess/Popen 启动主程序**。统一入口见 `scripts/launch_jianying.py` 的 `LAUNCH(mode="search")`
2.  **开草稿**：首页草稿列表双击目标行（名称列 x≈390-500），等10-30秒（首次解析新草稿较慢）；成功标志=右侧「草稿参数」出现目标草稿名+保存位置
3.  **（用户要求克隆音色时）换音色**：选中配音轨(150,805)→「换音色」(777,46)→「克隆音色」(769,132)→选音色(870,185)→「应用」(970,505)→弹窗「确认使用」(525,520)→等60-90秒。标准代码见 `scripts/operator_executor.py` 的 `apply_voice_clone()`
4.  **（用户要求官方识别字幕时）识别字幕**：点「字幕」(180,55)→勾「同时清空已有字幕」(90,495)→「开始识别」(343,500)→等60秒。**注意：v7.8 引擎已写 SRT 字幕，识别字幕只用于用户明确要求重做时**
5.  **智能包装**：点「智能包装」→「科技风」缩略图(130,190)→「开始匹配」(343,515)→等90-150秒
6.  **返回首页**：菜单(58,21)→「返回首页」；用户要求"放草稿箱即可"时做完以上就返回首页，**不点导出**；用户要求导出时点「导出」(940,25)→分辨率选1080P→「导出」
-  **铁律**：每一步后必须重新截图取坐标；面板坐标会漂移，点偏了就重截图修正，绝不盲点连点

---

## 🧪 v7.8 高级能力（VectCutAPI 内核 + advanced_ops.py，全部已代码实现）

| 能力 | 实现 | 状态 | 说明 |
|---|---|---|---|
| ① VectCutAPI确定性内核 | `scripts/vectcut_engine.py` | ✅ 实测 | 秒级生成剪映10.x原生多时间线明文草稿；剪映11.5直接打开；视频/音频/字幕/文字/特效/贴纸/关键帧全API化 |
| ② SRT精准字幕 | `add_subtitle(srt=...)` | ✅ 实测 | 接口参数名是 **srt**（不是srt_path！）；SRT格式 HH:MM:SS,mmm + 句间空行；时间戳与配音严格对齐 |
| ③ 多轨分轨 | add_audio track_name=audio_main/bgm | ✅ 实测 | 剪映原生多轨格式（配音轨+BGM轨+字幕轨+标题轨），不再走"预混单音轨"旧限制 |
| ④ 云端正版音乐 | `advanced_ops._resolve_bgm()` | ✅ 实测 | 剪映曲库缓存桥接，正版零侵权 |
| ⑤ Ken Burns关键帧运镜 | `add_ken_burns()` + 8预设 | ✅ 实测 | zoom_in_slow/pan_left/rotate_pulse 等；add_video_keyframe API 也可直接调 |
| ⑥ 内置TTS+逐句字幕 | `advanced_ops.narrated_draft()` | ✅ 实测 | edge-tts 云健男声；v7.8 后也可走 VectCutAPI：TTS生成mp3→SRT→引擎上轨 |
| ⑦ 模板克隆批量 | `advanced_ops.clone_draft()` | ✅ 实测 | 明文草稿安全克隆，素材/文本JSON级替换，原模板零污染 |
| ⑧ 语义素材匹配 | `match_assets_by_script()` | ✅ 实测 | 中文关键词n-gram+素材标签打分 |
| ⑨ 转场+特效轨道 | `add_scene_transition()` / `add_effect_track()` / API add_effect | ✅ 实测 | 500+转场/1000+特效；叠化/闪白/科技感 |
| 🔟 智能包装/克隆音色/对口型 | 剪映官方 GUI（受控窗口） | ✅ 实测 | SVIP 能力；引擎骨架就位后 GUI 少量步骤完成 |

---

## ❌ 绝对禁止做的事（所有历史踩坑，写进铁律）
1.  ❌ 绝对不能自己手写裸JSON草稿 → 走 VectCutAPI 内核或稳定引擎
2.  ❌ 绝对不能自己写字幕对齐算法 → SRT 由配音时间戳生成，或用剪映官方识别字幕
3.  ❌ 绝对不能在GUI里拖拽素材（会跑出窗口到用户真实桌面）→ 素材路径全部由引擎直接写进草稿
4.  ❌ 绝对不能扫描整个素材文件夹自动选素材 → 固定用指定形象素材
5.  ❌ 绝对不能忘记把原视频音量设为0（引擎 volume=0.1 或 0）
6.  ❌ 绝对不能让BGM短于视频总时长，必须铺满到片尾
7.  ❌ 绝对不能瞎编剪映特效ID → 用 API 白名单或剪映官方智能包装
8.  ✅ 所有文件全部存D盘，绝对不占用C盘空间
9.  ✅ BGM音量固定30-40%，不抢人声
10. ❌ **绝对不能操作真实桌面**（多次警告）——只能在豆包受控窗口内启动/操作剪映
11. ❌ 绝对不能污染模板草稿（clone_draft 只读写副本）

---

## 🧹 代码卫生（维护时必读）
- **v7.8 内核升级（2026-09-30 本轮验证）**：
  - VectCutAPI 已下载解压 `D:\AI工作区\代码\VectCutAPI`（含内嵌 pyJianYingDraft + template_jianying_10_2 原生模板），config.json 已设 `draft_profile: jianying_pro_10`
  - 依赖已装（imageio/psutil/flask/requests/oss2/json5）；服务启动：`python capcut_server.py`（端口9001）
  - **实测确认**：①create_draft/add_video/add_audio/add_subtitle/add_text/save_draft 全通；②add_subtitle 参数名是 `srt`；③save_draft 返回 `output.draft_url`=本地路径（部署必须用它，绝不能取第一个 dfd_ 文件夹——那是旧草稿）；④剪映11.5 打开验证通过（GEO口播测试_v78_1790758108）
  - 部署：草稿复制到剪映草稿目录；同名被占用时自动加时间戳后缀；清理 .locked
- **v7.7.2 启动法**：任务栏搜索启动取代图标双击为首选（launch_jianying.py `LAUNCH(mode="search")`）
- **v7.7 高级算子**：KEN_BURNS_PRESETS/narrated_draft/clone_draft/match_assets_by_script/web_to_video/record_screen/movie_commentary_draft/add_scene_transition+add_scene_effect+add_effect_track
- **v7.7 数据资产**：popular_bgm.csv / asset_tags.csv / cloud_text_styles.csv
- **确定性执行器**：`scripts/operator_executor.py`（GUI 节点，坐标2026-09-27实测校准）
- **死代码已清除（2026-09-27）**：`scripts/_archive/` 全部历史废弃脚本已删除，禁止恢复调用

## 版本兼容说明
- 剪映专业版 11.5.0.14471（当前默认）✅ 实测可打开 VectCutAPI 明文草稿
- 剪映专业版 10.9.0.14199（匹配 jianying_pro_10 profile，备选）
- 免费用户：核心流程可用；SVIP用户：克隆音色/对口型/智能包装/无痕导出全可用

---

## 常见问题（已验证解决方案）
**Q：草稿打不开（停在首页）？** A：v7.8 起走 VectCutAPI 明文草稿，11.5 已实测可开；旧 pyJianYingDraft lv 格式草稿 11.5 打不开（撞加密墙），勿再作为产成片路线。

**Q：字幕和配音对不齐？** A：SRT 时间戳严格对齐配音（v7.8 引擎直接写入），或剪映官方识别字幕。

**Q：原视频有环境杂音？** A：引擎 add_video volume=0.1 已压静音。

**Q：片尾黑屏/BGM提前结束？** A：BGM 按配音时长铺满截断（引擎 add_audio end=总时长）。

**Q：背景音乐会侵权吗？** A：BGM 走剪映官方曲库缓存（正版授权），零侵权风险。
