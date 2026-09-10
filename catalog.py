"""Official STT model/feature snapshot, checked 2026-09-10. No credentials here.

Chirp 3 / Chirp 2 / telephony live in Speech-to-Text API V2.
Medical and latest_long / video / phone_call live primarily in V1.
Chirp 3 is us / eu. Chirp 2 is us-central1 / europe-west4 / asia-southeast1.
"""
from __future__ import annotations

from locales import (
    CHIRP1_LANGUAGES, CHIRP2_LANGUAGES, CHIRP3_LANGUAGES, CHIRP_TELEPHONY_LANGUAGES,
    TELEPHONY_LANGUAGES, V1_LANGUAGES,
)


def _doc(title, url, why):
    return {'title': title, 'url': url, 'why': why}


def _lang(code, label, stage='GA'):
    return {'code': code, 'label': label, 'stage': stage}


CHECKED = '2026-09-10'

# Official regional homes. Chirp 3 is a multi-region; Chirp 2 is a single region.
ENGINE_LOCATIONS = {
    'chirp3': 'us',
    'chirp2': 'us-central1',
    'telephony': 'us',
    'medical': '',
    'v1': '',
}
CHIRP3_REGIONS = {'us', 'eu'}
CHIRP2_REGIONS = {'us-central1', 'europe-west4', 'asia-southeast1'}
TRANSLATION_ALIASES = {
    'zh': 'cmn-Hans-CN', 'zh-CN': 'cmn-Hans-CN', 'zh-Hans': 'cmn-Hans-CN',
    'cmn': 'cmn-Hans-CN', 'cn': 'cmn-Hans-CN',
    'en': 'en-US', 'ja': 'ja-JP', 'ko': 'ko-KR', 'fr': 'fr-FR', 'de': 'de-DE',
}

CHIRP3_DIARIZATION_LANGS = {
    'cmn-Hans-CN', 'de-DE', 'en-GB', 'en-IN', 'en-US', 'es-ES', 'es-US',
    'fr-CA', 'fr-FR', 'hi-IN', 'it-IT', 'ja-JP', 'ko-KR', 'pt-BR',
}

MODELS = {
    'chirp3': ['chirp_3'],
    'chirp2': ['chirp_2', 'chirp'],
    'telephony': ['telephony', 'telephony_short', 'chirp_telephony'],
    'medical': ['medical_dictation', 'medical_conversation'],
    'v1': ['latest_long', 'latest_short', 'telephony', 'telephony_short', 'video', 'phone_call', 'command_and_search', 'default'],
}

MODEL_LANGUAGES = {
    'chirp': CHIRP1_LANGUAGES,
    'chirp_telephony': CHIRP_TELEPHONY_LANGUAGES,
}

MODEL_CARDS = {
    'chirp_3': 'Chirp 3：最新一代多语言 ASR。仅 V2。Recognize / StreamingRecognize / BatchRecognize。说话人分离官方写明主要在 Batch；自动语言检测、短语提示、降噪、自定义格式提示（Preview）。区域是 us / eu。',
    'chirp_2': 'Chirp 2：USM + LLM。仅 V2。区域是 us-central1 / europe-west4 / asia-southeast1，不是 Chirp 3 的 us。可流式。有词级时间戳、短语提示、语音翻译。降噪可用。官方写明不做 diarization / language detection。',
    'chirp': '第一代 Chirp（语言表仍列出 chirp）。区域与 Chirp 2 相同。新项目请用 chirp_2 或 chirp_3。',
    'telephony': 'V2 telephony：针对电话/8 kHz 客服音频。适合 IVR、呼叫中心。官方语言表在 us/eu 约 44 个 locale，没有普通话。不要拿它去听播客。',
    'telephony_short': 'V2/V1 telephony_short：同样是电话通道，针对很短甚至单个词的电话语音。区域与 telephony 相同（us/eu）。',
    'chirp_telephony': 'V2 chirp_telephony：把 Chirp 准确率用到 8 kHz 电话。官方区域是 us-central1 / europe-west4 / asia-southeast1，不是 Chirp 3 的 us。语言只有约 10 个（英/德/西/法/意/葡）。',
    'medical_dictation': '医学口授：一位医生独自对着麦克风念病历。官方只支持 en-US（美国英语），不是中文，也不是英式/澳式英语。Premium，更贵，项目未必已开通。',
    'medical_conversation': '医学对话：医生和病人两个人在说话，并尝试标出谁在说。同样只支持 en-US。Premium，项目未必已开通。',
    'latest_long': 'V1 latest_long：长内容、自发讲话、媒体。可替代旧 video 模型。官方语言表没有普通话；中文请用 default 或 command_and_search。',
    'latest_short': 'V1 latest_short：几秒短指令、搜索框说话。',
    'video': 'V1 video：视频音轨优化的旧模型。许多语言请改 latest_long。',
    'phone_call': 'V1 phone_call：电话音频旧模型。新项目优先试 V2 telephony。',
    'command_and_search': 'V1 command_and_search：短命令。新项目优先试 latest_short。',
    'default': 'V1 default：未指定模型时的通用路径。新项目不要从它开始。',
}

COMPARE_MODELS = [
    ['', 'Chirp 3', 'Chirp 2', 'telephony（V2）', 'V1 latest_* / video / phone_call'],
    ['API', 'V2', 'V2', 'V2', 'V1'],
    ['定位', '最新多语言 ASR', '上一代多语言 USM', '8 kHz 电话', '长内容 / 短指令 / 旧电话与视频'],
    ['同步 Recognize（<1 分钟）', '能', '能', '能', '能'],
    ['流式 Streaming', '能', '能', '能（浏览器麦 16 kHz，不是 8 kHz 听筒）', '能（V1 streaming）'],
    ['Batch（长音频 / GCS）', '能', '能', '能', 'V1 longrunning'],
    ['自动语言检测', '能（auto 或列预期 locale）', '官方：Language Detection 不支持', '不支持', '有独立 LID，本 Demo 不接'],
    ['说话人分离', '官方：Batch；语言表也写 Recognize', '官方不支持', '官方语言表未作为卖点', 'V1 diarization_config'],
    ['短语提示', '简单词/短语，无 class token', '简单词/短语', '能（语言表：Model adaptation）', '短语 + speechContexts boost'],
    ['词级时间戳', 'Recognize / Batch；可能略降质量', '可开', '可开', 'enable_word_time_offsets'],
    ['语音翻译', '不是卖点', '可指定目标语言', '无', '无'],
    ['降噪', 'denoiser_config', 'denoiser_config', '无（这是 Chirp 文档能力；本页不发送）', '无此字段'],
    ['自定义格式提示', 'Preview custom prompt', '无', '无', '无'],
    ['多声道分轨', 'V2 有字段；1–8 轨；功能表未列（混音请用分离）', '功能表未列', '能；样例 2 或 4 轨，上限 8', '能（latest_short 除外；上限 8 轨）'],
    ['区域', 'us / eu 多区域', 'us-central1 / europe-west4 / asia-southeast1', 'telephony / telephony_short：us 或 eu；chirp_telephony：us-central1', '多为 global speech.googleapis.com'],
    ['计费', 'V2 Chirp 价目', 'V2 Chirp 价目', 'V2 telephony 价目', 'V1 标准/增强价目'],
]

COMPARE_METHODS = [
    ['你在问什么', '同步转写（点「转写」）', '实时听写（点「实时听写」）', '批量转写（命令行）'],
    ['人话', '把整段录音交给云端，等它听完，一次性拿回全文', '麦克风开着，话说到一半屏幕就开始出字', '文件先放到云存储，提交过夜任务，跑完再取稿'],
    ['官方接口名', 'Recognize', 'StreamingRecognize', 'BatchRecognize'],
    ['业务上值什么', '语音消息、短留言、几十秒口播；实现最简单', '直播字幕、客服坐席边听边检索、语音输入框', '一小时会议、全天呼叫中心录音、会后出纪要'],
    ['音频多长', '官方：大约短于 1 分钟', '只要连接还在', '分钟到小时（Chirp 3 开词级时间戳时大约 20 分钟一段）'],
    ['声音从哪来', '请求里直接塞文件', '边说边把声音碎片传上去', '云存储（GCS）里的文件'],
    ['本 Demo', '工作台「转写」走这条', '工作台「实时听写」', '命令行 batch_demo.py，需要自己有存储桶'],
    ['说话人分离（Chirp 3）', '语言表写可以；功能表写主要在批量。以端点为准', '官方不把它当主路径', '官方主路径'],
]

COMPARE_API = [
    ['你可能听到的说法', '新接口（V2）', '旧接口（V1）'],
    ['人话', '同一家速记公司的新柜台。Chirp 3 / Chirp 2 / 电话页走这里', '旧柜台。医学页、V1 对照页走这里'],
    ['对业务意味着什么', '新项目请从这里起步：准确率、多语言、实时、批量官方都押在这一代', '旧系统还能跑；医学模型目前也在这里。新项目不要默认开 V1'],
    ['Python 包', '同一个 google-cloud-speech 里的 speech_v2', '同一个包里的 speech_v1'],
    ['识别器', '路径里有 recognizers/_（本 Demo 用临时的 _，不在你项目里留下永久配置）', '没有这个资源，填表方式更老'],
    ['语言怎么填', '可以填一串，Chirp 3 还可以填 auto 让模型猜', '只能填一个语言码，没有 auto'],
    ['音频格式', '常见 WAV / MP3 / WebM 可让服务自己判断', '更稳妥的是 WAV；WebM 可能被拒'],
    ['本 Demo 默认区域', 'Chirp 3 / 电话：us 或 eu；Chirp 2：us-central1', '默认全球接口 speech.googleapis.com'],
    ['新项目建议', 'Chirp 3 起', '只为医学模型（且仅 en-US）或对照已经上线的旧链路'],
]

WHY_NOT_CHIRP3 = [
    ['你会离开 Chirp 3 页，如果…', 'Chirp 3', '去哪一页'],
    ['音频来自电话、8 kHz、IVR', '也能转，但不是为它训练的', 'telephony'],
    ['要对照上一代多语言 / 要翻译成另一种语言', '主打转写，不是翻译产品', 'Chirp 2 的翻译开关'],
    ['英语病历口授 / 英语问诊（仅 en-US）', '通用模型，药名靠短语提示碰运气', 'Medical 页（Premium，官方只支持美国英语）'],
    ['中文病历、英式/澳式英语病历', '用 Chirp 3 + 短语提示药名', '不要打开 Medical 页，那里听不懂'],
    ['必须走已经上线的 V1 管道', 'V2 资源名、区域都不同', 'V1 页'],
    ['坐席/客户已经分轨的通话（2–8 轨）', '也能发 V2 字段，但不是电话通道专精', 'telephony 分轨识别'],
    ['音频超过 1 分钟且在 GCS', '工作台同步 Recognize 拒收超长文件', 'batch_demo.py'],
]

FIT_GUIDE = [
    ['你的业务更像…', '优先试', '不要先试', '听哪条样例'],
    ['会议、采访、多语言内容、要最新准确率', 'Chirp 3', 'V1 default', '入门 · 第一段中文；自动检测语言'],
    ['一段录音里中日英德等切换', 'Chirp 3 列最多 2 个 locale（或 auto）', '在 chirp_3 的 language_codes 里写 3 个', 'Chirp 3 · 多语切换 · 列预期 locale'],
    ['实时字幕、麦克风边说边出字', 'Chirp 3 流式', '同步 Recognize 假装实时', '功能 · 实时听写（点麦克风）'],
    ['呼叫中心、8 kHz 录音', 'telephony', 'Chirp 3 近讲麦', '电话 · 英语 IVR'],
    ['IVR 按键后的短口令、单个词', 'telephony_short', '用 telephony 去听一小时通话', '电话 · 短口令 telephony_short'],
    ['要把 Chirp 准确率用到 8 kHz 电话（仅约 10 个语言）', 'chirp_telephony', '拿 chirp_telephony 去听普通话', '电话 · chirp_telephony'],
    ['坐席/客户已经分轨的通话（2–8 轨）', 'telephony 分轨识别', '用说话人分离去猜混音', '电话 · 双声道样例；四声道样例'],
    ['英语医生口授病历（仅美式英语 en-US）', 'Medical 口授', '中文病历硬套医学页', '医学 · 口授'],
    ['英语医患对话（仅 en-US）', 'Medical 对话', '普通说话人分离当病历系统', '医学 · 对话'],
    ['短口令、搜索框说话', 'V1 latest_short', 'latest_long', 'V1 · 短指令'],
    ['专有名词 / 项目 ID / 人名', '任意页 + 短语提示', '只换模型、不给提示', 'Chirp 3 · 专有名词'],
]

FEATURE_VALUE = [
    ['功能 / 特性', '业务上值什么', '什么时候不要开 / 不要用它做', '哪一页'],
    ['同步转写 Recognize', '语音消息、短留言、几十秒口播一次性出稿；实现最简单', '拿它假装实时字幕；也不要塞 1 小时文件', '各页「转写」'],
    ['实时听写 Streaming', '直播字幕、客服坐席边听边检索、语音输入框', '浏览器麦是单声道 16 kHz，测不出电话听筒和分轨', 'Chirp 3 / Chirp 2 / Telephony / V1'],
    ['批量 Batch', '一小时会议、全天通话、会后出纪要', '工作台同步转写扛不住长文件', '命令行 batch_demo.py'],
    ['Chirp 3', '会议、采访、字幕、多语言、要最新准确率', '8 kHz 电话专精、英语医学口授', 'Chirp 3 默认页'],
    ['Chirp 2 语音翻译', '听英语直接出中文稿，少一次翻译接口', '当新项目默认模型；目标码必须是 cmn-Hans-CN', 'Chirp 2'],
    ['telephony', '呼叫中心、IVR、8 kHz 录音质检', '拿它去听播客或会议室麦', 'Telephony'],
    ['telephony_short', '按键后的短口令、单个词', '用它听一小时通话', 'Telephony'],
    ['chirp_telephony', '电话通道还想要 Chirp 准确率（约 10 个语言）', '听普通话；区域必须 us-central1', 'Telephony'],
    ['医学口授 / 对话', '英语诊所电子病历、英语问诊出稿（Premium）', '中文病历、英式/澳式英语', 'Medical · 仅 en-US'],
    ['自动标点', '出稿直接给人读：留言、字幕、纪要', '你自己后处理标点时可以关', '有开关的页，默认开'],
    ['短语提示', '品牌名、工单号、药名、项目 ID 少写错', '没有清单却指望模型猜专有名词', 'Chirp / 电话 / V1'],
    ['词级时间戳', '字幕对画面、质检跳到某一秒', '只要全文、在乎速度和准确率时不必开', '非流式；Chirp 3 流式不保证字级时间'],
    ['说话人分离', '一路混音的会议纪要按人分段', '已经分轨的电话；不能当考勤/声纹', 'Chirp 3（官方更强调 Batch）；V1 也有'],
    ['分轨识别', '录音系统已经分轨：2 轨=一对一，3–8 轨=多方会议。按轨出稿，channel_tag 标轨', '拿混音去分轨；MULAW/AMR 只能 1 轨；latest_short 不能开。按轨计费', 'Telephony / V1 / Chirp 3 开关；样例 2 轨和 4 轨（Chirp 3 也有四声道）'],
    ['降噪', '马路边、有背景乐的录音偶尔有用', '干净近讲麦；电话页没有这个字段', 'Chirp 3 / Chirp 2'],
    ['自定义格式 Preview', '想统一数字写法、日期格式', '当合同条款；效果不保证', '仅 Chirp 3'],
    ['脏话过滤', '客服质检要打码脏话再给人看', '可能误伤正常词', 'V1'],
    ['多候选', '对照模型还在犹豫什么', '候选不一定更对，不能当投票器', 'V1'],
    ['自动检测语言', '音频语种不固定、入口无法先选 locale。官方转最主要的语言', '已知会夹杂哪几种时不要只用 auto，应列具体 locale；电话页没有 auto；医学页只有 en-US', '仅 Chirp 3'],
    ['多语 / 语码切换', '一段录音里中日英德等切换时仍能出稿。Chirp 3 已知语种时列最多 2 个 locale', '不是保证每种语言都按原文脚本；chirp_3 写 3 个会 400；中英术语夹杂不是多语切换；Telephony / V1 没有这条路径', 'Chirp 3 · 多语切换样例'],
]

FEATURE_HINTS = {
    'punctuation': '自动标点：出稿能不能直接给人读。客服留言、字幕几乎都要开。',
    'word_time': '词级时间戳：字幕对画面、质检跳到某一秒。会略慢。纯出稿不必开。',
    'diarization': '说话人分离：一路混音里猜谁在说话。不能当考勤。已经分轨请改用分轨识别。',
    'denoiser': '降噪：嘈杂环境偶尔有用。干净样例上几乎听不出差别。',
    'channels': '分轨识别：录音已经分轨。WAV/FLAC/OGG 官方 1–8 轨，3、4 轨合法。样例用 2 轨（一对一）和 4 轨（多方）。MULAW/AMR 只能 1 轨。按轨计费。不是说话人分离。',
    'adaptation': '短语提示：品牌名、工单号、人名。没有清单模型只能猜。Chirp 没有 V1 的 class token。',
    'custom_prompt': '自定义格式：想统一数字/日期写法。Preview，效果不保证。',
    'translation': '语音翻译：听一种语言写出另一种。英语→简体中文填 cmn-Hans-CN，不是 zh-CN。',
    'profanity': '脏话过滤：质检出稿要打码。可能误伤正常词。',
    'alternatives': '多候选：看模型还在犹豫什么。候选不一定更对。',
    'stream': '实时听写：边说边出字。浏览器麦是单声道，测不出分轨和 8 kHz 听筒。',
    'language_auto': '自动检测：入口无法先选 locale 时用 auto。官方转最主要的语言。Chirp 3 列预期 locale 最多 2 个。发 3 个会 400。中英术语夹杂是另一条样例。',
}

API_OUT_OF_DEMO = [
    ['能力', '业务价值', '为什么网页 Demo 不做', '客户接入文档'],
    [
        '长期 Recognizer / PhraseSet 资源',
        '呼叫中心把模型、语言、提示短语做成可复用配置，多条线路共用，不必每次请求带齐字段',
        '会在你们 GCP 项目里留下资源。教学一律用隐式 recognizers/_，短语用请求内联（工作台「短语提示」已覆盖效果）。',
        'V2 Recognizer\nhttps://cloud.google.com/speech-to-text/v2/docs/reference/rest/v2/projects.locations.recognizers',
    ],
    [
        '自定义语音模型训练（Custom Speech）',
        '领域口音、产品黑话、内部代号特别多时，用自有语料把识别率拉上去',
        '要准备标注数据并启动训练任务，网页当场点不了。短语提示解决不了系统性口音。',
        'Custom Speech\nhttps://cloud.google.com/speech-to-text/v2/docs/custom-speech-models/overview',
    ],
    [
        'BatchRecognize 写回 GCS',
        '一小时会、全天通话、会后出纪要；Chirp 3 说话人分离官方也更走批量',
        '要云存储和异步任务。工作台是本地文件立刻出字。命令行见 batch_demo.py。',
        '批量识别\nhttps://cloud.google.com/speech-to-text/docs/batch-recognize',
    ],
]

MODEL_RULES = [
    ['能力', '官方是否原生支持', '你在 Demo 里怎么做'],
    ['把声音变成文字', '支持。这就是 STT', '上传、样例或麦克风，再点转写'],
    ['边说边出字', 'V2 StreamingRecognize', '「实时听写」。不是把整段录完再假装流式'],
    ['自动加标点 / 大小写', 'Chirp 3 默认可选关闭', '标点开关'],
    ['自动检测语言', 'Chirp 3：language_codes=["auto"] 转主导语言；也可列最多 2 个，例如 [en-US, fr-FR]。Chirp 2 官方不支持', '下拉选 auto，或再填 1 个预期 locale。不要和 auto 混写；不要填 3 个'],
    ['说话人分离', 'Chirp 3：功能表写 Batch；语言表写 Recognize+Batch', '勾选后发送 diarization_config；失败则看官方限制'],
    ['多声道分轨', 'WAV/FLAC/OGG：1–8 轨。3、4 轨合法。MULAW/AMR 只能 1 轨。latest_short 不能开', '「分轨识别」。样例用 2 或 4 轨，不是上限'],
    ['专有名词', '短语提示 / Speech Adaptation。Chirp 无 class token', '填提示短语，不要指望模型猜项目名'],
    ['词级时间戳', 'Recognize / Batch 可开，可能略降质量', '时间戳开关；流式是句级时间'],
    ['降噪', 'denoiser_config.denoise_audio。snr_threshold 在 Chirp 3 已弃用', '降噪开关。本 Demo 固定 snr=0'],
    ['自定义格式', 'Chirp 3 custom prompt，Preview', '格式提示框。效果不保证'],
    ['语音翻译', 'Chirp 2 translation_config', '仅 Chirp 2 页。不是单独 Translation API'],
    ['克隆说话人 / 声纹登录', '不支持', '做不到'],
    ['本地离线模型', '不支持。请求发到 Google', '没有网就没有转写'],
    ['医学模型听中文 / 英式英语', '不支持。官方只支持 en-US', '中文病历回 Chirp 3；医学页语言下拉只有美国英语'],
]

DOC_CHIRP3 = _doc('Chirp 3 Transcription', 'https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3', '模型 ID、方法、区域 us/eu、语言、分离/提示/降噪/自定义提示。')
DOC_CHIRP2 = _doc('Chirp 2', 'https://docs.cloud.google.com/speech-to-text/docs/models/chirp-2', '词级时间戳、adaptation、翻译、降噪。')
DOC_MODELS = _doc('V2 模型对照', 'https://cloud.google.com/speech-to-text/v2/docs/transcription-model', 'chirp_3 / chirp_2 / telephony。')
DOC_V1_MODELS = _doc('V1 模型对照', 'https://docs.cloud.google.com/speech-to-text/docs/v1/transcription-model', 'latest_long / telephony / medical_*。')
DOC_MEDICAL = _doc('医学模型（仅 en-US）', 'https://docs.cloud.google.com/speech-to-text/docs/v1/medical-models', '口授 / 医患对话。官方原文：Medical models are only available for en-US。')
DOC_STREAM = _doc('流式识别', 'https://cloud.google.com/speech-to-text/docs/streaming-recognize', 'StreamingRecognize 概念。V2 示例见 Chirp 3 页。')
DOC_BATCH = _doc('批量识别', 'https://cloud.google.com/speech-to-text/docs/batch-recognize', '长音频与 GCS。')
DOC_ADAPT = _doc('Speech adaptation', 'https://cloud.google.com/speech-to-text/docs/adaptation', '短语提示。Chirp 不支持 class token。')
DOC_CHANNELS = _doc('多声道识别（V2）', 'https://docs.cloud.google.com/speech-to-text/docs/multi-channel', '默认只转第一轨。WAV/FLAC/OGG：1–8 轨。样例常用 2 轨，3、4 轨同样合法。')
DOC_V1_CHANNELS = _doc('多声道识别（V1）', 'https://docs.cloud.google.com/speech-to-text/docs/v1/multi-channel', 'LINEAR16/FLAC/OGG：1–8 轨。MULAW/AMR 只能 1 轨。按轨计费。latest_short 不能开。')
DOC_SDK = _doc('Python Speech 客户端', 'https://docs.cloud.google.com/python/docs/reference/speech/latest', 'speech_v1 与 speech_v2。')
DOC_PRICING = _doc('Speech-to-Text 定价', 'https://cloud.google.com/speech-to-text/pricing', '按音频时长与模型计费。')
DOC_ENABLE = _doc('启用 Speech-to-Text API', 'https://console.cloud.google.com/flows/enableapi?apiid=speech.googleapis.com', '项目需启用 speech.googleapis.com。')
DOC_ADC = _doc('Application Default Credentials', 'https://docs.cloud.google.com/docs/authentication/provide-credentials-adc', 'gcloud auth application-default login。')
DOC_MULTI_LANG = _doc('多语言识别（V2 最多 3 个）', 'https://cloud.google.com/speech-to-text/v2/docs/multiple-languages', 'latest_long / short / telephony 最多 3 个。Chirp 3 实测同一请求只能 2 个。')
DOC_LANG = _doc('V2 语言与区域', 'https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages', 'Chirp / telephony 按模型列出的 locale。本 Demo 下拉按此表补全。')
DOC_V1_LANG = _doc('V1 语言表', 'https://docs.cloud.google.com/speech-to-text/docs/v1/speech-to-text-supported-languages', 'V1 全部 locale。医学模型除外只有 en-US。')

V2_DOCS = [DOC_MODELS, DOC_SDK, DOC_ADAPT, DOC_STREAM, DOC_BATCH, DOC_CHANNELS, DOC_MULTI_LANG, DOC_PRICING, DOC_ENABLE, DOC_ADC, DOC_LANG]
V1_DOCS = [DOC_V1_MODELS, DOC_V1_LANG, DOC_SDK, DOC_V1_CHANNELS, DOC_PRICING, DOC_ENABLE, DOC_ADC, DOC_LANG]

WORKSPACES = [
    {
        'id': 'chirp3', 'nav': 'Chirp 3', 'api': 'v2',
        'eyebrow': 'SPEECH-TO-TEXT V2 · CHIRP 3', 'title': '先听懂，再谈模型。',
        'lead': '把声音变成可以阅读的文字。短录音点「转写」：整段交上去，等全文回来（大约一分钟内）。要对着麦克风边说边出字，点「实时听写」。区域填 us 或 eu。',
        'model': 'chirp_3',
        'features': ['stream', 'punctuation', 'word_time', 'diarization', 'adaptation', 'language_auto', 'denoiser', 'custom_prompt', 'mic', 'channels'],
        'advantages': [
            '准确率和多语言是这一页的理由。电话请去 telephony，医学请去 Medical。',
            'language_codes 可以是具体 locale，也可以是 auto。已知会夹杂哪几种时，Chirp 3 最多列 2 个（官方示例 en-US + fr-FR）。auto 转的是最主要的语言。',
            '短语提示只接受普通词，没有 V1 那种 $OOV_CLASS_DIGIT。',
        ],
        'limit_note': '说话人分离：官方功能表写仅 BatchRecognize；语言表写 Recognize 与 Batch。词级时间戳仅非流式。custom prompt 是 Preview。分轨识别：WAV/FLAC/OGG 最多 8 轨，样例 2 轨不是上限。',
        'fit': [
            {'title': '适合', 'body': '会议、采访、字幕、多语言内容、要最新转写质量。'},
            {'title': '不适合', 'body': '8 kHz 电话专精、医学口授专精、离线部署、声纹登录。'},
        ],
        'coverage': '语言下拉是 Chirp 3 模型页 2026-09-10 完整表（29 个 GA + 82 个 Preview）加上语言表多出的 ur-PK，以及 auto。不是 Locations API 实时探测。',
        'surface': [
            'V2 Recognize', 'V2 StreamingRecognize', 'model=chirp_3', 'language_codes / auto / 预期 locale 清单',
            'automatic punctuation', 'word time offsets', 'phrase hints', 'denoiser',
            'diarization_config', 'custom prompt（Preview）', '分轨识别（V2 multi_channel_mode）',
        ],
        'docs': [DOC_CHIRP3] + V2_DOCS,
        'languages': CHIRP3_LANGUAGES,
        'language_hint': '下拉可以选具体 locale 或 auto。auto 官方转「最主要」的语言。已知会夹杂哪几种时，再填预期 locale，Chirp 3 同一请求最多 2 个（含下拉那一个）。发 3 个会 400。不要和 auto 混写。中英术语夹杂不是多语切换。',
    },
    {
        'id': 'chirp2', 'nav': 'Chirp 2', 'api': 'v2',
        'eyebrow': 'SPEECH-TO-TEXT V2 · CHIRP 2', 'title': '上一代多语言，还能翻译。',
        'lead': '相对 Chirp 3：这一页能开语音翻译，但必须打到 us-central1（或 europe-west4 / asia-southeast1）。抄 Chirp 3 的 us 会 400：模型不存在。',
        'model': 'chirp_2',
        'features': ['stream', 'punctuation', 'word_time', 'adaptation', 'denoiser', 'translation', 'mic'],
        'advantages': [
            'translation_config 把源语言音频写成另一种语言的文字，不是单独的 Translation API。',
            '词级时间戳、短语提示、降噪在这一代就已经有。',
        ],
        'limit_note': '翻译对不是对称的；英语→简体中文的目标码是 cmn-Hans-CN，不是 zh-CN。官方不做说话人分离和自动语言检测。译文不是 Translation API 合同结果。',
        'fit': [
            {'title': '适合', 'body': '对照 Chirp 3、需要源语言音频直接出外语稿。'},
            {'title': '不适合', 'body': '新项目默认选型（请 Chirp 3）；电话与医学。'},
        ],
        'coverage': '语言下拉是 V2 语言表里 chirp_2 在 us-central1 的完整 117 个 locale。官方不做 Language Detection，所以没有 auto。完整表见 Chirp 2 模型页与语言表。',
        'surface': [
            'V2 Recognize / Streaming', 'model=chirp_2', 'us-central1 区域',
            'translation_config（en-US→cmn-Hans-CN）', 'word time offsets',
            'phrase hints', 'denoiser',
        ],
        'docs': [DOC_CHIRP2] + V2_DOCS,
        'languages': CHIRP2_LANGUAGES,
    },
    {
        'id': 'telephony', 'nav': 'Telephony', 'api': 'v2',
        'eyebrow': 'SPEECH-TO-TEXT V2 · TELEPHONY', 'title': '电话是电话，不是会议室麦。',
        'lead': '相对 Chirp 3：为 8 kHz 电话训练。客服录音、IVR、呼叫中心走这一页。近讲麦克风请回去 Chirp 3。官方语言表没有普通话、粤语，也没有 auto（自动检测语言是 Chirp 3 的能力）。',
        'model': 'telephony',
        'features': ['stream', 'punctuation', 'word_time', 'adaptation', 'mic', 'channels'],
        'advantages': [
            '同样一句话，8 kHz 电话音色用 telephony 通常比通用 Chirp 稳。',
            '本页有常规电话（telephony）、短口令（telephony_short）、chirp_telephony。中文客服不在这一页。官方 StreamingRecognize 能用电话模型；工作台已开放实时听写。',
        ],
        'language_hint': '官方 us/eu 语言表约 44 个 locale，没有普通话、粤语，也没有 auto。中文客服请用 Chirp 3。选 auto 会被拒绝：那是 Chirp 3 的 language_codes=auto，不是电话模型的能力。',
        'limit_note': '下拉有三个官方模型 ID：telephony、telephony_short、chirp_telephony。chirp_telephony 必须打到 us-central1。实时听写走官方 StreamingRecognize；浏览器麦克风是 16 kHz，不能代表 8 kHz 听筒音质。分轨：一对一用 2 轨样例，多方会议用 4 轨样例，API 上限 8 轨。',
        'fit': [
            {'title': '适合', 'body': '呼叫中心、IVR、8 kHz 录音、自动话机。'},
            {'title': '不适合', 'body': '播客、会议麦、要说话人分离的圆桌（先 Chirp 3 Batch）。'},
        ],
        'coverage': 'telephony / telephony_short 在 us/eu 官方语言表约 44 个 locale，没有普通话、粤语。chirp_telephony 只有 10 个（英/德/西/法/意/葡），选它时下拉会收成这 10 个。',
        'surface': [
            'V2 Recognize', 'V2 StreamingRecognize', 'model=telephony / telephony_short / chirp_telephony',
            '8 kHz 英语样例', 'punctuation', 'phrase hints', '分轨识别（1–8 轨；样例 2 轨和 4 轨）',
        ],
        'docs': V2_DOCS,
        'languages': TELEPHONY_LANGUAGES,
    },
    {
        'id': 'medical', 'nav': 'Medical', 'api': 'v1',
        'eyebrow': 'SPEECH-TO-TEXT V1 · MEDICAL', 'title': '医学模型只听美式英语。',
        'lead': '药名、剂量、医患对话有专用模型，但官方只支持 en-US（美国英语）。不是「所有英语」：英式 en-GB、澳式 en-AU 也不行，更不是中文。中文病历请回 Chirp 3，用短语提示药名。这一页更贵（Premium），项目未必已开通；失败常见 403/404，不是 Demo 坏了。',
        'model': 'medical_dictation',
        'features': ['punctuation', 'word_time', 'mic'],
        'advantages': [
            '口授模型 = 一位医生独自对着麦克风念病历；对话模型 = 医生和病人两个人在说话。',
            '这是旧柜台（V1）上的专用模型，不是「把 Chirp 3 调得更医学」那么简单。',
        ],
        'language_hint': '语言下拉只有 en-US，不是漏做了中文。官方原文：Medical models are only available for en-US。',
        'limit_note': '官方只支持 en-US。未开通时 403/404 是预期。本 Demo 不把你上传的医学音频存盘，刷新即消失。',
        'fit': [
            {'title': '适合', 'body': '英语诊所口授电子病历、英语问诊录音出稿（项目已开通 Premium）。'},
            {'title': '不适合', 'body': '中文病历、英式/澳式英语、普通会议。未开通时不要拿 Chirp 3 冒充医学模型。'},
        ],
        'coverage': '界面只放英语样例和 en-US。普通话、粤语、英式英语都不在医学模型语言表里。',
        'surface': [
            'V1 同步转写', '医学口授 medical_dictation', '医学对话 medical_conversation', '仅 en-US',
        ],
        'docs': [DOC_MEDICAL] + V1_DOCS,
        'languages': [_lang('en-US', '英语（美国）· 唯一支持')],
    },
    {
        'id': 'v1', 'nav': 'V1 对照', 'api': 'v1',
        'eyebrow': 'SPEECH-TO-TEXT V1', 'title': '旧管道还在，新项目别从这起步。',
        'lead': '相对 Chirp 3：latest_long / latest_short / video / phone_call 仍能跑。用来对照账单、已上线系统和短指令，不是默认推荐。',
        'model': 'latest_long',
        'features': ['punctuation', 'word_time', 'diarization', 'adaptation', 'profanity', 'alternatives', 'mic', 'stream', 'channels'],
        'advantages': [
            'V1 有 max_alternatives、profanity_filter、speaker_tag 这些老字段，V2 Chirp 不完全一一对应。',
            'phone_call 是旧电话模型；新电话请到 telephony 页。',
        ],
        'language_hint': '下拉是 V1 语言表并集。不是每个模型都有普通话：latest_long / latest_short / video / phone_call / telephony 官方表没有中文。中文样例用的是 default。新项目仍应先 Chirp 3。',
        'limit_note': 'V1 上传请尽量用 WAV。WebM 自动解码是 V2 的能力。语言字段是单值 language_code。分轨：WAV 1–8 轨，样例有 2 轨和 4 轨；latest_short 官方不能开。',
        'fit': [
            {'title': '适合', 'body': '对照旧系统、短指令 latest_short、暂时不能迁 V2 的项目。'},
            {'title': '不适合', 'body': '新项目默认选型。'},
        ],
        'coverage': '语言下拉是 V1 官方语言表的全部 locale（约 147 个，不含医学模型）。不是每个模型都有每一种语言：例如 video 几乎只有英语，latest_long 覆盖也小于 command_and_search。',
        'surface': [
            'V1 recognize / streaming', 'latest_long / latest_short', 'video / phone_call / default',
            'speechContexts', 'diarization_config', 'max_alternatives', 'profanity_filter', '分轨识别',
        ],
        'docs': V1_DOCS,
        'languages': V1_LANGUAGES,
    },
]

CHINESE_CODES = {'cmn-Hans-CN', 'cmn-Hant-TW', 'yue-Hant-HK'}
# V1 language table: these models do not list Mandarin/Cantonese.
# default / command_and_search do.
V1_MODELS_WITHOUT_CHINESE = {
    'latest_long', 'latest_short', 'video', 'phone_call', 'telephony', 'telephony_short',
}
V1_NO_SEPARATE_CHANNELS = {'latest_short'}


def language_codes_for(engine: str, model: str) -> set[str]:
    if model in MODEL_LANGUAGES:
        return {item['code'] for item in MODEL_LANGUAGES[model]}
    spec = next((item for item in WORKSPACES if item['id'] == engine), None)
    if spec is None:
        return set()
    codes = {item['code'] for item in spec['languages']}
    if engine == 'v1' and model in V1_MODELS_WITHOUT_CHINESE:
        return codes - CHINESE_CODES
    return codes


EXAMPLES = [
    {
        'title': '第一段中文', 'engine': 'chirp3', 'audio': 'welcome_cmn.wav',
        'expected': '你好，欢迎来到听写实验室。把声音交给 Google Cloud，让它变成可以阅读的文字。',
    },
]
