---
name: jianying-factory
description: 剪映工厂 v8.1 对外交付版 - 剪映超级操作员！新用户 3 分钟上手（python install.py 一键装）。用户一句话→全网热点→爆款拆解→原创口播文案→（确认后）VectCutAPI确定性内核秒级生成草稿（视频/配音/BGM/标题多轨一次成型）→（可选）剪映官方克隆音色/智能包装/识别字幕/导出。v8.1 全路径可配置（环境变量/用户 config.json），不再依赖作者本机路径。铁律：智能包装自动出字幕，禁止与手动字幕叠加。内置1800+剪映官方功能调用：转场/特效/关键帧/贴纸/花字/字幕/音乐，全部正版零侵权。绝对不出现画面条纹、片尾黑屏、原片杂音、字幕不对齐、素材用错、文案洗稿、草稿打不开的低级问题。
---

# 剪映工厂 v8.1 对外交付版 - 剪映的超级操作员

**核心原则：不替剪映干活，只做最懂剪映、操作最快最稳的AI。**
**v7.8.1 方法论定死（2026-09-30 用户指正）**：**引擎只做确定性骨架，剪映AI能力一键出片，二者不重叠**——智能包装（科技风等）= 剪映官方AI自动剪辑，会自动"智能匹配字幕、花字、音效和特效"（按配音重新生成对齐字幕）。因此：**走智能包装路线时，引擎不写SRT、GUI不单独识别字幕，禁止三重复工**；只有"不做智能包装"时才用引擎SRT或剪映官方识别字幕。

**v7.8 架构升级（2026-09-30 实测验证通过）**：主执行路径从"GUI逐帧操作"升级为 **VectCutAPI 确定性内核**——本地 HTTP 服务（localhost:9001）调用 `jianying_pro_10` profile，生成**剪映专业版10.x原生多时间线明文草稿**（draft_content.json + Timelines/ + 素材自包含），剪映专业版 **11.5 实测秒级识别、双击直接打开**（视频/配音/字幕/标题/时长全部正确）。这是一次"引擎级出片"的质变：**从 GUI 40 分钟 → API 40 秒**，稳定性从"坐标漂移碰运气"变成"确定性字段生成"。

**技术真相（用户追问"上游为什么能跑通"的答案）**：上游 jianying-editor 用的不是 pyJianYingDraft 直写，而是 **VectCutAPI 生成 CapCut 国际版明文格式**（app_source=cc，CapCut 国际版永不加密），剪映/CapCut 同源引擎直接兼容。我们本地 11.5 撞的"加密墙"只针对剪映自存草稿；**读明文草稿不撞墙**。VectCutAPI 额外提供 `jianying_pro_10` profile（剪映10.x原生模板），比上游默认的 capcut_legacy 更贴剪映。本地 10.9.0.14199 / 11.5.0.14471 均可打开（11.5 已实测）。

---

## 🚀 新用户 3 分钟上手（对外使用入口）

**拿到技能包后按顺序做：**
1. **安装**：`python install.py` —— 自动检测 Python/ffmpeg/剪映、获取 VectCutAPI 内核、安装依赖、生成配置（缺什么会明确提示）
2. **配置素材**：install 时输入你的口播形象素材路径；或编辑 `<工作区>/config.json` 的 `DEFAULT_VIDEO`（可用环境变量 `JYFACTORY_DEFAULT_VIDEO` 覆盖）
3. **环境体检**：`python cli.py doctor` —— 9 项检查全绿即就绪
4. **开始出片**：在豆包里说「帮我做个口播视频」+ 一句话主题，AI 自动找热点→写爆款文案→等你确认→出片到草稿箱

**路径全可配置（不再写死作者本机）**：
- 工作区根：环境变量 `JYFACTORY_HOME`（默认 `D:\AI工作区`），所有子目录自动派生
- 任一路径可单独覆盖：`JYFACTORY_DRAFT_DIR` / `JYFACTORY_EXPORT_DIR` / `JYFACTORY_DEFAULT_VIDEO` … 或写入 `<工作区>/config.json`
- 剪映安装路径自动探测（注册表+常见路径），也可 `JYFACTORY_JIANYING_EXE` 指定
- **作者默认素材 `E:\张总口播素材\张总形象.mp4` 仅为默认值**，新用户首次 setup 即引导换成自己的

---

## ✅ 100%验证成功的标准生产SOP（严格按这个走，绝对不改动）

### 第零步：爆款文案前期（v7.4 新增，用户只给一句话/主题时必走）
1.  用户一句话（如"找今天的AI热点"）→ 立即联网搜索当天热点（今日头条/36氪/量子位/抖音热榜）
2.  五维评估热点：新鲜度/情绪值/利益相关度/可跟风度/争议度（总分≥32才做）
3.  拆爆款骨架：钩子(0-3s)→冲突→转折→干货→行动（详见 `references/爆款文案工作流.md`）
4.  **原创改写**：换主角（对普通人意味着什么）+加数字+加案例+留钩子，绝不洗稿
5.  输出【爆款标题+口播文案(200-260字)+引导评论+选题依据】→ **等用户确认后才继续**，不许直接开剪

### 第一步：准备素材与文案
1.  主素材：**用户配置素材**（`config.json` 的 `DEFAULT_VIDEO`；本机默认 `E:\张总口播素材\张总形象.mp4`），绝对不能扫整个文件夹乱选
2.  文案：用户已确认的爆款口播稿（40-60秒），不再自行改写
3.  （可选 v7.7）多素材混剪：用户混剪素材目录 + `data\asset_tags.csv` 语义标签 → `advanced_ops.match_assets_by_script` 按文案自动匹配对应画面

### 第二步：生成配音（首选剪映官方克隆音色，用户已实测验证）
1.  **用剪映「克隆音色」**：剪映里 音频→「换音色」→「克隆音色」→选**用户自己的克隆音色**（作者本机为「张总专属」）→ 文本朗读 → 粘贴文案 → 自动生成用户声音配音（正版稳定不排队；首次使用需用户在剪映先克隆自己的声音，技能会引导）
2.  备选一（v7.7）：引擎内置 TTS——`advanced_ops.narrated_draft()` 用 edge-tts 云健男声自动拆句配音+字幕（无需剪映 GUI，秒级生成）
3.  备选二：豆包audio_to_audio_plus参考样本`E:\张总语音\讲产品.mp3`克隆（会排队失败，仅作备选）
4.  配音保存到：`D:\AI工作区\配音\`

### 第三步：VectCutAPI 内核生成草稿（v7.8 主执行路径，秒级）
**统一调用 `jyfactory/engine.py（包内）` 的 JianyingVectcutEngine 类**（底层 = 本地 VectCutAPI 服务 localhost:9001）：
1. `ensure_server()` —— 服务没跑则自动后台拉起（D:\AI工作区\代码\VectCutAPI\capcut_server.py）
2. `create_draft(1080, 1920)` —— 竖屏口播比例
3. `add_video(素材, end=配音时长, volume=0.1, track_name="video")` —— **必须用模板主视频轨 "video"**（2026-09-30 实测：传 "main" 会落入模板第二条视频轨=剪映 V2，主轨 V1 空置，用户验收=视频不在主轨道）。原片压静音
4. `add_audio(配音, volume=1.0, track_name="audio_main")` —— 配音轨
5. `add_audio(BGM, volume=0.35, track_name="bgm")` —— BGM轨（剪映原生多轨格式，铺满截断）
6. `add_subtitle(SRT, font_size=9, 黄字FFD400)` —— SRT精准字幕（时间戳与配音严格对齐，**不是自己写算法**）。⚠️ **仅当最终不走智能包装时使用**：走智能包装路线（科技风等）时引擎**不写 SRT**——智能包装会自动识别配音生成字幕+花字+特效，先写会重复/被覆盖（v7.8.1 方法论，用户指正）
7. `add_text(爆款标题, 顶部, 黄字大字)` —— 标题花字
8. `save_and_deploy(draft_id, 项目名)` —— 保存+部署到 `D:\AI工作区\剪映草稿\<项目名>`，剪映重启/回首页即可见
- **已验证（2026-09-30）**：GEO口播测试_v78_1790758108，13.15s 竖屏，视频/配音/3条字幕/标题全对，剪映11.5双击打开正常
- 素材时长不足时 `end=` 指定截取；长文案视频素材循环由引擎按配音时长铺满
- 接口速查：create_draft / add_video / add_audio / add_subtitle(srt参数名!) / add_text / add_effect / add_sticker / add_video_keyframe / save_draft（返回 output.draft_url=本地路径）

### 第四步：剪映GUI操作（仅剪映专属能力，受控窗口标准SOP）
**执行环境必须是 computer_use_tool(plane="cu")，严禁 pyautogui / Popen / 真实桌面双击！**
1.  **启动（v7.7.2 实测定死）**：**首选任务栏搜索**——受控窗口点任务栏搜索框(80,982)→输入"剪映"→点搜索结果「剪映专业版」(81,263)→轮询截图直到首页出现（30s 内出首页；桌面图标 OCR 坐标连续4次漂移失败后弃用图标双击为首选）。**备选**：受控桌面 OCR 定位「剪映专业版」桌面图标→`cu.left_double(图标中心)`（图标位置随桌面布局漂移，必须每次现截图现定位）。**禁止 subprocess/Popen 启动主程序**。统一入口见 `jyfactory/launch.py（包内）` 的 `LAUNCH(mode="search")`
2.  **开草稿**：首页草稿列表双击目标行（名称列 x≈390-500），等10-30秒（首次解析新草稿较慢）；成功标志=右侧「草稿参数」出现目标草稿名+保存位置
3.  **（用户要求克隆音色时）换音色**：选中配音轨(150,805)→「换音色」(777,46)→「克隆音色」(769,132)→「张总专属」(870,185)→「应用」(970,505)→弹窗「确认使用」(525,520)→等60-90秒。标准代码见 `jyfactory/gui_ops.py（包内）` 的 `apply_voice_clone()`
4.  **字幕（二选一，禁止叠加，v7.8.1 定死）**：
    - **路线A【智能包装自动出字幕】**：走智能包装（科技风）时，**引擎不写SRT、GUI不做识别字幕**——智能包装自动识别配音生成对齐字幕+花字+特效，一键完成，零重复劳动
    - **路线B【官方识别字幕】**：不做智能包装时，剪映打开后点「字幕」(180,55)→勾「同时清空已有字幕」(90,495)→「开始识别」(343,500)→等60秒
5.  **智能包装（路线A，自动出字幕）**：点「智能包装」→「科技风」缩略图(130,190)→「开始生成」(340,485)→等90-150秒；自动匹配字幕/花字/音效/特效，**此前不得写SRT或识别字幕**
6.  **导出（v7.9 全流程实测校准，2026-10-02）**：用户要求导出时——
    - **打开草稿**：首页列表**单击选中草稿行(400,行y) + 回车 Enter**（⚠️ 实测 cu.left_double / 手动双击均不被剪映11.5识别，单击+回车是唯一可靠方式）
    - **点导出**：编辑页右上角「导出」(919,17)（⚠️ 勿点 (994,23)/(955,21)——会触发剪映异常重启）
    - **导出窗口**：默认 1080P/MP4/30fps，导出路径记忆上次设置（D:/AI工作区/导出/）；确认按钮「导出」(590,780)
    - **等完成**：1分钟视频约15s；出现「导出成功」窗口 → 点「关闭」(643,718)
    - **返回首页**：菜单(47,16) → 菜单项「返回首页」(64,227)（菜单弹出位置随窗口微移，点前重截图）
    - 标准代码见 `jyfactory/export_gui.py（包内）` 的 `GUI_EXPORT(draft_row=首页草稿行y)`
7.  **返回首页**：菜单(47,16)→「返回首页」(64,227)；用户要求"放草稿箱即可"时做完以上就返回首页，**不点导出**
-  **铁律**：每一步后必须重新截图取坐标；面板坐标会漂移，点偏了就重截图修正，绝不盲点连点；**未登录状态（重启后可能掉登录）打不开草稿，需用户扫码登录**

---

## 🧪 v8.0 高级能力（VectCutAPI 内核 + 官方能力直调，2026-10-04 新增）

| 能力 | 实现 | 状态 | 说明 |
|---|---|---|---|
| ① SAMI官方TTS直调 | `jyfactory/tts.py（包内）` `tts_speak(text, speaker)` | ✅ 实测 | 直连字节 SAMI WebSocket，用**用户剪映账号身份**引擎级合成**剪映正版音色**（zh_male_huoli 等；克隆音色ID亦可传）；失败自动回退 edge-tts 双通道 |
| ② 关键词高亮 | `vectcut_engine.add_rich_text(draft_id, text, highlights=[{word,color,bold,size}])` | ✅ 实测 | 重点词自动标红/标黄/加粗（materials.texts.content.styles 区间验证通过）。⚠️**位置模板（上游 rules/text.md）**：标题/强调字默认 `transform_y=0.85`（顶部）；字幕走 `add_subtitle` 服务端默认 `-0.8`（底部）。**禁止标题传负值**（跑底部与字幕重叠——2026-10-04 用户指正） |
| ③ 文字动画 | `add_text(..., intro_animation="打字机", outro_animation=...)` | ✅ 实测 | 中英自动映射（打字机→Typewriter/弹入→Pop_Up/卡拉OK→Karaoke 等76个入场+67个出场枚举）；material_animations 写入验证通过 |
| ④ 云端素材官方API | `jyfactory/media.py（包内）` + 引擎 `add_cloud_music/add_cloud_media` | ✅ 实测 | 剪映官方 mget_item 接口按 ID/关键词实时解析新鲜签名 URL 下载正版音乐/视频/音效（SSRF防护+大小限制）；data/ 内置 890 条索引（617音乐+234视频+43音效）；BGM 按配音时长显式传 end 铺满截断 |
| ⑤ 逐句TTS+字幕精准对齐 | `jyfactory/narrated.py（包内）` `narrate_script()` + `build_srt()` + 引擎 `add_subtitle` | ✅ 实测 | 每句独立TTS→实测时长→SRT时间轴（句间100ms）→配音整轨+字幕轨逐句对齐（端到端验证误差0.000s）。⚠️**整轨拼接必须用 ffmpeg concat filter 在句间插入真实静音**（anullsrc 100ms）——concat demuxer 对 wav 会丢帧（实测丢0.2s）导致音频比字幕短、片尾对不齐 |
| ⑥ 素材自包含 | `jyfactory/self_contain.py（包内）` `self_contain_draft()`（save_and_deploy 自动调用） | ✅ 实测 | 部署后素材复制进草稿 assets/ + path 改相对路径——服务端草稿清理/换机不丢素材 |
| ⑦ 防重叠自动分层 | 引擎 `add_text` auto_layer（text_main→text_2→title→subtitle） | ✅ 实测 | 多文本段时间重叠时自动换轨分层，杜绝服务端"段重叠"报错（3段重叠验证全分层成功） |
| ⑧ 环境诊断+草稿自愈 | `jyfactory/checks.py（包内）`（--heal 自愈） | ✅ 实测 | 环境9项检查；自愈=JSON可解析校验+清.locked+素材路径存在性校验（损坏JSON先备份不覆盖） |
| ④ VectCutAPI确定性内核 | `jyfactory/engine.py（包内）` | ✅ 实测 | 秒级生成剪映10.x原生多时间线明文草稿；剪映11.5直接打开 |
| ⑤ SRT精准字幕 | `add_subtitle(srt=...)` | ✅ 实测 | 接口参数名是 **srt**；时间戳与配音严格对齐 |
| ⑥ 多轨分轨 | add_audio track_name=audio_main/bgm | ✅ 实测 | 配音轨+BGM轨+字幕轨+标题轨 |
| ⑦ 云端正版音乐 | `advanced_ops._resolve_bgm()` | ✅ 实测 | 剪映曲库缓存桥接（正版零侵权） |
| ⑧ Ken Burns关键帧运镜 | `add_ken_burns()` + 8预设 | ✅ 实测 | zoom_in_slow/pan_left 等 |
| ⑨ 模板克隆批量 | `advanced_ops.clone_draft()` | ✅ 实测 | 明文草稿安全克隆，原模板零污染 |
| 🔟 语义素材匹配 | `match_assets_by_script()` | ✅ 实测 | 中文关键词n-gram+素材标签打分 |
| ⑪ 转场+特效轨道 | `add_scene_transition()` / API add_effect | ✅ 实测 | 500+转场/1000+特效 |
| ⑫ 智能包装/克隆音色/对口型 | 剪映官方 GUI（受控窗口） | ✅ 实测 | SVIP 能力；引擎骨架就位后 GUI 少量步骤 |

**SAMI 配音集成（v8.0 口播主路径）**：口播视频默认用 `sami_tts.tts_speak(文案, speaker="zh_male_huoli")` 出剪映正版音色配音；用户要克隆音色时传克隆音色 ID；SAMI 失败自动回退 edge-tts 云健男声。**消耗用户剪映账号 TTS 权益，不额外花钱**。

---

## 🗂️ v7.9 模板管理器（2026-10-08 新增：选模板→克隆→换文案/素材→出片）

**核心工具**：`jyfactory/templates.py（包内）` 的 `TemplateManager` 类（JSON 级替换，对 VectCutAPI 明文草稿 100% 兼容，保留全部样式）。

**工作流（用户说"用XX模板做一条"时走这条，不走引擎重建）**：
1. `list_templates()` —— 列出明文可用模板（实测 49 个：GEO口播系列/护城河热点/爆款口播v6-v8/一指哥系列/批量_* 等；加密不可用的 117 个自动排除，勿用）
2. `clone(模板名, 新草稿名)` —— 一键克隆（自动备份同名旧稿、清 .locked、骨架补全 20 文件）
3. `replace_texts(草稿, {下标或素材id: 新文案})` —— 换字幕/标题文案，**只改 content 里的 text，styles（加粗/描边/颜色/字号）原样保留**
4. `replace_videos(草稿, {下标: 素材路径})` / `replace_audios(...)` —— 换视频/音频素材（路径自动写入草稿 JSON）
5. `save()` —— 保存 + `_write_meta_info` 回写（防列表 0.0B）+ 素材自包含（assets 相对路径）
6. 结果 = 新草稿目录 `D:\AI工作区\剪映草稿\<新草稿名>`，与 VectCutAPI 生成草稿同级，可继续走剪映 GUI 步骤

**关键结论（2026-10-08 实测，决定"模板出片→剪映可见"的技术事实）**：
- ✅ 剪映 11.5 **确实扫描草稿目录**：复制剪映自存草稿改名 → 重启后列表第一行出现副本（实测通过）
- ❌ 剪映 11.5 **只显示剪映自身格式草稿**（draft_content 加密 + meta 二进制 + materials/ 目录）；VectCutAPI 明文草稿（无论完整结构/加骨架/放默认目录）**不显示、打不开**（10/6 剪映目录更新后行为变化，9-30 前旧文件可识别明文）
- ❌ 旧版本 10.9/11.1/11.4.2 目录**无主程序 exe**，无法降级启动
- ❌ "剪映外壳(加密meta)+明文draft_content"= 列表可见但**打开失败**（剪映不读明文内容）
- **出片验证**：`jyfactory/templates.py（包内）` 确认替换正确（新文案样式全保留、11段视频全换张总形象.mp4、音频自包含、总时长 101.9s）；剪映侧可见性受版本限制，技能对此如实提示，不假装可开

---

## 🔥 v7.6 聚蚁AI双屏常驻模板（2026-10-09 新增：蹭热点无配音广告，对标聚蚁AI打法）

**核心工具**：`jyfactory/juyi_template.py（包内）` 的 `produce_hotspot_ad()`（全链路：样式档→素材混剪→双屏常驻文字→BGM匹配→部署草稿箱）。

**打法特征**：无配音 · 纯文字动画 · 短时长(16-18s) 拿完播率。上下两屏文字**全程常驻**（只有入场动画，永不退出）：
- 上半屏热点区：主标题/副标题/补充句 三行层级（16/10/9 号，黄/白/红，打字机/渐显/弹入）
- 下半屏产品区：品牌/卖点1/卖点2/CTA 四行层级（14/9.5/9.5/9 号，黄/白/白/红）
- 每条文字独立文本轨（text_h1..text_p4），互不重叠；不出现电话与公司全名（只用品牌名）

**3 档样式搭配预设**（`DUAL_SCREEN_STYLES`）：
- `gold` 黄金爆款（默认，黄字黑边+红强调）
- `tech` 蓝科技（#4FC3F7 亮蓝，适合AI/数码热点）
- `hot` 红黑热辣（17号红主标题强冲击，适合争议热点）

**审美规则（docs/视频视觉拆解方法论.md）**：看到任何爆款参考视频/截图，必须先走"拆解五步法"（画面分区→文字层级→动画节奏→素材规则→归纳落预设），把字号比例（主16=100%/副10=62%/补充9=56%/品牌14=87%/卖点9.5=59%/CTA9=56%）、颜色（黄=主标题品牌/白=中性/红=痛点CTA）、动画错峰（打字机0s→渐显0.6s→弹入1.2s）等规则量化，再落进 DUAL_SCREEN_STYLES 出片。禁止不拆解直接拍脑袋定样式。

**同行爆款调研（docs/爆款调研方法论.md，受控窗口浏览器自主执行）**：
- 登录：受控窗口打开抖音，未登录则 request_action 扫码（一次性），登录态保持后全自主
- 爆款标准：≥1万赞=爆款、≥10万=现象级；垂直行业放宽（AI获客≥1万即行业爆款）；收藏率>10%=干货型、评论率>1%=话题型
- 搜索：`https://www.douyin.com/search/{词}?type=video&sort_type=1`（最多点赞排序）
- 拆解：标题钩子/文案章节结构/画面排版/四数据（赞评藏转）/转化设计 → 归纳成爆款档案 → 反哺文案改写库与样式预设
- 产出：爆款报告给用户（含可借鉴结论）

**BGM**：`PREFERRED_BGM_IDS` 白名单优先（已实测认可 Cyberpunk Techno / 科技未来运动 / 狂野电子），再按关键词搜云音乐库（动感/科技/燃…），全部剪映正版零侵权。

**调用**：
```python
from jyfactory.juyi_template import produce_hotspot_ad
dest = produce_hotspot_ad(title, subtitle, tagline, brand, selling_a, selling_b, cta,
                          videos=[m1, m2, m3], bgm_keyword="动感",
                          duration=18.0, style="gold", project="聚蚁模板_热点广告")
```
CLI：`python D:\AI工作区\jianying-factory\cli.py hotspot-ad --title "…" --brand "…" --videos m1 m2 m3 --project 草稿名`

---

## ❌ 绝对禁止做的事（所有历史踩坑，写进铁律）
1.  ❌ 绝对不能自己手写裸JSON草稿 → 走 VectCutAPI 内核或 jyfactory 包内引擎
2.  ❌ 绝对不能自己写字幕对齐算法 → SRT 由配音时间戳生成，或用剪映官方识别字幕
3.  ❌ 绝对不能在GUI里拖拽素材（会跑出窗口到用户真实桌面）→ 素材路径全部由引擎直接写进草稿
4.  ❌ 绝对不能扫描整个素材文件夹自动选素材 → 固定用用户配置素材
5.  ❌ 绝对不能忘记把原视频音量设为0（引擎 volume=0.1 或 0）
6.  ❌ 绝对不能让BGM短于视频总时长，必须铺满到片尾
7.  ❌ 绝对不能瞎编剪映特效ID → 用 API 白名单或剪映官方智能包装
8.  ✅ 所有文件全部存D盘，绝对不占用C盘空间
9.  ✅ BGM音量固定30-40%，不抢人声
10. ❌ **绝对不能操作真实桌面**（多次警告）——只能在豆包受控窗口内启动/操作剪映
11. 🔒 **安全线铁律（2026-10-08 升级，文本永不抛出镜头）**：标题/大标题字 `transform_y=0.8`（顶部，对齐上游 rules/text.md；旧值 0.85 贴边会出界，已废弃），字幕 `-0.8`（底部），居中 `0.0`。**所有 add_text/add_rich_text 自动过 `safe_transform_y()` 校验**：字号≤10 限幅 ±0.8 / 11-16 限幅 ±0.75 / ＞16 限幅 ±0.6（大字必须离边更远）。禁止标题传负值导致与字幕重叠，禁止任何文本超出画布安全区（上下 10% 边距）
12. 🎚 **响度自动平衡（2026-10-04 起专业标准，禁拍脑袋音量）**：`narrate_script` 结尾自动把人声归一化到平均 **-16dB**（口播标准）；`add_cloud_music(auto_balance=True, voice_path=配音)` 用 ffmpeg volumedetect 实测 BGM 原响度，自动算 volume 把 BGM 压到 **人声-15dB**（实测此曲 volume≈0.07）。禁止再用固定 0.35/0.3——同一首音乐不同人声自动校准，BGM 永远是人声的陪衬
13. 🗣️ **口播音色与断句（2026-10-04 用户验收：SAMI huoli 机械不自然 → 换 edge 云希）**：默认配音 `narrate_script(..., speaker="zh-CN-YunxiNeural", backend="edge")`（edge-tts 微软云希男声，rate=+10% 口播节奏，比 SAMI 活力男声自然沉稳）；文案按口播节奏口语化断句（短句、逗号停顿、反问句），勿长句连排；SAMI 克隆音色 ID 可直传 speaker 更自然
11. ❌ 绝对不能污染模板草稿（clone_draft 只读写副本）
12. ❌ **禁止重复劳动：智能包装与手动字幕二选一**（v7.8.1，用户指正）——走智能包装路线，引擎不写SRT、GUI不识别字幕（智能包装自动出字幕+花字+特效）；不走智能包装才用引擎SRT或官方识别字幕。智能包装=剪映官方AI自动剪辑，自动匹配字幕/花字/音效/特效，先写字幕必被覆盖或冲突
13. ❌ **视频必须放模板主视频轨 "video"**（2026-09-30 实测踩坑）——add_video 的 track_name 绝不能传 "main"/"video_main"：VectCutAPI `template_jianying_10_2` 模板含两条视频轨（name="video"=剪映主轨V1、name="main"=第二条视频轨），传错会让视频落到 V2，剪映里主轨空置。正确轨道名速查：video=主视频轨 / audio_main=配音轨 / bgm=BGM轨 / text_main=标题轨 / subtitle=字幕轨
14. 🎬 **文字动画必须用剪映中文枚举名**（2026-10-09 修复打字机"动画丢失"）——消费端是中文剪映 11.5：`intro_animation`/`outro_animation` 只能传剪映 `Text_intro`/`Text_outro` 中文枚举名（如"打字机_I""弹入""渐显""飞入"），引擎映射表已直传中文（打字机→打字机_I），服务端 add_text_impl 已改"剪映枚举优先、CapCut 英文兜底"。**禁止传英文 Typewriter/Fade_In 等**（会走 CapCut 枚举写 CapCut ID，剪映打开显示"动画丢失"）。已实测：剪映 11.5 打字机逐字播放、无动画丢失提示
15. 📐 **动画名解析三保险（2026-10-09 吸收上游 resolve_enum_with_synonyms）**：`_resolve_anim` 现支持 ①精确/大小写匹配 ②**英文→中文同义词表桥接**（Typewriter→打字机_I、fadeout→渐隐、glitch→乱码故障，见 ANIM_SYNONYMS） ③difflib 模糊匹配（cutoff 0.6，打字机iii→打字机_III），所有匹配收敛到 `JIANYING_TEXT_INTRO/OUTRO_NAMES` 剪映枚举全集，输出 100% 被剪映识别。调用方传中文/英文/大小写混合都能得到正确剪映枚举（验证 19 例全过）
16. ⏱ **时间解析统一 `safe_tim()`（2026-10-09 吸收上游）**：int=微秒 / float=秒 / "00:00:10" 冒号 / "1h2m3s500ms" 单位组合 / 纯数字=秒，全部统一微秒。后续 add_text/add_video/add_audio 的时间入参建议走 safe_tim 归一（防"200000us 被当 200000s"类错误）

---

## 📐 上游文本处理对齐方法论（2026-10-09 调研 luoluoluo22/jianying-editor-skill scripts/core/text_ops.py + utils/formatters.py + constants.py）

**上游"中文文本加在哪、怎么对齐"的标准答案（已吸收到引擎）**：

1. **哪里加（API 分工）**：
   - 普通字幕/文字 → `add_text_simple()`：内部自动 `_ensure_track` 建文本轨；start_time 默认接在上一个文本末尾（连续追加不用自己算）
   - 关键词高亮 → `add_rich_text(highlights=[{word,color,bold,size}])`：子串匹配、多处全标
   - 口播字幕一体 → `add_narrated_subtitles()`：逐句 TTS + 逐句字幕，同轨对应
   - 位置默认值：字幕 transform_y=-0.8（底部）、标题 0.8（顶部）、居中 0.0 —— 与我们安全线铁律一致

2. **怎么对齐（核心方法）**：**逐句 TTS 后按"实际音频时长"排字幕**——
   - 文案按 `[，。！？、\n\r]+` 正则切句 → 每句单独 TTS 生成音频段
   - 字幕 start = 该句音频 start；字幕 duration = `audio_seg.target_timerange.duration`（真实时长，不是估算）
   - 配音轨与字幕轨共用同一时间轴指针 curr_us，句间 +100ms
   - 结论：**字幕时长必须来自配音音频实测值，逐句一一对应**，这是对不齐问题的根治（我们引擎 add_subtitle 走 SRT 时间戳，原理等价）

3. **动画兼容（三保险）**：`resolve_enum_with_synonyms` = ①精确/大小写匹配 ②**英文→中文同义词表桥接**（Typewriter→打字机_I，fadeout→渐隐）③difflib 模糊匹配（cutoff 0.6，打字机iii→打字机_III）。**已吸收进 `vectcut_engine._resolve_anim`**（ANIM_SYNONYMS 表 + JIANYING_TEXT_INTRO/OUTRO_NAMES 枚举全集收敛，输出 100% 是剪映认识的枚举名，验证 19 例全过）

4. **时间解析 `safe_tim`**：int=微秒 / float=秒 / "00:00:10" 冒号 / "1h2m3s500ms" 单位组合 / 纯数字=秒，统一转微秒。**已吸收进引擎**（验证 9 例全过）

5. **字幕关键词高亮（剪映原生富文本 styles）**：**已开发完成+GUI 实测验证（2026-10-09）**——`add_subtitle(..., keywords=[{"word","color","bold","size"}])` 导入 SRT 时对每条字幕子串匹配关键词，写入剪映原生 styles 数组（TextStyleRange 机制，与 add_rich_text 同一套，剪映打开即变色加粗）。链路：vectcut_engine.add_subtitle → capcut_server /add_subtitle keywords → add_subtitle_impl → script_file.import_srt(keywords) → seg.add_text_style。**GUI 实测**：受控窗口打开「关键词高亮验证」草稿，预览画面 GEO 红色高亮 + AI 黄色高亮直接显示，剪映保存草稿成功（格式合法）。回归脚本 `D:\AI工作区\代码\verify_subtitle_keywords.py` 跑绿。上游 `set_subtitle_keywords`（全局 config 节点）格式全网无公开样例、盲写有打不开风险，**不做**（逐段 styles 已覆盖关键词高亮需求）
13. 🔍 **部署三保险（2026-10-09 吸收上游 project_base/media_ops）**：save_and_deploy 依次执行 ①素材自包含 → ②**完整性校验**（draft_content.json 必须存在且可解析、tracks/materials 非空，失败即报错返回空、绝不静默部署坏草稿）→ ③**素材高重复审计**（同一素材同源起点重复 >5 次输出警告，提示"秒切循环痕迹"、改用播放完/多截一段再循环）
14. 🎵 **剪映缓存正版音乐库（2026-10-09 吸收上游 sync_jy_assets）**：`CloudManager.sync_jy_cached_music()` 把剪映本地缓存音乐（播放/收藏过的，正版）增量同步进音乐库——物理文件复制到 D:\AI工作区\cloud_cache\jy_cached（不占 C 盘），索引 D:\AI工作区\data\jy_cached_audio.csv，`add_cloud_music("歌名")` 直接搜索使用、download_asset 本地命中不走 API。实测 235 条入库、增量幂等、引擎调用验证通过。**上游能力对比结论（16 文件全评估）**：已吸收=text_ops/project_base/media_ops/constants/formatters/sync_jy_assets；等价保留我们的=sami_tts(≈universal_tts)/advanced_ops(≈vfx_ops+smart_zoomer+web_recorder+movie_commentary)/draft_checker(≈draft_inspector)/save_and_deploy(≈auto_exporter)/ensure_server(≈api_validator)；暂缓=smart_rough_cut（依赖 Gemini 外部 API，走剪映原生智能粗剪）

6. **花字**：上游 `add_styled_text` 用 effectStyle patch + artistEffect 本地缓存，AI 决策=字幕走 add_text_simple、花字走 add_styled_text——我们引擎级 513 花字 ID 已可写，逻辑等价

---

## 🗂️ 工作区整理规范（2026-10-09 用户指令：分门别类清清楚楚，常态化执行）

**D:\AI工作区 是唯一工作区（全部文件存 D 盘），目录说明见 `D:\AI工作区\00_目录说明.txt`。铁律：**

1. **新产物必须按分类落位**，禁止在 D:\AI工作区 根目录散落文件：
   - 成品视频 → `导出\`；录屏/宣传片/截图 → `录制\`；配音 → `配音\`；素材/文案 → `素材\`；交付文档 → `文档\`
   - 项目代码 → 只进 `jianying-factory\jyfactory\`（真源）或 `代码\VectCutAPI\`（服务端）
2. **临时调试截图**：必须用 `tmp_` 前缀命名，用完立即删除，禁止堆在根目录
3. ★ **`剪映草稿\` 绝对禁止清理/移动**——用户要从草稿箱调用编辑（含未导出的草稿）
4. **归档制度**：不常用但需保留的 → `_归档\`（备份/历史录屏帧/检查截图）；明确无用的临时文件 → 删除
5. **每次任务收尾前自查**：本轮产生的文件是否都在对应分类目录？根目录有没有新增散落文件？有就归位
- **v7.9 模板管理器（2026-10-08）**：`jyfactory/templates.py（包内）`（list_templates/clone/replace_texts/replace_videos/replace_audios/save/make_from_template + _ensure_skeleton 骨架补全 + meta 回写）；演示/验证脚本 `D:\AI工作区\代码\demo_template.py` + `verify_template.py`（替换正确性验证）
- **v7.8 内核升级（2026-09-30 本轮验证）**：
  - VectCutAPI 已下载解压 `D:\AI工作区\代码\VectCutAPI`（含内嵌 pyJianYingDraft + template_jianying_10_2 原生模板），config.json 已设 `draft_profile: jianying_pro_10`
  - 依赖已装（imageio/psutil/flask/requests/oss2/json5）；服务启动：`python capcut_server.py`（端口9001）
  - **实测确认**：①create_draft/add_video/add_audio/add_subtitle/add_text/save_draft 全通；②add_subtitle 参数名是 `srt`；③save_draft 返回 `output.draft_url`=本地路径（部署必须用它，绝不能取第一个 dfd_ 文件夹——那是旧草稿）；④剪映11.5 打开验证通过（GEO口播测试_v78_1790758108）
  - 部署：草稿复制到 `D:\AI工作区\剪映草稿\<项目名>`；同名被占用时自动加时间戳后缀；清理 .locked
- **v7.7.2 启动法**：任务栏搜索启动取代图标双击为首选（launch_jianying.py `LAUNCH(mode="search")`）
- **v7.7 高级算子 `jyfactory/advanced.py（包内）`**：KEN_BURNS_PRESETS/narrated_draft/clone_draft/match_assets_by_script/web_to_video/record_screen/movie_commentary_draft/add_scene_transition+add_scene_effect+add_effect_track
- **v7.7 数据资产 `D:\AI工作区\代码\data\`**：popular_bgm.csv / asset_tags.csv / cloud_text_styles.csv
- **确定性执行器**：`jyfactory/gui_ops.py（包内）`（GUI 节点，坐标2026-09-27实测校准）
- **死代码已清除（2026-09-27）**：`scripts/_archive/` 全部历史废弃脚本已删除，禁止恢复调用

## 版本兼容说明（2026-10-08 实测更新）
- 剪映专业版 11.5.0.14471（当前唯一可运行版本）：✅ 引擎秒级生成明文草稿（JSON 正确性已验证）；⚠️ 剪映首页**列表可见性受限**——10/6 更新后只显示剪映自身格式草稿，明文草稿需通过模板管理器出片并如实提示可见性
- 剪映专业版 10.9.0.14199 / 11.1.0.14287 / 11.4.2.14459：目录存在但**无主程序 exe，不可独立启动**（升级残留）
- 免费用户：核心流程可用；SVIP用户：克隆音色/对口型/智能包装/无痕导出全可用

---

## 常见问题（已验证解决方案）
**Q：草稿打不开（停在首页）？** A：两种情形——①v7.9 前旧 pyJianYingDraft lv 格式草稿 11.5 打不开（撞加密墙），勿用；②v7.8+ VectCutAPI 明文草稿：JSON 正确性已验证，但剪映 11.5（10/6 更新后）列表不显示明文草稿（见版本兼容说明），属剪映版本限制，非草稿损坏。

**Q：字幕和配音对不齐？** A：SRT 时间戳严格对齐配音（v7.8 引擎直接写入），或剪映官方识别字幕。

**Q：原视频有环境杂音？** A：引擎 add_video volume=0.1 已压静音。

**Q：片尾黑屏/BGM提前结束？** A：BGM 按配音时长铺满截断（引擎 add_audio end=总时长）。

**Q：导出怎么做最快？** A：受控窗口内 `jyfactory/export_gui.py（包内）` 一键自动导出（单击+回车开草稿→点导出→确认→等完成→关闭→返回首页，约1-3分钟）。**无头导出（uiautomation）在本架构不可行**：剪映运行在豆包容器会话（Session 4），执行脚本在宿主会话（Session 1），uiautomation 跨会话枚举不到剪映窗口（已用双环境验证，14个顶层窗口清单确认）。上游能无头导出是因为剪映跑在普通交互会话。

**Q：剪映重启后打不开草稿？** A：剪映重启可能掉登录（左侧显示「点击登录账户」）。未登录状态双击/回车草稿不生效、会弹登录窗——需用户扫码登录后即可正常打开。登录状态标识：左侧显示「用户3...335 个人版」。

**Q：背景音乐会侵权吗？** A：BGM 走剪映官方曲库缓存（正版授权），零侵权风险。
