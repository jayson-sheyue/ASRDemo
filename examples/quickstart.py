"""最小可运行的 Chirp 3 同步转写（Speech-to-Text V2 + ADC）。

用法（在项目根目录）：
    .venv/bin/python examples/quickstart.py

需要 ADC、GOOGLE_CLOUD_PROJECT，以及已启用 speech.googleapis.com。
这会发起一次真实的付费/配额调用。
对照：https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
AUDIO = ROOT / 'sample_assets' / 'audio' / 'welcome_cmn.wav'
REGION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')
if REGION == 'global':
    REGION = 'us'


def main() -> int:
    project = (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip()
    if not project:
        print('缺少 GOOGLE_CLOUD_PROJECT。请复制 .env.example 为 .env，并先运行 gcloud auth application-default login。', file=sys.stderr)
        return 1
    if not AUDIO.is_file():
        print(f'找不到样例音频 {AUDIO}', file=sys.stderr)
        return 1

    client = SpeechClient(client_options=ClientOptions(api_endpoint=f'{REGION}-speech.googleapis.com'))
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=['cmn-Hans-CN'],
        model='chirp_3',
    )
    request = cloud_speech.RecognizeRequest(
        recognizer=f'projects/{project}/locations/{REGION}/recognizers/_',
        config=config,
        content=AUDIO.read_bytes(),
    )
    response = client.recognize(request=request)
    for result in response.results:
        if result.alternatives:
            print(result.alternatives[0].transcript)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
