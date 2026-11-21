/* AI denetim masası (Yönetim › Bilişsel inceleme): the owner, a behavioural-science expert, judges one AI finding at a
   time. Each judgement is a structured review (each necessary condition, a verdict, why it is wrong, the concept it
   should have been, an explanation, seconds spent) saved to the shared `reviews` collection; the verdict keeps the
   public pages' meaning (verified / corrected / rejected), the rest is training data for the learning loop
   (validation/feedback). Pure rules live in logic.js: deskDoc, deskQueue, deskStats. */
var DESK = { g: "davranis", state: "todo", card: "", outlet: "", key: "", form: null, t0: 0, msg: "", undo: null };
var DESK_GROUPS = [["davranis", "Davranışsal"], ["medya", "Medya teknikleri"], ["bekleyen", "Bekleyen medya kartları"], ["anlati", "Anlatı kodlamaları"], ["kor", "Kör kodlama"]];
var DESK_NARR_REASONS = [["unsupported", "Başlık bu kodu desteklemiyor"], ["wrong_outlet", "Kurumlar karışmış"],
  ["missing_dim", "Önemli bir boyut eksik"], ["other", "Başka bir neden (açıklamada)"]];
var DESK_MIN = 20;   /* reviews per concept before its keep-rate counts (validation/reference/gates.json min_reviews_to_judge is 15; 20 is the report's stage-1 target) */

function deskName(id, fallback) {
  var m = MEDIA_CONCEPTS.filter(function (c) { return c[0] === id; })[0], b = biasBrief(id, BREG, bg7k);
  return m ? m[1] : b ? b.name : fallback || id;
}
function deskOutlets(f) {
  var seen = []; (f.evidence || []).forEach(function (e) { (e.o || []).forEach(function (o) { if (seen.indexOf(o) < 0) seen.push(o); }); });
  return seen;
}
/* Every reviewable item, by group. A review counts only on the pack and event text it was made on (reviewValid). */
function deskItems(g) {
  if (g === "anlati") return Object.keys(D.N).filter(function (k) { return D.N[k].status === "agent_coded"; }).map(function (k) {
    var n = D.N[k]; return { key: "narr__" + k, card: "anlati", name: "Anlatı kodlaması", nk: k, event: n.ev, size: (n.rows || []).length, outlets: (n.rows || []).map(function (r) { return r.s; }) };
  });
  var B = g === "davranis" ? D.BG : D.BGM, evs = !B ? [] : g === "bekleyen" ? (B.pending || {}).events || [] : B.events || [];
  var out = [];
  evs.forEach(function (x) {
    if (g !== "bekleyen" && x.status !== "review_complete") return;
    var full = g === "bekleyen" ? (B.events || []).filter(function (y) { return y.event === x.event; })[0] || x : x;
    (x.supported || []).concat(x.uncertain || []).forEach(function (f) {
      out.push({ key: x.event + "__" + f.id, card: f.id, name: deskName(f.id, f.name), event: x.event, f: f, x: full, size: (EV[x.event] || {}).s ? EV[x.event].s.length : full.outlets || 0, outlets: deskOutlets(f) });
    });
  });
  return out;
}
function deskReviews(items) {
  var r = {}; items.forEach(function (i) { var v = rev7(i.key); if (v && (i.card === "anlati" || reviewValid(v, D.meta.built, i.x && i.x.text))) r[i.key] = v; });
  return r;
}
function deskCardOptions() {
  var inv = {}; Object.keys(BG7ALIAS).forEach(function (k) { inv[BG7ALIAS[k]] = k; });
  var ids = (D.BR || []).map(function (b) { return inv[b.k] || b.k; }).concat(MEDIA_CONCEPTS.map(function (c) { return c[0]; }));
  return ids.filter(function (id, i) { return ids.indexOf(id) === i; }).map(function (id) { return [id, deskName(id)]; })
    .sort(function (a, b) { return trCmp(a[1], b[1]); });
}

/* The event's headlines, one per outlet (earliest), quoted words marked; cited outlets first. */
function deskHeadlines(it) {
  var e = EV[it.event]; if (!e) return "";
  var first = {}; e.a.forEach(function (i) { var a = ART[i]; if (a && (!first[a.s] || a.d < first[a.s].d)) first[a.s] = a; });
  var qs = it.f ? (it.f.evidence || []).map(function (x) { return String(x.q || "").replace(/^\[[^\]]+\]\s*/, "").trim(); }).filter(Boolean) : [];
  var cited = it.outlets || [];
  var rows = Object.keys(first).sort(function (a, b) { return (cited.indexOf(a) < 0) - (cited.indexOf(b) < 0) || trCmp(srcName(a), srcName(b)); });
  var mark = function (t) {
    var q = qs.filter(function (x) { return t.indexOf(x) >= 0; })[0]; if (!q) return esc(t);
    var i = t.indexOf(q); return esc(t.slice(0, i)) + "<mark>" + esc(q) + "</mark>" + esc(t.slice(i + q.length));
  };
  return '<ol class="desk-hl">' + rows.map(function (s, n) {
    return "<li" + (n >= 12 ? " hidden" : "") + '><span class="desk-src ' + bloc(s) + '">' + esc(srcName(s)) + "</span> " + mark(first[s].t || "") + "</li>";
  }).join("") + "</ol>" + (rows.length > 12 ? '<button class="chip" data-desk="allhl">Bütün ' + rows.length + " başlık</button>" : "");
}
function deskSeg(name, opts, val) {
  return '<div class="desk-seg" role="radiogroup">' + opts.map(function (o, i) {
    return '<button type="button" role="radio" aria-checked="' + (val === o[0]) + '" data-desk="' + name + '" data-v="' + o[0] + '">' +
      (o[2] ? '<kbd>' + o[2] + "</kbd> " : "") + esc(o[1]) + "</button>";
  }).join("") + "</div>";
}
function deskStatusWord(r) {
  return !r ? "İncelenmedi" : { verified: "Doğru", corrected: "Kısmen doğru", rejected: "Yanlış" }[r.status] || "İncelendi";
}

function deskWork(it, rev) {
  if (!it) return '<div class="desk-empty"><h2>Bu kuyrukta inceleme kalmadı.</h2><p>Filtreyi “Tümü” yapın ya da başka bir grubu seçin.</p></div>';
  var F = DESK.form, narr = it.card === "anlati", f = it.f || {}, e = EV[it.event], h = "";
  h += '<header class="desk-wh"><div><span class="eyebrow">' + esc(DESK_GROUPS.filter(function (g) { return g[0] === DESK.g; })[0][1]) + "</span>" +
    "<h2>" + esc(it.name) + (f.name && f.name !== it.name ? ' <span class="desk-en">' + esc(f.name) + "</span>" : "") + "</h2>" +
    '<p class="desk-ev">' + esc(e ? storyLabel(e, 120) : it.event || "") + (it.size ? " · " + it.size + " kurum" : "") +
    (e ? ' · <a class="lnk" href="#/olay?e=' + esc(it.event) + '" target="_blank" rel="noopener">olay sayfası</a>' : "") + "</p></div>" +
    '<span class="desk-state s-' + (rev ? rev.status : "todo") + '">' + deskStatusWord(rev) + "</span></header>";
  if (narr) {
    var n = D.N[it.nk] || {}, q = n.q || {};
    h += '<section class="desk-box"><h3>AI’nin özeti</h3>' + ["happened", "agree", "differ", "care"].filter(function (k) { return q[k]; })
      .map(function (k) { return "<p>" + esc(q[k]) + "</p>"; }).join("") + "</section>";
    h += '<section class="desk-box"><h3>Kurum kurum kodlama</h3><div class="scroller"><table class="desk-tab"><thead><tr><th>Kurum</th><th>Başlık</th><th>Çerçeve</th><th>Sorumlu tutulan</th><th>Merkezdeki aktör</th></tr></thead><tbody>' +
      (n.rows || []).map(function (r) { return "<tr><td>" + esc(srcName(r.s)) + "</td><td>" + esc(r.hl || "") + "</td><td>" + esc(r.frame || "") + "</td><td>" + esc(r.blame || "") + "</td><td>" + esc(r.hero || "") + "</td></tr>"; }).join("") +
      "</tbody></table></div></section>";
  } else {
    var b = biasBrief(it.card, BREG, bg7k), ex = f.explain || {};
    h += '<section class="desk-box"><h3>Başlıklar <span class="desk-sub">alıntılanan sözcükler işaretli</span></h3>' + deskHeadlines(it) + "</section>";
    h += '<section class="desk-box"><h3>AI’nin iddiası</h3>' + (ex.noticed ? "<p>" + esc(ex.noticed) + "</p>" : "") +
      (f.mechanisms || []).map(function (m) { return '<p class="desk-role"><b>' + (m.role === "advocate" ? "Savunan" : "Sorgulayan") + ":</b> " + esc(m.text) + "</p>"; }).join("") +
      ((f.alternatives || []).length ? '<p class="desk-role"><b>Yanlılık dışı açıklama:</b> ' + esc(f.alternatives[0].text) + "</p>" : "") +
      '<details><summary>Kavramın tanımı</summary><p>' + esc(b ? b.text : f.definition || "") + "</p></details></section>";
  }
  var ro = !REV7OWNER ? " disabled" : "";
  h += '<form class="desk-form" data-desk-form' + ro + ">";
  var conds = !narr && D.BGC && D.BGC[it.card] ? D.BGC[it.card].c : [];
  if (conds.length) h += '<fieldset class="desk-conds"><legend>Zorunlu koşullar <span class="desk-sub">kartın kendi metni</span></legend>' + conds.map(function (c, i) {
    return '<div class="desk-cond"><p><span class="mono">' + (i + 1) + "</span> " + esc(c) + "</p>" +
      deskSeg("cond" + i, [["met", "Var"], ["unmet", "Yok"], ["unclear", "Belirsiz"]], F.conditions[i] || "") + "</div>";
  }).join("") + "</fieldset>";
  h += '<fieldset><legend>Karar</legend>' + deskSeg("verdict", [["correct", "Doğru", "1"], ["partly", "Kısmen doğru", "2"], ["wrong", "Yanlış", "3"]], F.verdict) + "</fieldset>";
  if (F.verdict === "partly" || F.verdict === "wrong") {
    var reasons = narr ? DESK_NARR_REASONS : DESK_REASONS;
    h += '<fieldset><legend>Neden</legend><div class="desk-chips">' + reasons.map(function (r) {
      return '<button type="button" class="chip" aria-pressed="' + (F.reason === r[0]) + '" data-desk="reason" data-v="' + r[0] + '">' + esc(r[1]) + "</button>";
    }).join("") + "</div></fieldset>";
  }
  if (F.reason === "wrong_concept") h += '<label class="desk-field">Doğru kavram<select data-desk="card"><option value="">Seçin</option>' +
    deskCardOptions().map(function (o) { return '<option value="' + esc(o[0]) + '"' + (F.card === o[0] ? " selected" : "") + ">" + esc(o[1]) + "</option>"; }).join("") + "</select></label>";
  h += '<label class="desk-field">Açıklama <span class="desk-sub">' + (F.verdict === "partly" ? "gerekli: ne düzeltilmeli" : "isteğe bağlı; yapay zekâ bundan öğrenir") + "</span>" +
    '<textarea data-desk="note" rows="3" placeholder="Bu bulgu neden doğru ya da yanlış?">' + esc(F.note) + "</textarea></label>";
  h += (DESK.msg ? '<p class="desk-msg" role="alert">' + esc(DESK.msg) + "</p>" : "") +
    '<div class="desk-act"><button type="submit" class="desk-save">Kaydet ve sonraki <kbd>↵</kbd></button>' +
    '<button type="button" class="chip" data-desk="prev"><kbd>K</kbd> Önceki</button><button type="button" class="chip" data-desk="next">Atla <kbd>J</kbd></button></div>';
  h += (REV7OWNER ? "" : '<p class="desk-sub">Salt okunur: kararları yalnızca site sahibi kaydedebilir.</p>') + "</form>";
  return h;
}

function deskLearning(st) {
  var top = st.cards.slice(0, 12);
  return '<details class="desk-learn"' + (DESK.learnOpen ? " open" : "") + ' data-desk-learn><summary>Öğrenme: ' + st.measurable + " / " + st.cards.length +
    " kavram ölçülebilir <span class=\"desk-sub\">(kavram başına " + DESK_MIN + " inceleme)</span></summary>" +
    '<div class="scroller"><table class="desk-tab"><thead><tr><th>Kavram</th><th>İlerleme</th><th class="r">Doğru sayılan</th><th class="r">Alt sınır</th></tr></thead><tbody>' +
    top.map(function (c) {
      var pct = Math.min(100, Math.round(100 * c.reviewed / DESK_MIN));
      return "<tr><td>" + esc(c.name) + '</td><td><span class="desk-bar"><i style="width:' + pct + '%"></i></span> <span class="mono">' + c.reviewed + "/" + DESK_MIN + "</span></td>" +
        '<td class="r num">' + (c.rate == null ? "—" : "%" + Math.round(100 * c.rate)) + '</td><td class="r num">' + (c.lower == null || c.need ? "—" : "%" + Math.round(100 * c.lower)) + "</td></tr>";
    }).join("") + "</tbody></table></div><p class=\"desk-sub\">Alt sınır: uzmanın doğru saydığı payın %95 güvenle en az olduğu değer. Bir kavram " + DESK_MIN +
    " incelemeye ulaşınca dış görünüme katılmaya aday olur; yapay zekâ değişikliği ancak öğrenme kapısını geçerse yayına girer.</p></details>";
}

function deskTabs() {
  return '<nav class="desk-tabs" aria-label="Kuyruklar">' + DESK_GROUPS.map(function (g) {
    /* In blind mode no count derived from the AI queues is shown. */
    var blind = DESK.g === "kor", n = g[0] === "kor" ? blindPackets().length : blind ? 1 : deskItems(g[0]).length; if (!n) return "";
    return '<button class="subtab' + (g[0] === DESK.g ? " on" : "") + '" data-desk="group" data-v="' + g[0] + '">' + esc(g[1]) + (blind ? "" : ' <span class="mono">' + n + "</span>") + "</button>";
  }).join("") + "</nav>";
}
function pgDesk(q) {
  q = q || {};
  if (q.v === "ozet") return pgBG7();
  if (q.g && DESK_GROUPS.some(function (g) { return g[0] === q.g; })) DESK.g = q.g;
  if (DESK.g === "kor") return pgBlind();
  var items = deskItems(DESK.g), rev = deskReviews(items), st = deskStats(items, rev, DESK_MIN);
  var queue = deskQueue(items, rev, { state: DESK.state, card: DESK.card, outlet: DESK.outlet });
  if (q.k && !DESK.key) DESK.key = q.k;
  var cur = queue.filter(function (i) { return i.key === DESK.key; })[0] || items.filter(function (i) { return i.key === DESK.key && DESK.state !== "todo"; })[0] || queue[0];
  if (!cur || cur.key !== DESK.form_key) deskOpen(cur, cur && rev[cur.key]);
  var pct = st.total ? Math.round(100 * st.done / st.total) : 0;
  var cards = items.reduce(function (o, i) { o[i.card] = i.name; return o; }, {}), outlets = {};
  items.forEach(function (i) { (i.outlets || []).forEach(function (s) { outlets[s] = 1; }); });
  var h = '<div class="wrap page desk"><div class="desk-top"><div><div class="eyebrow">Yönetim · ' + bg7AiTag() + '</div><h1>AI denetim masası</h1></div>' +
    '<div class="desk-prog" aria-label="İlerleme"><span class="mono">' + st.done + " / " + st.total + "</span> incelendi" +
    '<span class="desk-bar wide"><i style="width:' + pct + '%"></i></span></div>' +
    '<a class="lnk desk-ozet" href="#/yonetim?t=bilissel&v=ozet">Özet ve yöntem</a></div>';
  h += deskTabs() + deskLearning(st);
  h += (REV7MSG ? '<div class="note warn">' + esc(REV7MSG) + "</div>" : "") + '<div class="desk-grid"><aside class="desk-q" aria-label="Kuyruk">' +
    deskSeg("state", [["todo", "İncelenmedi"], ["done", "İncelendi"], ["all", "Tümü"]], DESK.state) +
    (DESK.g === "anlati" ? "" : '<select data-desk="fcard" aria-label="Kavram"><option value="">Bütün kavramlar</option>' + Object.keys(cards).sort(function (a, b) { return trCmp(cards[a], cards[b]); })
      .map(function (k) { return '<option value="' + esc(k) + '"' + (DESK.card === k ? " selected" : "") + ">" + esc(cards[k]) + "</option>"; }).join("") + "</select>") +
    '<select data-desk="foutlet" aria-label="Kurum"><option value="">Bütün kurumlar</option>' + Object.keys(outlets).sort(function (a, b) { return trCmp(srcName(a), srcName(b)); })
      .map(function (s) { return '<option value="' + esc(s) + '"' + (DESK.outlet === s ? " selected" : "") + ">" + esc(srcName(s)) + "</option>"; }).join("") + "</select>" +
    '<p class="desk-sub">' + queue.length + " öğe · aynı kavram art arda</p><ol class=\"desk-list\">" + queue.slice(0, 80).map(function (i) {
      var e = EV[i.event];
      return '<li><button data-desk="pick" data-v="' + esc(i.key) + '"' + (cur && i.key === cur.key ? ' aria-current="true"' : "") + '><span class="desk-dot s-' + (rev[i.key] ? rev[i.key].status : "todo") + '"></span>' +
        "<b>" + esc(i.name) + "</b><span>" + esc(e ? storyLabel(e, 60) : i.event || "") + "</span></button></li>";
    }).join("") + "</ol>" + (queue.length > 80 ? '<p class="desk-sub">İlk 80 gösteriliyor; filtreyle daraltın.</p>' : "") + "</aside>" +
    '<main class="desk-w" id="desk-w">' + deskWork(cur, cur && rev[cur.key]) + "</main></div>" +
    (DESK.undo ? '<div class="desk-toast" role="status">' + esc(DESK.undo.text) + ' <button class="chip" data-desk="undo">Geri al</button></div>' : "") + "</div>";
  DESK.view = { queue: queue, cur: cur };
  return h;
}
function deskOpen(it, rev) {
  DESK.key = it ? it.key : ""; DESK.form_key = DESK.key; DESK.t0 = Date.now(); DESK.msg = "";
  DESK.form = { verdict: rev ? rev.verdict || ({ verified: "correct", corrected: "partly", rejected: "wrong" })[rev.status] || "" : "",
    conditions: rev && rev.conditions ? rev.conditions.slice() : [], reason: rev && rev.reason || "", card: rev && rev.card || "", note: rev && rev.note || "" };
}
function deskRerender() { var p = document.querySelector(".desk"); if (p && location.hash.indexOf("t=bilissel") >= 0) { p.outerHTML = pgDesk({}); } }
function deskStep(d) {
  var qq = DESK.view.queue, i = qq.indexOf(DESK.view.cur), nx = qq[Math.max(0, Math.min(qq.length - 1, i + d))];
  if (nx) { deskOpen(nx, rev7(nx.key)); deskRerender(); }
}
function deskSave() {
  var it = DESK.view && DESK.view.cur; if (!it || !REV7OWNER) return;
  var doc = deskDoc(DESK.form);
  if (doc.error) { DESK.msg = doc.error; return deskRerender(); }
  var before = rev7(it.key), rest = { verdict: doc.verdict, conditions: doc.conditions, reason: doc.reason, card: doc.card, ms: Date.now() - DESK.t0 };
  rev7Save(it.key, doc.status, doc.note, false, rest);
  REV7[it.key] = Object.assign({ status: doc.status, note: doc.note }, rest);   /* shown at once; the shared record confirms it */
  var c = deskStats(deskItems(DESK.g), deskReviews(deskItems(DESK.g)), DESK_MIN).cards.filter(function (x) { return x.card === it.card; })[0];
  DESK.undo = { key: it.key, before: before, text: "Kaydedildi: " + it.name + (c ? " · " + c.reviewed + "/" + DESK_MIN + " inceleme" : "") };
  var qq = DESK.view.queue, i = qq.indexOf(it), nx = DESK.state === "todo" ? qq[i + 1] || qq[i - 1] : qq[i + 1];
  if (nx && nx !== it) deskOpen(nx, rev7(nx.key)); else deskOpen(it, REV7[it.key]);
  deskRerender();
}
document.addEventListener("click", function (ev) {
  var b = ev.target.closest && ev.target.closest("[data-desk]"); if (!b || !document.querySelector(".desk")) return;
  var a = b.getAttribute("data-desk"), v = b.getAttribute("data-v"), F = DESK.form;
  if (b.tagName === "SELECT" || b.tagName === "TEXTAREA") return;
  ev.preventDefault();
  if (a.indexOf("blind-") === 0) return blindClick(a, v, b);
  if (a === "group") { DESK.g = v; DESK.bp = ""; DESK.card = DESK.outlet = DESK.key = ""; DESK.form_key = null; }
  else if (a === "state") { DESK.state = v; DESK.key = ""; DESK.form_key = null; }
  else if (a === "pick") { var it = deskItems(DESK.g).filter(function (i) { return i.key === v; })[0]; deskOpen(it, rev7(v)); }
  else if (a === "verdict") { F.verdict = v; if (v === "correct") { F.reason = ""; F.card = ""; } DESK.msg = ""; }
  else if (a === "reason") { F.reason = F.reason === v ? "" : v; DESK.msg = ""; }
  else if (a.indexOf("cond") === 0) { var k = +a.slice(4); F.conditions[k] = F.conditions[k] === v ? "" : v; }
  else if (a === "next") return deskStep(1);
  else if (a === "prev") return deskStep(-1);
  else if (a === "allhl") { b.parentNode.querySelectorAll(".desk-hl li[hidden]").forEach(function (li) { li.hidden = false; }); b.remove(); return; }
  else if (a === "undo" && DESK.undo) {
    var u = DESK.undo, p = u.before; rev7Save(u.key, p ? p.status : null, p ? p.note : "", false, p || {});
    if (p) REV7[u.key] = p; else delete REV7[u.key];
    DESK.undo = null; DESK.state = "all"; DESK.key = u.key; DESK.form_key = null;
  }
  for (var i = 0; F && i < F.conditions.length; i++) if (F.conditions[i] === undefined) F.conditions[i] = "";
  deskRerender();
});
document.addEventListener("change", function (ev) {
  var s = ev.target; if (!s.closest || !s.closest(".desk")) return;
  var a = s.getAttribute("data-desk");
  if (a === "blind-sel") { DESK.ba[s.getAttribute("data-f")] = s.value; DESK.msg = ""; return deskRerender(); }
  if (a === "fcard") DESK.card = s.value; else if (a === "foutlet") DESK.outlet = s.value; else if (a === "card") DESK.form.card = s.value; else return;
  if (a !== "card") { DESK.key = ""; DESK.form_key = null; }
  deskRerender();
});
document.addEventListener("input", function (ev) { if (ev.target.getAttribute && ev.target.getAttribute("data-desk") === "note") DESK.form.note = ev.target.value; });
document.addEventListener("toggle", function (ev) { if (ev.target.hasAttribute && ev.target.hasAttribute("data-desk-learn")) DESK.learnOpen = ev.target.open; }, true);
document.addEventListener("submit", function (ev) { if (ev.target.hasAttribute("data-desk-form")) { ev.preventDefault(); deskSave(); } });
document.addEventListener("keydown", function (ev) {
  if (!document.querySelector(".desk") || ev.altKey || ev.metaKey && ev.key !== "Enter") return;
  if (DESK.g === "kor") return blindKeydown(ev);
  var typing = /^(TEXTAREA|INPUT|SELECT)$/.test((ev.target || {}).tagName || "");
  if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey || !typing)) { ev.preventDefault(); return deskSave(); }
  if (typing || ev.ctrlKey) return;
  var k = ev.key.toLowerCase(), v = { "1": "correct", "2": "partly", "3": "wrong" }[k];
  if (v) { DESK.form.verdict = v; if (v === "correct") { DESK.form.reason = ""; DESK.form.card = ""; } DESK.msg = ""; deskRerender(); }
  else if (k === "j") deskStep(1);
  else if (k === "k") deskStep(-1);
});

/* Kör kodlama: packets of items the owner codes without any AI result (logic.js: blind*). */
var BLIND_KIND = { behaviour: "Davranışsal kavram", narrative: "Anlatı" };
function blindPackets() { return (D.BLIND && D.BLIND.packets) || []; }
function blindToday() { return new Date().toISOString().slice(0, 10); }
function blindDateTr(d) { return +d.slice(8, 10) + " " + V3MONTH[+d.slice(5, 7) - 1] + " " + d.slice(0, 4); }
function blindPacket() { return blindPackets().filter(function (p) { return p.id === DESK.bp && blindOpen(p, blindToday()); })[0]; }
function blindStart(pk, key) {
  var items = pk.items, cur = items.filter(function (i) { return i.item === key; })[0] ||
    items.filter(function (i) { var r = rev7(blindKey(pk.id, i.item)); return !(r && blindDone(pk.kind, r.answers)); })[0] || items[0];
  var r = cur && rev7(blindKey(pk.id, cur.item));
  DESK.bi = cur ? cur.item : ""; DESK.ba = Object.assign({}, r && r.answers || {}); DESK.msg = "";
}
function blindList() {
  return '<div class="wrap page desk"><div class="desk-top"><div><div class="eyebrow">Yönetim · Kör kodlama</div><h1>Kör kodlama</h1></div></div>' + deskTabs() +
    '<p class="desk-sub">Hiçbir otomatik karar gösterilmez; yanıtlarınız insan anahtarına aktarılır.</p><ul class="blind-packets">' + blindPackets().map(function (p) {
      var pr = blindProgress(p, REV7), ok = blindOpen(p, blindToday());
      return "<li><button" + (ok ? "" : " disabled") + ' data-desk="blind-packet" data-v="' + esc(p.id) + '"><b>' + esc(p.id) + "</b> <span>" + BLIND_KIND[p.kind] + '</span> <span class="mono">' + pr.done + "/" + pr.total + "</span>" +
        (ok ? "" : '<span class="desk-sub">Bu tur ' + blindDateTr(p.not_before) + " tarihinde açılır; ilk turdaki yanıtlarınızın etkisi geçsin diye.</span>") + "</button></li>";
    }).join("") + "</ul></div>";
}
function pgBlind() {
  var pk = blindPacket(); if (!pk) return blindList();
  if (!DESK.bi || !pk.items.some(function (i) { return i.item === DESK.bi; })) blindStart(pk);
  var pr = blindProgress(pk, REV7), cur = pk.items.filter(function (i) { return i.item === DESK.bi; })[0];
  var h = '<div class="wrap page desk"><div class="desk-top"><div><div class="eyebrow">Yönetim · Kör kodlama · ' + esc(pk.id) + '</div><h1>Kör kodlama</h1></div>' +
    '<div class="desk-prog"><span class="mono">' + pr.done + " / " + pr.total + '</span> kodlandı<span class="desk-bar wide"><i style="width:' + Math.round(100 * pr.done / (pr.total || 1)) + '%"></i></span></div>' +
    '<button class="chip" data-desk="blind-back">Paketler</button></div>' + deskTabs();
  h += '<div class="desk-grid"><aside class="desk-q" aria-label="Öğeler"><ol class="desk-list">' + pk.items.slice(0, 400).map(function (i) {
    var r = rev7(blindKey(pk.id, i.item)), ev = (pk.events || {})[i.event] || {}, t = pk.kind === "narrative" ? i.kurum + " · " + i.baslik : (i.ad || i.card);
    return '<li><button data-desk="blind-pick" data-v="' + esc(i.item) + '"' + (i.item === DESK.bi ? ' aria-current="true"' : "") + '><span class="desk-dot s-' + (r && blindDone(pk.kind, r.answers) ? "verified" : "todo") + '"></span><b>' + esc(t) + "</b><span>" + esc(ev.baslik || ev.olay || "") + "</span></button></li>";
  }).join("") + '</ol></aside><main class="desk-w" id="desk-w">';
  h += cur ? blindItemHtml(D.BLIND, pk, cur, DESK.ba) : '<div class="desk-empty"><h2>Bu pakette öğe yok.</h2></div>';
  h += (DESK.msg ? '<p class="desk-msg" role="alert">' + esc(DESK.msg) + "</p>" : "") +
    '<div class="desk-act"><button type="button" class="desk-save" data-desk="blind-save"' + (REV7OWNER ? "" : " disabled") + '>Kaydet ve sonraki <kbd>↵</kbd></button>' +
    '<button type="button" class="chip" data-desk="blind-prev"><kbd>K</kbd> Önceki</button><button type="button" class="chip" data-desk="blind-next">Atla <kbd>J</kbd></button></div></main></div></div>';
  return h;
}
function blindStep(d) {
  var pk = blindPacket(); if (!pk) return;
  var i = pk.items.findIndex(function (x) { return x.item === DESK.bi; }), nx = pk.items[Math.max(0, Math.min(pk.items.length - 1, i + d))];
  if (nx) blindStart(pk, nx.item);
}
function blindSave() {
  var pk = blindPacket(); if (!pk || !REV7OWNER) return;
  if (!blindDone(pk.kind, DESK.ba)) { DESK.msg = "Önce bütün alanları yanıtlayın."; return deskRerender(); }
  var key = blindKey(pk.id, DESK.bi), answers = Object.assign({}, DESK.ba);
  rev7Save(key, "coded", "", false, { answers: answers });
  REV7[key] = { status: "coded", note: "", answers: answers };
  var i = pk.items.findIndex(function (x) { return x.item === DESK.bi; }), nx = pk.items.slice(i + 1).concat(pk.items.slice(0, i + 1)).filter(function (x) {
    var r = rev7(blindKey(pk.id, x.item)); return !(r && blindDone(pk.kind, r.answers));
  })[0];
  if (nx) blindStart(pk, nx.item); else DESK.bp = "";
  deskRerender();
}
function blindClick(a, v, b) {
  if (a === "blind-packet") { DESK.bp = v; DESK.bi = ""; }
  else if (a === "blind-back") DESK.bp = "";
  else if (a === "blind-pick") blindStart(blindPacket(), v);
  else if (a === "blind-field") DESK.ba[b.getAttribute("data-f")] = v;
  else if (a === "blind-save") return blindSave();
  else if (a === "blind-next") blindStep(1);
  else if (a === "blind-prev") blindStep(-1);
  deskRerender();
}
function blindKeydown(ev) {
  var pk = blindPacket(); if (!pk) return;
  var typing = /^(TEXTAREA|INPUT|SELECT)$/.test((ev.target || {}).tagName || "");
  if (ev.key === "Enter" && (!typing || ev.target.tagName === "SELECT")) { ev.preventDefault(); return blindSave(); }
  if (typing || ev.ctrlKey) return;
  var k = ev.key.toLowerCase(), f = BLIND_FIELDS[pk.kind][0], o = f[2] && f[2][+k - 1];
  if (o) { DESK.ba[f[0]] = o[0]; DESK.msg = ""; deskRerender(); }
  else if (k === "j") { blindStep(1); deskRerender(); }
  else if (k === "k") { blindStep(-1); deskRerender(); }
}
