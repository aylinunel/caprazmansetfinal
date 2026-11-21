/* Single-source lens (data/reference/lens-82.json, D.LENS): what you would have missed and how an outlet tells the SAME stories
   compared with the others. Outlet page: lensSection(slug); Kurumlar list: lensRanking(). Pure strings (inline SVG), no chart library.
   Numbers and sentences come from logic.js (LENS_MEASURES, lensSentence, lensDistanceText). AI findings sit in their own box and never enter a measure. */
var LENS_PARTIAL = "Bu kurumun derlemesi eksik olabildiği için atlanan olaylar ve ilk veriş ölçülmedi; bütün resimden uzaklık için en az üç ölçü gerekiyor.";
var LENS_MIN = 20;   /* stories a measure needs before it is shown (pipeline PARAMS) */
var LENS_SLICE = {};   /* outlet slug -> slice key chosen on the page */

function lensX(v, w) { return Math.round(w * (Math.log(Math.min(4, Math.max(0.25, v))) / Math.LN2 + 2) / 4 * 10) / 10; }
/* one measure: dot and interval on a log axis centred on 1 (open ends run to the axis edge; RR 0 sits on the left edge, hollow) */
function lensRowSvg(m, label) {
  var W = 600, y = 16, tk = [0.25, 0.5, 1, 2, 4], s = '<svg class="lens-svg" viewBox="0 0 ' + W + ' 40" role="img" aria-label="' + esc(label) + '" focusable="false">' +
    '<line x1="0" x2="' + W + '" y1="' + y + '" y2="' + y + '" class="lens-axis"/>';
  tk.forEach(function (t) {
    var x = lensX(t, W - 2) + 1;
    s += '<line x1="' + x + '" x2="' + x + '" y1="' + (y - (t === 1 ? 12 : 5)) + '" y2="' + (y + (t === 1 ? 12 : 5)) + '" class="' + (t === 1 ? "lens-one" : "lens-tick") + '"/>' +
      '<text x="' + Math.min(W - 14, Math.max(14, x)) + '" y="38" text-anchor="middle" class="lens-tl">' + (t < 1 ? "1/" + Math.round(1 / t) : t) + "×</text>";
  });
  if (m.rr != null) {
    var lo = m.lo == null ? 0 : lensX(m.lo, W - 2) + 1, hi = m.hi == null ? W : lensX(m.hi, W - 2) + 1, x = m.rr === 0 ? 5 : lensX(m.rr, W - 2) + 1;
    if (m.rr === 0) lo = 0;
    s += '<line x1="' + lo + '" x2="' + hi + '" y1="' + y + '" y2="' + y + '" class="lens-ci"/>' +
      '<circle cx="' + x + '" cy="' + y + '" r="7" class="lens-dot' + (m.strong ? " strong" : "") + (m.rr === 0 ? " zero" : "") + '"/>';
  }
  return s + "</svg>";
}
/* all lens outlets on one line by distance; this outlet is the large dot */
function lensStripSvg(k, sl) {
  var rows = [], max = 1.5, W = 600;
  Object.keys(D.LENS.outlets).forEach(function (s) {
    var o = D.LENS.outlets[s], d = o.lens && o.slices[sl] ? o.slices[sl].distance : null;
    if (d != null) { rows.push([s, d]); if (d > max) max = d; }
  });
  var x = function (d) { return Math.round(8 + (W - 16) * (d - 1) / (max * 1.04 - 1)); };
  var s = '<svg class="lens-svg lens-strip-svg" viewBox="0 0 ' + W + ' 64" role="img" aria-label="Kurumların bütün resimden uzaklığı; bu kurum işaretli" focusable="false">' +
    '<line x1="8" x2="' + (W - 8) + '" y1="34" y2="34" class="lens-axis"/>';
  rows.filter(function (r) { return r[0] !== k; }).forEach(function (r) { s += '<circle cx="' + x(r[1]) + '" cy="34" r="5" class="lens-dot other"><title>' + esc(srcName(r[0])) + " · " + lensDec(r[1]) + " kat</title></circle>"; });
  var me = rows.filter(function (r) { return r[0] === k; })[0];
  if (me) s += '<circle cx="' + x(me[1]) + '" cy="34" r="9" class="lens-dot me"/><text x="' + Math.min(W - 60, Math.max(60, x(me[1]))) + '" y="14" text-anchor="middle" class="lens-me">' + esc(srcName(k)) + "</text>";
  return s + '<text x="8" y="62" class="lens-tl">1× (herkes gibi)</text><text x="' + (W - 8) + '" y="62" text-anchor="end" class="lens-tl">' + lensDec(max) + "×</text></svg>";
}

/* ---- Ek bulgular: AI citation rates, most-quoted concepts, narrative blame codes. Never part of a measure. ---- */
function lensAiBox(k) {
  var parts = [], P = D.AIX && D.AIX.profile, row = P && P.outlets.filter(function (o) { return o.s === k; })[0];
  if (row) {
    var rs = P.measures.filter(function (m) { return m.kind === "ai" && row.m[m.k] != null; });
    if (rs.length) parts.push("<dt>AI incelemesinde alıntılanma</dt><dd>" + rs.map(function (m) { return esc(m.label) + ": <b class=\"num\">" + esc(proFmt(m.k, row.m[m.k])) + "</b>"; }).join("<br>") + "</dd>");
  }
  var cnt = {};
  [[bgm7(), true], [bg7(), false]].forEach(function (p) {
    if (!p[0]) return;
    p[0].events.forEach(function (x) {
      if (x.status !== "review_complete") return;
      bg7Live(x).forEach(function (f) {
        var n = (f.evidence || []).filter(function (q) { return (q.o || []).indexOf(k) >= 0; }).length;
        if (!n) return;
        var id = (p[1] ? "m:" : "b:") + f.id, c = cnt[id] = cnt[id] || { name: aiConceptName(f, p[1]), n: 0 };
        c.n += n;
      });
    });
  });
  var top = Object.keys(cnt).map(function (i) { return cnt[i]; }).sort(function (a, b) { return b.n - a.n || trCmp(a.name, b.name); }).slice(0, 3);
  if (top.length) parts.push("<dt>En çok alıntılanan üç kavram</dt><dd>" + top.map(function (c) { return esc(c.name) + " · <span class=\"num\">" + c.n + "</span> alıntı"; }).join("<br>") + "</dd>");
  var bl = {};
  Object.keys(D.N).forEach(function (key) {
    var n = D.N[key]; if (!narrOk(key)) return;
    var hand = n.status === "hand_coded" || n.status === "headline_coded";
    (n.rows || []).forEach(function (r) {
      var v = String(r.blame == null ? "" : r.blame).trim(); if (r.s !== k || !v || /^(Belirtilmiyor|—|Belirsiz)/.test(v)) return;
      var id = v + "|" + hand, c = bl[id] = bl[id] || { v: v, hand: hand, n: 0 }; c.n++;
    });
  });
  var bt = Object.keys(bl).map(function (i) { return bl[i]; }).sort(function (a, b) { return b.n - a.n || trCmp(a.v, b.v); }).slice(0, 3);
  if (bt.length) parts.push("<dt>Anlatıda en sık sorumlu tutulan</dt><dd>" + bt.map(function (c) {
    return esc(c.v) + " · <span class=\"num\">" + c.n + "</span> olay · " + (c.hand ? "elle kodlandı" : "AI ile kodlandı"); }).join("<br>") + "</dd>");
  if (!parts.length) return "";
  return '<div class="lens-ai"><h3>Ek bulgular ' + yzBadge() + '</h3><p class="sub">Bunlar yukarıdaki ölçülere ve uzaklığa girmez; yalnızca bağlam verir.</p><dl class="lens-dl">' + parts.join("") + "</dl></div>";
}

function lensBody(k, sl) {
  var L = D.LENS, o = L.outlets[k], name = srcName(k), S = o.slices[sl] || { measures: {}, distance: null }, h = "";
  var d = S.distance;
  h += '<p class="lens-dist">' + esc(d == null && !o.feed.complete ? LENS_PARTIAL : lensDistanceText(d)) + "</p>";
  if (d != null) h += '<div class="lens-strip">' + lensStripSvg(k, sl) + "</div>";
  h += "<h3>Kaçırdığınız büyük olaylar</h3>";
  if (!o.feed.complete) h += '<p class="sub lens-miss-none">Bu kurumun derlemesi eksik olabildiği için atlanan olaylar ölçülmedi.</p>';
  else {
    var ms = (o.missed || []).filter(function (id) { return EV[id]; });
    h += ms.length ? '<ul class="lens-miss">' + ms.map(function (id) { return '<li><a href="#/olay?e=' + encodeURIComponent(id) + '">' + esc(storyLabel(EV[id], 110)) + "</a></li>"; }).join("") + "</ul>"
      : '<p class="sub">Bu kurum, büyük olayların hiçbirini atlamamış görünüyor.</p>';
  }
  h += "<h3>Aynı haberleri nasıl anlattı</h3>";
  var shown = LENS_MEASURES.filter(function (m) { var x = S.measures[m[0]]; return x && x.n >= LENS_MIN; });
  h += shown.length ? shown.map(function (m) {
    var x = S.measures[m[0]], sent = lensSentence(name, m[0], x);
    return '<div class="lens-row"><div class="lens-lab">' + esc(m[1].charAt(0).toLocaleUpperCase("tr") + m[1].slice(1)) + "</div>" + lensRowSvg(x, sent) + '<p class="lens-sent">' + esc(sent) + "</p></div>";
  }).join("") : '<p class="sub lens-few">Bu dilimde yeterli haber yok.</p>';
  h += '<div class="lens-sw" role="group" aria-label="Dilim">' + L.slices.map(function (s) {
    return '<button type="button" class="chip" data-lens-slice="' + esc(s.k) + '" aria-pressed="' + (s.k === sl) + '">' + esc(s.l) + "</button>";
  }).join("") + "</div>";
  return h + lensAiBox(k);
}
function lensSection(k) {
  var L = typeof D !== "undefined" && D.LENS, o = L && L.outlets[k]; if (!o) return "";
  if (!o.lens) return o.reason ? '<p class="lens-none sub">' + esc(o.reason) + "</p>" : "";
  return '<section class="sec lens" data-k="' + esc(k) + '"><h2>Bu kaynağı tek başına okusaydınız</h2><div class="lens-in">' + lensBody(k, LENS_SLICE[k] || "all") + "</div></section>";
}
document.addEventListener("click", function (ev) {
  var b = ev.target.closest && ev.target.closest("button[data-lens-slice]"); if (!b) return;
  var sec = b.closest("section.lens"), k = sec && sec.getAttribute("data-k"), sl = b.getAttribute("data-lens-slice");
  if (!k || !D.LENS) return;
  LENS_SLICE[k] = sl; sec.querySelector(".lens-in").innerHTML = lensBody(k, sl);
  var nb = sec.querySelector('button[data-lens-slice="' + sl + '"]'); if (nb) nb.focus({ preventScroll: true });
});

/* ---- Kurumlar: lens outlets by distance from the whole picture (whole season) ---- */
function lensRanking() {
  var L = typeof D !== "undefined" && D.LENS; if (!L) return "";
  var all = Object.keys(L.outlets).filter(function (s) { return L.outlets[s].lens && SRC[s]; }), dist = function (s) { return (L.outlets[s].slices.all || {}).distance; };
  var rs = all.filter(function (s) { return dist(s) != null; }).sort(function (a, b) { return dist(b) - dist(a) || trCmp(srcName(a), srcName(b)); });
  if (!rs.length) return "";
  var max = Math.max(1.5, dist(rs[0]));
  var h = '<section class="sec lens-rank"><h2>Kim bütün resimden ne kadar uzak</h2><p class="sub">Aynı haberlerde dört ölçüde (büyük olayı atlama, yüklü başlık, başlığı haberinden sert yazma, ilk verme) diğer kurumlardan ortalama kaç kat farklı davrandığı; 1 kat tam ortalamadır. Bütün sezon. Bir kuruma tıklayınca ölçüler açılır.</p><ol class="lens-rl">' +
    rs.map(function (s) {
      var d = dist(s);
      return '<li><a href="#/kurum?s=' + encodeURIComponent(s) + '"><span class="lens-rn">' + esc(srcName(s)) + '</span><span class="lens-tr" aria-hidden="true"><i style="left:' + (100 * (d - 1) / (max * 1.04 - 1)).toFixed(1) + '%"></i></span><b class="num">' + lensDec(d) + "×</b></a></li>";
    }).join("") + "</ol>";
  var no = all.filter(function (s) { return dist(s) == null; });
  if (no.length) h += '<p class="sub">Uzaklığı hesaplanamayan kurumlar (yeterli ölçü yok): ' + no.map(function (s) { return '<a class="lnk" href="#/kurum?s=' + encodeURIComponent(s) + '">' + esc(srcName(s)) + "</a>"; }).join(", ") + ".</p>";
  return h + "</section>";
}
function lensMethod() {
  return "<h3>Tek kaynak merceği (8.2)</h3><p>Bir kurumun sayfasındaki “Bu kaynağı tek başına okusaydınız” bölümü dört şeyi ölçer: büyük bir olayı atlamayı, yüklü başlık atmayı, başlığı haberinin kendisinden sert yazmayı ve olayı ilk vermeyi. Her ölçü aynı haberler üzerinde karşılaştırılır: bir olayda hem bu kurum hem diğerleri varsa, kurumun o olaydaki davranışı diğerlerinin aynı olaydaki davranışıyla kıyaslanır, böylece kurumun hangi haberleri seçtiği sonucu bulandırmaz. Karşılaştırma grubu, sezonun yarısında en az etkin olan genel haber kurumlarıdır (ajanslar ve özel yayınlar dışında). “Sistematik” denmesi için en az 20 haber, iki kat ya da yarısı kadar fark, çoklu karşılaştırma düzeltmesinden sonra q < 0,01 ve her ayda aynı yönde en az 1,5 kat fark gerekir (en az iki ayda). Derlemesi eksik olabilen kurumlarda atlanan olay ve ilk veriş ölçülmez. AI bulguları hiçbir ölçüye, uzaklığa ya da hükme girmez.</p>";
}
