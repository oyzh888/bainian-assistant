#!/usr/bin/env python3
"""
拜年助手 (bainian-assistant)
AI-powered Chinese New Year reply generator
https://github.com/oyzh888/bainian-assistant
"""
import base64, os, json
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)

# ── Config from environment ──────────────────────────────────────────────────
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
PORT = int(os.environ.get("PORT", 3005))

if not OPENROUTER_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable is required. See README.md")

client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")

# ── Supported models ─────────────────────────────────────────────────────────
MODELS = {
    "gemini-flash":  {"label": "🌟 Gemini Flash",  "model": "google/gemini-2.0-flash-001"},
    "qwen-vl-72b":   {"label": "🇨🇳 通义千问 VL",  "model": "qwen/qwen2.5-vl-72b-instruct"},
    "claude-sonnet": {"label": "🤖 Claude Sonnet", "model": "anthropic/claude-sonnet-4-5"},
    "deepseek":      {"label": "🔥 DeepSeek V3",   "model": "deepseek/deepseek-chat-v3-0324"},
}
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gemini-flash")

# ── System prompt (customise via SYSTEM_PROMPT env var or config.json) ────────
DEFAULT_SYSTEM_PROMPT = """你是一个智能拜年回复助手，帮助用户快速生成个性化的春节祝福回复。

## 回复风格
- 简短真实：15-35字，最多2句话
- 有温度：听起来像真人说的，不像模板
- 少用烂大街套话："万事如意""恭喜发财""阖家幸福"等词语换个更鲜活的说法
- emoji 最多1个，或不用
- 根据关系调整：家人/长辈稍正式温情；朋友随意幽默；同事/客户简短有礼

## 输出格式（严格JSON，不要任何其他文字）
{
  "recognized": "发送人和内容简述（如：朋友张三发来蛇年祝福）",
  "replies": [
    {"type": "formal", "label": "🎩 正式温馨", "text": "回复内容"},
    {"type": "humor",  "label": "😄 幽默俏皮", "text": "回复内容"},
    {"type": "short",  "label": "⚡ 简短精炼", "text": "回复内容"}
  ]
}"""

# Load custom system prompt from config.json if exists
_config_path = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(_config_path):
    with open(_config_path) as f:
        _cfg = json.load(f)
        SYSTEM_PROMPT = _cfg.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
else:
    SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🐍 拜年助手</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
  background:linear-gradient(135deg,#c0392b,#e74c3c 50%,#e67e22);min-height:100vh;padding:16px}
.wrap{max-width:680px;margin:0 auto}
.card{background:rgba(255,255,255,.97);border-radius:20px;padding:22px 18px;margin-bottom:14px;
  box-shadow:0 8px 32px rgba(0,0,0,.12)}
h1{color:#c0392b;font-size:22px;font-weight:800;text-align:center;margin-bottom:3px}
.sub{color:#888;font-size:13px;text-align:center;margin-bottom:18px}
.drop-zone{border:2px dashed #ffb347;border-radius:14px;padding:24px 16px;
  text-align:center;cursor:pointer;background:#fff9f0;transition:.2s;position:relative;min-height:90px}
.drop-zone:hover,.drop-zone.over{border-color:#e74c3c;background:#fff3f0}
.drop-zone .icon{font-size:36px;display:block;margin-bottom:6px}
.drop-zone p{color:#666;font-size:14px;line-height:1.6}
.drop-zone input{position:absolute;inset:0;opacity:0;cursor:pointer}
.thumb-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:8px;margin-top:12px}
.thumb-item{position:relative;aspect-ratio:1;border-radius:8px;overflow:hidden;background:#f0f0f0}
.thumb-item img{width:100%;height:100%;object-fit:cover}
.thumb-item .del{position:absolute;top:3px;right:3px;background:rgba(0,0,0,.55);color:#fff;
  border:none;border-radius:50%;width:20px;height:20px;font-size:11px;cursor:pointer;
  display:flex;align-items:center;justify-content:center}
.thumb-count{font-size:12px;color:#888;margin-top:6px;text-align:right}
.model-row{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 10px}
.mtag{display:flex;align-items:center;gap:5px;padding:7px 12px;border:1.5px solid #e0e0e0;
  border-radius:20px;cursor:pointer;font-size:13px;background:#fff;transition:.15s}
.mtag.on{border-color:#e74c3c;background:#fff0f0;color:#c0392b;font-weight:600}
.go{width:100%;padding:13px;background:linear-gradient(135deg,#e74c3c,#c0392b);
  color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:700;
  cursor:pointer;transition:.2s;letter-spacing:1px}
.go:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(192,57,43,.35)}
.go:disabled{background:#ccc;transform:none;box-shadow:none;cursor:not-allowed}
.progress-wrap{display:none;margin-top:10px}
.progress-bar{height:6px;background:#ffe0d0;border-radius:3px;overflow:hidden;margin-bottom:5px}
.progress-fill{height:100%;background:linear-gradient(90deg,#e74c3c,#e67e22);border-radius:3px;transition:width .3s}
.progress-text{font-size:12px;color:#888;text-align:center}
.result-card{border:1.5px solid #ffe0d0;border-radius:14px;overflow:hidden;margin-bottom:12px}
.rc-header{display:flex;align-items:center;gap:10px;padding:10px 14px;
  background:linear-gradient(135deg,#fff0f0,#fff9f0);cursor:pointer}
.rc-thumb{width:48px;height:48px;border-radius:7px;object-fit:cover;flex-shrink:0}
.rc-info{flex:1;min-width:0}
.rc-recognized{font-size:13px;color:#555;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rc-status{font-size:11px;color:#aaa;margin-top:2px}
.rc-toggle{font-size:18px;color:#ccc;flex-shrink:0}
.rc-body{border-top:1.5px solid #ffe0d0;padding:12px 14px;background:#fff}
.reply-row{display:flex;align-items:flex-start;gap:8px;padding:7px 0;border-bottom:1px solid #f5f5f5}
.reply-row:last-child{border-bottom:none}
.rtag{font-size:11px;padding:2px 8px;border-radius:10px;white-space:nowrap;flex-shrink:0;margin-top:2px}
.tf{background:#e8f5e9;color:#2e7d32}.th{background:#fff3e0;color:#e65100}.ts{background:#e3f2fd;color:#1565c0}
.rtext{font-size:14px;color:#333;line-height:1.6;flex:1}
.cpbtn{font-size:11px;padding:3px 9px;border:1px solid #ddd;background:#fff;
  border-radius:6px;cursor:pointer;white-space:nowrap;flex-shrink:0;color:#666}
.cpbtn:hover,.cpbtn.ok{background:#e8f5e9;border-color:#4caf50;color:#2e7d32}
.rc-loading{padding:16px;text-align:center;color:#e74c3c;font-size:13px}
.spin{display:inline-block;width:18px;height:18px;border:2px solid #ffcdd2;border-top-color:#e74c3c;
  border-radius:50%;animation:sp .7s linear infinite;vertical-align:middle;margin-right:6px}
.rc-error{padding:12px;color:#c62828;font-size:13px;background:#fff8f8}
@keyframes sp{to{transform:rotate(360deg)}}
.footer{text-align:center;color:rgba(255,255,255,.7);font-size:12px;padding:4px 0 16px}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
  <h1>🐍 拜年助手</h1>
  <p class="sub">批量上传截图 · AI 生成回复 · 一键复制</p>

  <div class="drop-zone" id="dz">
    <span class="icon">📱</span>
    <p><strong>点击上传</strong>或拖拽截图（支持多选）<br>
    <span style="font-size:12px;color:#bbb">Ctrl+V 直接粘贴截图 · 任何平台截图均可</span></p>
    <input type="file" id="fi" accept="image/*" multiple>
  </div>
  <div class="thumb-grid" id="thumbs"></div>
  <div class="thumb-count" id="cnt" style="display:none"></div>

  <p style="font-size:13px;color:#888;margin:14px 0 6px;font-weight:600">选择模型</p>
  <div class="model-row" id="modelRow">
    <label class="mtag on"><input type="radio" name="m" value="gemini-flash" checked>🌟 Gemini Flash</label>
    <label class="mtag"><input type="radio" name="m" value="qwen-vl-72b">🇨🇳 通义千问</label>
    <label class="mtag"><input type="radio" name="m" value="claude-sonnet">🤖 Claude</label>
    <label class="mtag"><input type="radio" name="m" value="deepseek">🔥 DeepSeek</label>
  </div>

  <button class="go" id="goBtn" disabled>🤖 批量生成回复</button>
  <div class="progress-wrap" id="progWrap">
    <div class="progress-bar"><div class="progress-fill" id="progFill" style="width:0%"></div></div>
    <div class="progress-text" id="progText">0 / 0</div>
  </div>
</div>

<div id="results"></div>
<div class="footer">
  Powered by <a href="https://openrouter.ai" style="color:rgba(255,255,255,.9)">OpenRouter</a> ·
  <a href="https://github.com/oyzh888/bainian-assistant" style="color:rgba(255,255,255,.9)">Open Source</a> ·
  蛇年大吉 🎊
</div>
</div>

<script>
let files=[];
const fi=document.getElementById('fi'),dz=document.getElementById('dz');
const thumbs=document.getElementById('thumbs'),cnt=document.getElementById('cnt');
const goBtn=document.getElementById('goBtn'),results=document.getElementById('results');

document.querySelectorAll('input[name=m]').forEach(r=>{
  r.addEventListener('change',()=>{
    document.querySelectorAll('.mtag').forEach(l=>l.classList.remove('on'));
    r.closest('.mtag').classList.add('on');
  });
});

fi.addEventListener('change',e=>{addFiles([...e.target.files]);fi.value='';});
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over');});
dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('over');addFiles([...e.dataTransfer.files]);});
document.addEventListener('paste',e=>{
  const imgs=[...e.clipboardData?.items||[]].filter(i=>i.type.startsWith('image/')).map(i=>i.getAsFile());
  if(imgs.length)addFiles(imgs);
});

function addFiles(newFiles){
  newFiles.filter(f=>f&&f.type.startsWith('image/')).forEach(f=>{
    const idx=files.push(f)-1;
    const div=document.createElement('div');
    div.className='thumb-item';div.id='thumb-'+idx;
    const img=document.createElement('img');
    const btn=document.createElement('button');
    btn.className='del';btn.textContent='✕';
    btn.onclick=()=>{files[idx]=null;div.remove();updateCount();};
    const r=new FileReader();
    r.onload=e=>img.src=e.target.result;
    r.readAsDataURL(f);
    div.append(img,btn);thumbs.appendChild(div);
  });
  updateCount();
}

function updateCount(){
  const valid=files.filter(Boolean);
  if(valid.length){cnt.style.display='block';cnt.textContent=valid.length+' 张截图已添加';goBtn.disabled=false;}
  else{cnt.style.display='none';goBtn.disabled=true;results.innerHTML='';}
}

goBtn.addEventListener('click',async()=>{
  const valid=files.map((f,i)=>({f,i})).filter(x=>x.f);
  if(!valid.length)return;
  const model=document.querySelector('input[name=m]:checked').value;
  goBtn.disabled=true;results.innerHTML='';

  valid.forEach(({f,i})=>{
    results.innerHTML+=`<div class="card result-card" id="rc-${i}">
      <div class="rc-header" onclick="toggle(${i})">
        <img class="rc-thumb" src="${URL.createObjectURL(f)}">
        <div class="rc-info">
          <div class="rc-recognized" id="rrec-${i}">识别中...</div>
          <div class="rc-status" id="rstat-${i}">⏳ 等待中</div>
        </div>
        <span class="rc-toggle" id="rtog-${i}">▼</span>
      </div>
      <div class="rc-body" id="rbody-${i}"><div class="rc-loading"><span class="spin"></span>生成中...</div></div>
    </div>`;
  });

  const progWrap=document.getElementById('progWrap');
  const progFill=document.getElementById('progFill');
  const progText=document.getElementById('progText');
  progWrap.style.display='block';
  let done=0;

  await Promise.all(valid.map(async({f,i})=>{
    const fd=new FormData();fd.append('image',f);fd.append('model',model);
    document.getElementById('rstat-'+i).textContent='⚡ 生成中...';
    try{
      const res=await fetch('/api/generate',{method:'POST',body:fd});
      const data=await res.json();
      done++;progFill.style.width=(done/valid.length*100)+'%';progText.textContent=done+' / '+valid.length+' 完成';
      if(data.error)throw new Error(data.error);
      document.getElementById('rrec-'+i).textContent=data.recognized||'已识别';
      document.getElementById('rstat-'+i).textContent='✅ 完成';
      const tc={formal:'tf',humor:'th',short:'ts'};
      document.getElementById('rbody-'+i).innerHTML=(data.replies||[]).map(r=>`
        <div class="reply-row">
          <span class="rtag ${tc[r.type]||''}">${r.label}</span>
          <span class="rtext">${esc(r.text)}</span>
          <button class="cpbtn" onclick="cp(this,${JSON.stringify(r.text)})">复制</button>
        </div>`).join('');
    }catch(e){
      done++;progFill.style.width=(done/valid.length*100)+'%';progText.textContent=done+' / '+valid.length+' 完成';
      document.getElementById('rstat-'+i).textContent='❌ 失败';
      document.getElementById('rbody-'+i).className='rc-error';
      document.getElementById('rbody-'+i).innerHTML='❌ '+e.message;
    }
  }));

  goBtn.disabled=false;
  progText.textContent='✅ 全部完成！';
});

function toggle(i){
  const b=document.getElementById('rbody-'+i),t=document.getElementById('rtog-'+i);
  b.style.display=b.style.display==='none'?'':'none';
  t.textContent=b.style.display==='none'?'▶':'▼';
}
function esc(s){return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function cp(btn,text){
  navigator.clipboard.writeText(text).then(()=>{
    btn.textContent='✅';btn.classList.add('ok');
    setTimeout(()=>{btn.textContent='复制';btn.classList.remove('ok');},2000);
  });
}
</script>
</body>
</html>"""

# ── API ───────────────────────────────────────────────────────────────────────

def call_model(model_key: str, img_b64: str, media_type: str) -> dict:
    cfg = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    resp = client.chat.completions.create(
        model=cfg["model"],
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{img_b64}"}},
                {"type": "text", "text": "分析截图，生成3种拜年回复。严格JSON，不要其他文字。"}
            ]}
        ],
        timeout=30
    )
    text = resp.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"error": "请上传图片"}), 400
    file = request.files["image"]
    model_key = request.form.get("model", DEFAULT_MODEL)
    img_b64 = base64.standard_b64encode(file.read()).decode()
    media_type = file.content_type or "image/jpeg"
    if media_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        media_type = "image/jpeg"
    try:
        return jsonify(call_model(model_key, img_b64, media_type))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "default_model": DEFAULT_MODEL})


if __name__ == "__main__":
    print(f"🐍 拜年助手启动，端口: {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
