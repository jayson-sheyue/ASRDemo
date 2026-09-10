"""Generate short WAV samples with macOS `say` + `afconvert`. Offline, no Google."""
from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'sample_assets' / 'audio'
ASSETS = ROOT / 'sample_assets'


def say_wav(text: str, voice: str, dest: Path, rate: int = 16000) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        aiff = Path(tmp) / 'clip.aiff'
        subprocess.run(['say', '-v', voice, '-o', str(aiff), text], check=True)
        subprocess.run(
            ['afconvert', '-f', 'WAVE', '-d', f'LEI16@{rate}', str(aiff), str(dest)],
            check=True,
        )


def interleave_channels(paths: list[Path], dest: Path) -> None:
    handles = [wave.open(str(path), 'rb') for path in paths]
    try:
        if any(handle.getnchannels() != 1 for handle in handles):
            raise ValueError('each source must be mono')
        width = handles[0].getsampwidth()
        rate = handles[0].getframerate()
        if any(handle.getsampwidth() != width or handle.getframerate() != rate for handle in handles):
            raise ValueError('channel sources must share format')
        raw = [handle.readframes(handle.getnframes()) for handle in handles]
        frames = max(handle.getnframes() for handle in handles)
        padded = [data + b'\x00' * (frames * width - len(data)) for data in raw]
        interleaved = bytearray()
        for index in range(frames):
            start = index * width
            for data in padded:
                interleaved += data[start:start + width]
    finally:
        for handle in handles:
            handle.close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), 'wb') as handle:
        handle.setparams((len(paths), width, rate, frames, 'NONE', 'not compressed'))
        handle.writeframes(bytes(interleaved))


def interleave_stereo(left: Path, right: Path, dest: Path) -> None:
    interleave_channels([left, right], dest)


def concat_wav(parts: list[Path], dest: Path, pause: float = 0.45) -> None:
    frames = []
    params = None
    for path in parts:
        with wave.open(str(path), 'rb') as handle:
            if params is None:
                params = handle.getparams()
            frames.append(handle.readframes(handle.getnframes()))
            silence = b'\x00' * int(params.framerate * params.sampwidth * params.nchannels * pause)
            frames.append(silence)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), 'wb') as handle:
        handle.setparams(params)
        handle.writeframes(b''.join(frames[:-1]))


def sample(id_, title, group, note, engine, audio, expected, **config):
    return {
        'id': id_,
        'title': title,
        'group': group,
        'note': note,
        'engine': engine,
        'audio': audio,
        'expected': expected,
        'config': config,
    }


def write_json(item: dict, filename: str) -> None:
    (ASSETS / filename).write_text(json.dumps(item, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    clips = {
        'welcome_cmn.wav': ('你好，欢迎来到听写实验室。把声音交给 Google Cloud，让它变成可以阅读的文字。', 'Tingting', 16000),
        'news_cmn.wav': ('请把这份通知听写清楚：会议改到周五上午九点，不要迟到。', 'Tingting', 16000),
        'names_cmn.wav': ('请帮我预约明天下午三点，在 Vertex 项目 webeye-internal-test 里启用 Speech to Text API。', 'Tingting', 16000),
        'lecture_cmn.wav': (
            '语音识别不是把声音变成人，它只是把已经说出来的话写成字。模型会猜，专有名词要靠短语提示。',
            'Tingting', 16000,
        ),
        'welcome_en.wav': ('Hello, welcome to the listening lab. Cloud Speech to Text turns your voice into readable text.', 'Samantha', 16000),
        'numbers_en.wav': ('Please ship to 1600 Amphitheatre Parkway, Mountain View, and call 650-555-0100.', 'Samantha', 16000),
        'welcome_ja.wav': ('こんにちは。音声認識ラボへようこそ。今日は、声を文字に変えてみましょう。', 'Kyoko', 16000),
        'welcome_ko.wav': ('안녕하세요. 음성 인식 실험실에 오신 것을 환영합니다.', 'Yuna', 16000),
        'welcome_yue.wav': ('你好，歡迎嚟到聽寫實驗室。', 'Sinji', 16000),
        'welcome_tw.wav': ('你好，歡迎來到聽寫實驗室。', 'Meijia', 16000),
        'host_en.wav': ('Speech to Text turns audio into text.', 'Samantha', 16000),
        'guest_en.wav': ('Yes, and Chirp 3 can also label different speakers in one recording.', 'Daniel', 16000),
        'medical_dictation.wav': (
            'Patient presents with hypertension and type two diabetes. Start metformin five hundred milligrams twice daily.',
            'Samantha', 16000,
        ),
        'doctor_en.wav': ('How long have you had the chest pain?', 'Daniel', 16000),
        'patient_en.wav': ('It started last night after dinner, and it is worse when I breathe in.', 'Samantha', 16000),
        'phone_cmn.wav': ('您好，这里是客户服务中心。您的订单号是 A 三 K 九 二 八。请按一转人工。', 'Tingting', 8000),
        'phone_en.wav': ('Thanks for calling. Your confirmation code is A three K nine. Press one for an agent.', 'Samantha', 8000),
        'command_en.wav': ('Set a timer for five minutes.', 'Samantha', 16000),
        'phone_short_en.wav': ('Press one.', 'Samantha', 8000),
        'agent_en.wav': ('Thanks for calling. How can I help you today?', 'Daniel', 16000),
        'customer_en.wav': ('I need to check my order A three K nine.', 'Samantha', 16000),
        'agent_phone_en.wav': ('Thanks for calling. How can I help you today?', 'Daniel', 8000),
        'customer_phone_en.wav': ('I need to check my order A three K nine.', 'Samantha', 8000),
        'quad1_en.wav': ('Welcome to the quarterly review.', 'Daniel', 16000),
        'quad2_en.wav': ('Revenue is up twelve percent.', 'Samantha', 16000),
        'quad3_en.wav': ('I have a question about the timeline.', 'Fred', 16000),
        'quad4_en.wav': ('Let us take that offline after the call.', 'Karen', 16000),
        'quad1_phone_en.wav': ('Welcome to the quarterly review.', 'Daniel', 8000),
        'quad2_phone_en.wav': ('Revenue is up twelve percent.', 'Samantha', 8000),
        'quad3_phone_en.wav': ('I have a question about the timeline.', 'Fred', 8000),
        'quad4_phone_en.wav': ('Let us take that offline after the call.', 'Karen', 8000),
        'mixed_cmn.wav': ('今天我们要用 Cloud Speech-to-Text 的 Chirp 3 模型，language code 选 cmn-Hans-CN。', 'Tingting', 16000),
        'polyglot_cmn.wav': ('大家好，欢迎参加今天的产品发布会。', 'Tingting', 16000),
        'polyglot_ja.wav': ('本日はお越しいただきありがとうございます。', 'Kyoko', 16000),
        'polyglot_en.wav': ('Hello everyone, thank you for joining this product launch.', 'Samantha', 16000),
        'polyglot_de.wav': ('Guten Tag, willkommen zur Produkteinführung.', 'Anna', 16000),
    }
    AUDIO.mkdir(parents=True, exist_ok=True)
    for name, (text, voice, rate) in clips.items():
        say_wav(text, voice, AUDIO / name, rate)
        print('wrote', name)

    concat_wav([AUDIO / 'host_en.wav', AUDIO / 'guest_en.wav'], AUDIO / 'dialogue_en.wav')
    concat_wav([AUDIO / 'doctor_en.wav', AUDIO / 'patient_en.wav'], AUDIO / 'medical_conversation.wav')
    interleave_stereo(AUDIO / 'agent_en.wav', AUDIO / 'customer_en.wav', AUDIO / 'stereo_en.wav')
    interleave_stereo(AUDIO / 'agent_phone_en.wav', AUDIO / 'customer_phone_en.wav', AUDIO / 'phone_stereo_en.wav')
    interleave_channels(
        [AUDIO / 'quad1_en.wav', AUDIO / 'quad2_en.wav', AUDIO / 'quad3_en.wav', AUDIO / 'quad4_en.wav'],
        AUDIO / 'quad_en.wav',
    )
    interleave_channels(
        [AUDIO / 'quad1_phone_en.wav', AUDIO / 'quad2_phone_en.wav', AUDIO / 'quad3_phone_en.wav', AUDIO / 'quad4_phone_en.wav'],
        AUDIO / 'phone_quad_en.wav',
    )
    concat_wav(
        [AUDIO / 'polyglot_cmn.wav', AUDIO / 'polyglot_ja.wav', AUDIO / 'polyglot_en.wav', AUDIO / 'polyglot_de.wav'],
        AUDIO / 'polyglot_cmn_ja_en_de.wav',
    )
    print('wrote dialogue_en.wav medical_conversation.wav stereo_en.wav phone_stereo_en.wav quad_en.wav phone_quad_en.wav polyglot_cmn_ja_en_de.wav')

    rows = [
        sample('welcome', '入门 · 第一段中文', '入门对照', '先转写这一条。下一步只换语言或只开一个功能。', 'chirp3', 'welcome_cmn.wav',
               clips['welcome_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True),
        sample('news', '入门 · 通知', '入门对照', '同一把普通话，换一句更清楚的口播。', 'chirp3', 'news_cmn.wav',
               clips['news_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True),
        sample('english', '多语言 · English', '多语言', 'Chirp 3 换 locale，不是换「引擎」。', 'chirp3', 'welcome_en.wav',
               clips['welcome_en.wav'][0], model='chirp_3', language='en-US', punctuation=True),
        sample('japanese', '多语言 · 日本語', '多语言', 'ja-JP。听写实验室四个字不会出现在日文里。', 'chirp3', 'welcome_ja.wav',
               clips['welcome_ja.wav'][0], model='chirp_3', language='ja-JP', punctuation=True),
        sample('korean', '多语言 · 한국어', '多语言', 'ko-KR。', 'chirp3', 'welcome_ko.wav',
               clips['welcome_ko.wav'][0], model='chirp_3', language='ko-KR', punctuation=True),
        sample('cantonese', '多语言 · 粤语 Preview', '多语言', 'yue-Hant-HK 在 Chirp 3 语言表是 Preview。失败不代表普通话坏了。', 'chirp3', 'welcome_yue.wav',
               clips['welcome_yue.wav'][0], model='chirp_3', language='yue-Hant-HK', punctuation=True),
        sample('taiwan', '多语言 · 台湾普通话 Preview', '多语言', 'cmn-Hant-TW 是 Preview。', 'chirp3', 'welcome_tw.wav',
               clips['welcome_tw.wav'][0], model='chirp_3', language='cmn-Hant-TW', punctuation=True),
        sample('auto', '功能 · 自动检测语言', '功能怎么测', 'language_codes=auto。样例是英语，不要先入为主填中文。', 'chirp3', 'welcome_en.wav',
               clips['welcome_en.wav'][0], model='chirp_3', language='auto', punctuation=True),
        sample('timestamps', '功能 · 词级时间戳', '功能怎么测', '打开 word time offsets。流式页没有这项官方保证。', 'chirp3', 'news_cmn.wav',
               clips['news_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True, word_time=True),
        sample('adaptation', '功能 · 专有名词', '功能怎么测', '不给提示时，webeye-internal-test 和 Speech-to-Text 容易写错。提示短语会进 adaptation。', 'chirp3', 'names_cmn.wav',
               clips['names_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True,
               adaptation='webeye-internal-test, Speech-to-Text, Vertex, Speech to Text API'),
        sample('mixed', '功能 · 中英夹杂', '功能怎么测', '这是普通话 locale 里夹英文术语，不是多语切换。中日英德串联请看「多语切换」样例。提示能帮一点英文术语。', 'chirp3', 'mixed_cmn.wav',
               clips['mixed_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True,
               adaptation='Cloud Speech-to-Text, Chirp 3, cmn-Hans-CN'),
        sample('polyglot-auto', '功能 · 多语切换 · auto', '功能怎么测', '同一段中→日→英→德串联。auto 官方转最主要的语言，不是保证四段都按原文脚本。请对照下一条「列预期 locale」。', 'chirp3', 'polyglot_cmn_ja_en_de.wav',
               '大家好，欢迎参加今天的产品发布会。本日はお越しいただきありがとうございます。Hello everyone, thank you for joining this product launch. Guten Tag, willkommen zur Produkteinführung.',
               model='chirp_3', language='auto', punctuation=True),
        sample('polyglot-list', '功能 · 多语切换 · 列预期 locale', '功能怎么测', '同一段中日英德音频。Chirp 3 列预期 locale 最多 2 个（官方示例 ["en-US","fr-FR"]），所以请求只列 cmn-Hans-CN, ja-JP。发 3 个会 400。英、德仍在录音里。更多语种请用 auto。', 'chirp3', 'polyglot_cmn_ja_en_de.wav',
               '大家好，欢迎参加今天的产品发布会。本日はお越しいただきありがとうございます。Hello everyone, thank you for joining this product launch. Guten Tag, willkommen zur Produkteinführung.',
               model='chirp_3', language='cmn-Hans-CN', punctuation=True, languages='ja-JP'),
        sample('denoiser', '功能 · 降噪', '功能怎么测', '干净样例上几乎听不出差别。有价值的是请求里带了 denoiser_config。', 'chirp3', 'welcome_cmn.wav',
               clips['welcome_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True, denoiser=True),
        sample('prompt', '功能 · 格式提示 Preview', '功能怎么测', 'custom prompt 是 Preview。这里请模型把数字写成阿拉伯数字。', 'chirp3', 'news_cmn.wav',
               clips['news_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True,
               custom_prompt='Write numbers with Arabic digits. Keep punctuation.'),
        sample('diarization', '功能 · 说话人分离', '功能怎么测', '两段英语拼接。官方功能表写分离主路径是 Batch；同步 Recognize 可能成功或 400。', 'chirp3', 'dialogue_en.wav',
               'Speech to Text turns audio into text. Yes, and Chirp 3 can also label different speakers in one recording.',
               model='chirp_3', language='en-US', punctuation=True, diarization=True, word_time=True),
        sample('chirp3-stereo', '对照 · 分轨不是说话人分离', '功能怎么测', '样例 2 轨（左坐席右客户）。4 轨见本页「四声道样例」。API 最多 8 轨。这不是混音里猜说话人。Chirp 3 功能表没把多声道列为卖点。', 'chirp3', 'stereo_en.wav',
               '通道 1：Thanks for calling. How can I help you today?\n通道 2：I need to check my order A three K nine.',
               model='chirp_3', language='en-US', punctuation=True, channels=True),
        sample('chirp3-quad', '对照 · 四声道样例（上限 8 轨）', '功能怎么测', 'Chirp 3 也能 4 轨，不是电话页专属。V2 WAV/FLAC/OGG 上限 8 轨。按 4 倍时长计费。功能表没把多声道当卖点；混音会议请用说话人分离。', 'chirp3', 'quad_en.wav',
               '通道 1：Welcome to the quarterly review.\n通道 2：Revenue is up twelve percent.\n通道 3：I have a question about the timeline.\n通道 4：Let us take that offline after the call.',
               model='chirp_3', language='en-US', punctuation=True, channels=True),
        sample('lecture', '业务 · 讲解', '业务选型', '会议/讲解用 Chirp 3，不要用 telephony。', 'chirp3', 'lecture_cmn.wav',
               clips['lecture_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True),
        sample('phone-cmn', '对照 · 8 kHz 中文请用 Chirp 3', '为什么不选电话模型', '这是 8 kHz 中文客服音色，但官方 telephony 语言表没有普通话。所以这一条放在 Chirp 3，不放在 Telephony 页。', 'chirp3', 'phone_cmn.wav',
               clips['phone_cmn.wav'][0], model='chirp_3', language='cmn-Hans-CN', punctuation=True,
               adaptation='A3K928'),
        sample('chirp2-en', '对照 · 同一句英语', '对照 Chirp 3', '和 Chirp 3 英语样例同一条音频，只换模型。', 'chirp2', 'welcome_en.wav',
               clips['welcome_en.wav'][0], model='chirp_2', language='en-US', punctuation=True),
        sample('chirp2-cmn', '对照 · 同一句中文', '对照 Chirp 3', '同一条普通话。先听差别，再谈要不要升级 Chirp 3。', 'chirp2', 'welcome_cmn.wav',
               clips['welcome_cmn.wav'][0], model='chirp_2', language='cmn-Hans-CN', punctuation=True),
        sample('chirp2-time', '功能 · 词级时间戳', '功能怎么测', 'Chirp 2 文档把词级时间戳列为能力。', 'chirp2', 'welcome_en.wav',
               clips['welcome_en.wav'][0], model='chirp_2', language='en-US', punctuation=True, word_time=True),
        sample('chirp2-translate', '独有 · 语音翻译', '独有能力', '源音频是英语。目标码必须是 cmn-Hans-CN，不是 zh-CN。区域是 us-central1，不是 Chirp 3 的 us。', 'chirp2', 'welcome_en.wav',
               '你好，欢迎来到听写实验室。Cloud Speech to Text 把你的声音变成可以阅读的文字。',
               model='chirp_2', language='en-US', punctuation=True, translation_target='cmn-Hans-CN'),
        sample('phone-en', '电话 · 英语 IVR', '为什么选电话模型', '验证码按字母读。telephony 为电话通道训练。', 'telephony', 'phone_en.wav',
               clips['phone_en.wav'][0], model='telephony', language='en-US', punctuation=True,
               adaptation='A3K9'),
        sample('phone-short', '电话 · 短口令 telephony_short', '为什么选电话模型', '官方：telephony_short 针对很短甚至单个词的电话语音。对照「英语 IVR」那条更长的录音（用的是 telephony）。语言是 en-US，因为电话模型官方表没有普通话，也没有 auto。', 'telephony', 'phone_short_en.wav',
               clips['phone_short_en.wav'][0], model='telephony_short', language='en-US', punctuation=True),
        sample('phone-chirp', '电话 · chirp_telephony', '为什么选电话模型', 'chirp_telephony 把 Chirp 用到 8 kHz 电话。区域必须是 us-central1。官方只有约 10 个语言，这条是 en-US。', 'telephony', 'phone_en.wav',
               clips['phone_en.wav'][0], model='chirp_telephony', language='en-US', punctuation=True,
               adaptation='A3K9'),
        sample('phone-stereo', '电话 · 双声道样例（一对一）', '为什么选电话模型', '样例是 2 轨：左坐席、右客户。API 对 WAV/FLAC/OGG 最多 8 轨，3、4 轨同样可以，见「四声道样例」。MULAW/AMR 只能 1 轨。按轨计费。语言 en-US。', 'telephony', 'phone_stereo_en.wav',
               '通道 1：Thanks for calling. How can I help you today?\n通道 2：I need to check my order A three K nine.',
               model='telephony', language='en-US', punctuation=True, channels=True),
        sample('phone-quad', '电话 · 四声道样例（上限 8 轨）', '为什么选电话模型', '证明分轨不是只能双声道。官方 WAV/LINEAR16/FLAC/OGG 是 1–8 轨。这条 4 轨 8 kHz。按 4 倍时长计费。语言 en-US。', 'telephony', 'phone_quad_en.wav',
               '通道 1：Welcome to the quarterly review.\n通道 2：Revenue is up twelve percent.\n通道 3：I have a question about the timeline.\n通道 4：Let us take that offline after the call.',
               model='telephony', language='en-US', punctuation=True, channels=True),
        sample('medical-note', '医学 · 口授', '专用模型', '英语病历口授。医学模型官方只支持 en-US，不是中文。hypertension / metformin 是专用模型存在的理由。未开通会 403/404。', 'medical', 'medical_dictation.wav',
               clips['medical_dictation.wav'][0], model='medical_dictation', language='en-US', punctuation=True, word_time=True),
        sample('medical-talk', '医学 · 对话', '专用模型', '英语医患对话，同样只支持 en-US。两段英语拼接，不是真人问诊。中文病历请回 Chirp 3。', 'medical', 'medical_conversation.wav',
               'How long have you had the chest pain? It started last night after dinner, and it is worse when I breathe in.',
               model='medical_conversation', language='en-US', punctuation=True),
        sample('v1-long', '对照 · default 中文', 'V1 还在的原因', 'V1 latest_long / latest_short 官方语言表没有普通话。中文请用 default 或 command_and_search。新项目仍应先试 Chirp 3。', 'v1', 'lecture_cmn.wav',
               clips['lecture_cmn.wav'][0], model='default', language='cmn-Hans-CN', punctuation=True),
        sample('v1-short', '独有 · 短指令', 'V1 还在的原因', 'latest_short 针对几秒口令。', 'v1', 'command_en.wav',
               clips['command_en.wav'][0], model='latest_short', language='en-US', punctuation=True),
        sample('v1-phone', '对照 · 旧 phone_call', 'V1 还在的原因', '旧电话模型。新电话请用 V2 telephony 页。', 'v1', 'phone_en.wav',
               clips['phone_en.wav'][0], model='phone_call', language='en-US', punctuation=True),
        sample('v1-stereo', '功能 · 双声道样例（一对一）', '功能怎么测', 'V1：audio_channel_count + enable_separate_recognition_per_channel。样例 2 轨；官方 WAV/FLAC/OGG 最多 8 轨。latest_short 不能开。语言 en-US。', 'v1', 'stereo_en.wav',
               '通道 1：Thanks for calling. How can I help you today?\n通道 2：I need to check my order A three K nine.',
               model='latest_long', language='en-US', punctuation=True, channels=True),
        sample('v1-quad', '功能 · 四声道样例（上限 8 轨）', '功能怎么测', '同一套 V1 分轨字段，4 条独立声道。3 轨、5 轨也可以，上限 8。按轨计费。latest_short 不能开。', 'v1', 'quad_en.wav',
               '通道 1：Welcome to the quarterly review.\n通道 2：Revenue is up twelve percent.\n通道 3：I have a question about the timeline.\n通道 4：Let us take that offline after the call.',
               model='latest_long', language='en-US', punctuation=True, channels=True),
        sample('v1-adapt', '功能 · speechContexts', '功能怎么测', 'V1 用 speechContexts.boost，不是 V2 PhraseSet。', 'v1', 'numbers_en.wav',
               clips['numbers_en.wav'][0], model='latest_long', language='en-US', punctuation=True, word_time=True,
               adaptation='1600 Amphitheatre Parkway, Mountain View, 650-555-0100'),
        sample('v1-alt', '功能 · 多候选', '功能怎么测', 'max_alternatives=3。候选不一定更对，只是对照用。', 'v1', 'welcome_en.wav',
               clips['welcome_en.wav'][0], model='latest_long', language='en-US', punctuation=True, max_alternatives=3),
    ]
    names = []
    for index, item in enumerate(rows, start=1):
        filename = f'{index:02d}_{item["id"]}.json'
        write_json(item, filename)
        names.append(filename)
    (ASSETS / 'index.json').write_text(json.dumps({'samples': names}, indent=2) + '\n', encoding='utf-8')
    print(f'{len(names)} samples')


if __name__ == '__main__':
    main()
