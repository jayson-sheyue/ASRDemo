"""Local ASR demo. Run: python -m uvicorn app:app --host 127.0.0.1 --port 8002."""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request as WebRequest, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from asr import Request, UserError, adc_available, error_payload, plan, recognize, require_auth, transcribe_stream
from catalog import (
    API_OUT_OF_DEMO, CHECKED, CHIRP3_DIARIZATION_LANGS, COMPARE_API, COMPARE_METHODS,
    COMPARE_MODELS, ENGINE_LOCATIONS, FEATURE_HINTS, FEATURE_VALUE, FIT_GUIDE, MODEL_CARDS, MODEL_LANGUAGES, MODEL_RULES, MODELS, WHY_NOT_CHIRP3, WORKSPACES,
)
from samples import load_samples

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
SAMPLES = load_samples()
SAMPLE_INDEX = {item['id']: item for item in SAMPLES}
app = FastAPI(title='听写实验室', description='Cloud Speech-to-Text · 本地教学 Demo')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', '[::1]', 'testserver'])
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
generation_lock = threading.Lock()
MAX_BODY = 10_000_000


@app.middleware('http')
async def local_only(request: WebRequest, call_next):
    if request.method == 'POST':
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': '请从本地 Demo 页面发起请求。'}, status_code=403)
        if request.headers.get('content-type', '').split(';')[0] != 'application/json':
            return JSONResponse({'detail': '需要 JSON 请求。'}, status_code=415)
        body = await request.body()
        if len(body) > MAX_BODY:
            return JSONResponse({'detail': '请求过大。请使用短于 1 分钟的音频。'}, status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse({'detail': '输入格式或长度不正确，请检查音频、语言和功能开关。'}, status_code=422)


@app.get('/')
def home():
    return FileResponse(ROOT / 'static' / 'index.html')


@app.get('/api/catalog')
def catalog():
    return {
        'models': MODELS,
        'model_cards': MODEL_CARDS,
        'model_languages': MODEL_LANGUAGES,
        'workspaces': WORKSPACES,
        'samples': SAMPLES,
        'compare_models': COMPARE_MODELS,
        'compare_methods': COMPARE_METHODS,
        'compare_api': COMPARE_API,
        'why_not_chirp3': WHY_NOT_CHIRP3,
        'fit_guide': FIT_GUIDE,
        'feature_value': FEATURE_VALUE,
        'feature_hints': FEATURE_HINTS,
        'api_out_of_demo': API_OUT_OF_DEMO,
        'model_rules': MODEL_RULES,
        'diarization_langs': sorted(CHIRP3_DIARIZATION_LANGS),
        'checked': CHECKED,
        'project_configured': bool(os.getenv('GOOGLE_CLOUD_PROJECT')),
        'adc_configured': adc_available(),
        'engine_locations': ENGINE_LOCATIONS,
        'location_raw': os.getenv('GOOGLE_CLOUD_LOCATION', 'us'),
    }


@app.get('/api/doc/{name}')
def document(name: str):
    files = {'readme': 'README.md', 'guide': 'learning_guide.md', 'sources': 'docs/official_sources.md'}
    if name not in files:
        raise HTTPException(404)
    path = ROOT / files[name]
    if not path.is_file():
        raise HTTPException(404)
    return {'text': path.read_text(encoding='utf-8')}


@app.get('/sample_assets/audio/{name}')
def sample_file(name: str):
    if '/' in name or '\\' in name or name.startswith('.'):
        raise HTTPException(404)
    path = ROOT / 'sample_assets' / 'audio' / name
    if not path.is_file():
        raise HTTPException(404)
    return FileResponse(path)


def resolve_audio(r: Request) -> bytes:
    if r.sample_id:
        item = SAMPLE_INDEX.get(r.sample_id)
        if not item:
            raise UserError('找不到这个样例。')
        audio = item.get('audio')
        path = ROOT / 'sample_assets' / 'audio' / audio if audio else None
        if not path or not path.is_file():
            raise UserError('这个样例没有音频文件。请录音或上传。')
        return path.read_bytes()
    from asr import decode_audio
    return decode_audio(r)


@app.post('/api/preview')
def preview_route(r: Request):
    try:
        audio = None
        if r.sample_id or r.audio_b64:
            audio = resolve_audio(r)
        return plan(r, audio)
    except UserError as error:
        raise HTTPException(400, str(error)) from None


@app.post('/api/recognize')
def recognize_route(r: Request):
    try:
        audio = resolve_audio(r)
        require_auth()
        planned = plan(r, audio)
    except UserError as error:
        raise HTTPException(400, str(error)) from None
    if not generation_lock.acquire(blocking=False):
        raise HTTPException(409, '已有转写任务运行中，请完成或停止后再试。')
    started = time.monotonic()
    try:
        result = recognize(r, audio)
        result['seconds'] = round(time.monotonic() - started, 2)
        result['audio_bytes'] = len(audio)
        result['plan'] = {key: planned[key] for key in ('api', 'model', 'language', 'location', 'warnings')}
        expected = SAMPLE_INDEX.get(r.sample_id, {}).get('expected')
        if expected:
            result['expected'] = expected
        return result
    except UserError as error:
        raise HTTPException(400, str(error)) from None
    except Exception as error:
        payload = error_payload(error)
        print(f'[recognize] {payload["error_type"]}: {error}', flush=True)
        raise HTTPException(400, payload) from None
    finally:
        generation_lock.release()


@app.websocket('/ws/stream')
async def stream_route(socket: WebSocket):
    await socket.accept()
    if not generation_lock.acquire(blocking=False):
        await socket.send_json({'type': 'error', 'message': '已有转写任务运行中。'})
        await socket.close()
        return
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    try:
        first = await socket.receive()
        if 'text' not in first:
            await socket.send_json({'type': 'error', 'message': '请先发送 JSON 配置。'})
            return
        r = Request.model_validate_json(first['text'])
        r.method = 'stream'
        require_auth()
        planned = plan(r)
        await socket.send_json({'type': 'start', 'warnings': planned['warnings'], 'model': r.model})

        def audio_chunks():
            while True:
                item = asyncio.run_coroutine_threadsafe(queue.get(), loop).result()
                if item is None:
                    break
                yield item

        def worker():
            try:
                for parsed in transcribe_stream(r, audio_chunks()):
                    asyncio.run_coroutine_threadsafe(
                        socket.send_json({'type': 'transcript', **parsed}),
                        loop,
                    ).result()
                asyncio.run_coroutine_threadsafe(socket.send_json({'type': 'done'}), loop).result()
            except Exception as error:
                payload = error_payload(error)
                print(f'[stream] {payload["error_type"]}: {error}', flush=True)
                asyncio.run_coroutine_threadsafe(socket.send_json({'type': 'error', **payload}), loop).result()

        task = asyncio.create_task(asyncio.to_thread(worker))
        try:
            while True:
                message = await socket.receive()
                if message.get('type') == 'websocket.disconnect':
                    break
                if message.get('bytes') is not None:
                    await queue.put(message['bytes'])
                elif message.get('text'):
                    data = json.loads(message['text'])
                    if data.get('type') == 'stop':
                        break
        except WebSocketDisconnect:
            pass
        await queue.put(None)
        await task
    except UserError as error:
        await socket.send_json({'type': 'error', 'message': str(error)})
    except Exception as error:
        payload = error_payload(error)
        try:
            await socket.send_json({'type': 'error', **payload})
        except Exception:
            pass
    finally:
        generation_lock.release()
        try:
            await socket.close()
        except Exception:
            pass


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='127.0.0.1', port=int(os.getenv('DEMO_PORT', '8002')), reload=False)
