from __future__ import annotations

from catalog import CHINESE_CODES, WORKSPACES, language_codes_for
from samples import load_samples


def test_samples_load_and_audio_exists():
    samples = load_samples()
    assert len(samples) >= 16
    assert samples[0]['id'] == 'welcome'
    engines = {item['engine'] for item in samples}
    assert engines == {'chirp3', 'chirp2', 'telephony', 'medical', 'v1'}
    assert any(item['config'].get('model') == 'telephony_short' for item in samples)
    assert any(item['id'] == 'phone-short' for item in samples)
    assert any(item['id'] == 'phone-chirp' and item['config'].get('model') == 'chirp_telephony' for item in samples)
    assert any(item['id'] == 'polyglot-auto' for item in samples)
    assert any(item['id'] == 'polyglot-list' and 'ja-JP' in (item['config'].get('languages') or '') for item in samples)
    for item in samples:
        assert item['config'].get('model')
        assert item.get('audio')
        assert item.get('expected')


def test_sample_locales_match_official_model_tables():
    samples = load_samples()
    ids = [item['id'] for item in samples]
    files = [item['file'] for item in samples]
    assert len(ids) == len(set(ids))
    assert len(files) == len(set(files))
    by_page = {item['id']: item for item in WORKSPACES}
    phone_cmn = next(item for item in samples if item['id'] == 'phone-cmn')
    assert phone_cmn['engine'] == 'chirp3'
    assert phone_cmn['config']['model'] == 'chirp_3'
    v1_long = next(item for item in samples if item['id'] == 'v1-long')
    assert v1_long['config']['model'] == 'default'
    stereo = [item for item in samples if item['id'] in {'chirp3-stereo', 'phone-stereo', 'v1-stereo'}]
    assert len(stereo) == 3
    assert all(item['config'].get('channels') for item in stereo)
    from asr import wav_info
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    polyglot = next(item for item in samples if item['id'] == 'polyglot-list')
    channels, _width, rate = wav_info((root / 'sample_assets' / 'audio' / polyglot['audio']).read_bytes())
    assert channels == 1 and rate == 16000
    for item in stereo:
        channels, _width, rate = wav_info((root / 'sample_assets' / 'audio' / item['audio']).read_bytes())
        assert channels == 2
        if item['id'] == 'phone-stereo':
            assert rate == 8000
        else:
            assert rate == 16000
    quad = [item for item in samples if item['id'] in {'phone-quad', 'v1-quad', 'chirp3-quad'}]
    assert len(quad) == 3
    for item in quad:
        channels, _width, rate = wav_info((root / 'sample_assets' / 'audio' / item['audio']).read_bytes())
        assert channels == 4
        assert item['config'].get('channels')
        if item['id'] == 'phone-quad':
            assert rate == 8000
        else:
            assert rate == 16000
    for item in samples:
        engine = item['engine']
        model = item['config']['model']
        language = item['config']['language']
        allowed = language_codes_for(engine, model)
        assert language in allowed, f'{item["id"]}: {language} 不在 {engine}/{model} 官方语言表'
        if language == 'auto':
            assert 'language_auto' in by_page[engine]['features']
        extras = [part.strip() for part in (item['config'].get('languages') or '').replace('，', ',').split(',') if part.strip()]
        for extra in extras:
            assert extra in allowed, f'{item["id"]}: extra {extra} 不在 {engine}/{model} 官方语言表'
            assert extra != 'auto'
        if extras:
            assert engine == 'chirp3'
            assert language != 'auto'
        if engine == 'telephony':
            assert language not in CHINESE_CODES
            assert language != 'auto'
