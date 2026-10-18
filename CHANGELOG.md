# Changelog

> 版本唯一真源。当前版本：**v8.1.0**（定义于 `jyfactory/__init__.py` 的 `__version__`，SKILL.md / README 与之保持一致）。

## v8.1.0 — 2026-10-11 对外交付友好化（新用户 3 分钟上手）

**目标：别人拿到技能包就能跑通，不依赖作者本机路径。**

- **config.py 参数化**：从纯硬编码升级为「环境变量 > config.json > 内置默认值」三级覆盖；`JYFACTORY_HOME` 可整体重定向工作区；自动探测剪映安装路径（注册表+常见路径）与 ffmpeg；JSON 读取兼容 UTF-8 BOM（记事本保存可用）
- **一键安装 `install.py`**：检测 Python/ffmpeg/剪映 → 自动获取 VectCutAPI 内核（sun-guannan/VectCutAPI，Apache 2.0）→ 装依赖 → 生成 config.json（引导用户素材路径）→ 环境体检
- **依赖清单 `requirements.txt`**：9 项核心依赖版本锁定；pyproject.toml 移除 pyJianYingDraft（由 VectCutAPI 内置精简版提供）
- **SKILL.md 泛化**：新增【新用户 3 分钟上手】；素材/克隆音色从"作者专属"改为"用户配置"；路径全部可覆盖
- **README 重写为对外文档**：安装/配置/出片/FAQ，去除内部路径硬编码
- **config.example.json**：配置字段示例
- 顺手修复：multi_platform.py / narrated.py 演示代码中 `r"config.XXX\..."` 字符串字面量 bug → 改用 config 变量
- 验证：新机器模拟（临时 JYFACTORY_HOME + config.json 覆盖）三级解析生效 · 冒烟回归 20/20 全绿 · install.py 语法通过

## v8.0.0 — 2026-10-09 产品级架构重构

**架构（消灭"东拼西凑"）**
- 唯一真源落地：`D:\AI工作区\jianying-factory`（jyfactory 分层包 37 模块 + cli.py + tests + README + pyproject）
- C 盘 skill 薄壳化（`__init__.py` / `syspath.py` / `produce.py` 三件套转发 D 盘真源）
- 统一入口：`cli.py`（doctor / ensure / sync-music / templates / produce-tally）+ `JianyingFactory` 门面
- 消灭双内核：engine_v2 / factory / jianying_music_bridge 降级为 `_*_legacy.py`（仅 advanced 内部使用）
- 数据资源集中：云端索引 890 条 + 剪映缓存正版音乐 235 条 → 项目 `data/`
- 文档对齐现实：重写 `代码/README.md`、项目 README；新增 `_archive/README.md` 下线清单；.workbuddy 旧副本薄壳化

**质量**
- 冒烟回归 `tests/smoke_test.py` 从 12 项扩展至 **20 项**：新增 ★强制静音 / ★分轨 / ★BGM 铺满截断 / ★三轨时长一致 / ★local_material_id 非空 / ★相对路径自包含（remote_url 一并清空）
- 路径单一真源：11 个活跃模块的硬编码路径全部收口到 `config.py`（checks / media / narrated / produce_talk / templates 等）
- 验证：37/37 模块可导入 · 回归 20/20 · `doctor` 9 项全绿

## v7.x — 2026-09-30 ~ 2026-10-08（历史演进，详见 SKILL.md）

- v7.9：模板管理器（TemplateManager，选模板→克隆→换文案/素材→出片，JSON 级替换 100% 兼容）
- v7.8：VectCutAPI 确定性内核上线（localhost:9001 生成剪映 10.x 明文草稿，剪映 11.5 秒级打开；GUI 40 分钟 → API 40 秒）
- v7.8.1：方法论定死——引擎只做确定性骨架，智能包装/识别字幕等剪映 AI 能力一键出片，禁止重复劳动
- v7.7：高级算子（Ken Burns / 语义素材匹配 / 逐句 TTS+字幕精准对齐 / 花字 / Web 录屏 / 影视解说）
- v7.7.2：剪映启动法实测定死（受控窗口内任务栏搜索优先）

## v7.0 及以前

- v7.0 前后：GUI 坐标逐帧操作时代（草稿直写 + 受控窗口 GUI 驱动官方功能）
- 早期：双击图标启动、手动导入素材的纯 GUI 时代（已在 v7.7.2 废弃）

## [7.6.1] 2026-10-09
- 新增 聚蚁AI双屏常驻模板 jyfactory/juyi_template.py（produce_hotspot_ad 全链路）
- 3 档文字样式预设 gold/tech/hot + PREFERRED_BGM_IDS 白名单
- CLI 新增 hotspot-ad 子命令

