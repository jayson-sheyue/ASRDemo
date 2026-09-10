from __future__ import annotations

from pathlib import Path

from asr import Request, UserError, location_for, phrases, plan, wav_info


ROOT = Path(__file__).resolve().parents[1]


def test_phrases_and_location():
    assert phrases('webeye-internal-test, Speech-to-Text；Vertex') == [
        'webeye-internal-test', 'Speech-to-Text', 'Vertex'
    ]
    r = Request(engine='chirp3', location='global')
    assert location_for(r) == 'us'
    assert location_for(Request(engine='chirp2', location='us')) == 'us-central1'
    assert location_for(Request(engine='chirp2', location='us-central1')) == 'us-central1'
    r2 = Request(engine='medical', location='us-central1')
    assert location_for(r2) == 'us-central1'
    assert location_for(Request(engine='telephony', model='chirp_telephony', location='us')) == 'us-central1'
    assert location_for(Request(engine='telephony', model='telephony', location='us')) == 'us'


def test_plan_v2_features():
    audio = (ROOT / 'sample_assets' / 'audio' / 'welcome_cmn.wav').read_bytes()
    assert wav_info(audio)[2] == 16000
    body = plan(Request(engine='chirp3', model='chirp_3', language='auto', denoiser=True, adaptation='Chirp 3'), audio)
    assert body['request']['language_codes'] == ['auto']
    assert body['request']['denoiser_config']['denoise_audio'] is True
    assert body['phrase_hints'] == ['Chirp 3']
    phone = (ROOT / 'sample_assets' / 'audio' / 'phone_cmn.wav').read_bytes()
    assert wav_info(phone)[2] == 8000
    tel_en = plan(Request(engine='telephony', model='telephony', language='en-US'),
                  (ROOT / 'sample_assets' / 'audio' / 'phone_en.wav').read_bytes())
    assert tel_en['model'] == 'telephony'
    assert not any('普通话' in item for item in tel_en['warnings'])
    tel = plan(Request(engine='telephony', model='telephony', language='cmn-Hans-CN'), phone)
    assert tel['model'] == 'telephony'
    assert any('普通话' in item or 'locale' in item for item in tel['warnings'])
    streamed = plan(Request(engine='telephony', model='telephony', language='en-US', method='stream'))
    assert 'stream' in streamed['features']
    assert any('16 kHz' in item for item in streamed['warnings'])
    chirp_tel = plan(Request(engine='telephony', model='chirp_telephony', language='en-US', location='us'))
    assert chirp_tel['location'] == 'us-central1'
    try:
        plan(Request(engine='telephony', model='chirp_telephony', language='cmn-Hans-CN'))
        assert False
    except UserError as error:
        assert 'chirp_telephony' in str(error)


def test_plan_polyglot_language_codes():
    audio = (ROOT / 'sample_assets' / 'audio' / 'welcome_cmn.wav').read_bytes()
    listed = plan(Request(
        engine='chirp3', model='chirp_3', language='cmn-Hans-CN', languages='ja-JP',
    ), audio)
    assert listed['language_codes'] == ['cmn-Hans-CN', 'ja-JP']
    assert listed['request']['language_codes'] == ['cmn-Hans-CN', 'ja-JP']
    assert any('最多 2' in item for item in listed['warnings'])
    auto = plan(Request(engine='chirp3', model='chirp_3', language='auto'), audio)
    assert auto['request']['language_codes'] == ['auto']
    assert any('最主要' in item for item in auto['warnings'])
    try:
        plan(Request(engine='chirp3', model='chirp_3', language='auto', languages='en-US'))
        assert False
    except UserError as error:
        assert 'auto' in str(error)
    try:
        plan(Request(engine='chirp3', model='chirp_3', language='cmn-Hans-CN', languages='ja-JP,en-US'))
        assert False
    except UserError as error:
        assert '最多 2' in str(error)
    try:
        plan(Request(engine='telephony', model='telephony', language='en-US', languages='de-DE'))
        assert False
    except UserError as error:
        assert 'Chirp 3' in str(error)
    try:
        plan(Request(engine='v1', model='latest_long', language='en-US', languages='de-DE'))
        assert False
    except UserError as error:
        assert 'Chirp 3' in str(error)


def test_plan_rejects_wrong_page_features():
    try:
        plan(Request(engine='telephony', model='telephony', translation_target='zh-CN'))
        assert False
    except UserError as error:
        assert '翻译' in str(error)
    try:
        plan(Request(engine='chirp3', model='chirp_2'))
        assert False
    except UserError as error:
        assert 'chirp_3' in str(error)
    translated = plan(Request(engine='chirp2', model='chirp_2', language='en-US', translation_target='zh-CN'))
    assert translated['location'] == 'us-central1'
    assert translated['request']['translation_config']['target_language'] == 'cmn-Hans-CN'
    assert any('cmn-Hans-CN' in item for item in translated['warnings'])
    v1_zh = plan(Request(engine='v1', model='latest_long', language='cmn-Hans-CN'))
    assert any('latest_long' in item and '普通话' in item for item in v1_zh['warnings'])
    try:
        plan(Request(engine='medical', model='medical_dictation', language='en-US', method='stream'))
        assert False
    except UserError as error:
        assert '流式' in str(error)


def test_plan_channels_flags_and_guards():
    stereo = (ROOT / 'sample_assets' / 'audio' / 'stereo_en.wav').read_bytes()
    phone = (ROOT / 'sample_assets' / 'audio' / 'phone_stereo_en.wav').read_bytes()
    v2 = plan(Request(engine='telephony', model='telephony', language='en-US', channels=True), phone)
    assert v2['request']['features']['multi_channel_mode'] == 'SEPARATE_RECOGNITION_PER_CHANNEL'
    v1 = plan(Request(engine='v1', model='latest_long', language='en-US', channels=True), stereo)
    assert v1['request']['enable_separate_recognition_per_channel'] is True
    assert v1['request']['audio_channel_count'] == 2
    chirp = plan(Request(engine='chirp3', model='chirp_3', language='en-US', channels=True), stereo)
    assert any('功能表' in item for item in chirp['warnings'])
    try:
        plan(Request(engine='v1', model='latest_short', language='en-US', channels=True))
        assert False
    except UserError as error:
        assert 'latest_short' in str(error)
    try:
        plan(Request(engine='chirp2', model='chirp_2', language='en-US', channels=True))
        assert False
    except UserError as error:
        assert '分轨' in str(error)
    try:
        plan(Request(engine='chirp3', model='chirp_3', language='en-US', channels=True, diarization=True))
        assert False
    except UserError as error:
        assert '说话人分离' in str(error)


def test_medical_language_only_en_us():
    ok = plan(Request(engine='medical', model='medical_dictation', language='en-US'))
    assert ok['language'] == 'en-US'
    assert any('en-US' in item for item in ok['warnings'])
    try:
        plan(Request(engine='medical', model='medical_dictation', language='cmn-Hans-CN'))
        assert False
    except UserError as error:
        assert 'en-US' in str(error)
        assert '中文' in str(error)
    try:
        plan(Request(engine='medical', model='medical_dictation', language='en-GB'))
        assert False
    except UserError as error:
        assert 'en-US' in str(error)
