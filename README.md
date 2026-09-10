# 听写实验室

一个中文、可在本机运行的 Cloud Speech-to-Text Web Demo。后端使用官方 Python SDK，前端无需 Node.js。你提供一段声音，选择模型和功能，得到可以阅读、对照、导出的转写。

**第一次接触？先运行本页的 4 步，再打开 [learning_guide.md](learning_guide.md)。**

资料核查日期：2026-09-10。完整入口见 [官方资料索引](docs/official_sources.md)。本项目不是 Google 官方产品。

## 1. 你拿到了什么

- 顶栏按模型分页：Chirp 3、Chirp 2、Telephony、Medical、V1 对照。每页只展示该模型的控件和适合该页的场景样例，不适合的不会跨页硬塞。
- Chirp 3 页：同步 Recognize、麦克风实时 StreamingRecognize、自动语言检测、短语提示、词级时间戳、降噪、说话人分离、自定义格式提示（Preview）。
- Chirp 2 页：对照上一代多语言，并单独提供语音翻译开关。
- Telephony 页：8 kHz 英语 IVR / 短口令 / chirp_telephony / 双声道分轨。中文 8 kHz 对照在 Chirp 3，因为官方电话语言表没有普通话。
- Medical 页：V1 医学口授与医患对话。**官方只支持 en-US（美国英语）**，不是中文，也不是英式/澳式英语。Premium，账号未必已开通。中文病历请用 Chirp 3 + 短语提示。
- V1 对照页：latest_long / latest_short / phone_call 等旧管道，用来对照而不是当新项目默认。
- 预览请求不调用 Google；转写才会计费。
- README、学习指南、官方参考索引及无需密钥的自动测试。

## 2. 四步启动（macOS / Linux）

### 第一步：进入项目目录

打开终端，进入本仓库根目录（含 `README.md` 的那一层）：

```bash
git clone https://github.com/jayson-sheyue/ASRDemo.git
cd ASRDemo
```

若已有本地拷贝，直接 `cd` 到该文件夹即可。需要 Python 3.10 或更新版本；本项目在 Python 3.14.6 上验证。

### 第二步：安装依赖

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`.venv` 是这个项目自己的 Python 环境，不要和本机其他项目混用。

### 第三步：用 ADC 登录（不需要 API Key）

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
gcloud services enable speech.googleapis.com --project YOUR_PROJECT_ID
cp .env.example .env
```

用文本编辑器打开 `.env`，填入你的 Google Cloud 项目：

```dotenv
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us
```

Chirp 3 官方区域是 `us` / `eu`。Chirp 2 是 `us-central1`（以及 europe-west4 / asia-southeast1），把 `chirp_2` 发到 `us` 会 400。Demo 会按模型改写区域。命令是 `gcloud auth application-default login`（中间是连字符）。项目需启用账单，并启用 Speech-to-Text API。

不填项目也可以打开界面、读文档、载入示例和预览请求；点击「转写」会提示配置。**没有假转写或本地识别替代结果。**

### 第四步：运行

```bash
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8002
```

或：`.venv/bin/python app.py`（同样默认 8002，可用环境变量 `DEMO_PORT` 覆盖）。

看到服务器启动后，在浏览器打开 [本地 Demo](http://127.0.0.1:8002)。保持终端开启。停止服务器按 `Ctrl+C`。

依次点击「第一段中文」→「预览请求」→「转写」。首次可能等待数秒。

## 3. Windows 启动

在项目目录打开 PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8002
```

## 4. 按钮怎么用

| 你想做什么 | 操作 | 观察什么 |
| --- | --- | --- |
| 第一次出字 | 留在 Chirp 3 页，点「入门 · 第一段中文」→ 转写 | 是否大致等于样例稿 |
| 换语言 | 点「多语言 · English / 日本語」 | 必须换对 locale |
| 专有名词 | 导入「专有名词」，对照不填提示时的错误 | 请求里是否出现 phrase hints |
| 自动检测语言 | 导入「自动检测语言」 | 英语样例不要先填中文 locale |
| 多语切换 | Chirp 3「多语切换 · auto / 列预期 locale」 | 中日英德串联。Chirp 3 清单最多 2 个 locale；写 3 个会 400 |
| 词级时间戳 | 打开开关再转写 | 每个词下面的秒数 |
| 说话人分离 | Chirp 3「说话人分离」样例 | 成功则按说话人分行；失败则对照官方 Batch 限制 |
| 电话 | 打开 Telephony 页 | 英语 IVR（8 kHz）。中文客服不在这一页 |
| 双声道分轨 | Telephony「电话 · 双声道样例」 | 一对一：通道 1 / 通道 2。上限是 8 轨 |
| 四声道分轨 | Chirp 3 / Telephony / V1「四声道样例」 | 证明 3、4 轨合法，不是只能立体声。Chirp 3 也有 |
| 医学 | Medical 页 | **只支持 en-US**。未开通会 403/404，这是预期。中文病历不要进这一页 |
| 实时听写 | Chirp 3 / Chirp 2 / Telephony / V1 点「实时听写」允许麦克风 | Telephony 的麦是 16 kHz，不是听筒 |
| 看实际输入 | 预览请求 | 不收费 |
| 对照旧 API | V1 页「对照 · default 中文」 | latest_long 官方表没有普通话 |

浏览器会询问麦克风权限。拒绝后仍可用样例和上传。

## 5. 选择模型

| 页 | API | 模型 ID | 身份 |
| --- | --- | --- | --- |
| Chirp 3 | V2 | `chirp_3` | ADC + Cloud 项目 |
| Chirp 2 | V2 | `chirp_2` / `chirp` | 同上；`chirp` 是第一代 |
| Telephony | V2 | `telephony` / `telephony_short` / `chirp_telephony` | 同上；后一个区域是 us-central1 |
| Medical | V1 | `medical_dictation` / `medical_conversation` | 同上，Premium，**仅 en-US** |
| V1 对照 | V1 | `latest_long` / `telephony` / `telephony_short` 等 | 同上 |

Python 包：`google-cloud-speech`（同时提供 `speech_v2` 与 `speech_v1`）。

V2 请求走 `projects/{project}/locations/{region}/recognizers/_` 隐式识别器，本 Demo 不创建长期 Recognizer 资源。

## 6. 项目结构与 API

```text
app.py                    FastAPI、静态页面、文档、转写与 WebSocket 流式
asr.py                    输入校验、V2/V1 SDK 适配、错误处理
catalog.py                模型、对照表、五页工作台快照
locales.py                各模型官方 locale 快照（Chirp 3 / Chirp 2 / 电话 / V1）
samples.py                加载 sample_assets 场景样例
sample_assets/            JSON 样例 + 短 WAV（macOS say 生成，供教学）
static/                   顶栏分页壳、样式、交互
examples/quickstart.py     最小 Python 同步转写
batch_demo.py             官方 BatchRecognize 命令行示例（需 GCS）
tests/                    无密钥测试
```

开发接口：[FastAPI Swagger](http://127.0.0.1:8002/docs)。`POST /api/preview` 不调用 Google；`POST /api/recognize` 返回 JSON 转写。`/ws/stream` 先收 JSON 配置，再收 16 kHz PCM 二进制帧。

## 7. 长度、格式与错误处理

- 同步 Recognize：官方短于约 1 分钟；本 Demo 拒收更长的 WAV。
- 请求体上限 10 MB；音频约 8 MB。
- 一次只接受一个转写任务。
- 失败后不提供伪装成完整结果的文字。
- 不把上游异常原文直接显示给浏览器主文案，以免泄漏凭据；详情在页面日志框。

## 8. 成本与数据

本项目不会预测你的真实账单。音频时长、模型、流式、重试都影响费用。价格看 [Speech-to-Text 定价](https://cloud.google.com/speech-to-text/pricing)。

凭据只在 Python 进程中使用。**不要把 `.env`、服务账户 JSON 提交进 git。** 浏览器只收到「是否已配置」的布尔值。音频在当前请求/页面内存中使用，不自动保存到服务器磁盘；样例 WAV 是仓库里的教学文件。刷新后本次录音消失。

这是单用户本地教学 Demo：默认绑定 127.0.0.1。不要直接改为公网监听。

## 9. 常见问题

| 现象 | 怎么处理 |
| --- | --- |
| 转写提示没有项目或 ADC | `.env` 填写 `GOOGLE_CLOUD_PROJECT`，运行 ADC login 后重启 |
| 404 / 400 模型或区域 | Chirp 3 用 `us` 或 `eu`；Chirp 2 用 `us-central1`。不要把 `chirp_2` 发到 `us` |
| 401 / 403 | 检查 ADC、账单、IAM、是否启用 `speech.googleapis.com`；医学模型可能未开通 |
| 医学页想转中文 / 英式英语 | 官方只支持 en-US。中文病历回 Chirp 3，用短语提示药名 |
| 400 说话人分离 | 官方功能表写 Chirp 3 分离主路径是 Batch；同步可能被拒 |
| 粤语 / 台湾普通话失败 | 语言表是 Preview |
| 实时听写没声音 | 允许麦克风；用耳机避免回授 |
| 端口被占用 | `--port 8766` 或设置 `DEMO_PORT` |

## 10. 运行测试

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

测试不联网、不转写收费音频。通过只能证明本地逻辑；不能证明你的账号可用。

## 11. Batch API（长音频）

工作台同步 Recognize 不提交 Batch。长文件请把音频放到 GCS：

```bash
.venv/bin/python batch_demo.py submit gs://YOUR_BUCKET/audio.wav
.venv/bin/python batch_demo.py status OPERATION_NAME
```

submit 会产生真实云端任务，可能计费。
