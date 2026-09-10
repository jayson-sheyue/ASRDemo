"""Speech-to-Text V2 / V1 adapters. Preview does not call Google."""
from __future__ import annotations

import base64
import io
import os
import re
import traceback
import wave
from typing import Any, Iterator, Literal

from pydantic import BaseModel, Field

from catalog import CHIRP2_REGIONS, CHIRP3_DIARIZATION_LANGS, CHIRP3_REGIONS, CHIRP_TELEPHONY_LANGUAGES, CHINESE_CODES, ENGINE_LOCATIONS, MODELS, TELEPHONY_LANGUAGES, TRANSLATION_ALIASES, V1_MODELS_WITHOUT_CHINESE, V1_NO_SEPARATE_CHANNELS, WORKSPACES

MAX_AUDIO_BYTES = 8_000_000
MAX_SYNC_SECONDS = 60
MAX_LANGUAGE_CODES = 3
CHIRP3_MAX_LANGUAGE_CODES = 2
WORKSPACE_INDEX = {item['id']: item for item in WORKSPACES}


class UserError(ValueError):
    pass


class Request(BaseModel):
    engine: Literal['chirp3', 'chirp2', 'telephony', 'medical', 'v1'] = 'chirp3'
    model: str = 'chirp_3'
    language: str = 'cmn-Hans-CN'
    method: Literal['recognize', 'stream'] = 'recognize'
    sample_id: str = Field(default='', max_length=80)
    audio_b64: str = Field(default='', max_length=12_000_000)
    filename: str = Field(default='', max_length=200)
    punctuation: bool = True
    word_time: bool = False
    word_confidence: bool = False
    diarization: bool = False
    adaptation: str = Field(default='', max_length=2000)
    denoiser: bool = False
    custom_prompt: str = Field(default='', max_length=500)
    translation_target: str = Field(default='', max_length=20)
    profanity_filter: bool = False
    max_alternatives: int = Field(default=1, ge=1, le=5)
    channels: bool = False
    languages: str = Field(default='', max_length=400)
    location: str = Field(default='', max_length=32)


def adc_available() -> bool:
    try:
        import google.auth
        credentials, _project = google.auth.default()
        return credentials is not None
    except Exception:
        return False


def require_auth() -> None:
    if not (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip():
        raise UserError('请在 .env 填写 GOOGLE_CLOUD_PROJECT，并运行：gcloud auth application-default login。预览无需凭据。')
    if not adc_available():
        raise UserError('未检测到 Application Default Credentials。请运行：gcloud auth application-default login，然后 gcloud auth application-default set-quota-project 你的项目ID，并重启服务。')


def workspace(engine: str) -> dict:
    spec = WORKSPACE_INDEX.get(engine)
    if not spec:
        raise UserError('未知工作台。')
    return spec


def phrases(raw: str) -> list[str]:
    items = []
    for part in re.split(r'[\n,，;；]+', raw or ''):
        text = part.strip()
        if text and text not in items:
            items.append(text[:100])
        if len(items) >= 20:
            break
    return items


def recognition_languages(r: Request) -> list[str]:
    spec = workspace(r.engine)
    primary = (r.language or '').strip() or ('en-US' if r.engine == 'medical' else 'cmn-Hans-CN')
    extras = []
    for part in re.split(r'[\n,，;；]+', r.languages or ''):
        text = part.strip()
        if text and text not in extras:
            extras.append(text)
    codes = []
    for item in [primary] + extras:
        if item and item not in codes:
            codes.append(item)
    if 'auto' in codes:
        if len(codes) > 1:
            raise UserError('language_codes=auto 不能和具体 locale 写在一起。Chirp 3 请改列最多 2 个具体 locale（例如 cmn-Hans-CN, ja-JP），或只保留 auto。')
        if 'language_auto' not in spec['features']:
            raise UserError('自动语言检测只在 Chirp 3。请选一个具体 locale。')
        return ['auto']
    if len(codes) > 1 and r.engine != 'chirp3':
        raise UserError('列出多个 locale 只在 Chirp 3。Chirp 2 / 电话 / V1 / 医学页请只选一个语言。V1 的 alternative_language_codes 也不是语码切换。')
    if r.engine == 'chirp3' and len(codes) > CHIRP3_MAX_LANGUAGE_CODES:
        raise UserError('Chirp 3 列预期 locale 最多 2 个。官方示例是 ["en-US","fr-FR"]。V2 多语言页写的「最多 3 个」针对 latest_long / short / telephony；chirp_3 发 3 个会 400。音频可以有更多语种，或改用 auto。')
    if len(codes) > MAX_LANGUAGE_CODES:
        raise UserError('language_codes 最多 3 个。官方文档：You can list up to three languages。')
    return codes


def location_for(r: Request) -> str:
    spec = workspace(r.engine)
    default = ENGINE_LOCATIONS.get(r.engine) or 'us'
    raw = (r.location or os.getenv('GOOGLE_CLOUD_LOCATION') or '').strip()
    if spec['api'] != 'v2':
        return raw or 'us'
    if r.engine == 'chirp2' or r.model == 'chirp_telephony':
        if raw in CHIRP2_REGIONS:
            return raw
        return 'us-central1'
    if raw in CHIRP3_REGIONS:
        return raw
    return default


def translation_target(raw: str) -> str:
    text = (raw or '').strip()
    if not text:
        return ''
    return TRANSLATION_ALIASES.get(text, TRANSLATION_ALIASES.get(text.replace('_', '-'), text))


def wav_info(data: bytes) -> tuple[int, int, int] | None:
    if len(data) < 44 or data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        return None
    try:
        with wave.open(io.BytesIO(data)) as handle:
            return handle.getnchannels(), handle.getsampwidth(), handle.getframerate()
    except wave.Error:
        return None


def wav_duration_seconds(data: bytes) -> float | None:
    info = wav_info(data)
    if not info:
        return None
    channels, width, rate = info
    if not rate or not width:
        return None
    frames = (len(data) - 44) / (channels * width)
    return frames / rate


def decode_audio(r: Request) -> bytes:
    if r.audio_b64.strip():
        try:
            data = base64.b64decode(r.audio_b64, validate=False)
        except Exception as error:
            raise UserError('音频 Base64 无法解码。') from error
        if not data:
            raise UserError('音频是空的。')
        if len(data) > MAX_AUDIO_BYTES:
            raise UserError('本 Demo 单次音频不超过 8 MB。请截短后再试。')
        return data
    raise UserError('请上传音频、录音，或点一个带声音的样例。')


def plan(r: Request, audio: bytes | None = None) -> dict:
    spec = workspace(r.engine)
    allowed = MODELS[r.engine]
    if r.model not in allowed:
        raise UserError(f'本页模型只能是：{" / ".join(allowed)}。')
    if r.method == 'stream' and 'stream' not in spec['features']:
        raise UserError('这一页不提供工作台流式。请用同步转写。')
    if r.diarization and 'diarization' not in spec['features']:
        raise UserError('这一页没有说话人分离开关。')
    if r.translation_target and 'translation' not in spec['features']:
        raise UserError('语音翻译只在 Chirp 2 页。')
    if r.custom_prompt and 'custom_prompt' not in spec['features']:
        raise UserError('自定义格式提示只在 Chirp 3 页，且是 Preview。')
    if r.denoiser and 'denoiser' not in spec['features']:
        raise UserError('降噪只在 Chirp 页发送 denoiser_config。')
    if r.channels and 'channels' not in spec['features']:
        raise UserError('这一页没有分轨识别。Chirp 2 / 医学页不开放该开关。')
    if r.channels and r.model in V1_NO_SEPARATE_CHANNELS:
        raise UserError('官方：SEPARATE_RECOGNITION_PER_CHANNEL 不能和 latest_short 一起用。请改 latest_long，或关掉分轨。')
    if r.channels and r.diarization:
        raise UserError('分轨识别和说话人分离不要一起开。录音已经分轨用「分轨识别」；一路混音才用说话人分离。')
    codes = recognition_languages(r)
    language = codes[0]
    if r.engine == 'medical' and language != 'en-US':
        raise UserError('医学模型官方只支持 en-US（美国英语）。不是所有英语，也不是中文。英式 en-GB、澳式 en-AU 也不行。中文病历请到 Chirp 3 页，并用短语提示药名。')
    loc = location_for(r)
    target = translation_target(r.translation_target) if r.translation_target else ''
    warnings = []
    raw_loc = (r.location or os.getenv('GOOGLE_CLOUD_LOCATION') or '').strip()
    if spec['api'] == 'v2' and raw_loc and raw_loc != loc:
        if r.engine == 'chirp2' or r.model == 'chirp_telephony':
            warnings.append(f'{r.model} 不在 {raw_loc}。已改用 {loc}（官方区域：us-central1 / europe-west4 / asia-southeast1）。')
        else:
            warnings.append(f'{r.model} 不在 {raw_loc}。已改用 {loc}（Chirp 3 / telephony 用 us 或 eu）。')
    if target and target != r.translation_target.strip():
        warnings.append(f'翻译目标 {r.translation_target.strip()} 已改成官方码 {target}。英语→简体中文是 cmn-Hans-CN，不是 zh-CN。')
    if r.diarization and r.engine == 'chirp3':
        if language != 'auto' and language not in CHIRP3_DIARIZATION_LANGS:
            warnings.append(f'{language} 不在 Chirp 3 说话人分离语言表。请求仍会发送，端点可能拒绝。')
        warnings.append('Chirp 3 功能表写分离仅 BatchRecognize；语言表写 Recognize 也可。本 Demo 同步请求仍会带上 diarization_config。')
    if r.word_time and r.method == 'stream' and r.engine == 'chirp3':
        warnings.append('Chirp 3 词级时间戳官方写在 Recognize / Batch，不在 Streaming。流式可能只有句级时间。')
    if r.custom_prompt.strip():
        warnings.append('custom prompt 是 Preview，格式不保证。')
    if r.method == 'stream' and r.engine == 'telephony':
        warnings.append('工作台实时听写走官方 StreamingRecognize，但浏览器麦克风是 16 kHz PCM，不能代表 8 kHz 听筒音质。')
    if r.channels:
        warnings.append('分轨识别按声道计费。WAV/FLAC/OGG 官方 1–8 轨；样例常用 2 轨，3、4 轨同样合法。MULAW/AMR 只能 1 轨。结果用 channel_tag 标轨，不是说话人分离。')
        if r.engine == 'chirp3':
            warnings.append('Chirp 3 官方功能表没有把多声道列为卖点。混音会议请用说话人分离；已经分轨的录音才开这个开关。')
        if r.method == 'stream':
            warnings.append('浏览器麦克风是单声道。分轨请用立体声样例或上传多声道 WAV，再点同步转写。')
    if r.model == 'chirp_telephony':
        allowed = {item['code'] for item in CHIRP_TELEPHONY_LANGUAGES}
        if language not in allowed:
            raise UserError('chirp_telephony 官方只有 10 个语言（en-US / en-GB / en-AU / de-DE / es-ES / es-US / fr-FR / fr-CA / it-IT / pt-BR）。普通话请用 Chirp 3，或改回 telephony。')
    if r.engine == 'telephony' and r.model in {'telephony', 'telephony_short'}:
        allowed = {item['code'] for item in TELEPHONY_LANGUAGES}
        if language not in allowed:
            warnings.append(f'{language} 不在 V2 telephony 官方语言表（us/eu 约 44 个 locale，没有普通话）。请求仍会发送，端点可能拒绝。')
    if r.engine == 'v1' and r.model in V1_MODELS_WITHOUT_CHINESE and language in CHINESE_CODES:
        warnings.append(f'{r.model} 官方语言表没有普通话/粤语。中文请改 default 或 command_and_search，新项目仍应先 Chirp 3。请求仍会发送，端点可能拒绝。')
    if codes == ['auto']:
        warnings.append('language_codes=auto 官方转「最主要 / 最常见」的语言，不是保证每种语言都按原文出稿。已知会夹杂哪几种时，请改列具体 locale。')
    elif len(codes) > 1:
        warnings.append('官方：列出预期 locale 会把资源集中在这些语种。Chirp 3 同一请求最多 2 个（示例 ["en-US","fr-FR"]）。proto 仍写结果是检测到的最可能语言。')
    if r.engine == 'medical':
        warnings.append('医学模型官方只支持 en-US，且是 Premium。项目未开通时会 403/404，这是预期。')
    if audio is not None:
        duration = wav_duration_seconds(audio)
        if duration and duration > MAX_SYNC_SECONDS and r.method == 'recognize':
            raise UserError(f'同步 Recognize 请使用短于 {MAX_SYNC_SECONDS} 秒的音频。更长的请用 batch_demo.py。')
        info = wav_info(audio)
        if spec['api'] == 'v1' and info is None:
            warnings.append('V1 页更稳妥的是 WAV。WebM/MP3 自动解码是 V2 能力，V1 可能拒绝。')
        if r.engine == 'telephony' and info and info[2] not in {8000, 16000}:
            warnings.append(f'当前 WAV 采样率是 {info[2]} Hz。telephony 更适合 8 kHz 电话。')
        if info and info[0] > 1 and not r.channels:
            warnings.append(f'当前 WAV 有 {info[0]} 个声道。默认只转第一轨。要按轨出稿请打开「分轨识别」。')
        if r.channels and info and info[0] <= 1:
            warnings.append('当前音频是单声道。打开分轨也不会出现第二条轨。请用立体声样例或上传多声道 WAV。')
        if r.channels and info and info[0] > 8:
            warnings.append(f'官方多声道最多 8 轨。当前 WAV 有 {info[0]} 个声道。')
    hints = phrases(r.adaptation)
    payload = request_preview(r, spec, codes, loc, hints, audio)
    return {
        'api': spec['api'],
        'engine': r.engine,
        'model': r.model,
        'method': r.method,
        'language': language,
        'language_codes': codes,
        'location': loc,
        'recognizer': f"projects/$PROJECT/locations/{loc}/recognizers/_" if spec['api'] == 'v2' else None,
        'features': [name for name in spec['features']],
        'phrase_hints': hints,
        'audio_bytes': len(audio) if audio is not None else 0,
        'warnings': warnings,
        'request': payload,
    }


def request_preview(r: Request, spec: dict, languages: list[str], loc: str, hints: list[str], audio: bytes | None) -> dict:
    features: dict[str, Any] = {
        'enable_automatic_punctuation': r.punctuation,
        'enable_word_time_offsets': r.word_time and r.method != 'stream',
        'enable_word_confidence': r.word_confidence,
    }
    if r.diarization:
        features['diarization_config'] = {'min_speaker_count': 2, 'max_speaker_count': 6}
    if r.channels:
        features['multi_channel_mode'] = 'SEPARATE_RECOGNITION_PER_CHANNEL'
    if r.profanity_filter and 'profanity' in spec['features']:
        features['profanity_filter'] = True
    if r.max_alternatives > 1 and 'alternatives' in spec['features']:
        features['max_alternatives'] = r.max_alternatives
    body: dict[str, Any] = {
        'model': r.model,
        'decoding': 'auto_detect' if spec['api'] == 'v2' else 'wav_or_explicit',
    }
    language = languages[0] if languages else 'en-US'
    if spec['api'] == 'v2':
        body['language_codes'] = languages
        body['features'] = features
        if hints:
            body['adaptation'] = {'phrases': hints}
        if r.denoiser:
            body['denoiser_config'] = {'denoise_audio': True, 'snr_threshold': 0.0}
        if r.custom_prompt.strip():
            body['features']['custom_prompt'] = r.custom_prompt.strip()
        if r.translation_target.strip():
            body['translation_config'] = {'target_language': translation_target(r.translation_target)}
        body['recognizer'] = f'projects/$PROJECT/locations/{loc}/recognizers/_'
        body['endpoint'] = f'{loc}-speech.googleapis.com'
    else:
        body['language_code'] = language if language != 'auto' else 'en-US'
        body['enable_automatic_punctuation'] = r.punctuation
        body['enable_word_time_offsets'] = r.word_time
        if r.diarization:
            body['diarization_config'] = {'enable_speaker_diarization': True, 'min_speaker_count': 2, 'max_speaker_count': 6}
        if hints:
            body['speech_contexts'] = [{'phrases': hints, 'boost': 15.0}]
        if r.profanity_filter:
            body['profanity_filter'] = True
        if r.max_alternatives > 1:
            body['max_alternatives'] = r.max_alternatives
        if r.channels:
            body['enable_separate_recognition_per_channel'] = True
        info = wav_info(audio) if audio else None
        if info:
            body['sample_rate_hertz'] = info[2]
            body['encoding'] = 'LINEAR16'
            body['audio_channel_count'] = info[0]
        elif r.channels:
            body['audio_channel_count'] = 2
    return body


def offset_seconds(value) -> float | None:
    if value is None:
        return None
    if hasattr(value, 'total_seconds'):
        return round(value.total_seconds(), 3)
    seconds = getattr(value, 'seconds', 0) or 0
    nanos = getattr(value, 'nanos', 0) or 0
    return round(seconds + nanos / 1e9, 3)


def word_entry(word) -> dict:
    item = {
        'word': getattr(word, 'word', None) or getattr(word, 'spoken_text', '') or '',
        'start': offset_seconds(getattr(word, 'start_offset', None) or getattr(word, 'start_time', None)),
        'end': offset_seconds(getattr(word, 'end_offset', None) or getattr(word, 'end_time', None)),
        'confidence': getattr(word, 'confidence', None),
        'speaker': getattr(word, 'speaker_label', None) or getattr(word, 'speaker_tag', None),
    }
    return item


def parse_v2_results(response) -> dict:
    results = []
    grouped: dict[int, list[str]] = {}
    texts = []
    for result in getattr(response, 'results', []) or []:
        alts = list(getattr(result, 'alternatives', []) or [])
        if not alts:
            continue
        top = alts[0]
        transcript = getattr(top, 'transcript', '') or ''
        texts.append(transcript)
        tag = int(getattr(result, 'channel_tag', 0) or 0)
        grouped.setdefault(tag, []).append(transcript)
        results.append({
            'transcript': transcript,
            'confidence': getattr(top, 'confidence', None),
            'language_code': getattr(result, 'language_code', None),
            'channel_tag': tag or None,
            'is_final': getattr(result, 'is_final', True),
            'alternatives': [getattr(item, 'transcript', '') for item in alts[1:]],
            'words': [word_entry(word) for word in getattr(top, 'words', []) or []],
        })
    if any(tag > 0 for tag in grouped):
        transcript = '\n'.join(
            f'通道 {tag}：{"".join(parts).strip()}'
            for tag, parts in sorted(grouped.items()) if tag > 0
        )
    else:
        transcript = ''.join(texts).strip() or ' '.join(part.strip() for part in texts if part.strip())
    return {
        'transcript': transcript,
        'results': results,
    }


def parse_v1_results(response) -> dict:
    return parse_v2_results(response)


def v2_config(r: Request, languages: list[str]):
    from google.cloud.speech_v2.types import cloud_speech
    spec = workspace(r.engine)
    features_kwargs: dict[str, Any] = {
        'enable_automatic_punctuation': r.punctuation,
        'enable_word_time_offsets': bool(r.word_time and r.method != 'stream'),
        'enable_word_confidence': r.word_confidence,
    }
    if r.diarization:
        features_kwargs['diarization_config'] = cloud_speech.SpeakerDiarizationConfig(min_speaker_count=2, max_speaker_count=6)
    if r.profanity_filter and 'profanity' in spec['features']:
        features_kwargs['profanity_filter'] = True
    if r.max_alternatives > 1 and 'alternatives' in spec['features']:
        features_kwargs['max_alternatives'] = r.max_alternatives
    if r.custom_prompt.strip():
        features_kwargs['custom_prompt_config'] = cloud_speech.CustomPromptConfig(custom_prompt=r.custom_prompt.strip())
    if r.channels:
        features_kwargs['multi_channel_mode'] = cloud_speech.RecognitionFeatures.MultiChannelMode.SEPARATE_RECOGNITION_PER_CHANNEL
    kwargs: dict[str, Any] = {
        'auto_decoding_config': cloud_speech.AutoDetectDecodingConfig(),
        'language_codes': languages,
        'model': r.model,
        'features': cloud_speech.RecognitionFeatures(**features_kwargs),
    }
    hints = phrases(r.adaptation)
    if hints:
        kwargs['adaptation'] = cloud_speech.SpeechAdaptation(
            phrase_sets=[
                cloud_speech.SpeechAdaptation.AdaptationPhraseSet(
                    inline_phrase_set=cloud_speech.PhraseSet(
                        phrases=[cloud_speech.PhraseSet.Phrase(value=item, boost=10) for item in hints]
                    )
                )
            ]
        )
    if r.denoiser:
        kwargs['denoiser_config'] = cloud_speech.DenoiserConfig(denoise_audio=True, snr_threshold=0.0)
    target = translation_target(r.translation_target)
    if target and hasattr(cloud_speech, 'TranslationConfig'):
        kwargs['translation_config'] = cloud_speech.TranslationConfig(target_language=target)
    return cloud_speech.RecognitionConfig(**kwargs)


def v2_client(loc: str):
    from google.api_core.client_options import ClientOptions
    from google.cloud.speech_v2 import SpeechClient
    return SpeechClient(client_options=ClientOptions(api_endpoint=f'{loc}-speech.googleapis.com'))


def recognize_v2(r: Request, audio: bytes) -> dict:
    from google.cloud.speech_v2.types import cloud_speech
    spec_plan = plan(r, audio)
    languages = spec_plan['language_codes']
    loc = spec_plan['location']
    project = os.environ['GOOGLE_CLOUD_PROJECT'].strip()
    client = v2_client(loc)
    request = cloud_speech.RecognizeRequest(
        recognizer=f'projects/{project}/locations/{loc}/recognizers/_',
        config=v2_config(r, languages),
        content=audio,
    )
    response = client.recognize(request=request)
    parsed = parse_v2_results(response)
    parsed['warnings'] = spec_plan['warnings']
    parsed['model'] = r.model
    parsed['api'] = 'v2'
    return parsed


def recognize_v1(r: Request, audio: bytes) -> dict:
    from google.cloud import speech_v1
    spec_plan = plan(r, audio)
    language = spec_plan['language']
    if language == 'auto':
        raise UserError('V1 没有 language_codes=auto。请选具体语言。')
    client = speech_v1.SpeechClient()
    info = wav_info(audio)
    config_kwargs: dict[str, Any] = {
        'language_code': language,
        'model': r.model,
        'enable_automatic_punctuation': r.punctuation,
        'enable_word_time_offsets': r.word_time,
        'enable_word_confidence': r.word_confidence,
        'profanity_filter': r.profanity_filter,
        'max_alternatives': r.max_alternatives,
    }
    if info:
        config_kwargs['encoding'] = speech_v1.RecognitionConfig.AudioEncoding.LINEAR16
        config_kwargs['sample_rate_hertz'] = info[2]
        config_kwargs['audio_channel_count'] = info[0]
    else:
        config_kwargs['encoding'] = speech_v1.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
    hints = phrases(r.adaptation)
    if hints:
        config_kwargs['speech_contexts'] = [speech_v1.SpeechContext(phrases=hints, boost=15.0)]
    if r.diarization:
        config_kwargs['diarization_config'] = speech_v1.SpeakerDiarizationConfig(
            enable_speaker_diarization=True, min_speaker_count=2, max_speaker_count=6
        )
    if r.channels:
        config_kwargs['enable_separate_recognition_per_channel'] = True
        if not info:
            config_kwargs['audio_channel_count'] = 2
    response = client.recognize(
        config=speech_v1.RecognitionConfig(**config_kwargs),
        audio=speech_v1.RecognitionAudio(content=audio),
    )
    parsed = parse_v1_results(response)
    parsed['warnings'] = spec_plan['warnings']
    parsed['model'] = r.model
    parsed['api'] = 'v1'
    return parsed


def recognize(r: Request, audio: bytes) -> dict:
    require_auth()
    planned = plan(r, audio)
    if planned['api'] == 'v2':
        return recognize_v2(r, audio)
    return recognize_v1(r, audio)


def stream_v2(r: Request, chunks: Iterator[bytes]) -> Iterator[dict]:
    from google.cloud.speech_v2.types import cloud_speech
    require_auth()
    planned = plan(r)
    languages = planned['language_codes']
    loc = planned['location']
    project = os.environ['GOOGLE_CLOUD_PROJECT'].strip()
    client = v2_client(loc)
    config = v2_config(r, languages)
    streaming_config = cloud_speech.StreamingRecognitionConfig(config=config)
    config_request = cloud_speech.StreamingRecognizeRequest(
        recognizer=f'projects/{project}/locations/{loc}/recognizers/_',
        streaming_config=streaming_config,
    )

    def requests():
        yield config_request
        for chunk in chunks:
            if chunk:
                yield cloud_speech.StreamingRecognizeRequest(audio=chunk)

    for response in client.streaming_recognize(requests=requests()):
        parsed = parse_v2_results(response)
        parsed['model'] = r.model
        parsed['api'] = 'v2'
        parsed['warnings'] = planned['warnings']
        yield parsed


def stream_v1(r: Request, chunks: Iterator[bytes]) -> Iterator[dict]:
    from google.cloud import speech_v1
    require_auth()
    planned = plan(r)
    language = planned['language']
    client = speech_v1.SpeechClient()
    config = speech_v1.RecognitionConfig(
        encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language,
        model=r.model,
        enable_automatic_punctuation=r.punctuation,
        enable_word_time_offsets=False,
    )

    def requests():
        yield speech_v1.StreamingRecognizeRequest(streaming_config=speech_v1.StreamingRecognitionConfig(config=config, interim_results=True))
        for chunk in chunks:
            if chunk:
                yield speech_v1.StreamingRecognizeRequest(audio_content=chunk)

    for response in client.streaming_recognize(requests=requests()):
        parsed = parse_v1_results(response)
        parsed['model'] = r.model
        parsed['api'] = 'v1'
        yield parsed


def transcribe_stream(r: Request, chunks: Iterator[bytes]) -> Iterator[dict]:
    spec = workspace(r.engine)
    if spec['api'] == 'v2':
        yield from stream_v2(r, chunks)
    else:
        yield from stream_v1(r, chunks)


_SECRET = re.compile(r'(?i)((?:api[_-]?key|token|bearer|authorization|ya29\.|AIza)[=:\s]+)[^\s,;\'"]+')


def redact(text: str) -> str:
    return _SECRET.sub(r'\1***', text)


def error_payload(error: Exception) -> dict:
    raw = redact(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
    return {
        'message': error_message(error),
        'detail': raw.strip() or type(error).__name__,
        'error_type': type(error).__name__,
    }


def error_message(error: Exception) -> str:
    if isinstance(error, UserError):
        return str(error)
    msg = str(error).lower()
    if any(x in msg for x in ('429', 'resource_exhausted', 'quota')):
        return '请求过于频繁或额度不足（429）。请检查配额/账单，稍后再试。'
    if any(x in msg for x in ('401', '403', 'permission', 'credential', 'adc', 'reauth', 'unauthenticated')):
        return '身份验证或权限失败。请检查 ADC、GOOGLE_CLOUD_PROJECT、是否已启用 speech.googleapis.com、账单和 IAM。医学模型可能需额外开通。'
    if 'does not exist in the location' in msg or 'does not exist in the location' in str(error):
        return '这个模型不在当前区域。Chirp 3 用 us / eu；Chirp 2 用 us-central1（不要把 chirp_2 发到 us）。'
    if '404' in msg or 'not_found' in msg:
        return '模型或区域不可用（404）。Chirp 3 请用 us 或 eu；Chirp 2 请用 us-central1。'
    if '400' in msg or 'invalid_argument' in msg:
        return '参数不被服务接受（400）。Chirp 3 列预期 locale 最多 2 个；3 个会 400。也请检查语言代码、模型与区域、音频格式。Chirp 2 翻译目标用 cmn-Hans-CN 而不是 zh-CN。说话人分离可能仅 Batch。'
    if any(x in msg for x in ('timeout', 'deadline', 'connect', 'resolve')):
        return '连接超时或网络不可达。已发出的请求仍可能计费。'
    return '转写失败。请换短音频、关一项高级功能后重试，并对照官方模型页。'
