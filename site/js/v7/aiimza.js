/* 8.2 Örüntüler › AI ne buldu: the two AI passes (D.BGM media techniques, D.BG behavioural biases) and their
   comparison with the rule-based findings (D.AIX, pipeline/capraz_pipeline/aix.py). Every AI output carries the
   "AI imzalı" label. Charts are drawn with D3 (vendor/d3.min.js, loaded on first use).
   "8.2'de yeni" (D.W82) stays a separate page. */

/* ---- concept texts ---- */
var MEDIA_TR = {
  "ad-hominem": "Bir başlık, kişinin söylediğine değil kişinin kendisine yükleniyor.",
  "causal-overclaim": "Başlık, metnin kanıtlamadığı bir neden-sonuç bağı kuruyor.",
  "cherry-picking": "Olayın bir yanını öne çıkarıp onu zayıflatan bilgiyi dışarıda bırakıyor.",
  "consequence-framing": "Olayı, kime ne kazandırıp kaybettireceği üzerinden anlatıyor.",
  "emphasis-framing": "Aynı olayda bir kurum bir ayrıntıyı, öteki başka bir ayrıntıyı başa koyuyor.",
  "episodic-framing": "Olayı, arka plandaki genel sorunu anmadan tek bir vaka olarak veriyor.",
  "false-dilemma": "Durumu, başka seçenek yokmuş gibi iki seçeneğe indiriyor.",
  "fear-appeal": "Başlık, bilgiden çok korku ve tehdit duygusuyla çalışıyor.",
  "labeling": "Kurumlar aynı kişiye ya da gruba farklı, yargı taşıyan adlar veriyor.",
  "loaded-language": "Olayı, yansız bir sözcük varken duygu yüklü sözcüklerle anlatıyor.",
  "metaphorical-framing": "Olayı bir mecazla (savaş, deprem, oyun) anlatıyor; mecaz okura bir yorum taşıyor.",
  "responsibility-framing": "Başlık, olaydan kimin sorumlu olduğunu ima ediyor ya da sorumluyu adlandırmıyor.",
  "selective-statistics": "Bir sayıyı, karşılaştırma ya da tabanını vermeden öne çıkarıyor.",
  "spin": "Olayı, kurumun genel çizgisine uyan bir yöne eğerek veriyor.",
  "strawman": "Bir tarafın görüşünü, çürütmesi kolay bir biçime sokarak aktarıyor.",
  "thematic-framing": "Olayı tek vakadan çok genel bir eğilimin parçası olarak anlatıyor.",
  "word-choice": "Aynı olgu için kurumlar farklı tonda sözcükler seçiyor."
};
/* behavioural concepts the registry (D.BR) has no Turkish text for; kept in step with biasguard/explain_rules.py */
var BEHAV_TR = {
  "framing-effect": ["Çerçeveleme etkisi", "Aynı olgu farklı sunulunca okurun ondan çıkardığı yargı da değişebilir."],
  "leveling-and-sharpening": ["Düzleştirme ve keskinleştirme", "Aktarıldıkça bazı ayrıntılar silinip bazıları keskinleşir; okur olayın sadeleşmiş bir sürümünü görür."],
  "illusory-correlation": ["Yanıltıcı ilişki", "Okura, aslında aralarında bağ kanıtlanmamış iki şey birbirine bağlıymış gibi görünür."],
  "fundamental-attribution-error": ["Temel atıf hatası", "Okur olayı koşullardan çok kişilerin karakterine bağlamaya yönlendirilir."],
  "optimism-bias": ["İyimserlik yanlılığı", "Okura gelecek, verilerin desteklediğinden daha iyimser gösterilir."],
  "outcome-bias": ["Sonuç yanlılığı", "Okur bir kararı, verildiği andaki bilgiye göre değil sonucuna göre değerlendirmeye yönlendirilir."],
  "belief-perseverance": ["İnanç direnci", "Okurun eski kanaati, onu çürüten bilgi gelse de korunur."],
  "priming": ["Hazırlama etkisi", "Başlıkta önce verilen bir öğe, okurun gerisini nasıl yorumlayacağını önceden belirler."],
  "hindsight-bias": ["Geriye dönük bilmişlik", "Olay olduktan sonra, olacağı baştan belliymiş gibi anlatılır."],
  "messenger-effect": ["Haberci etkisi", "Okur bilgiyi içeriğinden çok onu kimin söylediğine göre tartmaya yönlendirilir."],
  "recency-effect": ["Sonluk etkisi", "Okurun aklında olayın en son gelişmesi kalır; önceki bağlam geri planda kalır."],
  "illusory-truth-effect": ["Yanıltıcı doğruluk etkisi", "Bir iddia sık tekrarlandıkça okura doğruymuş gibi gelmeye başlar."],
  "automation-bias": ["Otomasyon yanlılığı", "Okur, bir makine ya da algoritmanın verdiği sonuca fazla güvenmeye yönlendirilir."],
  "source-confusion": ["Kaynak karışıklığı", "Okur bir bilginin nereden geldiğini (iddia mı, resmî açıklama mı) karıştırabilir."],
  "peak-end-rule": ["Zirve-son kuralı", "Okurun olaydan aklında kalan, en çarpıcı anı ve sonu olur."],
  "affect-heuristic": ["Duygu kestirimi", "Okurun olay hakkındaki yargısını bilgiden çok uyandırılan duygu belirler."],
  "bikeshedding": ["Önemsiz ayrıntıya takılma", "Okurun dikkati önemli konudan, tartışması kolay bir ayrıntıya kayar."]
};
function aiItems(B) {
  var out = [];
  (B ? B.events : []).forEach(function (x) {
    if (x.status !== "review_complete") return;
    bg7Live(x).forEach(function (f) { out.push({ x: x, f: f }); });
  });
  return out;
}
function aiConceptText(f, media) {
  if (media) return MEDIA_TR[f.id] || f.definition;
  if (BEHAV_TR[f.id]) return BEHAV_TR[f.id][1];
  var b = biasBrief(f.id, BREG, bg7k); return b ? b.text : f.definition;
}
function aiConceptName(f, media) {
  if (!media) return f.name.replace(/\s*\(.*\)$/, "");  /* owner: behavioural concept names stay in English; the explanation is Turkish */
  var c = MEDIA_CONCEPTS.filter(function (m) { return m.id === f.id; })[0]; return c ? c.tr : f.name;
}
/* "[cumhuriyet · 17:34] 'Fon' vurgununda…" → "'Fon' vurgununda…": the outlet is named beside the quote. */
function aiQuote(q) { return String(q || "").replace(/^\[[^\]]+\]\s*/, ""); }

/* ---- one finding as an evidence card (also used on event pages) ---- */
function aiCard(it, media, withEvent) {
  var f = it.f, x = it.x, e = EV[x.event], t = yzText(f, rev7For(x, f)) || {};
  var qs = (f.evidence || []).slice(0, 3).map(function (q) {
    var who = (q.o || []).map(function (o) { return esc(srcName(o)); }).join(", ");
    return "<li><q>" + esc(aiQuote(q.q)) + "</q>" + (who ? '<span class="ai-who">' + who + "</span>" : "") + "</li>";
  }).join("");
  return '<article class="ai-card">' +
    '<header class="ai-card-h"><span class="ai-kind">' + esc(aiConceptName(f, media)) + "</span>" + yzBadge() + "</header>" +
    (withEvent ? '<h4 class="ai-ev"><a href="#/olay?e=' + encodeURIComponent(x.event) + '">' + esc(e ? storyLabel(e, 110) : x.title) + "</a></h4>" : "") +
    '<dl class="ai-dl">' +
    (t.noticed ? "<dt>" + (t.editor ? "Editör notu" : "Ne fark etti") + "</dt><dd>" + esc(t.noticed) + "</dd>" : "") +
    (qs ? "<dt>Başlıklarda</dt><dd><ul class=\"ai-q\">" + qs + "</ul></dd>" : "") +
    '<dt class="ai-means">Ne anlama geliyor</dt><dd class="ai-means">' + esc(t.means || aiConceptText(f, media)) + "</dd>" +
    (t.why ? "<dt>Neden kesin değil</dt><dd>" + esc(t.why) + "</dd>" : "") + "</dl></article>";
}

/* ---- D3: loaded on first use, local copy first ---- */
var D3_SRC = ["vendor/d3.min.js", "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"], D3Q = null;
function d3Load(cb) {
  if (window.d3) return cb();
  if (D3Q) return D3Q.push(cb);
  D3Q = [cb];
  var i = 0, next = function () {
    var s = document.createElement("script"); s.src = D3_SRC[i++];
    s.onload = function () { var q = D3Q; D3Q = null; q.forEach(function (f) { f(); }); };
    s.onerror = function () { if (i < D3_SRC.length) next(); else { D3Q = null; [].forEach.call(document.querySelectorAll(".ai-d3"), function (b) { b.innerHTML = '<p class="ai-fail">Grafik yüklenemedi; aynı veri “Tabloyu göster” altında.</p>'; }); } };
    document.head.appendChild(s);
  };
  next();
}
function aiTok() {
  var cs = getComputedStyle(document.documentElement), t = {};
  ["left", "right", "mid", "ink", "ink2", "muted", "line", "line2", "hot", "np", "surface"].forEach(function (k) { t[k] = cs.getPropertyValue("--" + k).trim(); });
  return t;
}
function aiBox(kind, label) { return '<div class="ai-d3" data-ai="' + kind + '" role="img" aria-label="' + esc(label) + '"><p class="ai-wait">Grafik çiziliyor…</p></div>'; }
function aiMount(root) {
  var boxes = (root || document).querySelectorAll(".ai-d3:not([data-done])");
  if (!boxes.length || !D.AIX) return;
  d3Load(function () {
    [].forEach.call(boxes, function (b) {
      b.setAttribute("data-done", "1"); b.innerHTML = "";
      try { AI_DRAW[b.getAttribute("data-ai")](b, aiTok()); } catch (e) { b.innerHTML = '<p class="ai-fail">Grafik çizilemedi.</p>'; }
    });
  });
}
var aiBlocC = function (T, b) { return b === "left" ? T.left : b === "right" ? T.right : b === "mid" ? T.mid : T.line2; };
var AI_DRAW = {
  /* outlets: rule-based loaded-language score (x) against the AI's wording citation rate (y, with 95 % interval) */
  wording: function (box, T) {
    var rows = D.AIX.wording.outlets, W = 720, H = 440, m = { t: 18, r: 24, b: 54, l: 58 };
    var x = d3.scaleLinear(d3.extent(rows, function (r) { return r.v; }), [m.l, W - m.r]).nice();
    var y = d3.scaleLinear([0, d3.max(rows, function (r) { return r.hi; })], [H - m.b, m.t]).nice();
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(0," + (H - m.b) + ")").call(d3.axisBottom(x).ticks(6).tickSizeOuter(0));
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(" + m.l + ",0)").call(d3.axisLeft(y).ticks(5).tickFormat(function (v) { return "%" + Math.round(100 * v); }).tickSize(-(W - m.l - m.r)));
    svg.append("text").attr("class", "ai-axt").attr("x", W - m.r).attr("y", H - 12).attr("text-anchor", "end").text("Kural tabanlı yüklü dil puanı (aynı başlıkların ortalaması) →");
    svg.append("text").attr("class", "ai-axt").attr("x", m.l).attr("y", 10).text("↑ AI’nin sözcük tekniği için alıntıladığı olay payı");
    var g = svg.append("g").selectAll("g").data(rows, function (r) { return r.s; }).join("g")
      .attr("tabindex", 0).attr("data-tip", function (r) { return "<span class='k'>" + esc(srcName(r.s)) + "</span>" + r.k + " / " + r.n + " olay · " + orP(r.rate) + "<br>%95 aralık " + orP(r.lo) + " – " + orP(r.hi) + "<br>Yüklü dil puanı " + dec(r.v, 1); })
      .attr("aria-label", function (r) { return srcName(r.s) + ": " + orP(r.rate) + ", yüklü dil " + dec(r.v, 1); });
    g.append("line").attr("x1", function (r) { return x(r.v); }).attr("x2", function (r) { return x(r.v); })
      .attr("y1", function (r) { return y(r.lo); }).attr("y2", function (r) { return y(r.hi); }).attr("stroke", function (r) { return aiBlocC(T, r.bloc); }).attr("stroke-opacity", .35).attr("stroke-width", 2);
    g.append("circle").attr("cx", function (r) { return x(r.v); }).attr("cy", function (r) { return y(r.rate); }).attr("r", 0)
      .attr("fill", function (r) { return aiBlocC(T, r.bloc); }).attr("stroke", T.surface || "#fff").attr("stroke-width", 1.5)
      .transition().delay(function (r, i) { return 12 * i; }).duration(500).attr("r", 6);
    /* label only the extremes: highest AI rate and highest rule score, never two labels on one spot */
    var lab = [], cand = rows.slice().sort(function (a, b) { return b.rate - a.rate; }).slice(0, 2).concat(rows.slice().sort(function (a, b) { return b.v - a.v; }).slice(0, 2));
    cand.forEach(function (r) { if (lab.every(function (l) { return Math.abs(x(l.v) - x(r.v)) > 90 || Math.abs(y(l.rate) - y(r.rate)) > 18; })) lab.push(r); });
    svg.append("g").selectAll("text").data(lab).join("text").attr("class", "ai-lab").attr("x", function (r) { return x(r.v) + 9; }).attr("y", function (r) { return y(r.rate) + 4; }).text(function (r) { return srcName(r.s); });
    box.append(svg.node());
  },
  /* media technique x bloc: share of a bloc's outlet-events the AI cited for the technique */
  heat: function (box, T) {
    var rows = D.AIX.heat.filter(function (r) { return r.events >= 3; }), B = ["left", "mid", "right"], W = 720, rh = 34, m = { t: 34, r: 16, b: 10, l: 230 };
    var H = m.t + rows.length * rh + m.b, mx = d3.max(rows, function (r) { return d3.max(B, function (b) { return r[b].rate; }); });
    var x = d3.scaleBand(B, [m.l, W - m.r]).padding(.08), y = d3.scaleBand(rows.map(function (r) { return r.id; }), [m.t, H - m.b]).padding(.1);
    var col = d3.scaleSequential([0, mx], d3.interpolateRgb(T.np || "#F5F0E3", T.hot || "#B45309"));
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("g").selectAll("text").data(B).join("text").attr("class", "ai-colh").attr("x", function (b) { return x(b) + x.bandwidth() / 2; }).attr("y", 20).attr("text-anchor", "middle")
      .text(function (b) { return SIDE[b]; }).attr("fill", function (b) { return aiBlocC(T, b); });
    svg.append("g").selectAll("text").data(rows).join("text").attr("class", "ai-rowh").attr("x", m.l - 12).attr("y", function (r) { return y(r.id) + y.bandwidth() / 2 + 4; }).attr("text-anchor", "end")
      .text(function (r) { var c = MEDIA_CONCEPTS.filter(function (k) { return k.id === r.id; })[0]; return (c ? c.tr : r.name) + " · " + r.events; });
    var cells = [];
    rows.forEach(function (r) { B.forEach(function (b) { cells.push({ r: r, b: b, v: r[b] }); }); });
    var c = svg.append("g").selectAll("g").data(cells).join("g").attr("tabindex", 0)
      .attr("data-tip", function (d) { return "<span class='k'>" + esc(d.r.name) + " · " + SIDE[d.b] + "</span>" + d.v.k + " / " + d.v.n + " kurum-olay · " + orP(d.v.rate) + "<br>%95 aralık " + orP(d.v.lo) + " – " + orP(d.v.hi); });
    c.append("rect").attr("x", function (d) { return x(d.b); }).attr("y", function (d) { return y(d.r.id); }).attr("width", x.bandwidth()).attr("height", y.bandwidth()).attr("rx", 3)
      .attr("fill", T.np).transition().delay(function (d, i) { return 15 * i; }).duration(450).attr("fill", function (d) { return col(d.v.rate); });
    c.append("text").attr("class", "ai-cell").attr("x", function (d) { return x(d.b) + x.bandwidth() / 2; }).attr("y", function (d) { return y(d.r.id) + y.bandwidth() / 2 + 4; }).attr("text-anchor", "middle")
      .attr("fill", function (d) { return d3.hsl(col(d.v.rate)).l > .55 ? "#1B1813" : "#FBF8F0"; }).text(function (d) { return orP(d.v.rate); });
    box.append(svg.node());
  },
  /* findings per event (both passes), mean with bootstrap 95 % interval, by context */
  where: function (box, T) {
    var Wh = D.AIX.where, groups = [["Konu", Wh.topic], ["Hafta", Wh.week], ["Yüklü dil farkı", Wh.spread], ["Kör nokta", Wh.blind]];
    var rows = []; groups.forEach(function (g) { rows.push({ head: g[0] }); g[1].forEach(function (r) { rows.push({ g: g[0], r: r }); }); });
    var W = 720, rh = 26, m = { t: 30, r: 70, b: 34, l: 200 }, H = m.t + rows.length * rh + m.b;
    var all = [].concat.apply([], groups.map(function (g) { return g[1]; }));
    var x = d3.scaleLinear([d3.min(all, function (r) { return r.lo; }) - .5, d3.max(all, function (r) { return r.hi; }) + .5], [m.l, W - m.r]).nice();
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(0," + (H - m.b) + ")").call(d3.axisBottom(x).ticks(6).tickSize(-(H - m.t - m.b)));
    svg.append("text").attr("class", "ai-axt").attr("x", W - m.r).attr("y", H - 4).attr("text-anchor", "end").text("Olay başına AI bulgusu (ortalama, %95 aralık) →");
    var g = svg.append("g").selectAll("g").data(rows).join("g").attr("transform", function (d, i) { return "translate(0," + (m.t + i * rh) + ")"; });
    g.filter(function (d) { return d.head; }).append("text").attr("class", "ai-grp").attr("x", 0).attr("y", 16).text(function (d) { return d.head; });
    var r = g.filter(function (d) { return !d.head; }).attr("tabindex", 0)
      .attr("data-tip", function (d) { return "<span class='k'>" + esc(d.r.k) + "</span>" + d.r.n + " olay · ortalama " + dec(d.r.mean, 1) + " bulgu<br>%95 aralık " + dec(d.r.lo, 1) + " – " + dec(d.r.hi, 1); });
    r.append("text").attr("class", "ai-rowh").attr("x", m.l - 12).attr("y", 16).attr("text-anchor", "end").text(function (d) { return (TOPIC_TR[d.r.k] || d.r.k) + " · " + d.r.n; });
    r.append("line").attr("x1", function (d) { return x(d.r.lo); }).attr("x2", function (d) { return x(d.r.hi); }).attr("y1", 12).attr("y2", 12).attr("stroke", T.ink2).attr("stroke-width", 2).attr("stroke-linecap", "round");
    r.append("circle").attr("cx", function (d) { return x(d.r.mean); }).attr("cy", 12).attr("r", 5.5).attr("fill", T.hot).attr("stroke", T.surface || "#fff").attr("stroke-width", 1.5);
    box.append(svg.node());
  }
};
var TOPIC_TR = {};
(D.TP || []).forEach(function (t) { if (t && t.k) TOPIC_TR[t.k] = t.n || t.l || t.k; });

/* ---- Örüntüler › AI ne buldu ---- */
OR_PAGES.yz = ["AI ne buldu", "İki AI incelemesi en çok kurumun verdiği olaylarda ne buldu, ve bu bulgular sitenin kural tabanlı ölçümleriyle örtüşüyor mu?"];
SUB["/oruntu"].push(["/oruntu", "yz", "AI ne buldu"]);

function orFindYZConcepts() {
  var M = bgm7(), B = bg7(), mi = aiItems(M), bi = aiItems(B);
  var rows = function (items, media, g) {
    var by = {}; items.forEach(function (it) { (by[it.f.id] = by[it.f.id] || { f: it.f, ev: {}, o: {} }).ev[it.x.event] = 1; (it.f.evidence || []).forEach(function (q) { (q.o || []).forEach(function (o) { by[it.f.id].o[o] = 1; }); }); });
    return Object.keys(by).map(function (k) { var r = by[k]; return { f: r.f, n: Object.keys(r.ev).length, o: Object.keys(r.o).length, g: g, media: media }; })
      .sort(function (a, b) { return b.n - a.n; });
  };
  var mr = rows(mi, true, "medya"), br = rows(bi, false, "davranis"), mx = Math.max(1, (mr[0] || {}).n || 1, (br[0] || {}).n || 1);
  var list = function (rs, title, done, of) {
    return '<div class="ai-cgrp"><h3>' + esc(title) + ' <span class="ai-sub">' + done + " / " + of + " olay incelendi</span></h3><ol class=\"ai-clist\">" + rs.map(function (r) {
      return '<li><a href="#/oruntu?q=yz&g=' + r.g + "&k=" + encodeURIComponent(r.f.id) + '"><span class="ai-cn">' + esc(aiConceptName(r.f, r.media)) + '</span><span class="ai-cbar"><i style="width:' + (100 * r.n / mx) + '%"></i></span><b>' + r.n + "</b></a>" +
        '<p class="ai-ct">' + esc(aiConceptText(r.f, r.media)) + "</p></li>"; }).join("") + "</ol></div>";
  };
  var top = mr[0];
  return { id: "yz-kavram", nopin: true, nocount: true,
    claim: "AI, incelediği olayların hepsinde en az bir medya tekniği buldu; en sık görülen <b>" + esc(top ? aiConceptName(top.f, true).toLocaleLowerCase("tr") : "—") + "</b> (" + (top ? top.n : 0) + " olay). " + yzBadge(),
    viz: '<div class="ai-concepts">' + (M ? list(mr, MEDIA_GROUP, M.summary.completed, M.summary.planned) : "") + (B ? list(br, BEHAVIOURAL_GROUP, B.summary.completed, B.summary.planned) : "") + "</div>",
    read: "Çubuk, kavramın bulunduğu olay sayısı. Bir kavrama " + orTap() + ": o kavramın bütün bulguları, her biri ne fark ettiği, ne anlama geldiği ve neden kesin olmadığıyla açılır.",
    means: "Medya teknikleri metnin ne yaptığını, davranışsal yanlılıklar başlıkların akıl yürütmesini anlatır. Davranışsal bulguların neredeyse hepsi “bağlam gerekli” düzeyinde kaldı: başlıklar bir kişinin akıl yürütmesini nadiren gösterir. Hiçbir bulgu insan tarafından doğrulanmadı.",
    how: orHow(["İki ayrı AI incelemesi: bir seçici olası kavramları seçer; birbirini görmeyen savunan ve sorgulayan inceleyici her kavramın zorunlu koşullarını tek tek değerlendirir; motor her alıntının başlıkta birebir geçtiğini denetler.",
      "Medya kartları 8.2 deneme sürümü için laboratuvar sınaması beklenmeden canlıya alındı. " + (M ? (M.summary.planned - M.summary.completed) + " olayın medya incelemesi tamamlanmadı." : "")], "yz") };
}
function orFindYZWording() {
  var A = D.AIX.wording, h = A.headlines, top = A.outlets[0], low = A.outlets[A.outlets.length - 1];
  return { id: "yz-kural", nopin: true, nocount: true,
    claim: "AI’nin bir başlığı sözcük tekniği için alıntılaması, kural tabanlı yüklü dil puanıyla <b>neredeyse hiç ilişkili değil</b>: kurumlar arasında sıra korelasyonu ρ = " + dec(A.rho, 2) +
      ", başlık düzeyinde AUC " + dec(h.auc, 2) + " (yazı tura 0,50). " + yzBadge(),
    viz: aiBox("wording", "Kurumlara göre kural tabanlı yüklü dil puanı ve AI’nin sözcük tekniği alıntılama payı") +
      legendHTML([{ c: "var(--left)", t: "sola yerleşik" }, { c: "var(--mid)", t: "merkez" }, { c: "var(--right)", t: "sağa yerleşik" }, { c: "var(--line2)", t: "yerleşimsiz" }], "Kurum"),
    read: "Her nokta bir kurum (en az " + D.AIX.minEvents + " incelenen olayı olanlar). Sağa gittikçe kural tabanlı puan yüksek, yukarı gittikçe AI daha sık alıntılamış. Dikey çizgi %95 aralık. Noktalar bir çizgi oluşturmuyor: iki ölçü farklı şeyi görüyor.",
    means: "Kural tabanlı puan sözcüğün kendisine bakar (“vurgun”, “skandal”); AI ise aynı olayı veren başlıkları karşılaştırır ve bir kurumun öteki kurumlardan farklı adlandırdığı yeri işaretler. Alıntılanan başlıkların ortalama puanı " + dec(h.vCited, 1) + ", alıntılanmayanlarınki " + dec(h.vNot, 1) +
      ". Bu yüzden iki ölçü birbirinin yerine geçmez; birlikte okunduğunda, yüklü sözcük kullanmadan da farklı çerçeveleyen başlıklar görünür olur. En sık alıntılanan " + esc(srcName(top.s)) + " (" + orP(top.rate) + "), en seyrek " + esc(srcName(low.s)) + " (" + orP(low.rate) + ").",
    table: vzTable(["Kurum", "Blok", "İncelenen olay", "AI alıntısı", "Pay", "%95 aralık", "Yüklü dil puanı"], A.outlets.map(function (r) {
      return [srcName(r.s), SIDE[r.bloc] || "yerleşimsiz", r.n, r.k, orP(r.rate), orP(r.lo) + " – " + orP(r.hi), dec(r.v, 1)]; })),
    how: orHow(["Sözcük teknikleri: duygu yüklü dil, sözcük seçimi, etiketleme. Bir kurum, bu tekniklerden birinin kanıtında başlığı alıntılandıysa o olayda ‘alıntılandı’ sayılır.",
      "Yüklü dil puanı: sitenin kural tabanlı puanlayıcısı, kurumun aynı olaylardaki ilk başlıkları üzerinden ortalama.",
      "ρ: Spearman sıra korelasyonu (" + A.outlets.length + " kurum). AUC: rastgele seçilen alıntılanmış bir başlığın puanının alıntılanmamış bir başlığınkinden yüksek olma olasılığı; %95 aralık " + dec(h.aucLo, 2) + " – " + dec(h.aucHi, 2) + " (bootstrap, " + orN(h.cited + h.notCited) + " başlık)."], "yz") };
}
function orFindYZHeat() {
  var rows = D.AIX.heat, t = rows[0], bl = D.AIX.wording.blocs;
  var spread = function (r) { var v = ["left", "mid", "right"].map(function (b) { return r[b].rate; }); return Math.max.apply(null, v) - Math.min.apply(null, v); };
  var widest = rows.filter(function (r) { return r.events >= 10; }).sort(function (a, b) { return spread(b) - spread(a); })[0] || t;
  return { id: "yz-blok", nopin: true, nocount: true,
    claim: "Hiçbir blok AI bulgularında öne çıkmıyor: en sık teknik olan " + esc(aiConceptName(t, true).toLocaleLowerCase("tr")) + " sol, merkez ve sağ kurumların olaylarında " +
      ["left", "mid", "right"].map(function (b) { return "<b>" + orPc(t[b].rate) + "</b>"; }).join(", ") + " oranında görülüyor. " + yzBadge(),
    viz: aiBox("heat", "Medya teknikleri ve bloklar: AI’nin kurum başlığını alıntıladığı kurum-olay payı"),
    read: "Satır bir teknik (yanındaki sayı, bulunduğu olay), sütun bir blok. Hücre, o bloktaki kurumların bu teknik için alıntılandığı kurum-olay payı; koyu renk daha sık. Kurum başına hesaplandığından, çok kurumlu blok sırf büyüklüğü yüzünden koyu görünmez.",
    means: "Blok farkları birkaç puanı geçmiyor; en geniş fark " + esc(aiConceptName(widest, true).toLocaleLowerCase("tr")) + " tekniğinde " + dec(100 * spread(widest), 1) + " puan. Sözcük tekniklerinde blok payları: " +
      ["left", "mid", "right"].filter(function (b) { return bl[b]; }).map(function (b) { return SIDE[b].toLocaleLowerCase("tr") + " " + orP(bl[b].rate); }).join(", ") +
      ". AI, çerçeveleme farkını yelpazenin bir ucuna değil, olayı veren kurumların arasına yerleştiriyor. Yerleşim kayıt defterinden gelir ve doğrulanmamıştır.",
    table: vzTable(["Teknik", "Olay", "Sol", "Merkez", "Sağ"], rows.map(function (r) { return [aiConceptName(r, true), r.events].concat(["left", "mid", "right"].map(function (b) { return orP(r[b].rate) + " (" + r[b].k + "/" + r[b].n + ")"; })); })),
    how: orHow(["Birim: kurum-olay; incelenen olayda olayı veren her kurum bir kez sayılır. Pay = AI’nin o teknik için kurumun başlığını alıntıladığı kurum-olay / bloktaki kurum-olay.", "Yerleşimsiz kurumlar bu tabloda yok."], "yz") };
}
function orFindYZBlame() {
  var b = D.AIX.blame, n = b.both + b.rule + b.ai + b.neither, ruleN = b.both + b.rule, aiN = b.both + b.ai;
  var cell = function (v, cls) { return '<div class="ai-x ' + cls + '"><b>' + orN(v) + "</b><span>" + orP(v / (n || 1)) + "</span></div>"; };
  var viz = '<div class="ai-2x2" role="table" aria-label="Anlatı haritası ile AI sorumluluk bulgularının karşılaştırması">' +
    '<span></span><span class="ai-ch" role="columnheader">AI sorumluluk çerçevesi buldu</span><span class="ai-ch" role="columnheader">AI bulmadı</span>' +
    '<span class="ai-rh" role="rowheader">Anlatı haritası birini sorumlu tutuyor</span>' + cell(b.both, "on") + cell(b.rule, "") +
    '<span class="ai-rh" role="rowheader">Kimseyi sorumlu tutmuyor</span>' + cell(b.ai, "") + cell(b.neither, "") + "</div>";
  return { id: "yz-sorumlu", nopin: true, nocount: true,
    claim: "Anlatı haritasının “sorumlu tutulan” kodlaması ile AI’nin sorumluluk çerçevesi bulguları <b>neredeyse hiç örtüşmüyor</b>: " + orN(b.events) + " olayda Cohen κ = " + dec(b.kappa, 2) + ". " + yzBadge(),
    viz: viz,
    read: "Her hücre bir kurum-olay satırı. Sol üst, iki yöntemin de sorumluluk gördüğü başlıklar; köşegen dışı hücreler ayrıştıkları yer.",
    means: "Anlatı haritası " + orN(ruleN) + " satırda başlığın birini sorumlu tuttuğunu kodladı; AI ise yalnızca " + orN(aiN) + " satırda sorumluluk çerçevesi gördü ve bunların " + orN(b.both) + " tanesi ortak. " +
      "İki yöntem farklı soru soruyor: anlatı kodu her başlıkta ‘kim sorumlu gösteriliyor’ diye sorar, AI ise yalnızca kurumların sorumluluğu farklı dağıttığı olayları işaretler. Örtüşmenin düşük olması birinin yanlış olduğunu göstermez; sorumluluk atfını ölçmenin tek bir yolu olmadığını gösterir.",
    table: vzTable(["", "AI buldu", "AI bulmadı"], [["Anlatı: sorumlu var", b.both, b.rule], ["Anlatı: sorumlu yok", b.ai, b.neither]]),
    how: orHow(["Birim: hem anlatı haritasında kodlanmış hem medya incelemesi tamamlanmış " + orN(b.events) + " olaydaki kurum satırları (" + orN(n) + ").",
      "Anlatı tarafı: ‘sorumlu tutulan’ boyutu boş değil ve ‘belirtilmiyor’ değil. AI tarafı: kurumun başlığı, sorumluluk atfı çerçevelemesi bulgusunun kanıtında alıntılanmış.",
      "κ: Cohen kappa; 0 şans düzeyinde uyum, 1 tam uyum."], "anlati") };
}
function orFindYZWhere() {
  var W = D.AIX.where, t = W.topic.slice().sort(function (a, b) { return b.mean - a.mean; }), sp = W.spread;
  var hi = t[0], lo = t[t.length - 1];
  return { id: "yz-nerede", nopin: true, nocount: true,
    claim: "AI bulguları olaylara oldukça eşit dağılıyor: konu, hafta ve kör nokta durumuna göre olay başına ortalama bulgu " + dec(Math.min.apply(null, [].concat(W.topic, W.week).map(function (r) { return r.mean; })), 1) + " ile " +
      dec(Math.max.apply(null, [].concat(W.topic, W.week).map(function (r) { return r.mean; })), 1) + " arasında; kurumların yüklü dil puanı birbirinden çok ayrılan olaylarda biraz daha fazla. " + yzBadge(),
    viz: aiBox("where", "Konu, hafta, yüklü dil farkı ve kör noktaya göre olay başına AI bulgusu"),
    read: "Her satır bir olay grubu (yanındaki sayı, gruptaki olay). Nokta ortalama bulgu, çizgi %95 aralık; çizgileri örtüşen gruplar arasındaki fark şansla açıklanabilir.",
    means: "Konular arasında en çok bulgu " + esc(TOPIC_TR[hi.k] || hi.k) + " (" + dec(hi.mean, 1) + "), en az " + esc(TOPIC_TR[lo.k] || lo.k) + " (" + dec(lo.mean, 1) + ") olaylarında, ama aralıklar örtüşüyor. " +
      "Yüklü dil farkı dar olan olaylarda ortalama " + dec(sp[0] ? sp[0].mean : 0, 1) + ", geniş olanlarda " + dec(sp.length ? sp[sp.length - 1].mean : 0, 1) + ": kurumların sözcükleri ayrıştıkça AI daha çok teknik görüyor, ama fark küçük. " +
      "Kör nokta olayları çok az (" + W.blind.filter(function (r) { return r.k !== "kör nokta yok"; }).reduce(function (s, r) { return s + r.n; }, 0) + " olay); bu satıra dayanarak sonuç çıkarmayın.",
    table: vzTable(["Grup", "Değer", "Olay", "Ortalama bulgu", "%95 aralık"], [["Konu", W.topic], ["Hafta", W.week], ["Yüklü dil farkı", W.spread], ["Kör nokta", W.blind]].reduce(function (o, g) {
      return o.concat(g[1].map(function (r) { return [g[0], TOPIC_TR[r.k] || r.k, r.n, dec(r.mean, 1), dec(r.lo, 1) + " – " + dec(r.hi, 1)]; })); }, [])),
    how: orHow(["Bulgu: iki incelemenin (medya ve davranışsal) bir olaydaki bütün bulguları. Birim: medya incelemesi tamamlanmış " + orN(D.AIX.wording.events) + " olay.",
      "Yüklü dil farkı: olayı veren kurumların ilk başlıklarındaki en yüksek ve en düşük kural tabanlı puan arasındaki fark, olaylar üç eşit gruba bölünerek. %95 aralık: bootstrap.", "Konu: olayın ilk konu etiketi; 5’ten az olayı olan konular gösterilmez."], "yz") };
}
function orYZDetail(q) {
  var sel = q.g === "davranis" ? [bg7(), false, BEHAVIOURAL_GROUP] : [bgm7(), true, MEDIA_GROUP];
  var items = aiItems(sel[0]).filter(function (it) { return it.f.id === q.k; }).sort(function (a, b) { return b.x.outlets - a.x.outlets; });
  var f0 = items[0] && items[0].f;
  var h = '<div class="wrap page or ai-detail"><nav class="xcrumb" aria-label="Konum"><a href="#/oruntu?q=yz">AI ne buldu</a><span aria-hidden="true">›</span><span aria-current="page">' + esc(sel[2]) + "</span></nav>";
  if (!f0) return h + '<p class="xempty">Bu kavramda bulgu yok.</p></div>';
  return h + '<div class="phead"><div class="eyebrow">' + esc(sel[2]) + " " + yzBadge() + "</div><h1>" + esc(aiConceptName(f0, sel[1])) + '</h1><p class="lede">' + esc(aiConceptText(f0, sel[1])) +
    ' <span class="ai-sub">' + items.length + " olay</span></p></div>" +
    '<div class="ai-grid">' + items.map(function (it) { return aiCard(it, sel[1], true); }).join("") + "</div></div>";
}
function orYZ(q) {
  if (q && q.k) return orYZDetail(q);
  if (!bg7() && !bgm7()) return orPage("yz", [], []);
  var fs = [orFindYZConcepts()];
  if (D.AIX) fs.push(orFindYZWording(), orFindYZHeat(), orFindYZBlame(), orFindYZWhere());
  return orPage("yz", fs, orExamplesYZ());
}
function orExamplesYZ() {
  var M = bgm7(); if (!M) return [];
  return M.events.filter(function (x) { return x.status === "review_complete" && EV[x.event]; })
    .sort(function (a, b) { return bg7Live(b).length - bg7Live(a).length || b.outlets - a.outlets; }).slice(0, 3).map(function (x) { return EV[x.event]; });
}

/* ---- 8.2'de yeni ---- */
function pgYeni82() {
  var W = D.W82;
  if (!W) return '<div class="wrap page"><div class="phead"><h1>8.2’de yeni</h1><p class="lede">Bu sürümde karşılaştırma verisi yok.</p></div></div>';
  return '<div class="wrap page v7-yn"><div class="phead"><div class="eyebrow">Çapraz Manşet 8.2</div><h1>8.2’de yeni: güncellenen AI incelemesi neyi değiştirdi?</h1>' +
    '<p class="lede">' + esc(W.lede) + "</p></div>" +
    '<div class="yn-grid">' + W.findings.map(ynCard).join("") + "</div>" +
    '<p class="xsmall">Bütün bulgular: <a href="#/oruntu?q=yz">Örüntüler › AI ne buldu</a>. 8.1’deki veri değişiklikleri: <a href="#/yenilikler">8.1’de yeni</a>.</p></div>';
}
SECTIONS.push({ p: "/yeni82", label: "8.2’de yeni", fn: pgYeni82 });
DETAIL["/yeni82"] = { fn: pgYeni82, of: "/yeni82" };
