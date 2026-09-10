from __future__ import annotations

from catalog import EXAMPLES, WORKSPACES


def test_home_and_static(client):
    home = client.get('/')
    assert home.status_code == 200
    assert '听写实验室' in home.text and 'id="workspaces"' in home.text
    assert 'data-page="chirp3"' in home.text and 'data-page="telephony"' in home.text
    assert 'data-page="medical"' in home.text and 'data-page="v1"' in home.text
    assert 'id="compare-models"' in home.text
    css = client.get('/static/style.css')
    js = client.get('/static/app.js')
    assert css.status_code == 200 and js.status_code == 200
    assert 'sample.engine===active' in js.text
    assert '本页场景样例' in js.text
    assert 'StreamingRecognize' in js.text
    assert '实时听写' in js.text


def test_catalog_and_docs(client):
    catalog = client.get('/api/catalog').json()
    assert catalog['checked'] == '2026-09-10'
    assert catalog['project_configured'] is False
    assert [item['id'] for item in catalog['workspaces']] == ['chirp3', 'chirp2', 'telephony', 'medical', 'v1']
    assert all(item.get('docs') and item.get('fit') and item.get('surface') for item in catalog['workspaces'])
    chirp = next(item for item in catalog['workspaces'] if item['id'] == 'chirp3')
    assert chirp['docs'] and all(item['url'].startswith('https://') for item in chirp['docs'])
    medical = next(item for item in catalog['workspaces'] if item['id'] == 'medical')
    assert 'en-US' in medical['lead'] and 'en-US' in medical['limit_note']
    assert medical['languages'] == [{'code': 'en-US', 'label': '英语（美国）· 唯一支持', 'stage': 'GA'}]
    assert any('medical-models' in item['url'] for item in medical['docs'])
    assert catalog['compare_models'][0][1] == 'Chirp 3'
    assert catalog['model_rules'][0][0] == '能力'
    samples = catalog['samples']
    assert len(samples) >= 16
    assert samples[0]['id'] == 'welcome'
    assert {item['engine'] for item in samples} >= {'chirp3', 'chirp2', 'telephony', 'medical', 'v1'}
    telephony = next(item for item in catalog['workspaces'] if item['id'] == 'telephony')
    assert 'stream' in telephony['features']
    assert 'channels' in telephony['features']
    phone_cmn = next(item for item in samples if item['id'] == 'phone-cmn')
    assert phone_cmn['engine'] == 'chirp3'
    assert any(item['id'] == 'phone-stereo' and item['config'].get('channels') for item in samples)
    assert any(item['id'] == 'phone-quad' for item in samples)
    assert catalog.get('feature_value') and catalog['feature_value'][0][1] == '业务上值什么'
    for name in ('readme', 'guide', 'sources'):
        body = client.get(f'/api/doc/{name}').json()['text']
        assert 'Speech-to-Text' in body or 'Chirp 3' in body
    assert client.get('/api/doc/missing').status_code == 404
    audio = client.get('/sample_assets/audio/welcome_cmn.wav')
    assert audio.status_code == 200
    assert audio.content[:4] == b'RIFF'


def test_preview_ok_and_validation(client):
    ok = client.post('/api/preview', json={'engine': 'chirp3', 'model': 'chirp_3', 'language': 'cmn-Hans-CN', 'sample_id': 'welcome'})
    assert ok.status_code == 200
    body = ok.json()
    assert body['api'] == 'v2'
    assert body['model'] == 'chirp_3'
    assert body['request']['language_codes'] == ['cmn-Hans-CN']
    assert 'recognizers/_' in body['request']['recognizer']
    assert body['location'] == 'us'
    bad = client.post('/api/preview', json={'engine': 'chirp3', 'model': 'latest_long', 'sample_id': 'welcome'})
    assert bad.status_code == 400
    auto = client.post('/api/preview', json={'engine': 'telephony', 'model': 'telephony', 'language': 'auto'})
    assert auto.status_code == 400
    medical_zh = client.post('/api/preview', json={'engine': 'medical', 'model': 'medical_dictation', 'language': 'cmn-Hans-CN'})
    assert medical_zh.status_code == 400
    assert 'en-US' in medical_zh.json().get('detail', medical_zh.text) or 'en-US' in medical_zh.text
    missing = client.post('/api/recognize', json={'engine': 'chirp3', 'sample_id': 'welcome'})
    assert missing.status_code == 400
    assert WORKSPACES[0]['id'] == 'chirp3'
    assert EXAMPLES[0]['title'] == '第一段中文'
