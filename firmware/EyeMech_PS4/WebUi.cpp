#include "WebUi.h"
#include "EyeSettings.h"
#include "Scenes.h"
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
:root{--bg:#fff;--fg:#111;--mut:#666;--line:#ddd;--acc:#0645ad}
@media (prefers-color-scheme:dark){:root{--bg:#111;--fg:#eee;--mut:#999;--line:#333;--acc:#8ab4f8}}
body{background:var(--bg);color:var(--fg);font:16px system-ui,sans-serif;margin:0 auto;max-width:560px;padding:16px}
h1{font-size:1.3em;margin:0 0 4px}.mut{color:var(--mut);font-size:.9em}
#st{margin:8px 0 16px;padding:8px;border:1px solid var(--line);border-radius:6px}
.row{margin:18px 0}.row label{display:flex;justify-content:space-between;font-weight:600}
input[type=range]{width:100%;height:32px}select{font-size:1em;padding:6px;width:100%}
.btns{display:flex;gap:8px;margin-top:20px}button{flex:1;font-size:1em;padding:12px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
button.pri{background:var(--acc);color:var(--bg);border-color:var(--acc)}
button:active{transform:scale(.95);filter:brightness(.8)}button:disabled{opacity:.6}
a{color:var(--acc)}
h2{font-size:1.05em;margin:26px 0 0;padding-top:10px;border-top:1px solid var(--line)}
#mode{font-size:1.15em;font-weight:600}.sc{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}
.sc button{padding:10px 4px}.pr{grid-template-columns:repeat(4,1fr)}
</style></head><body>
<h1>EyeMech</h1>
<div class="mut" id="bi"></div>
<div id="st">…</div>
<div id="mode">…</div>
<div class="sc"><button data-c="show">∿ Show</button><button data-c="extended">∿∿ Extended</button><button data-c="play">▶ Play</button><button data-c="record">⏺ Record</button>
<button data-c="stop">■ Stop</button><button data-c="sleep">☾ Sleep</button><button data-c="wake">☀ Wake</button></div>
<div class="mut" id="scm">Record needs the controller: it records what you do with it.</div>
<h2>Eyes and lids</h2>
<p class="mut">Pupil center: set where the eyes look straight ahead. Moving either slider stops idle and
holds the eyes there. The sticks and idle glances all work around this point.</p>
<div class="row"><label>Pupil center up / down <span id="v_parkY"></span></label>
<input type="range" id="parkY" min="0" max="300" step="5"><div class="mut">0 = kit center, higher = lower</div></div>
<div class="row"><label>Pupil center left / right <span id="v_parkX"></span></label>
<input type="range" id="parkX" min="-150" max="150" step="5" style="direction:rtl"><div class="mut" style="display:flex;justify-content:space-between"><span>◂ his left</span><span>0 = kit center</span><span>his right ▸</span></div></div>
<p class="mut">Lid presets, % open. D-pad up/down steps closed ‹ squint ‹ normal ‹ wide; power-up is normal,
a blink goes to closed. The buttons, or moving a slider, show that preset.</p>
<div class="sc pr"><button data-k="lidWide">▲ Wide</button><button data-k="lidNormal">● Normal</button><button data-k="lidSquint">◒ Squint</button><button data-k="lidClosed">▬ Closed</button></div>
<div class="row"><label>▲ Wide <span id="v_lidWide"></span>%</label><input type="range" id="lidWide" min="0" max="100" step="1"></div>
<div class="row"><label>● Normal <span id="v_lidNormal"></span>%</label><input type="range" id="lidNormal" min="0" max="100" step="1"></div>
<div class="row"><label>◒ Squint <span id="v_lidSquint"></span>%</label><input type="range" id="lidSquint" min="0" max="100" step="1"></div>
<div class="row"><label>▬ Closed <span id="v_lidClosed"></span>%</label><input type="range" id="lidClosed" min="0" max="100" step="1">
<div class="mut">0 = the positions the horns were seated to</div></div>
<div class="row"><label>Bottom lids come up <span id="v_lowLidCurve"></span></label>
<input type="range" id="lowLidCurve" min="25" max="300" step="5"><div class="mut">50 = gently, 100 = same as the top, higher = further up. Closed and wide don't change</div></div>
<div class="row"><label>Top lid max open <span id="v_lidMin"></span></label>
<input type="range" id="lidMin" min="160" max="280" step="2"><div class="mut">Sets 100% open for the presets. 280 = kit, 250 = your original sketch, 200 matched to the re-seated horns. Lower opens the top lids further: watch for a straining servo</div></div>
<div class="row"><label>Bottom lid max open <span id="v_lowLidMax"></span></label>
<input type="range" id="lowLidMax" min="400" max="520" step="2"><div class="mut">400 = kit. Higher opens the bottom lids further</div></div>
<div class="row"><label>Lids follow eyes <span id="v_lidFollow"></span>%</label>
<input type="range" id="lidFollow" min="0" max="100" step="5"><div class="mut">100 = kit, 0 = lids stay put when the eyes look up or down</div></div>
<div class="row"><b>Lid trims for: <span id="trp">● Normal</span></b><div class="mut">Pick a preset with the buttons above, then match the eyes. − more closed, + more open. Left/right are HIS left and right, like up and down: his left eye is the one on your right as you face him</div></div>
<div class="row"><label>His left eye, top lid <span id="v_tLTop"></span></label><input type="range" id="tLTop" min="-60" max="60" step="1"></div>
<div class="row"><label>His left eye, bottom lid <span id="v_tLBot"></span></label><input type="range" id="tLBot" min="-60" max="60" step="1"></div>
<div class="row"><label>His right eye, top lid <span id="v_tRTop"></span></label><input type="range" id="tRTop" min="-60" max="60" step="1"></div>
<div class="row"><label>His right eye, bottom lid <span id="v_tRBot"></span></label><input type="range" id="tRBot" min="-60" max="60" step="1"></div>
<h2>Controller</h2>
<div class="row"><label>Blink button</label>
<select id="blinkBtn"><option value="0">✕ Cross</option><option value="1">□ Square</option><option value="2">Either</option></select></div>
<h2>Shows</h2>
<p class="mut">A show is a spell of alive idle that ends with the eyes asleep. Everyday: you arrive, the eyes
wait, do one show, then sleep while you're in the lab, with another show now and then. A show that starts
from sleep opens wide and looks far to his left first; about once a minute he squints slowly and looks side to
side; now and then he winks, either eye.</p>
<div class="row"><label>Shows</label>
<select id="idleMode"><option value="0">Off (eyes rest open)</option><option value="1">Automatic: on arrival and now and then</option><option value="2">On demand only (Triangle, this page, voice)</option></select></div>
<div class="row"><label>Show starts <span id="v_arriveDelay"></span> s after you arrive</label>
<input type="range" id="arriveDelay" min="0" max="300" step="5"><div class="mut">Power-up counts as an arrival</div></div>
<div class="row"><label>A show lasts <span id="v_showSecs"></span> s</label>
<input type="range" id="showSecs" min="30" max="900" step="10"></div>
<div class="row"><label>Another show every <span id="v_showEvery"></span> min while you're here</label>
<input type="range" id="showEvery" min="0" max="240" step="5"><div class="mut">0 = only on arrival. Needs the radar</div></div>
<div class="row"><label>Extended play lasts <span id="v_extendMins"></span> min</label>
<input type="range" id="extendMins" min="1" max="120" step="1"></div>
<div class="row"><label>Back to sleep <span id="v_handsOffSecs"></span> s after the controller</label>
<input type="range" id="handsOffSecs" min="5" max="600" step="5"></div>
<div class="row"><label>While asleep</label>
<select id="sleepQuiet"><option value="1">Silent (servos let go once the lids close)</option><option value="0">Hold (servos powered)</option></select></div>
<div class="row"><label>What a show is</label>
<select id="arriveAction"><option value="0">Nothing</option><option value="1">Alive idle</option><option value="2">Play the recording, then idle</option></select></div>
<h2>Alive idle</h2>
<div class="row"><label>Time between glances <span id="v_glanceTenths"></span> ×0.1 s</label>
<input type="range" id="glanceTenths" min="5" max="50" step="1"></div>
<div class="row"><label>How far glances go <span id="v_glanceRange"></span>%</label>
<input type="range" id="glanceRange" min="10" max="100" step="5"></div>
<div class="row"><label>Blinks per minute <span id="v_blinkRate"></span></label>
<input type="range" id="blinkRate" min="0" max="30" step="1"></div>
<h2>Bench radar (Home Assistant)</h2>
<div class="row"><label>A return counts as a new arrival after <span id="v_emptyMins"></span> min empty</label>
<input type="range" id="emptyMins" min="1" max="60" step="1"><div class="mut">So a quick step out doesn't start a show</div></div>
<h2>Calibration</h2>
<p class="mut">Set once, after a horn is moved. Everyday adjustments are the sliders above.</p>
<div class="row"><label>Left/right servo center <span id="v_xCenter"></span></label>
<input type="range" id="xCenter" min="-40" max="40" step="1" style="direction:rtl"><div class="mut" style="display:flex;justify-content:space-between"><span>◂ his left</span><span>pulse counts; set with pupil center at 0</span><span>his right ▸</span></div></div>
<div class="row"><b>Look test</b><div class="mut">Holds the eyes at full travel to check for a stop or strain. Stop, a preset or a show ends it.</div>
<div class="sc lk"><button data-c="lookL">◂ His left</button><button data-c="lookU">▴ Up</button><button data-c="lookR">His right ▸</button>
<button data-c="lookC">● Center</button><button data-c="lookD">▾ Down</button><button data-c="stop">■ Stop</button></div></div>
<div class="btns"><button class="pri" id="save">Save</button><button id="revert">Revert</button><button id="defaults">Defaults</button></div>
<p class="mut">Changes move the eyes immediately. <b>Save</b> keeps them after power-off.
<br><a href="/update">Firmware update</a></p>
<script>
const K=['parkY','parkX','xCenter','lidWide','lidNormal','lidSquint','lidClosed','lowLidCurve','lidMin','lowLidMax','lidFollow','blinkBtn','idleMode','arriveDelay','showSecs','showEvery','extendMins','handsOffSecs','sleepQuiet',
 'glanceTenths','glanceRange','blinkRate','arriveAction','emptyMins'];
const M={live:'● Live: controller driving',idle:'∿ Show (alive idle)',play:'▶ Playing the recording',record:'⏺ RECORDING',sleep:'☾ Asleep (lids closed)',rest:'○ Resting'};let dirty=false,busy=false,pend=null;
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
 $('st').innerHTML=(s.conn?'● Controller connected':'○ Controller not connected')+
 ' &nbsp; '+(dirty?'✎ <b>Unsaved changes</b>':'✓ Saved')+' &nbsp; '+(s.present?'◉ Someone at the bench':'◌ Bench empty');
 $('mode').textContent=(M[s.mode]||s.mode)+(s.showLeft>=0?' · '+fm(s.showLeft)+' left':'')+(s.nextShow>=0?' · next show in '+fm(s.nextShow):'')+' · recording '+(s.recMs?(s.recMs/1000).toFixed(1)+' s':'none');
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
      server.send(409, "text/plain", "can't " + c + " now (idle off? no recording? no controller?)\n");
      return;
    }
    sendJson(eyeStatusJson());
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
