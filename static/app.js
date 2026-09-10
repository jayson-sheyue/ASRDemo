'use strict';
const GLOBAL = new Set(['guide-content','source-content','source-links','show-guide','show-readme','model-rules','compare-models','compare-methods','compare-api','compare-why','compare-fit','feature-value','api-out-of-demo','workspaces']);
let catalog, active='chirp3', busy=false, controller, objectUrl=null, savedConfig=null, requestSerial=0, rec=null, liveSocket=null, liveTimer=null, liveSession=null;
const primed=new Set();
const $ = id => {
  if(GLOBAL.has(id)) return document.getElementById(id);
  const page=document.getElementById('page-'+active);
  if(page){const el=page.querySelector(`[data-id="${id}"]`); if(el) return el;}
  return document.getElementById(id);
};
function workspace(id){return (catalog.workspaces||[]).find(item=>item.id===id)||catalog.workspaces[0];}
function has(feature, spec){return ((spec||workspace(active)).features||[]).includes(feature);}
function val(id, fallback=''){const el=$(id); return el?el.value:fallback;}
function isOn(id){const el=$(id); return !!(el&&el.checked);}
function options(select,entries){if(!select)return; select.replaceChildren(); entries.forEach(([value,label])=>select.add(new Option(label,value)));}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function report(state, summary, detail=''){
  const box=$('log-box'); if(!box) return;
  box.className='log-box '+state;
  $('log-state').textContent={idle:'待命',loading:'进行中',ok:'成功',error:'失败'}[state]||state;
  $('log-summary').textContent=summary;
  $('log-spinner').hidden=state!=='loading';
  const pre=$('log-detail');
  if(detail){pre.hidden=false;pre.textContent=detail;}else{pre.hidden=true;pre.textContent='';}
  if(state!=='idle') box.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function fail(error, fallback){
  const summary=error&&error.name==='AbortError'?'已停止。已提交的请求仍可能计费。':((error&&error.message)||fallback||'操作失败');
  report('error', summary, error&&error.detail||'');
}
function config(){
  const spec=workspace(active);
  const sample=$('source-player')&&$('source-player').dataset.sampleId||'';
  return {
    engine: spec.id,
    model: spec.features.includes('model_select')?val('model', spec.model):val('model', spec.model),
    language: val('language', spec.languages&&spec.languages[0]&&spec.languages[0].code||'cmn-Hans-CN'),
    method: 'recognize',
    sample_id: sample,
    audio_b64: sample?'':($('audio-b64')?$('audio-b64').value:''),
    filename: $('filename')?$('filename').value:'',
    punctuation: !has('punctuation')||isOn('punctuation'),
    word_time: has('word_time')&&isOn('word_time'),
    word_confidence: false,
    diarization: has('diarization')&&isOn('diarization'),
    adaptation: has('adaptation')?val('adaptation'):'',
    denoiser: has('denoiser')&&isOn('denoiser'),
    custom_prompt: has('custom_prompt')?val('custom_prompt'):'',
    translation_target: has('translation')?val('translation_target'):'',
    profanity_filter: has('profanity')&&isOn('profanity'),
    max_alternatives: has('alternatives')?Number(val('max_alternatives','1'))||1:1,
    channels: has('channels')&&isOn('channels'),
    languages: has('language_auto')?val('languages'):'',
  };
}
function languageEntries(spec){
  const model=val('model', spec.model);
  const override=(catalog.model_languages||{})[model];
  return override||spec.languages||[];
}
function fillLanguages(){
  const spec=workspace(active);
  const sel=$('language'); if(!sel) return;
  const keep=val('language');
  const list=languageEntries(spec);
  options(sel, list.map(item=>[item.code, `${item.label} · ${item.code}${item.stage&&item.stage!=='GA'?' · '+item.stage:''}`]));
  const prefer=keep && list.some(item=>item.code===keep)?keep:(list[0]&&list[0].code||'');
  sel.value=prefer;
}
function fillModels(){
  const spec=workspace(active);
  const sel=$('model'); if(!sel) return;
  const list=(catalog.models[spec.id])||[spec.model];
  options(sel, list.map(name=>[name, name]));
  sel.value=spec.model;
  const card=catalog.model_cards&&catalog.model_cards[sel.value];
  if($('capability')) $('capability').textContent=card||'';
}
function applySample(sample, button, quiet=false){
  if(busy) return;
  const c=sample.config||{};
  fillLanguages(); fillModels();
  if(c.language&&$('language')) $('language').value=c.language;
  if(c.model&&$('model')&&[...$('model').options].some(o=>o.value===c.model)) $('model').value=c.model;
  ['punctuation','word_time','diarization','denoiser','profanity','channels'].forEach(id=>{if($(id)) $(id).checked=!!c[id];});
  if($('punctuation')&&c.punctuation!==false) $('punctuation').checked=true;
  if($('adaptation')) $('adaptation').value=c.adaptation||'';
  if($('custom_prompt')) $('custom_prompt').value=c.custom_prompt||'';
  if($('translation_target')){
    $('translation_target').placeholder='cmn-Hans-CN（不要填 zh-CN）';
    $('translation_target').value=c.translation_target||'';
  }
  if($('max_alternatives')&&c.max_alternatives) $('max_alternatives').value=String(c.max_alternatives);
  if($('languages')) $('languages').value=c.languages||'';
  if($('audio-b64')) $('audio-b64').value='';
  if($('filename')) $('filename').value=sample.audio||'';
  const player=$('source-player');
  if(player){
    player.dataset.sampleId=sample.id||'';
    if(sample.audio){ player.src='/sample_assets/audio/'+sample.audio; player.hidden=false; }
    else { player.removeAttribute('src'); player.hidden=true; }
  }
  if($('expected')) $('expected').textContent=sample.expected?('样例稿：'+sample.expected):'';
  if($('sample-note')) $('sample-note').textContent=sample.note||'';
  document.querySelectorAll(`#page-${active} [data-id="samples"] button`).forEach(item=>item.classList.toggle('selected',item===button));
  capabilities();
  if(!quiet) report('ok',`已导入「${sample.title}」。这是 ${workspace(active).nav} 页的样例。`,sample.note||'');
}
function renderSamples(){
  const root=$('samples'); if(!root) return;
  root.replaceChildren();
  const mine=(catalog.samples||[]).filter(sample=>sample.engine===active);
  const groups=new Map();
  mine.forEach(sample=>{const name=sample.group||'本页样例'; if(!groups.has(name)) groups.set(name,[]); groups.get(name).push(sample);});
  groups.forEach((items,name)=>{
    const block=document.createElement('div'); block.className='sample-group';
    const heading=document.createElement('small'); heading.textContent=name; block.append(heading);
    const chips=document.createElement('div'); chips.className='examples';
    items.forEach(sample=>{
      const button=document.createElement('button'); button.type='button'; button.textContent=sample.title;
      button.onclick=()=>applySample(sample,button); chips.append(button);
    });
    block.append(chips); root.append(block);
  });
  if(!mine.length){const p=document.createElement('p'); p.className='hint'; p.textContent='这一页还没有样例。'; root.append(p); return;}
  applySample(mine[0], root.querySelector('button'), true);
}
function htmlTable(rows){
  if(!rows||!rows.length) return '';
  const head=rows[0].map(cell=>`<th>${escapeHtml(String(cell))}</th>`).join('');
  const body=rows.slice(1).map(row=>'<tr>'+row.map(cell=>`<td>${escapeHtml(String(cell))}</td>`).join('')+'</tr>').join('');
  return `<div class="compare-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
function capabilities(){
  const spec=workspace(active);
  const model=val('model', spec.model);
  const card=catalog.model_cards&&catalog.model_cards[model];
  if($('capability')) $('capability').textContent=card||'';
  if($('stream-btn')) $('stream-btn').hidden=!has('stream');
  const channels=$('channels');
  if(channels){
    const blocked=val('model')==='latest_short';
    channels.disabled=blocked;
    if(blocked) channels.checked=false;
  }
}
function pageIntro(spec){
  const fit=(spec.fit||[]).map(item=>`<article class="fit-item"><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.body)}</p></article>`).join('');
  const surface=(spec.surface||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join('');
  return `<section class="card page-intro"><div class="fit-row">${fit}</div>${spec.coverage?`<p class="hint coverage">${escapeHtml(spec.coverage)}</p>`:''}${spec.limit_note?`<p class="hint">${escapeHtml(spec.limit_note)}</p>`:''}${surface?`<div class="surface"><small>本页可试的 API 能力</small><ul>${surface}</ul></div>`:''}</section>`;
}
function pageDocs(spec){
  const docs=spec.docs||[];
  if(!docs.length) return '';
  const items=docs.map(d=>`<a class="doc-link" href="${escapeHtml(d.url)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(d.title)}</strong><small>${escapeHtml(d.why||'')}</small></a>`).join('');
  return `<section class="card docs-footer"><div class="card-heading"><h2>测通以后：接入你们系统</h2><span class="muted">官方文档</span></div><p class="hint">效果满意后再打开这些链接。本 Demo 不是 Google 产品；请求字段以对应页面为准。</p><div class="doc-grid">${items}</div></section>`;
}
function workspaceHTML(spec){
  const ok=feature=>has(feature, spec);
  const advList=(spec.advantages||[]).map(item=>`<li>${item}</li>`).join('');
  const advBox=advList?`<ul class="advantage-list">${advList}</ul>`:'';
  const features=[
    ok('punctuation')?`<label class="check"><input data-id="punctuation" type="checkbox" checked> 自动标点</label>`:'',
    ok('word_time')?`<label class="check"><input data-id="word_time" type="checkbox"> 词级时间戳</label>`:'',
    ok('diarization')?`<label class="check"><input data-id="diarization" type="checkbox"> 说话人分离</label>`:'',
    ok('denoiser')?`<label class="check"><input data-id="denoiser" type="checkbox"> 降噪</label>`:'',
    ok('channels')?`<label class="check"><input data-id="channels" type="checkbox"> 分轨识别（最多 8 轨）</label>`:'',
    ok('profanity')?`<label class="check"><input data-id="profanity" type="checkbox"> 脏话过滤</label>`:'',
  ].filter(Boolean).join('');
  const adapt=ok('adaptation')?`<label>短语提示（专有名词、一行或逗号分隔）<textarea data-id="adaptation" rows="2" placeholder="webeye-internal-test, Speech-to-Text"></textarea></label><p class="hint">Chirp 只接受普通词/短语，没有 V1 的 class token。</p>`:'';
  const prompt=ok('custom_prompt')?`<label>自定义格式提示 Preview<input data-id="custom_prompt" placeholder="例如：数字用阿拉伯数字"></label>`:'';
  const trans=ok('translation')?`<label>翻译成（空=只转写）<input data-id="translation_target" placeholder="cmn-Hans-CN"></label><p class="hint">Chirp 2 的 translation_config。英语→简体中文填 cmn-Hans-CN，不是 zh-CN。得到的是译文。</p>`:'';
  const alts=ok('alternatives')?`<label>候选条数<select data-id="max_alternatives"><option value="1">1</option><option value="3">3</option><option value="5">5</option></select></label>`:'';
  const hintMap=catalog.feature_hints||{};
  const whyKeys=['punctuation','word_time','diarization','denoiser','channels','adaptation','custom_prompt','translation','profanity','alternatives','stream','language_auto'];
  const why=whyKeys.filter(key=>ok(key)&&hintMap[key]).map(key=>`<li>${escapeHtml(hintMap[key])}</li>`).join('');
  const whyBox=why?`<ul class="feature-why">${why}</ul>`:'';
  return `<section class="engine-page" id="page-${spec.id}" ${spec.id==='chirp3'?'':'hidden'}>
<div class="hero"><div><div class="eyebrow">${spec.eyebrow}</div><h1>${spec.title}</h1><p>${spec.lead}</p></div><div class="hero-wave" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
<div class="notice" data-id="connection">正在读取配置…</div>${advBox}${pageIntro(spec)}
<div class="workspace">
<div class="editor-col">
<section class="card">
<div class="card-heading"><h2><span class="step">01</span> 准备一段声音</h2><span class="muted">${spec.nav}</span></div>
<div class="sample-panel"><div class="sample-head"><strong>本页场景样例</strong><span class="muted">只导入 ${spec.nav}</span></div><div data-id="samples"></div><p data-id="sample-note" class="hint sample-note">样例不会跨页共用。</p></div>
<audio data-id="source-player" class="audio-source" controls hidden></audio>
<p data-id="expected" class="expected"></p>
<div class="record-row">
<label class="file-button secondary">上传音频<input data-id="upload" type="file" accept="audio/*,.wav,.flac,.mp3,.ogg,.webm"></label>
<button class="secondary" data-id="record" type="button">开始录音</button>
<button class="secondary live" data-id="stream-btn" type="button"${ok('stream')?'':' hidden'}>实时听写</button>
</div>
<p class="hint">上传 WAV / FLAC / MP3 / OGG / WebM。V1 页请尽量用 WAV。录音为 16 kHz 单声道 PCM。实时听写走 StreamingRecognize，不是先录完再转。${spec.id==='telephony'?' 电话页可以测流式通路，但浏览器麦不是 8 kHz 听筒。':''}</p>
<input data-id="audio-b64" type="hidden"><input data-id="filename" type="hidden">
</section>
<section class="card">
<div class="card-heading"><h2><span class="step">02</span> 本页相对别的模型多出来的</h2><span class="muted">请求字段</span></div>
${features}${adapt}${prompt}${trans}${alts}${whyBox}
</section>
</div>
<aside>
<section class="card">
<div class="card-heading"><h2><span class="step">03</span> 转写</h2><span class="pill">${spec.api.toUpperCase()}</span></div>
<label>模型<select data-id="model"></select></label>
<label>语言 / locale<select data-id="language"></select></label>
${ok('language_auto')?`<label>再加预期 locale（逗号分隔，连同下拉合计最多 2 个）<input data-id="languages" placeholder="ja-JP"></label><p class="hint">Chirp 3 列预期 locale 最多 2 个，官方示例是 en-US, fr-FR。auto 转最主要的语言。不要和 auto 混写。V2 多语言页写的「最多 3 个」不是 chirp_3：发 3 个会 400。音频可以有更多语种。</p>`:''}
${spec.language_hint?`<p class="hint">${escapeHtml(spec.language_hint)}</p>`:''}
<p data-id="capability" class="hint"></p>
<button class="primary" data-id="recognize" type="button"><span class="spinner" aria-hidden="true"></span><span class="btn-text">▶ 转写</span></button>
<div class="button-row">
<button class="secondary" data-id="preview" type="button">预览请求 · 不收费</button>
<button class="secondary" data-id="stop" type="button" disabled>停止</button>
</div>
<div data-id="log-box" class="log-box idle">
<div class="log-head"><span data-id="log-spinner" class="spinner" hidden></span><strong>操作记录</strong><span data-id="log-state">待命</span></div>
<p data-id="log-summary">本页只提交 ${spec.nav} 的请求。</p>
<pre data-id="log-detail" hidden></pre>
</div>
</section>
</aside>
</div>
<section class="card output">
<div class="card-heading"><h2>转写结果</h2><span data-id="status">等待第一段文字</span></div>
<div data-id="empty-output" class="empty"><span>▁ ▃ ▆ ▂ ▅ ▇ ▃ ▁</span><p>在 ${spec.nav} 页转写的文字只出现在这里。</p></div>
<div data-id="result" hidden>
<p data-id="transcript" class="transcript"></p>
<div data-id="speakers"></div>
<div data-id="words" class="word-wrap"></div>
<p data-id="metrics" class="hint"></p>
<div class="button-row"><button class="secondary" data-id="export" type="button">导出本次配置</button></div>
</div>
<details data-id="preview-panel"><summary>请求预览</summary><p data-id="plan-info"></p><pre data-id="request-preview"></pre></details>
</section>
${pageDocs(spec)}
</section>`;
}
function stopAll(){
  controller?.abort();
  if(liveTimer){clearInterval(liveTimer); liveTimer=null;}
  if(liveSession){stopCapture(liveSession); liveSession=null;}
  if(liveSocket){try{liveSocket.send(JSON.stringify({type:'stop'})); liveSocket.close();}catch{} liveSocket=null;}
  if(rec){const session=rec; rec=null; stopCapture(session); if($('record')) $('record').textContent='开始录音';}
  setBusy(false);
}
function setBusy(value){
  busy=value;
  ['recognize','preview','upload','record','stream-btn'].forEach(id=>{if($(id)) $(id).disabled=value;});
  if($('stop')) $('stop').disabled=!value;
  if($('recognize')) $('recognize').classList.toggle('busy',value);
}
function showResult(data){
  const text=data.transcript||'（没有文字）';
  if($('transcript')) $('transcript').textContent=text;
  if($('result')) $('result').hidden=false;
  if($('empty-output')) $('empty-output').hidden=true;
  const words=(data.results||[]).flatMap(item=>item.words||[]);
  const box=$('words');
  if(box){
    box.replaceChildren();
    words.forEach(word=>{
      const chip=document.createElement('span'); chip.className='word-chip';
      chip.textContent=word.word||'';
      const meta=[];
      if(word.start!=null) meta.push(`${word.start}s`);
      if(word.speaker!=null&&word.speaker!=='') meta.push('说话人 '+word.speaker);
      if(meta.length){const small=document.createElement('small'); small.textContent=meta.join(' · '); chip.append(small);}
      box.append(chip);
    });
  }
  const speakers=$('speakers');
  if(speakers){
    speakers.replaceChildren();
    const byChannel=new Map();
    (data.results||[]).forEach(item=>{
      if(!item.channel_tag) return;
      byChannel.set(item.channel_tag, (byChannel.get(item.channel_tag)||[]).concat(item.transcript||''));
    });
    byChannel.forEach((parts, tag)=>{
      const block=document.createElement('div'); block.className='speaker-block channel-block';
      block.innerHTML=`<strong>通道 ${escapeHtml(String(tag))}</strong><p>${escapeHtml(parts.join('').trim())}</p>`;
      speakers.append(block);
    });
    const map=new Map();
    words.forEach(word=>{
      if(word.speaker==null||word.speaker==='') return;
      const key=String(word.speaker);
      map.set(key, (map.get(key)||[]).concat(word.word||''));
    });
    map.forEach((parts, key)=>{
      const block=document.createElement('div'); block.className='speaker-block';
      block.innerHTML=`<strong>说话人 ${escapeHtml(key)}</strong><p>${escapeHtml(parts.join(' '))}</p>`;
      speakers.append(block);
    });
  }
  const metrics=[];
  if(data.seconds!=null) metrics.push(`耗时 ${data.seconds} 秒`);
  if(data.audio_bytes) metrics.push(`${(data.audio_bytes/1024).toFixed(1)} KB 音频`);
  if(data.model) metrics.push(data.model);
  if(data.expected) metrics.push('样例稿仅供对照，不是评分器');
  const langs=[...new Set((data.results||[]).map(item=>item.language_code).filter(Boolean))];
  if(langs.length) metrics.push('检测语言 '+langs.join(' / '));
  if($('metrics')) $('metrics').textContent=metrics.join(' · ');
  if($('status')) $('status').textContent='转写完成 · 请对照原文';
}
async function post(path,data,signal){
  const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal});
  if(!response.ok){
    let body; try{body=await response.json();}catch{}
    const d=body&&body.detail;
    const err=Error(typeof d==='string'?d:(d&&d.message)||`请求失败（${response.status}）`);
    err.detail=typeof d==='string'?d:(d&&d.detail)||(body?JSON.stringify(body,null,2):'HTTP '+response.status);
    throw err;
  }
  return response;
}
async function preview(){
  if(busy) return; setBusy(true); report('loading','正在预览请求，不会调用 Speech-to-Text…');
  try{
    const p=await(await post('/api/preview',config())).json();
    if($('plan-info')) $('plan-info').textContent=`${p.api.toUpperCase()} · ${p.model} · ${(p.language_codes||[p.language]).join(', ')} · ${p.location}${p.warnings&&p.warnings.length?' · '+p.warnings.join(' '):''}`;
    if($('request-preview')) $('request-preview').textContent=JSON.stringify({page:active,config:config(),google:p.request},null,2);
    if($('preview-panel')) $('preview-panel').open=true;
    report('ok','预览成功，没有调用 Google。',(p.warnings||[]).join('\n'));
  }catch(e){fail(e,'预览失败');}
  finally{setBusy(false);}
}
async function transcribe(){
  if(busy) return;
  const r=config();
  if(!r.sample_id && !r.audio_b64){ report('error','请先点一个样例、上传音频或录音。'); return; }
  controller=new AbortController(); const serial=++requestSerial; setBusy(true);
  report('loading','正在连接 Speech-to-Text…'); if($('status')) $('status').textContent='检查音频并连接…';
  try{
    const data=await(await post('/api/recognize',r,controller.signal)).json();
    savedConfig=Object.assign({page:active},r,{transcript:data.transcript});
    showResult(data);
    report('ok','转写成功。请对照样例稿或你自己说的话。', (data.warnings||[]).join('\n'));
  }catch(e){
    if($('result')) $('result').hidden=true; if($('empty-output')) $('empty-output').hidden=false;
    if($('status')) $('status').textContent=e.name==='AbortError'?'已停止':'未完成';
    fail(e,'转写失败');
  }finally{if(serial===requestSerial) setBusy(false);}
}
function encodeWav(chunks, rate=16000){
  const length=chunks.reduce((n,b)=>n+b.length,0);
  const pcm=new Int16Array(length);
  let offset=0; chunks.forEach(part=>{pcm.set(part,offset); offset+=part.length;});
  const header=new ArrayBuffer(44), v=new DataView(header);
  const bytes=new Uint8Array(pcm.buffer);
  function str(o,s){[...s].forEach((c,i)=>v.setUint8(o+i,c.charCodeAt(0)));}
  str(0,'RIFF'); v.setUint32(4,bytes.length+36,true); str(8,'WAVE'); str(12,'fmt ');
  v.setUint32(16,16,true); v.setUint16(20,1,true); v.setUint16(22,1,true);
  v.setUint32(24,rate,true); v.setUint32(28,rate*2,true); v.setUint16(32,2,true); v.setUint16(34,16,true);
  str(36,'data'); v.setUint32(40,bytes.length,true);
  return new Blob([header, bytes],{type:'audio/wav'});
}
function blobToB64(blob){
  return new Promise((resolve,reject)=>{const reader=new FileReader(); reader.onload=()=>resolve(String(reader.result).split(',')[1]||''); reader.onerror=reject; reader.readAsDataURL(blob);});
}
async function startCapture(){
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  const ctx=new AudioContext({sampleRate:16000});
  const src=ctx.createMediaStreamSource(stream);
  const proc=ctx.createScriptProcessor(4096,1,1);
  const chunks=[];
  proc.onaudioprocess=event=>{
    const data=event.inputBuffer.getChannelData(0);
    const buf=new Int16Array(data.length);
    for(let i=0;i<data.length;i++) buf[i]=Math.max(-1,Math.min(1,data[i]))*32767;
    chunks.push(buf);
  };
  src.connect(proc); proc.connect(ctx.destination);
  return {stream, ctx, proc, chunks};
}
function stopCapture(session){
  try{session.proc.disconnect(); session.ctx.close();}catch{}
  session.stream.getTracks().forEach(track=>track.stop());
}
async function toggleRecord(){
  if(rec){
    const session=rec; rec=null;
    stopCapture(session);
    const blob=encodeWav(session.chunks);
    const b64=await blobToB64(blob);
    if($('audio-b64')) $('audio-b64').value=b64;
    if($('filename')) $('filename').value='recording.wav';
    const player=$('source-player');
    if(player){ if(objectUrl) URL.revokeObjectURL(objectUrl); objectUrl=URL.createObjectURL(blob); player.src=objectUrl; player.hidden=false; player.dataset.sampleId=''; }
    if($('record')) $('record').textContent='开始录音';
    report('ok',`已录制 ${(blob.size/1024).toFixed(1)} KB。点转写。`);
    return;
  }
  rec=await startCapture();
  if($('record')) $('record').textContent='停止录音';
  report('loading','正在录音…再点一次结束。');
}
async function liveStream(){
  if(liveSocket){ try{liveSocket.send(JSON.stringify({type:'stop'})); liveSocket.close();}catch{} liveSocket=null; return; }
  if(busy) return;
  const r=config(); r.method='stream'; r.sample_id=''; r.audio_b64='';
  setBusy(true); report('loading','正在打开麦克风并连接 StreamingRecognize…');
  if($('transcript')) $('transcript').textContent=''; if($('result')) $('result').hidden=false; if($('empty-output')) $('empty-output').hidden=true;
  let session;
  try{
    session=await startCapture();
    const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/stream`);
    liveSocket=socket;
    await new Promise((resolve,reject)=>{socket.onopen=resolve; socket.onerror=()=>reject(Error('无法建立 WebSocket'));});
    socket.send(JSON.stringify(r));
    socket.onmessage=event=>{
      const data=JSON.parse(event.data);
      if(data.type==='error'){ const err=Error(data.message||'流式失败'); err.detail=data.detail||''; fail(err,'流式失败'); setBusy(false); liveSocket=null; }
      if(data.type==='start') report('loading','已连接，正在听…',(data.warnings||[]).join('\n'));
      if(data.type==='transcript'){
        showResult(data);
        if($('transcript')) $('transcript').classList.toggle('interim', (data.results||[]).some(item=>item.is_final===false));
      }
      if(data.type==='done'){ report('ok','实时听写结束。'); if(liveTimer){clearInterval(liveTimer); liveTimer=null;} liveSocket=null; setBusy(false); }
    };
    const send=()=>{
      if(!liveSocket||liveSocket.readyState!==1) return;
      while(session.chunks.length){
        const part=session.chunks.shift();
        liveSocket.send(part.buffer);
      }
    };
    liveTimer=setInterval(send, 200);
    liveSession=session;
    report('loading','正在听。点停止结束。');
  }catch(e){
    if(session) stopCapture(session);
    liveSocket=null; setBusy(false); fail(e,'实时听写失败');
  }
}
function bindWorkspace(root, spec){
  const click=(id, fn)=>{const el=root.querySelector(`[data-id="${id}"]`); if(el) el.onclick=fn;};
  click('recognize', transcribe); click('preview', preview); click('record', toggleRecord); click('stream-btn', liveStream);
  click('stop', stopAll);
  click('export', ()=>{if(!savedConfig)return; const u=URL.createObjectURL(new Blob([JSON.stringify(savedConfig,null,2)],{type:'application/json'})); const a=document.createElement('a'); a.href=u; a.download=`${spec.id}-config.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(u),1000);});
  const model=root.querySelector('[data-id="model"]'); if(model) model.onchange=()=>{fillLanguages(); capabilities();};
  const language=root.querySelector('[data-id="language"]');
  if(language) language.onchange=()=>{ if($('languages')) $('languages').value=''; };
  const upload=root.querySelector('[data-id="upload"]');
  if(upload) upload.onchange=async()=>{
    const f=upload.files[0]; if(!f)return;
    if(f.size>MAX_UPLOAD){report('error','文件过大，请使用短于约 1 分钟的音频。'); return;}
    const b64=await blobToB64(f);
    if($('audio-b64')) $('audio-b64').value=b64;
    if($('filename')) $('filename').value=f.name;
    const player=$('source-player');
    if(player){ if(objectUrl) URL.revokeObjectURL(objectUrl); objectUrl=URL.createObjectURL(f); player.src=objectUrl; player.hidden=false; player.dataset.sampleId=''; }
    report('ok',`已导入 ${f.name}。`); upload.value='';
  };
}
const MAX_UPLOAD=8_000_000;
function connectionText(){
  const ready=catalog.project_configured&&catalog.adc_configured;
  if(ready) return `✓ 已配置 Cloud 项目与 ADC。Chirp 3 走 ${catalog.engine_locations&&catalog.engine_locations.chirp3||'us'}，Chirp 2 走 ${catalog.engine_locations&&catalog.engine_locations.chirp2||'us-central1'}。两个模型的区域不一样，不要混用。`;
  if(catalog.project_configured) return '○ 已填项目，但未检测到 ADC。请运行 gcloud auth application-default login 后重启。';
  if(catalog.adc_configured) return '○ 已有 ADC，请在 .env 填写 GOOGLE_CLOUD_PROJECT 并重启。';
  return '○ 预览不需要凭据。转写请配置 ADC 与项目，并启用 speech.googleapis.com。';
}
function page(name){
  if(!catalog) return;
  const engines=(catalog.workspaces||[]).map(item=>item.id);
  const isEngine=engines.includes(name);
  document.querySelectorAll('.engine-page').forEach(el=>el.hidden=el.id!=='page-'+name);
  ['learn','sources'].forEach(id=>{const el=document.getElementById(id); if(el) el.hidden=name!==id;});
  document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.page===name));
  if(isEngine){
    active=name;
    if(!primed.has(name)){
      primed.add(name);
      fillModels(); fillLanguages(); renderSamples(); capabilities();
      const notice=$('connection'); if(notice) notice.textContent=connectionText();
    }
  }
  window.scrollTo({top:0,behavior:'smooth'});
}
function inlineMarkdown(value){return escapeHtml(value).replace(/\[([^\]]+)\]\((https:\/\/[^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');}
function renderMarkdown(src){
  const lines=src.replace(/\r\n/g,'\n').split('\n'), out=[]; let i=0;
  while(i<lines.length){
    const line=lines[i];
    if(line.startsWith('```')){const buf=[]; i++; while(i<lines.length&&!lines[i].startsWith('```')){buf.push(escapeHtml(lines[i])); i++;} i++; out.push('<pre><code>'+buf.join('\n')+'</code></pre>'); continue;}
    if(line.startsWith('|')&&lines[i+1]&&/^\|?\s*-+/.test(lines[i+1])){
      const rows=[]; while(i<lines.length&&lines[i].startsWith('|')){if(!/^\|?\s*-+/.test(lines[i])) rows.push(lines[i]); i++;}
      out.push('<table>'+rows.map((row,index)=>{const cells=row.split('|').slice(1,-1).map(cell=>inlineMarkdown(cell.trim())); const tag=index?'td':'th'; return '<tr>'+cells.map(cell=>`<${tag}>${cell}</${tag}>`).join('')+'</tr>';}).join('')+'</table>'); continue;
    }
    if(/^---+$/.test(line.trim())){out.push('<hr>'); i++; continue;}
    const heading=line.match(/^(#{1,3})\s+(.*)$/); if(heading){out.push(`<h${heading[1].length}>${inlineMarkdown(heading[2])}</h${heading[1].length}>`); i++; continue;}
    if(/^\s*[-*]\s+/.test(line)){const items=[]; while(i<lines.length&&/^\s*[-*]\s+/.test(lines[i])){items.push('<li>'+inlineMarkdown(lines[i].replace(/^\s*[-*]\s+/,''))+'</li>'); i++;} out.push('<ul>'+items.join('')+'</ul>'); continue;}
    if(/^\s*\d+\.\s+/.test(line)){const items=[]; while(i<lines.length&&/^\s*\d+\.\s+/.test(lines[i])){items.push('<li>'+inlineMarkdown(lines[i].replace(/^\s*\d+\.\s+/,''))+'</li>'); i++;} out.push('<ol>'+items.join('')+'</ol>'); continue;}
    if(!line.trim()){i++; continue;}
    const buf=[line]; i++; while(i<lines.length&&lines[i].trim()&&!/^(#{1,3}\s|```|\||---|[-*]\s|\d+\.\s)/.test(lines[i])) buf.push(lines[i++]);
    out.push('<p>'+inlineMarkdown(buf.join(' '))+'</p>');
  }
  return out.join('');
}
async function loadDoc(kind,target){const response=await fetch('/api/doc/'+kind); if(!response.ok) throw Error('文档加载失败'); const data=await response.json(); $(target).innerHTML=renderMarkdown(data.text); return data.text;}
async function init(){
  try{
    catalog=await(await fetch('/api/catalog')).json();
    const host=$('workspaces');
    (catalog.workspaces||[]).forEach(spec=>{
      host.insertAdjacentHTML('beforeend', workspaceHTML(spec));
      bindWorkspace(document.getElementById('page-'+spec.id), spec);
    });
    $('model-rules').innerHTML=htmlTable(catalog.model_rules);
    $('compare-models').innerHTML=htmlTable(catalog.compare_models);
    $('compare-methods').innerHTML=htmlTable(catalog.compare_methods);
    $('compare-api').innerHTML=htmlTable(catalog.compare_api);
    $('compare-why').innerHTML=htmlTable(catalog.why_not_chirp3);
    $('compare-fit').innerHTML=htmlTable(catalog.fit_guide);
    if($('feature-value')) $('feature-value').innerHTML=htmlTable(catalog.feature_value);
    $('api-out-of-demo').innerHTML=htmlTable(catalog.api_out_of_demo);
    page('chirp3');
    try{await loadDoc('guide','guide-content');}catch(e){$('guide-content').textContent='学习指南加载失败：'+e.message;}
    try{
      const text=await loadDoc('sources','source-content'); const seen=new Set();
      for(const match of text.matchAll(/\[([^\]]+)\]\((https:\/\/[^)]+)\)/g)){
        if(seen.has(match[2])) continue; seen.add(match[2]);
        const a=document.createElement('a'); a.className='source-link'; a.href=match[2]; a.target='_blank'; a.rel='noopener noreferrer'; a.textContent=match[1]+' ↗';
        const sub=document.createElement('small'); sub.textContent=new URL(match[2]).hostname; a.append(sub); $('source-links').append(a);
      }
    }catch(e){$('source-content').textContent='官方资料加载失败：'+e.message;}
  }catch(e){fail(e,'初始化失败');}
}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>page(b.dataset.page));
$('show-guide').onclick=()=>loadDoc('guide','guide-content').catch(e=>fail(e,'文档加载失败'));
$('show-readme').onclick=()=>loadDoc('readme','guide-content').catch(e=>fail(e,'文档加载失败'));
window.addEventListener('beforeunload',()=>{controller?.abort(); if(objectUrl) URL.revokeObjectURL(objectUrl);});
init();
