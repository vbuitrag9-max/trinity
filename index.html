<!DOCTYPE html>
<html lang="es-419">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trinity</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family:'Segoe UI', system-ui, sans-serif;
    background:radial-gradient(ellipse at 50% 0%, #0b1026 0%, #05070f 60%, #020308 100%);
    color:#e5e9f5; height:100vh; display:flex; flex-direction:column; overflow:hidden;
  }
  header { display:flex; align-items:center; justify-content:space-between; padding:16px 20px; }
  .logo { font-size:18px; font-weight:500; letter-spacing:4px; color:#c7d2fe; }
  .logo span { color:#7c8cff; }
  .badge { font-size:11px; color:#5a648a; border:1px solid #232c4d; border-radius:999px; padding:3px 10px; }
  #stage { position:relative; height:260px; display:flex; align-items:center; justify-content:center; flex:none; }
  #orb { width:240px; height:240px; }
  #status { position:absolute; bottom:6px; font-size:12px; letter-spacing:3px; text-transform:uppercase; color:#5a648a; transition:color .4s; }
  #status.listening { color:#67e8f9; } #status.thinking { color:#a78bfa; } #status.speaking { color:#93c5fd; }
  #chat { flex:1; overflow-y:auto; padding:8px 20px; display:flex; flex-direction:column; gap:12px; scrollbar-width:thin; }
  .msg { max-width:78%; padding:10px 14px; border-radius:16px; font-size:15px; line-height:1.5; animation:pop .25s ease-out; white-space:pre-wrap; }
  @keyframes pop { from{opacity:0; transform:translateY(8px);} to{opacity:1;} }
  .user { align-self:flex-end; background:linear-gradient(135deg,#4f46e5,#7c3aed); border-bottom-right-radius:4px; }
  .trinity { align-self:flex-start; background:rgba(124,140,255,.08); border:1px solid #232c4d; border-bottom-left-radius:4px; }
  #composer { display:flex; gap:8px; padding:16px 20px 20px; align-items:center; }
  #input { flex:1; background:rgba(124,140,255,.06); border:1px solid #232c4d; border-radius:999px; padding:12px 18px; color:#e5e9f5; font-size:15px; outline:none; }
  #input:focus { border-color:#4f46e5; }
  .btn { width:46px; height:46px; border-radius:50%; border:1px solid #232c4d; background:rgba(124,140,255,.08); color:#a5b4fc; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:.2s; flex:none; }
  .btn:hover { border-color:#4f46e5; }
  .btn.rec { background:#7c3aed; border-color:#7c3aed; color:#fff; animation:pulse 1.2s infinite; }
  @keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(124,58,237,.5);} 50%{box-shadow:0 0 0 12px rgba(124,58,237,0);} }
  .btn svg { width:20px; height:20px; }
</style>
<base target="_blank">
</head>
<body>
<header>
  <div class="logo">TRINI<span>TY</span></div>
  <div class="badge" id="engine">gemini · make.com · render</div>
</header>

<div id="stage">
  <canvas id="orb"></canvas>
  <div id="status">en línea</div>
</div>

<div id="chat"></div>

<div id="composer">
  <button class="btn" id="mic" title="Hablar">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
  </button>
  <input id="input" type="text" placeholder="Escribe o usa el micrófono..." autocomplete="off">
  <button class="btn" id="send" title="Enviar">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
  </button>
</div>

<script>
// ---------- Orbe plasma ----------
const canvas = document.getElementById('orb');
const ctx = canvas.getContext('2d');
const BLOBS = [
  {h:200,s:90,l:60,ph:0},{h:225,s:95,l:62,ph:1.3},{h:255,s:90,l:64,ph:2.6},
  {h:275,s:85,l:60,ph:4},{h:210,s:100,l:70,ph:5.2}
];
const STATE_CFG = {
  idle:      {e:.32, rot:.25},
  listening: {e:.60, rot:.40, ring:true},
  thinking:  {e:.95, rot:1.60, jit:true},
  speaking:  {e:.72, rot:.50, breath:true}
};
let curState = 'idle';

function fitOrb(){
  const d = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = 240 * d; canvas.height = 240 * d;
  ctx.setTransform(d,0,0,d,0,0);
}
fitOrb(); window.addEventListener('resize', fitOrb);

function drawOrb(t){
  const w = 240, h = 240, cx = 120, cy = 120, R = 105;
  ctx.clearRect(0,0,w,h);
  const s = STATE_CFG[curState];
  const e = curState==='speaking' ? s.e + .12*Math.sin(t*5) : s.e;
  let sc = 1;
  if (s.breath) sc = 1 + .07*Math.sin(t*4.5);
  if (s.jit)    sc = 1 + .03*Math.sin(t*13);
  ctx.save(); ctx.translate(cx,cy); ctx.scale(sc,sc); ctx.translate(-cx,-cy);

  if (s.ring){
    for (let i=0;i<3;i++){
      const p = ((t*.5)+(i/3)) % 1;
      ctx.beginPath(); ctx.arc(cx,cy,R*(.45+p*.75),0,7);
      ctx.strokeStyle = 'hsla(225,90%,70%,' + ((1-p)*.4*e+.05) + ')';
      ctx.lineWidth = 1.5; ctx.stroke();
    }
  }
  ctx.globalCompositeOperation = 'lighter';
  const n = BLOBS.length;
  for (let i=0;i<n;i++){
    const b = BLOBS[i];
    const ang = t*s.rot*(i%2?1:-1) + i*Math.PI*2/n + b.ph;
    const orbit = R*.34*(1+.18*Math.sin(t*.9+b.ph*2));
    const px = cx+Math.cos(ang)*orbit, py = cy+Math.sin(ang)*orbit;
    const br = R*.42*(1+.22*Math.sin(t*1.4+b.ph*3))*(.55+e*.7);
    const g = ctx.createRadialGradient(px,py,0,px,py,br);
    g.addColorStop(0, 'hsla('+b.h+','+b.s+'%,'+b.l+'%,'+(.5*e+.15)+')');
    g.addColorStop(1, 'hsla(0,0%,0%,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px,py,br,0,7); ctx.fill();
  }
  const cr = R*.5*(.7+e*.5);
  const cg = ctx.createRadialGradient(cx,cy,0,cx,cy,cr);
  cg.addColorStop(0,   'hsla(210,100%,92%,'+(.85*Math.min(1,e+.4))+')');
  cg.addColorStop(.55, 'hsla(210,95%,70%,'+(.35*e)+')');
  cg.addColorStop(1,   'hsla(0,0%,0%,0)');
  ctx.fillStyle = cg; ctx.beginPath(); ctx.arc(cx,cy,cr,0,7); ctx.fill();
  ctx.restore();
}
(function loop(now){ drawOrb(now/1000); requestAnimationFrame(loop); })(performance.now());

// ---------- Estados y UI ----------
const statusEl = document.getElementById('status');
const chatEl   = document.getElementById('chat');
const inputEl  = document.getElementById('input');

const STATUS_TXT = {
  idle:'en línea', listening:'escuchando', thinking:'procesando', speaking:'trinity responde'
};
function setState(s){
  curState = s;
  statusEl.textContent = STATUS_TXT[s];
  statusEl.className = s;
}

function addMsg(text, who){
  const d = document.createElement('div');
  d.className = 'msg ' + who; d.textContent = text;
  chatEl.appendChild(d); chatEl.scrollTop = chatEl.scrollHeight;
  return d;
}

// ---------- Voz de salida (TTS) ----------
let esVoice = null;
function pickVoice(){
  const vs = speechSynthesis.getVoices().filter(v => v.lang.toLowerCase().startsWith('es'));
  esVoice = vs.find(v => /mexico|latam|america|419/i.test(v.lang + v.name)) || vs[0] || null;
}
pickVoice();
if (speechSynthesis.onvoiceschanged !== undefined) speechSynthesis.onvoiceschanged = pickVoice;

function speak(text, onEnd){
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  if (esVoice) u.voice = esVoice;
  u.lang = 'es-419'; u.rate = 1.02; u.pitch = 1.05;
  u.onend = () => { if (onEnd) onEnd(); };
  u.onerror = () => { if (onEnd) onEnd(); };
  speechSynthesis.speak(u);
}

// ---------- Voz de entrada (reconocimiento) ----------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec = null, recording = false;
if (SR){
  rec = new SR();
  rec.lang = 'es-419'; rec.interimResults = false; rec.maxAlternatives = 1;
  rec.onstart  = () => { recording = true;  setState('listening'); };
  rec.onend    = () => { recording = false; };
  rec.onerror  = () => { recording = false; setState('idle'); };
  rec.onresult = (ev) => {
    const text = ev.results[0][0].transcript;
    inputEl.value = text;
    setState('idle');
    send(text);
  };
}
document.getElementById('mic').addEventListener('click', () => {
  if (!rec){ addMsg('Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge.', 'trinity'); return; }
  if (recording){ rec.stop(); return; }
  speechSynthesis.cancel(); setState('idle');
  try { rec.start(); } catch(e){}
});

// ---------- Conversación ----------
async function send(text){
  text = (text || '').trim();
  if (!text) return;
  inputEl.value = '';
  addMsg(text, 'user');
  setState('thinking');

  const bubble = document.createElement('div');
  bubble.className = 'msg trinity'; bubble.textContent = '...';
  chatEl.appendChild(bubble); chatEl.scrollTop = chatEl.scrollHeight;

  let reply;
  try {
    const r = await fetch('/chat', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    const data = await r.json();
    if (!data.ok){ throw new Error(data.error || 'Error desconocido'); }
    reply = data.reply;
  } catch(err){
    bubble.textContent = 'No pude contactar a Gemini: ' + err.message;
    setState('idle'); return;
  }

  // Efecto de escritura sincronizado con la voz
  setState('speaking');
  bubble.textContent = '';
  let i = 0;
  const typer = setInterval(() => {
    bubble.textContent = reply.slice(0, ++i);
    chatEl.scrollTop = chatEl.scrollHeight;
    if (i >= reply.length) clearInterval(typer);
  }, 24);

  speak(reply, () => setState('idle'));
}

document.getElementById('send').addEventListener('click', () => send(inputEl.value));
inputEl.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') send(inputEl.value); });

// Saludo inicial
setState('speaking');
addMsg("Hola, soy Trinity. Escríbeme o toca el micrófono para hablarme.", 'trinity');
speak("Hola, soy Trinity. Escríbeme o toca el micrófono para hablarme.", () => setState('idle'));
</script>
</body>
</html>
