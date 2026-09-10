"""Chirp 3 BatchRecognize 命令行。需要 GCS 上的音频。工作台不会调用它。

用法：
    .venv/bin/python batch_demo.py submit gs://BUCKET/audio.wav
    .venv/bin/python batch_demo.py status OPERATION_NAME

submit 会产生真实云端任务，可能计费。
对照：https://cloud.google.com/speech-to-text/docs/batch-recognize
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


def client_and_region():
    from google.api_core.client_options import ClientOptions
    from google.cloud.speech_v2 import SpeechClient
    region = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')
    if region == 'global':
        region = 'us'
    project = (os.getenv('GOOGLE_CLOUD_PROJECT') or '').strip()
    if not project:
        raise SystemExit('缺少 GOOGLE_CLOUD_PROJECT')
    client = SpeechClient(client_options=ClientOptions(api_endpoint=f'{region}-speech.googleapis.com'))
    return client, project, region


def submit(uri: str) -> None:
    from google.cloud.speech_v2.types import cloud_speech
    client, project, region = client_and_region()
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=['cmn-Hans-CN'],
        model='chirp_3',
        features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            diarization_config=cloud_speech.SpeakerDiarizationConfig(),
        ),
    )
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=f'projects/{project}/locations/{region}/recognizers/_',
        config=config,
        files=[cloud_speech.BatchRecognizeFileMetadata(uri=uri)],
        recognition_output_config=cloud_speech.RecognitionOutputConfig(
            inline_response_config=cloud_speech.InlineOutputConfig(),
        ),
    )
    operation = client.batch_recognize(request=request)
    print(operation.operation.name)
    print('用 status 子命令查询。不要循环刷。')


def status(name: str) -> None:
    client, _project, _region = client_and_region()
    operation = client._transport.operations_client.get_operation(name)
    print('done' if operation.done else 'running')
    if operation.error and operation.error.message:
        print(operation.error.message, file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description='Speech-to-Text V2 BatchRecognize 示例')
    sub = parser.add_subparsers(dest='cmd', required=True)
    submit_p = sub.add_parser('submit')
    submit_p.add_argument('uri')
    status_p = sub.add_parser('status')
    status_p.add_argument('name')
    args = parser.parse_args()
    if args.cmd == 'submit':
        submit(args.uri)
    else:
        status(args.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
