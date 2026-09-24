#include "WebUi.h"
#include "EyeSettings.h"
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

static bool authorised() {
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
a{color:var(--acc)}
</style></head><body>
<h1>EyeMech</h1>
<div class="mut" id="bi"></div>
<div id="st">…</div>
<div class="row"><label>Eye rest height <span id="v_parkY"></span></label>
<input type="range" id="parkY" min="0" max="300" step="5"><div class="mut">0 = centre, higher = lower</div></div>
<div class="row"><label>Eye rest left / right <span id="v_parkX"></span></label>
<input type="range" id="parkX" min="-150" max="150" step="5"><div class="mut">0 = centre, + = right</div></div>
<div class="row"><label>Lid opening at power-up <span id="v_bootTrim"></span></label>
<input type="range" id="bootTrim" min="-40" max="40" step="5"><div class="mut">40 = fully open (applies now, too)</div></div>
<div class="row"><label>Blink button</label>
<select id="blinkBtn"><option value="0">✕ Cross</option><option value="1">□ Square</option><option value="2">Either</option></select></div>
<div class="row"><label>Lid trim per D-pad press <span id="v_trimStep"></span></label>
<input type="range" id="trimStep" min="1" max="20" step="1"></div>
<div class="btns"><button class="pri" id="save">Save</button><button id="revert">Revert</button><button id="defaults">Defaults</button></div>
<p class="mut">Changes move the eyes immediately. <b>Save</b> keeps them after power-off.
<br><a href="/update">Firmware update</a></p>
<script>
const K=['parkY','parkX','bootTrim','blinkBtn','trimStep'];let dirty=false,busy=false,pend=null;
const $=id=>document.getElementById(id);
function show(v){K.forEach(k=>{$(k).value=v[k];const o=$('v_'+k);if(o)o.textContent=v[k]});dirty=v.dirty}
async function j(u,o){const r=await fetch(u,o);if(!r.ok)throw new Error(r.status);return r.json()}
async function send(){if(busy||!pend)return;busy=true;const q=pend;pend=null;
 try{const v=await j('/set?'+q,{method:'POST'});dirty=v.dirty}catch(e){}busy=false;send()}
K.forEach(k=>$(k).addEventListener('input',e=>{const o=$('v_'+k);if(o)o.textContent=e.target.value;
 pend=k+'='+e.target.value;send()}));
$('save').onclick=async()=>{show(await j('/save',{method:'POST'}));poll()};
$('revert').onclick=async()=>{show(await j('/revert',{method:'POST'}));poll()};
$('defaults').onclick=async()=>{show(await j('/defaults',{method:'POST'}));poll()};
async function poll(){try{const s=await j('/status');
 $('st').innerHTML=(s.conn?'● Controller connected':'○ Controller not connected')+
 ' &nbsp; '+(dirty?'✎ <b>Unsaved changes</b>':'✓ Saved');
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
    if (!authorised()) return;
    server.send_P(200, "text/html", PAGE);
  });
  server.on("/values", HTTP_GET, [] {
    if (!authorised()) return;
    sendJson(settingsJson());
  });
  server.on("/status", HTTP_GET, [] {
    if (!authorised()) return;
    sendJson(eyeStatusJson());
  });
  server.on("/set", HTTP_POST, [] {
    if (!authorised()) return;
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
    if (!authorised()) return;
    if (!saveSettings()) {
      server.send(500, "text/plain", "NVS write failed\n");
      return;
    }
    sendJson(settingsJson());
  });
  server.on("/revert", HTTP_POST, [] {
    if (!authorised()) return;
    loadSettings();
    applyLiveSetting("");  // "" = everything may have changed
    sendJson(settingsJson());
  });
  server.on("/defaults", HTTP_POST, [] {
    if (!authorised()) return;
    settings = EyeSettings();
    applyLiveSetting("");
    sendJson(settingsJson());  // not saved until Save
  });

  server.on("/update", HTTP_GET, [] {
    if (!authorised()) return;
    String page = FPSTR(UPDATE_PAGE);
    page.replace("%BUILD%", BUILD_ID);
    server.send(200, "text/html", page);
  });
  server.on(
      "/update", HTTP_POST,
      [] {
        if (!authorised()) return;
        bool ok = !Update.hasError() && Update.isFinished();  // isFinished: a file actually arrived
        server.send(ok ? 200 : 500, "text/plain",
                    ok ? "Update OK, restarting.\n" : "Update FAILED, old firmware kept.\n");
        delay(300);
        if (ok) ESP.restart();
      },
      [] {
        // The upload handler can't send a challenge mid-stream, so an unauthorised
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
