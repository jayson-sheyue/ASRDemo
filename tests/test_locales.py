from __future__ import annotations

from catalog import COMPARE_MODELS, FEATURE_VALUE, MODELS, MODEL_LANGUAGES, WORKSPACES
from locales import CHIRP2_LANGUAGES, CHIRP3_LANGUAGES, CHIRP_TELEPHONY_LANGUAGES, TELEPHONY_LANGUAGES, V1_LANGUAGES


def _codes(items):
    return {item['code'] for item in items}


def test_official_locale_counts_and_needles():
    c3 = _codes(CHIRP3_LANGUAGES)
    assert 'auto' in c3 and 'cmn-Hans-CN' in c3 and 'pl-PL' in c3 and 'tr-TR' in c3 and 'ur-PK' in c3
    assert len(c3) >= 112
    assert 'auto' not in _codes(CHIRP2_LANGUAGES)
    assert len(CHIRP2_LANGUAGES) >= 117
    tel = _codes(TELEPHONY_LANGUAGES)
    assert 'en-US' in tel and 'ja-JP' in tel
    assert 'cmn-Hans-CN' not in tel
    assert len(tel) == 44
    assert _codes(CHIRP_TELEPHONY_LANGUAGES) <= tel
    assert len(CHIRP_TELEPHONY_LANGUAGES) == 10
    v1 = _codes(V1_LANGUAGES)
    assert 'cmn-Hans-CN' in v1 and 'yue-Hant-HK' in v1
    assert len(v1) >= 147


def test_model_ids_match_official_tables():
    assert MODELS['chirp3'] == ['chirp_3']
    assert MODELS['chirp2'] == ['chirp_2', 'chirp']
    assert MODELS['telephony'] == ['telephony', 'telephony_short', 'chirp_telephony']
    assert 'telephony' in MODELS['v1'] and 'telephony_short' in MODELS['v1']
    assert 'chirp' in MODEL_LANGUAGES and 'chirp_telephony' in MODEL_LANGUAGES


def test_compare_table_does_not_hedge_telephony_as_视模型():
    blob = '\n'.join('|'.join(row) for row in COMPARE_MODELS)
    assert '视模型' not in blob
    tel_col = [row[3] for row in COMPARE_MODELS]
    assert any('adaptation' in cell or '短语' in cell or '能' in cell for cell in tel_col)
    assert any('无' in cell and 'Chirp' in cell for cell in tel_col)


def test_workspace_language_lists_are_model_specific():
    by_id = {item['id']: item for item in WORKSPACES}
    assert by_id['chirp3']['languages'] is CHIRP3_LANGUAGES
    assert by_id['chirp2']['languages'] is CHIRP2_LANGUAGES
    assert by_id['telephony']['languages'] is TELEPHONY_LANGUAGES
    assert by_id['v1']['languages'] is V1_LANGUAGES
    assert by_id['medical']['languages'][0]['code'] == 'en-US'
    assert 'stream' in by_id['telephony']['features']
    assert 'channels' in by_id['telephony']['features']
    assert 'channels' in by_id['chirp3']['features']
    assert 'channels' in by_id['v1']['features']
    assert 'channels' not in by_id['chirp2']['features']
    assert 'channels' not in by_id['medical']['features']
    blob = '\n'.join('|'.join(row) for row in COMPARE_MODELS)
    assert '本 Demo 工作台不开放' not in blob
    assert any('分轨' in cell or '多声道' in cell for row in COMPARE_MODELS for cell in row)
    blob_value = '\n'.join('|'.join(row) for row in FEATURE_VALUE)
    assert '1–8' in blob_value or '1-8' in blob_value or '8 轨' in blob_value
    assert any('业务上值什么' in cell for cell in FEATURE_VALUE[0])
    assert any('主导' in cell or '最主要' in cell for row in FEATURE_VALUE for cell in row)
    assert any('语码切换' in cell or '多语' in cell for row in FEATURE_VALUE for cell in row)
    assert '最多 2' in blob_value
