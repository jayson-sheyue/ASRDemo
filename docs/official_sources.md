# Cloud Speech-to-Text 官方参考资料索引

核查日期：2026-09-10。检索范围：Google Cloud Documentation、Speech-to-Text V2 模型页、Python 客户端参考。下面按功能去重。

本项目不是 Google 官方产品。“全部”指覆盖本 Demo 用到的主干文档，不宣称穷尽历史版本、论坛帖或未来页面。

## 先读这几个

| 官方链接 | 能解决的问题 | 对应项目位置 |
| --- | --- | --- |
| [Chirp 3 Transcription](https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3) | 模型 ID、Recognize / Streaming / Batch、us/eu 区域、语言、分离/提示/降噪/自定义提示。`auto` 转主导语言；列预期 locale 官方示例是 2 个 | Chirp 3 页；asr.py |
| [V2 模型对照](https://cloud.google.com/speech-to-text/v2/docs/transcription-model) | chirp_3 / chirp_2 / telephony | 顶栏分页 |
| [Chirp 2](https://docs.cloud.google.com/speech-to-text/docs/models/chirp-2) | 词级时间戳、adaptation、翻译、降噪 | Chirp 2 页 |
| [Python Speech 客户端](https://docs.cloud.google.com/python/docs/reference/speech/latest) | speech_v1 与 speech_v2 | asr.py |
| [ADC 配置](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc) | 本地登录 | README 第 2 节 |
| [医学模型（仅 en-US）](https://docs.cloud.google.com/speech-to-text/docs/v1/medical-models) | 口授 / 医患对话。官方原文：Medical models are only available for en-US | Medical 页 |

## 模型与方法

| 官方链接 | 用途 |
| --- | --- |
| [V1 模型对照](https://docs.cloud.google.com/speech-to-text/docs/v1/transcription-model) | latest_long / latest_short / telephony / medical_* |
| [医学模型](https://docs.cloud.google.com/speech-to-text/docs/v1/medical-models) | 仅 en-US。不要拿中文病历试这一页 |
| [流式识别](https://cloud.google.com/speech-to-text/docs/streaming-recognize) | StreamingRecognize 概念 |
| [批量识别](https://cloud.google.com/speech-to-text/docs/batch-recognize) | 长音频与 GCS |
| [Speech adaptation](https://cloud.google.com/speech-to-text/docs/adaptation) | 短语提示。Chirp 不支持 class token |
| [多声道识别（V2）](https://docs.cloud.google.com/speech-to-text/docs/multi-channel) | 默认只转第一轨。WAV/FLAC/OGG：1–8 轨 |
| [多声道识别（V1）](https://docs.cloud.google.com/speech-to-text/docs/v1/multi-channel) | LINEAR16/FLAC/OGG：1–8 轨。MULAW/AMR 只能 1 轨。按轨计费 |
| [多语言识别](https://cloud.google.com/speech-to-text/v2/docs/multiple-languages) | latest_long / short / telephony 最多 3 个。Chirp 3 实测同一请求只能 2 个 |
| [V2 语言与区域](https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages) | Chirp / telephony 按模型列出的 locale |
| [V1 语言表](https://docs.cloud.google.com/speech-to-text/docs/v1/speech-to-text-supported-languages) | V1 全部 locale。医学模型除外只有 en-US |
| [更新记录](https://docs.cloud.google.com/speech-to-text/docs/release-notes) | chirp_3 GA 与功能变更 |
| [Chirp 3 notebook](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/audio/speech/getting-started/get_started_with_chirp_3_transcription.ipynb) | 官方可运行示例 |

## 成本、运行和服务边界

| 官方链接 | 阅读时机 |
| --- | --- |
| [Speech-to-Text 定价](https://cloud.google.com/speech-to-text/pricing) | 确认模型与时长计费 |
| [启用 Speech-to-Text API](https://console.cloud.google.com/flows/enableapi?apiid=speech.googleapis.com) | 403 / API 未启用 |
| [配额](https://cloud.google.com/speech-to-text/quotas) | 429 |
| [RecognitionFeatures](https://docs.cloud.google.com/python/docs/reference/speech/latest/google.cloud.speech_v2.types.RecognitionFeatures) | 词级时间戳、custom prompt 等字段 |

## 相关但不是本 Demo 的路径

这些页面容易和 ASR 搜到一起。

| 官方链接 | 用途 |
| --- | --- |
| [Gemini 音频理解](https://ai.google.dev/gemini-api/docs/audio) | 生成式模型听音频，不是 Chirp ASR |
| [Gemini Live API](https://ai.google.dev/gemini-api/docs/live-api) | 实时对话与打断 |
| [自定义语音模型](https://cloud.google.com/speech-to-text/v2/docs/custom-speech-models/overview) | 训练自定义模型。本 Demo 不训练 |
| [V2 Recognizer 资源](https://cloud.google.com/speech-to-text/v2/docs/reference/rest/v2/projects.locations.recognizers) | 长期识别器。本 Demo 用 `_` |
