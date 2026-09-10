# 场景样例

这些 JSON 是各模型页「本页场景样例」的一键导入源。点一下会填入该页能用的字段，并加载对应 WAV，再点「转写」。

WAV 由 macOS `say` 生成，方便没有麦克风时也能走通 API。它们不是真人录音，转写结果只能证明通路，不能代表生产麦克风。重新生成：

```bash
python3 scripts/make_samples.py
```

## 字段

| 字段 | 作用 |
| --- | --- |
| `id` / `title` / `group` | 界面分组和按钮文案 |
| `engine` | 只出现在对应顶栏页：`chirp3` / `chirp2` / `telephony` / `medical` / `v1` |
| `audio` | `sample_assets/audio/` 下的 WAV |
| `expected` | 样例稿，供对照，不是评分器 |
| `config` | 与该页导出配置相同的字段 |
