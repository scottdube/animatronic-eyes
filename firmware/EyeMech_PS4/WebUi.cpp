#include "WebUi.h"
#include "EyeSettings.h"
#include "Scenes.h"
#include "Rail.h"
#include "secrets.h"
#include <Update.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp_ota_ops.h>
#if __has_include("build_id.h")
#include "build_id.h"  // written by build.sh: git describe of the source
#endif
#ifndef BUILD_ID
#define BUILD_ID "unknown"
#endif

// The core marks a freshly flashed app valid at boot unless this says to wait.
// Waiting means: if the new firmware never gets Wi-Fi up, the next reset can
// roll back to the old one (when the bootloader has rollback enabled).
extern "C" bool verifyRollbackLater() { return true; }

static WebServer server(80);
static bool started = false, markedValid = false;

static bool authorized() {
#ifdef OTA_PASSWORD
  if (!server.authenticate("admin", OTA_PASSWORD)) {
    server.requestAuthentication();
    return false;
  }
#endif
  return true;
}

static const char PAGE[] PROGMEM = R"HTML(<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EyeMech</title>
<style>
:root{--bg:#fff;--fg:#111;--mut:#666;--line:#d4d7dc;--card:#f5f6f8;--acc:#0645ad;--warn:#b35900}
@media (prefers-color-scheme:dark){:root{--bg:#111;--fg:#eee;--mut:#9a9a9a;--line:#3a3d42;--card:#1b1c1f;--acc:#8ab4f8;--warn:#ffb74d}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:16px system-ui,sans-serif;margin:0 auto;max-width:1080px;padding:12px 16px 0}
header{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px}
h1{font-size:1.3em;margin:0}.mut{color:var(--mut);font-size:.88em}
nav{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 14px}
nav a{padding:5px 10px;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-size:.9em;background:var(--card)}
a{color:var(--acc)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px 14px;margin:0 0 14px;break-inside:avoid;scroll-margin-top:8px}
.card>h2{font-size:1.12em;margin:0 0 4px;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.tag{font-size:.72em;font-weight:600;color:var(--mut);border:1px solid var(--line);border-radius:4px;padding:1px 6px;white-space:nowrap}
.sub{border-top:1px solid var(--line);margin-top:14px;padding-top:10px}
.sub h3{font-size:.8em;margin:0 0 2px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut)}
.cols{columns:2 440px;column-gap:14px}
.cal{border:2px dashed var(--mut)}
.cal .cols{column-gap:28px}.cal .sub{break-inside:avoid}.cal .sub:first-child{border-top:0;margin-top:4px}
.row{margin:12px 0}.row label{display:flex;justify-content:space-between;gap:8px;font-weight:600}
.row label span{font-variant-numeric:tabular-nums}
input[type=range]{width:100%;height:30px;margin:2px 0}select{font-size:1em;padding:6px;width:100%;margin-top:4px}
button{flex:1;font-size:1em;padding:10px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
button.pri{background:var(--acc);color:var(--bg);border-color:var(--acc);font-weight:600}
button:active{transform:scale(.95);filter:brightness(.8)}button:disabled{opacity:.6}
.sc{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}
.sc button{padding:10px 4px}.lk{grid-template-columns:repeat(3,1fr)}
#now{display:grid;grid-template-columns:1fr;gap:4px}
#mode{font-size:1.2em;font-weight:700}
#st{font-size:.95em}
details.help{margin-top:6px}details.help summary{cursor:pointer;color:var(--acc);font-size:.9em}
details.help p{margin:6px 0 0}
.ends{display:flex;justify-content:space-between}
.bar{position:sticky;bottom:0;background:var(--bg);border-top:1px solid var(--line);padding:10px 0 12px;margin-top:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#sv{flex:1 1 100%;font-size:.95em}.bar.dirty #sv{color:var(--warn);font-weight:700}
.bar button{flex:1}
</style></head><body>
<header><h1>👁 EyeMech</h1><span class="mut" id="bi"></span></header>
<nav><a href="#now">▶ Now</a><a href="#eyes">◉ Eyes &amp; lids</a><a href="#shows">∿ Shows</a><a href="#idle">≈ Alive idle</a><a href="#ctl">✕ Controller</a><a href="#radar">◉ Radar</a><a href="#cal">🔧 Calibration</a></nav>

<section class="card" id="now">
<h2>▶ Now</h2>
<div id="mode">…</div>
<div id="st">…</div>
<div id="pw" class="mut">…</div>
<div class="sc"><button data-c="show">∿ Show</button><button data-c="extended">∿∿ Extended</button><button data-c="play">▶ Play</button><button data-c="record">⏺ Record</button>
<button data-c="stop">■ Stop</button><button data-c="sleep">☾ Sleep</button><button data-c="wake">☀ Wake</button>
<button data-c="service">🔧 Service</button></div>
<div class="mut" id="scm">Record needs the controller: it records what you do with it.</div>
</section>

<div class="cols">
<section class="card" id="eyes">
<h2>◉ Eyes &amp; lids <span class="tag">everyday</span></h2>
<div class="sub" style="border:0;margin-top:4px;padding-top:0"><h3>Pupil center</h3>
<div class="mut">Where the eyes look straight ahead; sticks and glances work around it. Moving a slider stops idle and holds the eyes there.</div>
<div class="row"><label>Up / down <span id="v_parkY"></span></label>
<input type="range" id="parkY" min="0" max="300" step="5"><div class="mut">0 = true center (set under Calibration), higher = lower</div></div>
<div class="row"><label>Left / right <span id="v_parkX"></span></label>
<input type="range" id="parkX" min="-150" max="150" step="5" style="direction:rtl"><div class="mut ends"><span>◂ his left</span><span>0 = true center</span><span>his right ▸</span></div></div>
</div>
<div class="sub"><h3>Lid presets, % open</h3>
<div class="mut">D-pad up/down steps closed ‹ squint ‹ normal ‹ wide. Power-up is normal; a blink goes to closed. A button or a slider shows that preset.</div>
<div class="sc pr"><button data-k="lidWide">▲ Wide</button><button data-k="lidNormal">● Normal</button><button data-k="lidSquint">◒ Squint</button><button data-k="lidClosed">▬ Closed</button></div>
<div class="row"><label>▲ Wide <span><span id="v_lidWide"></span>%</span></label><input type="range" id="lidWide" min="0" max="100" step="1"></div>
<div class="row"><label>● Normal <span><span id="v_lidNormal"></span>%</span></label><input type="range" id="lidNormal" min="0" max="100" step="1"></div>
<div class="row"><label>◒ Squint <span><span id="v_lidSquint"></span>%</span></label><input type="range" id="lidSquint" min="0" max="100" step="1"></div>
<div class="row"><label>▬ Closed <span><span id="v_lidClosed"></span>%</span></label><input type="range" id="lidClosed" min="0" max="100" step="1">
<div class="mut">0 = the positions the horns were seated to</div></div>
</div>
<div class="sub"><h3>Lid shape</h3>
<div class="row"><label>Bottom lids come up <span id="v_lowLidCurve"></span></label>
<input type="range" id="lowLidCurve" min="25" max="300" step="5"><div class="mut">50 = gently, 100 = same as the top, higher = further up. Closed and wide don't change</div></div>
<div class="row"><label>Lids follow eyes <span><span id="v_lidFollow"></span>%</span></label>
<input type="range" id="lidFollow" min="0" max="100" step="5"><div class="mut">100 = kit, 0 = lids stay put when the eyes look up or down</div></div>
</div>
</section>

<section class="card" id="shows">
<h2>∿ Shows</h2>
<div class="mut">A show is a spell of alive idle that ends with the eyes asleep.</div>
<details class="help"><summary>How shows work</summary><p class="mut">Everyday: you arrive, the eyes wait, do one show,
then sleep while you're in the lab, with another show now and then. A show that starts from sleep opens wide and looks far
to his left first; now and then he winks, either eye. Every 30-50 s he also does one of: the slow squint, an eye roll, or a
circle around the edge of his travel.</p></details>
<div class="row"><label>Shows</label>
<select id="idleMode"><option value="0">Off (eyes rest open)</option><option value="1">Automatic: on arrival and now and then</option><option value="2">On demand only (Triangle, this page, voice)</option></select></div>
<div class="row"><label>What a show is</label>
<select id="arriveAction"><option value="0">Nothing</option><option value="1">Alive idle</option><option value="2">Play the recording, then idle</option></select></div>
<div class="row"><label>Starts after you arrive <span><span id="v_arriveDelay"></span> s</span></label>
<input type="range" id="arriveDelay" min="0" max="300" step="5"><div class="mut">Power-up counts as an arrival</div></div>
<div class="row"><label>A show lasts <span><span id="v_showSecs"></span> s</span></label>
<input type="range" id="showSecs" min="30" max="900" step="10"></div>
<div class="row"><label>Another show every <span><span id="v_showEvery"></span> min</span></label>
<input type="range" id="showEvery" min="0" max="240" step="5"><div class="mut">While you're here. 0 = only on arrival. Needs the radar</div></div>
<div class="row"><label>Extended play lasts <span><span id="v_extendMins"></span> min</span></label>
<input type="range" id="extendMins" min="1" max="120" step="1"></div>
<div class="sub"><h3>Sleep</h3>
<div class="row"><label>Back to sleep after the controller <span><span id="v_handsOffSecs"></span> s</span></label>
<input type="range" id="handsOffSecs" min="5" max="600" step="5"></div>
<div class="row"><label>While asleep</label>
<select id="sleepQuiet"><option value="1">Silent (servos let go once the lids close)</option><option value="0">Hold (servos powered)</option></select></div>
</div>
</section>

<section class="card" id="idle">
<h2>≈ Alive idle</h2>
<div class="row"><label>Time between glances <span><span id="v_glanceTenths"></span> ×0.1 s</span></label>
<input type="range" id="glanceTenths" min="5" max="50" step="1"></div>
<div class="row"><label>How far glances go <span><span id="v_glanceRange"></span>%</span></label>
<input type="range" id="glanceRange" min="10" max="100" step="5"></div>
<div class="row"><label>Blinks per minute <span id="v_blinkRate"></span></label>
<input type="range" id="blinkRate" min="0" max="30" step="1"></div>
</section>

<section class="card" id="ctl">
<h2>✕ Controller</h2>
<div class="row"><label>Blink button</label>
<select id="blinkBtn"><option value="0">✕ Cross</option><option value="1">□ Square</option><option value="2">Either</option></select></div>
<div class="mut">Reconnect after a restart: hold P4 ~10 s until the light goes out, then press P4.</div>
</section>

<section class="card" id="radar">
<h2>◉ Bench radar <span class="tag">Home Assistant</span></h2>
<div class="row"><label>New arrival after empty for <span><span id="v_emptyMins"></span> min</span></label>
<input type="range" id="emptyMins" min="1" max="60" step="1"><div class="mut">So a quick step out doesn't start a show</div></div>
</section>
</div>

<section class="card cal" id="cal">
<h2>🔧 Calibration <span class="tag">set once, after a horn moves</span></h2>
<div class="mut">Servo centers, travel limits, lid max open and lid trims. Everyday adjustments are in the boxes above.</div>
<div class="cols">
<div class="sub"><h3>Eye servos</h3>
<div class="row"><label>Left/right servo center <span id="v_xCenter"></span></label>
<input type="range" id="xCenter" min="-40" max="40" step="1" style="direction:rtl"><div class="mut ends"><span>◂ his left</span><span>pulse counts, pupil center at 0</span><span>his right ▸</span></div></div>
<div class="row"><label>Up/down servo center <span id="v_yCenter"></span></label>
<input type="range" id="yCenter" min="-40" max="40" step="1"><div class="mut ends"><span>▾ down</span><span>pulse counts, pupil center at 0</span><span>up ▴</span></div></div>
<div class="row"><label>Up travel limit <span id="v_upMax"></span></label>
<input type="range" id="upMax" min="420" max="500" step="2"><div class="mut">500 = kit. Lower it until a full look up (Look test ▴ Up) doesn't strain</div></div>
</div>
<div class="sub"><h3>Look test</h3>
<div class="mut">Holds the eyes at full travel to check for a stop or strain. Stop, a preset or a show ends it.</div>
<div class="sc lk"><button data-c="lookL">◂ His left</button><button data-c="lookU">▴ Up</button><button data-c="lookR">His right ▸</button>
<button data-c="lookC">● Center</button><button data-c="lookD">▾ Down</button><button data-c="stop">■ Stop</button></div>
</div>
<div class="sub"><h3>Lid max open</h3>
<div class="row"><label>Top lids <span id="v_lidMin"></span></label>
<input type="range" id="lidMin" min="160" max="280" step="2"><div class="mut">Sets 100% open for the presets. 280 = kit, 250 = your original sketch, 200 matched to the re-seated horns. Lower opens further: watch for a straining servo</div></div>
<div class="row"><label>Bottom lids <span id="v_lowLidMax"></span></label>
<input type="range" id="lowLidMax" min="400" max="520" step="2"><div class="mut">400 = kit. Higher opens the bottom lids further</div></div>
</div>
<div class="sub"><h3>Lid trims for: <span id="trp">● Normal</span></h3>
<div class="mut">Pick a preset, then match the eyes. − more closed, + more open. Left/right are HIS: his left eye is the one on your right as you face him.</div>
<div class="sc pr"><button data-k="lidWide">▲ Wide</button><button data-k="lidNormal">● Normal</button><button data-k="lidSquint">◒ Squint</button><button data-k="lidClosed">▬ Closed</button></div>
<div class="row"><label>His left eye, top lid <span id="v_tLTop"></span></label><input type="range" id="tLTop" min="-60" max="60" step="1"></div>
<div class="row"><label>His left eye, bottom lid <span id="v_tLBot"></span></label><input type="range" id="tLBot" min="-60" max="60" step="1"></div>
<div class="row"><label>His right eye, top lid <span id="v_tRTop"></span></label><input type="range" id="tRTop" min="-60" max="60" step="1"></div>
<div class="row"><label>His right eye, bottom lid <span id="v_tRBot"></span></label><input type="range" id="tRBot" min="-60" max="60" step="1"></div>
</div>
</div>
</section>
<p class="mut">Changes move the eyes immediately. <b>Save</b> keeps them after power-off. <a href="/update">Firmware update</a></p>
<div class="bar" id="bar"><span id="sv">…</span><button class="pri" id="save">Save</button><button id="revert">Revert</button><button id="defaults">Defaults</button></div>
<script>
const K=['parkY','parkX','xCenter','yCenter','upMax','lidWide','lidNormal','lidSquint','lidClosed','lowLidCurve','lidMin','lowLidMax','lidFollow','blinkBtn','idleMode','arriveDelay','showSecs','showEvery','extendMins','handsOffSecs','sleepQuiet',
 'glanceTenths','glanceRange','blinkRate','arriveAction','emptyMins'];
const M={live:'● Live: controller driving',idle:'∿ Show (alive idle)',play:'▶ Playing the recording',record:'⏺ RECORDING',sleep:'☾ Asleep (lids closed)',rest:'○ Resting',service:'🔧 SERVICE: holding still, shows and controller off (🔧 again to end)'};let dirty=false,busy=false,pend=null;
const $=id=>document.getElementById(id);
const fm=t=>t<90?t+' s':Math.round(t/60)+' min';
// Trims: one set of four sliders edits the selected preset's (prefix c/s/n/w)
const T=['LTop','LBot','RTop','RBot'],P={lidClosed:['c','▬ Closed'],lidSquint:['s','◒ Squint'],lidNormal:['n','● Normal'],lidWide:['w','▲ Wide']};
let V={},tp='n';
function showT(){T.forEach(t=>{const v=V[tp+t];if(v===undefined)return;$('t'+t).value=v;$('v_t'+t).textContent=v})}
function show(v){V=v;K.forEach(k=>{$(k).value=v[k];const o=$('v_'+k);if(o)o.textContent=v[k]});showT();dirty=v.dirty}
T.forEach(t=>$('t'+t).addEventListener('input',e=>{$('v_t'+t).textContent=e.target.value;V[tp+t]=+e.target.value;
 pend=tp+t+'='+e.target.value;send()}));
// A request lost to a restart (OTA) can hang forever, and send() waits on each
// one: give up after 3 s so later slider moves still go out.
async function j(u,o){const c=new AbortController(),t=setTimeout(()=>c.abort(),3000);
 try{const r=await fetch(u,{...o,signal:c.signal});if(!r.ok)throw new Error(r.status);return r.json()}finally{clearTimeout(t)}}
async function send(){if(busy||!pend)return;busy=true;const q=pend;pend=null;
 try{const v=await j('/set?'+q,{method:'POST'});dirty=v.dirty}catch(e){}busy=false;send()}
K.forEach(k=>$(k).addEventListener('input',e=>{const o=$('v_'+k);if(o)o.textContent=e.target.value;
 pend=k+'='+e.target.value;send()}));
// Save / Revert / Defaults answer on the button itself: working, then done or failed
async function act(b,u,ok){const t=b.textContent;b.disabled=true;b.textContent='…';let m;
 try{show(await j(u,{method:'POST'}));m='✓ '+ok}catch(e){m='⚠ Failed'}
 b.textContent=m;poll();setTimeout(()=>{b.textContent=t;b.disabled=false},2000)}
$('save').onclick=e=>act(e.target,'/save','Saved');
$('revert').onclick=e=>act(e.target,'/revert','Reverted');
$('defaults').onclick=e=>act(e.target,'/defaults','Defaults');
// Preset buttons show a preset: re-sending its current value switches the eyes to it
document.querySelectorAll('.pr button').forEach(b=>b.onclick=()=>{const k=b.dataset.k;tp=P[k][0];$('trp').textContent=P[k][1];showT();
 pend=k+'='+$(k).value;send()});
document.querySelectorAll('.sc:not(.pr) button').forEach(b=>b.onclick=async()=>{
 const r=await fetch('/scene?cmd='+b.dataset.c,{method:'POST'});
 $('scm').textContent=r.ok?'':'⚠ '+(await r.text());poll()});
async function poll(){try{const s=await j('/status');
 const bt=s.batt<0?'':' · '+(s.batt<=2&&!s.charging?'⚠ ':'')+'battery '+Math.min(s.batt,10)+'/10'+(s.charging?(s.batt>=11?' (charged)':' (charging)'):'')+(s.conn?'':' at last contact');
 $('st').innerHTML=(s.conn?'● Controller connected':'○ Controller not connected')+bt+
 ' &nbsp;·&nbsp; '+(s.present?'◉ Someone at the bench':'◌ Bench empty');
 $('sv').textContent=dirty?'✎ Unsaved changes: Save keeps them after power-off':'✓ All changes saved';$('bar').classList.toggle('dirty',dirty);
 $('mode').textContent=(M[s.mode]||s.mode)+(s.showLeft>=0?' · '+fm(s.showLeft)+' left':'')+(s.nextShow>=0?' · next show in '+fm(s.nextShow):'')+' · recording '+(s.recMs?(s.recMs/1000).toFixed(1)+' s':'none');
 const v=x=>(x/1000).toFixed(2)+' V',low=s.railDips>0||s.rail<4400;
 $('pw').innerHTML=s.rail<1000?'Last restart: '+(s.reset=='brownout'?'<b>⚠ BROWNOUT</b>':s.reset):
  (low?'⚠':'✓')+' ⚡ 5 V rail '+v(s.rail)+' · min '+v(s.railMin)+' · max '+v(s.railMax)+' · sags over 0.4 V: '+s.railDips+
  ' · last restart: '+(s.reset=='brownout'?'<b>⚠ BROWNOUT</b>':s.reset)+' <button id="rr" style="flex:none;padding:2px 8px;font-size:.85em">reset min</button>';
 const rr=$('rr');if(rr)rr.onclick=async()=>{await fetch('/railreset',{method:'POST'});poll()};
 $('bi').textContent='build '+s.build+' · '+s.slot+' · '+s.ip+' · heap '+s.heap}catch(e){$('st').textContent='⚠ lost contact with the eyes'}}
j('/values').then(show).then(poll);setInterval(poll,2000);
</script></body></html>)HTML";

static const char UPDATE_PAGE[] PROGMEM = R"HTML(<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EyeMech update</title><style>body{font:16px system-ui,sans-serif;max-width:560px;margin:0 auto;padding:16px}
@media (prefers-color-scheme:dark){body{background:#111;color:#eee}}</style></head><body>
<h1>EyeMech firmware update</h1><p>Running build <b>%BUILD%</b></p>
<form method="POST" action="/update" enctype="multipart/form-data">
<input type="file" name="firmware" accept=".bin"> <input type="submit" value="Upload"></form>
<p>Use <code>build/EyeMech_PS4.ino.bin</code> (from <code>./build.sh</code>). The eyes restart when it is
done, which drops the controller: hold P4 ~10 s until the light goes out, then press P4.</p>
<p><a href="/">Settings</a></p></body></html>)HTML";

static void sendJson(const String &s) { server.send(200, "application/json", s); }

void webBegin() {
  server.on("/", HTTP_GET, [] {
    if (!authorized()) return;
    server.send_P(200, "text/html", PAGE);
  });
  server.on("/values", HTTP_GET, [] {
    if (!authorized()) return;
    sendJson(settingsJson());
  });
  server.on("/status", HTTP_GET, [] {
    if (!authorized()) return;
    sendJson(eyeStatusJson());
  });
  server.on("/set", HTTP_POST, [] {
    if (!authorized()) return;
    for (int i = 0; i < server.args(); i++) {
      String k = server.argName(i);
      if (k == "plain") continue;  // WebServer's name for the body
      if (!setSetting(k, server.arg(i).toInt())) {
        server.send(400, "text/plain", "unknown setting " + k + "\n");
        return;
      }
      applyLiveSetting(k);
    }
    sendJson(settingsJson());
  });
  server.on("/save", HTTP_POST, [] {
    if (!authorized()) return;
    if (!saveSettings()) {
      server.send(500, "text/plain", "NVS write failed\n");
      return;
    }
    sendJson(settingsJson());
  });
  server.on("/revert", HTTP_POST, [] {
    if (!authorized()) return;
    loadSettings();
    applyLiveSetting("");  // "" = everything may have changed
    sendJson(settingsJson());
  });
  server.on("/defaults", HTTP_POST, [] {
    if (!authorized()) return;
    resetSettings(settings);
    applyLiveSetting("");
    sendJson(settingsJson());  // not saved until Save
  });

  // idle | play | record | stop | sleep | wake
  server.on("/scene", HTTP_POST, [] {
    if (!authorized()) return;
    String c = server.arg("cmd");
    if (!sceneCommand(c)) {
      server.send(409, "text/plain", "can't " + c + " now (in service? shows off? no recording? no controller?)\n");
      return;
    }
    sendJson(eyeStatusJson());
  });
  server.on("/pca", HTTP_GET, [] {  // PCA9685 registers: MODE1/2, prescale, ALL_LED, ch 0-5
    if (!authorized()) return;
    sendJson(pcaRegsJson());
  });
  server.on("/pcatest", HTTP_POST, [] {  // out=high|low|run: hold ch 0-5 full-on/off
    if (!authorized()) return;
    String o = server.arg("out");
    setPcaTest(o == "high" ? 1 : o == "low" ? -1 : 0);
    sendJson(pcaRegsJson());
  });
  server.on("/railreset", HTTP_POST, [] {  // start the rail's min/max/dips afresh
    if (!authorized()) return;
    railReset();
    server.send(200, "text/plain", "ok\n");
  });
  // Home Assistant, from the bench radar
  server.on("/presence", HTTP_POST, [] {
    if (!authorized()) return;
    String st = server.arg("state");
    if (st != "on" && st != "off") {
      server.send(400, "text/plain", "state=on|off\n");
      return;
    }
    scenePresence(st == "on");
    sendJson(eyeStatusJson());
  });

  server.on("/update", HTTP_GET, [] {
    if (!authorized()) return;
    String page = FPSTR(UPDATE_PAGE);
    page.replace("%BUILD%", BUILD_ID);
    server.send(200, "text/html", page);
  });
  server.on(
      "/update", HTTP_POST,
      [] {
        if (!authorized()) return;
        bool ok = !Update.hasError() && Update.isFinished();  // isFinished: a file actually arrived
        server.send(ok ? 200 : 500, "text/plain",
                    ok ? "Update OK, restarting.\n" : "Update FAILED, old firmware kept.\n");
        delay(300);
        if (ok) ESP.restart();
      },
      [] {
        // The upload handler can't send a challenge mid-stream, so an unauthorized
        // upload is simply not written; the final handler then sends the challenge.
        // Update.end(true) switches the boot slot, so this check must be here too.
        static bool allowed = false;
        HTTPUpload &up = server.upload();
        if (up.status == UPLOAD_FILE_START) {
#ifdef OTA_PASSWORD
          allowed = server.authenticate("admin", OTA_PASSWORD);
#else
          allowed = true;
#endif
        }
        if (!allowed) return;
        if (up.status == UPLOAD_FILE_START) {
          Serial.printf("OTA: receiving %s\n", up.filename.c_str());
          if (!Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH)) Update.printError(Serial);
        } else if (up.status == UPLOAD_FILE_WRITE) {
          if (Update.write(up.buf, up.currentSize) != up.currentSize) Update.printError(Serial);
        } else if (up.status == UPLOAD_FILE_END) {
          if (Update.end(true)) Serial.printf("OTA: %u bytes written\n", up.totalSize);
          else Update.printError(Serial);
        } else if (up.status == UPLOAD_FILE_ABORTED) {
          Update.abort();
          Serial.println("OTA: aborted");
        }
      });
  server.onNotFound([] { server.send(404, "text/plain", "not found\n"); });

  server.begin();
  started = true;
  Serial.printf("Web: build %s\n", BUILD_ID);
#ifndef OTA_PASSWORD
  Serial.println("Web: no OTA_PASSWORD - anyone on this network can change settings and flash");
#endif
}

void webHandle() {
  if (!started) return;
  server.handleClient();
  // New firmware counts as good once it has joined Wi-Fi with the server up.
  if (!markedValid && WiFi.status() == WL_CONNECTED) {
    esp_ota_mark_app_valid_cancel_rollback();  // harmless when nothing is pending
    markedValid = true;
    Serial.printf("Web: http://%s/  (firmware marked valid)\n", WiFi.localIP().toString().c_str());
  }
}
