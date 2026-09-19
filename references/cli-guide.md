# 剪映工厂 - 剪映官方CLI参考

## 可用CLI

剪映专业版内置 `jianying-agent-cli.exe`，位于版本目录下。

### 子命令
- `fetch-feishu-doc` - 飞书文档拉取
- `query-content` - 查询草稿内容
- `plan-patch` - 生成补丁计划
- `validate-patch` - 校验补丁
- `apply-patch` - 应用补丁

### patch结构
```json
{
  "lyraCommands": [
    {"type": "add_track", "track_type": "video"},
    {"type": "add_clip", "track_id": 0, "target_timerange": {...}},
    {"type": "trim_clip", "clip_id": "...", "target_timerange": {...}},
    {"type": "split_clip", "clip_id": "...", "at": 1000000}
  ],
  "operations": []
}
```

### 注意事项
- 时间单位为**微秒**（1秒 = 1,000,000微秒）
- `query-content` 需要剪映主程序作为宿主进程
- 加密格式草稿无法通过CLI直接读取
- 建议优先使用GUI通道操作加密草稿
