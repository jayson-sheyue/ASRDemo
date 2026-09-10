from __future__ import annotations

from pathlib import Path

REQUIRED_URLS = [
    'https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3',
    'https://cloud.google.com/speech-to-text/v2/docs/transcription-model',
    'https://docs.cloud.google.com/speech-to-text/docs/models/chirp-2',
    'https://docs.cloud.google.com/python/docs/reference/speech/latest',
    'https://docs.cloud.google.com/docs/authentication/provide-credentials-adc',
    'https://docs.cloud.google.com/speech-to-text/docs/v1/transcription-model',
    'https://docs.cloud.google.com/speech-to-text/docs/v1/medical-models',
    'https://cloud.google.com/speech-to-text/docs/streaming-recognize',
    'https://cloud.google.com/speech-to-text/docs/batch-recognize',
    'https://cloud.google.com/speech-to-text/docs/adaptation',
    'https://docs.cloud.google.com/speech-to-text/docs/multi-channel',
    'https://docs.cloud.google.com/speech-to-text/docs/v1/multi-channel',
    'https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages',
    'https://cloud.google.com/speech-to-text/v2/docs/multiple-languages',
    'https://docs.cloud.google.com/speech-to-text/docs/v1/speech-to-text-supported-languages',
    'https://cloud.google.com/speech-to-text/pricing',
    'https://cloud.google.com/speech-to-text/v2/docs/custom-speech-models/overview',
    'https://cloud.google.com/speech-to-text/v2/docs/reference/rest/v2/projects.locations.recognizers',
    'https://ai.google.dev/gemini-api/docs/live-api',
]


def test_required_docs_exist():
    root = Path(__file__).resolve().parents[1]
    for name in ('README.md', 'learning_guide.md', 'docs/official_sources.md'):
        assert (root / name).is_file()
        assert len((root / name).read_text(encoding='utf-8')) > 500


def test_official_index_covers_主干入口():
    text = (Path(__file__).resolve().parents[1] / 'docs/official_sources.md').read_text(encoding='utf-8')
    missing = [url for url in REQUIRED_URLS if url not in text]
    assert missing == []


def test_learning_guide_covers_can_and_cannot():
    text = (Path(__file__).resolve().parents[1] / 'learning_guide.md').read_text(encoding='utf-8')
    for needle in (
        '能干什么', '不能干什么', '同步转写', '实时听写', '批量',
        'Recognize', 'StreamingRecognize', 'BatchRecognize',
        'language_codes', '说话人分离', 'class token', '声纹',
        'us-central1', 'cmn-Hans-CN', 'en-US', '医学模型',
        '分轨', 'channel_tag', '8 轨', '多语切换', '主导', '最多 2',
        '网页 Demo 故意没接', '业务价值',
    ):
        assert needle in text
    readme = (Path(__file__).resolve().parents[1] / 'README.md').read_text(encoding='utf-8')
    assert 'GOOGLE_CLOUD_LOCATION=us' in readme
    assert 'speech.googleapis.com' in readme
    assert 'sample_assets' in readme
    assert (Path(__file__).resolve().parents[1] / 'examples' / 'quickstart.py').is_file()
    assert (Path(__file__).resolve().parents[1] / 'batch_demo.py').is_file()
