/* 8.2 Örüntüler analysis: one outlet profile across every measure (Genel bakış), and the AI imzalı findings woven into
   the existing pages: concepts, wording vs loaded language and technique x bloc (Nasıl anlatıyor), AI responsibility vs
   blame coding (Kimi sorumlu tutuyor), where findings cluster (Kim neyi haber yapıyor). Numbers come from D.AIX
   (pipeline/capraz_pipeline/aix.py), findings from D.BGM / D.BG. Charts: D3 (vendor/d3.min.js, loaded on first use).
   Concept detail pages: #/oruntu?q=yz&g=…&k=…. "8.2'de yeni" (D.W82) is its own page. */

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
/* behavioural concepts the registry (D.BR) has no Turkish text for; biasguard/test_explain_rules.py keeps biasguard/explain_rules.py in step */
var BEHAV_TR = {
  "framing-effect": "Aynı olgu farklı sunulunca okurun ondan çıkardığı yargı da değişebilir.",
  "leveling-and-sharpening": "Aktarıldıkça bazı ayrıntılar silinip bazıları keskinleşir; okur olayın sadeleşmiş bir sürümünü görür.",
  "illusory-correlation": "Okura, aslında aralarında bağ kanıtlanmamış iki şey birbirine bağlıymış gibi görünür.",
  "fundamental-attribution-error": "Okur olayı koşullardan çok kişilerin karakterine bağlamaya yönlendirilir.",
  "optimism-bias": "Okura gelecek, verilerin desteklediğinden daha iyimser gösterilir.",
  "outcome-bias": "Okur bir kararı, verildiği andaki bilgiye göre değil sonucuna göre değerlendirmeye yönlendirilir.",
  "belief-perseverance": "Okurun eski kanaati, onu çürüten bilgi gelse de korunur.",
  "priming": "Başlıkta önce verilen bir öğe, okurun gerisini nasıl yorumlayacağını önceden belirler.",
  "hindsight-bias": "Olay olduktan sonra, olacağı baştan belliymiş gibi anlatılır.",
  "messenger-effect": "Okur bilgiyi içeriğinden çok onu kimin söylediğine göre tartmaya yönlendirilir.",
  "recency-effect": "Okurun aklında olayın en son gelişmesi kalır; önceki bağlam geri planda kalır.",
  "illusory-truth-effect": "Bir iddia sık tekrarlandıkça okura doğruymuş gibi gelmeye başlar.",
  "automation-bias": "Okur, bir makine ya da algoritmanın verdiği sonuca fazla güvenmeye yönlendirilir.",
  "source-confusion": "Okur bir bilginin nereden geldiğini (iddia mı, resmî açıklama mı) karıştırabilir.",
  "peak-end-rule": "Okurun olaydan aklında kalan, en çarpıcı anı ve sonu olur.",
  "affect-heuristic": "Okurun olay hakkındaki yargısını bilgiden çok uyandırılan duygu belirler.",
  "bikeshedding": "Okurun dikkati önemli konudan, tartışması kolay bir ayrıntıya kayar."
};
var MEDIA_NAME = {}; MEDIA_CONCEPTS.forEach(function (c) { MEDIA_NAME[c.id] = c.tr; });

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
  if (BEHAV_TR[f.id]) return BEHAV_TR[f.id];
  var b = biasBrief(f.id, BREG, bg7k); return b ? b.text : f.definition;
}
/* owner: behavioural concept names stay in English; the explanation is Turkish */
function aiConceptName(f, media) { return media ? MEDIA_NAME[f.id] || f.name : f.name.replace(/\s*\(.*\)$/, ""); }
/* "[cumhuriyet · 17:34] 'Fon' vurgununda…" → "'Fon' vurgununda…": the outlet is named beside the quote. */
function aiQuote(q) { return String(q || "").replace(/^\[[^\]]+\]\s*/, ""); }
function aiTopic(k) { var t = TPX[k]; return t && (t.n || t.l) || k; }

/* ---- one finding as an evidence card (event pages and concept pages) ---- */
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
  ["left", "right", "mid", "ink", "ink2", "muted", "line", "line2", "hot", "np", "surface", "paper"].forEach(function (k) { t[k] = cs.getPropertyValue("--" + k).trim(); });
  return t;
}
function aiBox(kind, label) { return '<div class="ai-d3" data-ai="' + kind + '" role="img" aria-label="' + esc(label) + '"><p class="ai-wait">Grafik çiziliyor…</p></div>'; }
/* Draws every chart placeholder under root; safe to call on any page (no placeholders = no work). */
function aiMount(root) {
  var boxes = (root || document).querySelectorAll(".ai-d3:not([data-done])");
  if (!boxes.length || !D.AIX) return;
  d3Load(function () {
    var T = aiTok();
    [].forEach.call(boxes, function (b) {
      b.setAttribute("data-done", "1"); b.innerHTML = "";
      try { AI_DRAW[b.getAttribute("data-ai")](b, T); } catch (e) { b.innerHTML = '<p class="ai-fail">Grafik çizilemedi; aynı veri “Tabloyu göster” altında.</p>'; }
    });
  });
}
var aiBlocC = function (T, b) { return b === "left" ? T.left : b === "right" ? T.right : b === "mid" ? T.mid : T.line2; };
function aiLum(c) { return d3.hsl(c).l; }

/* ---- the outlet profile (D.AIX.profile): measure metadata and formatting ---- */
var PRO_PCT = { cover: 1, first: 1, blame: 1, ai_media: 1, ai_wording: 1, ai_behav: 1 };
var PRO_KIND = { "kayıt": "Kayıt", kural: "Kural", "anlatı": "Anlatı kodu", ai: "AI imzalı" };
function proFmt(k, v) { return v == null ? "—" : PRO_PCT[k] ? orP(v) : dec(v, 1); }
function proM(k) { return D.AIX.profile.measures.filter(function (m) { return m.k === k; })[0]; }
function proCell(a, b) {
  var c = D.AIX.profile.matrix.filter(function (c) { return (c.a === a && c.b === b) || (c.a === b && c.b === a); })[0];
  return c || null;
}
function proSig(c) { return c && c.rho != null && c.q != null && c.q < .05; }
/* The pairs worth a sentence: significant, and not two AI measures (those share a source and agree by construction). */
function proKey() {
  return D.AIX.profile.matrix.filter(function (c) { return proSig(c) && !(proM(c.a).kind === "ai" && proM(c.b).kind === "ai"); })
    .sort(function (a, b) { return Math.abs(b.rho) - Math.abs(a.rho); });
}
function proPlain(c) {
  var a = proM(c.a).label.toLocaleLowerCase("tr"), b = proM(c.b).label.toLocaleLowerCase("tr");
  return c.rho > 0 ? "“" + a + "” yüksek olan kurumlarda “" + b + "” de yüksek" : "“" + a + "” yüksek olan kurumlarda “" + b + "” düşük";
}
function proSentence(c) {
  var a = proM(c.a).label.toLocaleLowerCase("tr"), b = proM(c.b).label.toLocaleLowerCase("tr");
  return (c.rho > 0 ? "“" + a + "” yüksek olan kurumlarda “" + b + "” de yüksek" : "“" + a + "” yüksek olan kurumlarda “" + b + "” düşük") +
    " (ρ " + dec(c.rho, 2) + ", " + c.n + " kurum)";
}
var PRO_SEL = { a: null, b: null, s: null };

var AI_DRAW = {
  /* correlation matrix of all outlet measures; a cell selects the pair shown in the scatter beside it */
  matrix: function (box, T) {
    var P = D.AIX.profile, M = P.measures, n = M.length, cs = 46, lw = 210, top = 8, bot = 150;
    var W = lw + (n - 1) * cs + 60, H = top + (n - 1) * cs + bot;
    var ink = d3.interpolateRgb(T.np || "#FBF8F0", T.ink || "#1B1813");
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg ai-mx");
    var cells = [];
    for (var i = 1; i < n; i++) for (var j = 0; j < i; j++) cells.push({ r: i, c: j, cell: proCell(M[i].k, M[j].k) });
    svg.append("g").selectAll("text").data(M.slice(1)).join("text").attr("class", "ai-rowh").attr("x", lw - 10)
      .attr("y", function (m, i) { return top + i * cs + cs / 2 + 4; }).attr("text-anchor", "end").text(function (m) { return m.label; });
    svg.append("g").selectAll("circle").data(M.slice(1)).join("circle").attr("cx", lw - 4).attr("cy", function (m, i) { return top + i * cs + cs / 2; })
      .attr("r", 3).attr("fill", function (m) { return m.kind === "ai" ? T.hot : m.kind === "kayıt" ? T.mid : T.ink; });
    /* column labels, angled under the grid, so every cell names both of its measures */
    svg.append("g").selectAll("text").data(M.slice(0, n - 1)).join("text").attr("class", "ai-colm")
      .attr("transform", function (m, j) { return "translate(" + (lw + j * cs + cs / 2 + 4) + "," + (top + (n - 1) * cs + 10) + ") rotate(-40)"; })
      .attr("text-anchor", "end").text(function (m) { return m.label; });
    var g = svg.append("g").selectAll("g").data(cells).join("g").attr("class", "ai-mxc").attr("tabindex", 0).attr("role", "button")
      .attr("transform", function (d) { return "translate(" + (lw + d.c * cs) + "," + (top + (d.r - 1) * cs) + ")"; })
      .attr("aria-label", function (d) { return M[d.r].label + " ve " + M[d.c].label + (d.cell && d.cell.rho != null ? ": ρ " + dec(d.cell.rho, 2) : ": yetersiz veri"); })
      .attr("data-tip", function (d) {
        var c = d.cell; if (!c || c.rho == null) return "<span class='k'>Yetersiz veri</span>";
        return "<span class='k'>" + esc(M[d.r].label) + " × " + esc(M[d.c].label) + "</span>ρ " + dec(c.rho, 2) + " · " + c.n + " kurum<br>q " + dec(c.q, 3) +
          (proSig(c) ? " · anlamlı" : " · anlamlı değil (şansla açıklanabilir)") + "<br>" + orGo() + ": saçılımı göster"; });
    g.append("rect").attr("x", 2).attr("y", 2).attr("width", cs - 4).attr("height", cs - 4).attr("rx", 4)
      .attr("fill", function (d) { var c = d.cell; return c && c.rho != null && proSig(c) ? ink(Math.min(1, Math.abs(c.rho))) : T.np; })
      .attr("stroke", function (d) { return d.cell && d.cell.rho != null && !proSig(d.cell) ? T.line : "none"; })
      .attr("stroke-dasharray", "3 2");
    g.append("text").attr("class", "ai-mxv").attr("x", cs / 2).attr("y", cs / 2 + 4).attr("text-anchor", "middle")
      .attr("fill", function (d) { var c = d.cell; if (!c || c.rho == null) return T.muted; if (!proSig(c)) return T.muted; return aiLum(ink(Math.min(1, Math.abs(c.rho)))) > .55 ? "#1B1813" : "#FBF8F0"; })
      .text(function (d) { var c = d.cell; return !c || c.rho == null ? "·" : (c.rho > 0 ? "+" : "−") + dec(Math.abs(c.rho), 2).replace(/^0/, ""); });
    var pick = function (d) {
      if (!d.cell || d.cell.rho == null) return;
      PRO_SEL.a = M[d.c].k; PRO_SEL.b = M[d.r].k;
      g.classed("on", function (e) { return e === d; });
      var sc = document.querySelector('.ai-d3[data-ai="pair"]'); if (sc) { sc.innerHTML = ""; AI_DRAW.pair(sc, T); }
    };
    g.on("click", function (ev, d) { pick(d); }).on("keydown", function (ev, d) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); pick(d); } });
    var start = cells.filter(function (d) { return d.cell && ((d.cell.a === PRO_SEL.a && d.cell.b === PRO_SEL.b) || (d.cell.a === PRO_SEL.b && d.cell.b === PRO_SEL.a)); })[0];
    if (start) g.classed("on", function (e) { return e === start; });
    box.append(svg.node());
  },
  /* the selected pair as a scatter: one dot per outlet, bloc colour (a claim about the outlet), extremes labelled */
  pair: function (box, T) {
    var P = D.AIX.profile, a = PRO_SEL.a, b = PRO_SEL.b, ma = proM(a), mb = proM(b), c = proCell(a, b);
    var rows = P.outlets.filter(function (o) { return o.m[a] != null && o.m[b] != null; });
    var W = 460, H = 380, m = { t: 56, r: 18, b: 48, l: 56 };
    var x = d3.scaleLinear(d3.extent(rows, function (o) { return o.m[a]; }), [m.l, W - m.r]).nice();
    var y = d3.scaleLinear(d3.extent(rows, function (o) { return o.m[b]; }), [H - m.b, m.t]).nice();
    var fx = function (k) { return function (v) { return PRO_PCT[k] ? "%" + Math.round(100 * v) : dec(v, 0); }; };
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("text").attr("class", "ai-pt").attr("x", m.l).attr("y", 18).text((c && c.rho != null ? "ρ " + dec(c.rho, 2) + " · " : "") + rows.length + " kurum" + (c && c.q != null ? " · q " + dec(c.q, 3) : ""));
    svg.append("text").attr("class", "ai-ps").attr("x", m.l).attr("y", 36).text(proSig(c) ? "Anlamlı ilişki (yanlış keşif oranı düzeltmesinden sonra)" : "Anlamlı değil: şansla açıklanabilir");
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(0," + (H - m.b) + ")").call(d3.axisBottom(x).ticks(5).tickFormat(fx(a)).tickSizeOuter(0));
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(" + m.l + ",0)").call(d3.axisLeft(y).ticks(5).tickFormat(fx(b)).tickSize(-(W - m.l - m.r)));
    svg.append("text").attr("class", "ai-axt").attr("x", W - m.r).attr("y", H - 10).attr("text-anchor", "end").text(ma.label + " →");
    svg.append("text").attr("class", "ai-axt").attr("transform", "translate(14," + (H - m.b) + ") rotate(-90)").text(mb.label + " →");
    var g = svg.append("g").selectAll("g").data(rows, function (o) { return o.s; }).join("g").attr("tabindex", 0)
      .attr("data-tip", function (o) { return "<span class='k'>" + esc(srcName(o.s)) + "</span>" + esc(ma.label) + ": " + proFmt(a, o.m[a]) + "<br>" + esc(mb.label) + ": " + proFmt(b, o.m[b]); });
    g.append("circle").attr("cx", function (o) { return x(o.m[a]); }).attr("cy", function (o) { return y(o.m[b]); }).attr("r", 0)
      .attr("fill", function (o) { return aiBlocC(T, o.bloc); }).attr("stroke", T.surface || "#fff").attr("stroke-width", 2)
      .transition().duration(450).delay(function (o, i) { return 8 * i; }).attr("r", 6.5);
    var ext = rows.slice().sort(function (p, q) { return q.m[b] - p.m[b]; }).slice(0, 1).concat(rows.slice().sort(function (p, q) { return q.m[a] - p.m[a]; }).slice(0, 1));
    if (PRO_SEL.s) ext = ext.concat(rows.filter(function (o) { return o.s === PRO_SEL.s; }));
    var lab = []; ext.forEach(function (o) { if (lab.indexOf(o) < 0) lab.push(o); });
    /* labels in the right third sit left of their dot, so they never run past the chart */
    svg.append("g").selectAll("text").data(lab).join("text").attr("class", "ai-lab").attr("y", function (o) { return y(o.m[b]) - 7; })
      .attr("x", function (o) { return x(o.m[a]) > W * .66 ? x(o.m[a]) - 9 : x(o.m[a]) + 9; }).attr("text-anchor", function (o) { return x(o.m[a]) > W * .66 ? "end" : "start"; })
      .text(function (o) { return srcName(o.s); });
    box.append(svg.node());
  },
  /* every measure as a strip of outlets; one outlet is picked and lit in every strip */
  strips: function (box, T) {
    var P = D.AIX.profile, M = P.measures, O = P.outlets, rh = 46, lw = 250, W = 760, m = { t: 14, r: 70, b: 10 };
    var H = m.t + M.length * rh + m.b;
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg ai-strips");
    var row = svg.append("g").selectAll("g").data(M).join("g").attr("transform", function (d, i) { return "translate(0," + (m.t + i * rh) + ")"; });
    row.append("line").attr("x1", lw).attr("x2", W - m.r).attr("y1", rh / 2).attr("y2", rh / 2).attr("stroke", T.line);
    row.append("text").attr("class", "ai-rowh").attr("x", lw - 14).attr("y", rh / 2 - 2).attr("text-anchor", "end").text(function (d) { return d.label; });
    row.append("text").attr("class", "ai-kindt").attr("x", lw - 14).attr("y", rh / 2 + 12).attr("text-anchor", "end").text(function (d) { return PRO_KIND[d.kind]; })
      .attr("fill", function (d) { return d.kind === "ai" ? T.hot : T.muted; });
    var dots = [];
    M.forEach(function (d, i) {
      var vals = O.filter(function (o) { return o.m[d.k] != null; });
      var sx = d3.scaleLinear(d3.extent(vals, function (o) { return o.m[d.k]; }), [lw + 8, W - m.r - 8]);
      vals.forEach(function (o) { dots.push({ o: o, k: d.k, i: i, x: sx(o.m[d.k]), rank: 1 + vals.filter(function (p) { return p.m[d.k] > o.m[d.k]; }).length, of: vals.length }); });
    });
    var dg = svg.append("g").selectAll("circle").data(dots).join("circle").attr("class", "ai-sd")
      .attr("cx", function (d) { return d.x; }).attr("cy", function (d) { return m.t + d.i * rh + rh / 2; }).attr("r", 5)
      .attr("fill", function (d) { return aiBlocC(T, d.o.bloc); }).attr("stroke", T.surface || "#fff").attr("stroke-width", 1.5)
      .attr("data-tip", function (d) { return "<span class='k'>" + esc(srcName(d.o.s)) + "</span>" + esc(proM(d.k).label) + ": " + proFmt(d.k, d.o.m[d.k]) + "<br>" + d.rank + ". / " + d.of + " kurum"; })
      .style("cursor", "pointer");
    var val = svg.append("g").selectAll("text").data(M).join("text").attr("class", "ai-sv").attr("x", W - m.r + 10).attr("y", function (d, i) { return m.t + i * rh + rh / 2 + 4; });
    var light = function (s) {
      PRO_SEL.s = s;
      dg.attr("opacity", function (d) { return !s || d.o.s === s ? 1 : .22; }).attr("r", function (d) { return d.o.s === s ? 8 : 5; })
        .attr("stroke", function (d) { return d.o.s === s ? T.ink : T.surface || "#fff"; }).attr("stroke-width", function (d) { return d.o.s === s ? 2.5 : 1.5; });
      dg.filter(function (d) { return d.o.s === s; }).raise();
      val.text(function (mm) { var d = dots.filter(function (x) { return x.o.s === s && x.k === mm.k; })[0]; return d ? d.rank + "/" + d.of : ""; });
      var sel = document.getElementById("ai-pick"); if (sel && sel.value !== s) sel.value = s || "";
    };
    dg.on("click", function (ev, d) { light(d.o.s); });
    box.append(svg.node());
    var sel = document.getElementById("ai-pick");
    if (sel) sel.onchange = function () { light(sel.value || null); };
    light(PRO_SEL.s);
  },
  /* outlets: rule-based loaded-language score (x) against the AI's wording citation rate (y, with 95 % interval) */
  wording: function (box, T) {
    var rows = D.AIX.wording.outlets, W = 720, H = 440, m = { t: 22, r: 24, b: 54, l: 58 };
    var x = d3.scaleLinear(d3.extent(rows, function (r) { return r.v; }), [m.l, W - m.r]).nice();
    var y = d3.scaleLinear([0, d3.max(rows, function (r) { return r.hi; })], [H - m.b, m.t]).nice();
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(0," + (H - m.b) + ")").call(d3.axisBottom(x).ticks(6).tickSizeOuter(0));
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(" + m.l + ",0)").call(d3.axisLeft(y).ticks(5).tickFormat(function (v) { return "%" + Math.round(100 * v); }).tickSize(-(W - m.l - m.r)));
    svg.append("text").attr("class", "ai-axt").attr("x", W - m.r).attr("y", H - 12).attr("text-anchor", "end").text("Kural tabanlı yüklü dil puanı (aynı başlıkların ortalaması) →");
    svg.append("text").attr("class", "ai-axt").attr("x", m.l).attr("y", 12).text("↑ AI’nin sözcük tekniği için alıntıladığı olay payı");
    var g = svg.append("g").selectAll("g").data(rows, function (r) { return r.s; }).join("g")
      .attr("tabindex", 0).attr("data-tip", function (r) { return "<span class='k'>" + esc(srcName(r.s)) + "</span>" + r.k + " / " + r.n + " olay · " + orP(r.rate) + "<br>%95 aralık " + orP(r.lo) + " – " + orP(r.hi) + "<br>Yüklü dil puanı " + dec(r.v, 1); })
      .attr("aria-label", function (r) { return srcName(r.s) + ": " + orP(r.rate) + ", yüklü dil " + dec(r.v, 1); });
    g.append("line").attr("x1", function (r) { return x(r.v); }).attr("x2", function (r) { return x(r.v); })
      .attr("y1", function (r) { return y(r.lo); }).attr("y2", function (r) { return y(r.hi); }).attr("stroke", function (r) { return aiBlocC(T, r.bloc); }).attr("stroke-opacity", .35).attr("stroke-width", 2);
    g.append("circle").attr("cx", function (r) { return x(r.v); }).attr("cy", function (r) { return y(r.rate); }).attr("r", 0)
      .attr("fill", function (r) { return aiBlocC(T, r.bloc); }).attr("stroke", T.surface || "#fff").attr("stroke-width", 1.5)
      .transition().delay(function (r, i) { return 12 * i; }).duration(500).attr("r", 6);
    /* label only the extremes, never two labels on one spot */
    var lab = [], cand = rows.slice().sort(function (a, b) { return b.rate - a.rate; }).slice(0, 2).concat(rows.slice().sort(function (a, b) { return b.v - a.v; }).slice(0, 2));
    cand.forEach(function (r) { if (lab.every(function (l) { return Math.abs(x(l.v) - x(r.v)) > 90 || Math.abs(y(l.rate) - y(r.rate)) > 18; })) lab.push(r); });
    svg.append("g").selectAll("text").data(lab).join("text").attr("class", "ai-lab").attr("y", function (r) { return y(r.rate) + 4; })
      .attr("x", function (r) { return x(r.v) > W * .66 ? x(r.v) - 9 : x(r.v) + 9; }).attr("text-anchor", function (r) { return x(r.v) > W * .66 ? "end" : "start"; })
      .text(function (r) { return srcName(r.s); });
    box.append(svg.node());
  },
  /* media technique x bloc: share of a bloc's outlet-events the AI quoted for the technique */
  heat: function (box, T) {
    var rows = D.AIX.heat.filter(function (r) { return r.events >= 3; }), B = ["left", "mid", "right"], W = 720, rh = 34, m = { t: 34, r: 16, b: 10, l: 250 };
    var H = m.t + rows.length * rh + m.b, mx = d3.max(rows, function (r) { return d3.max(B, function (b) { return r[b].rate; }); }) || 1;
    var x = d3.scaleBand(B, [m.l, W - m.r]).padding(.08), y = d3.scaleBand(rows.map(function (r) { return r.id; }), [m.t, H - m.b]).padding(.1);
    var col = d3.scaleSequential([0, mx], d3.interpolateRgb(T.np || "#FBF8F0", T.hot || "#B45309"));
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("g").selectAll("text").data(B).join("text").attr("class", "ai-colh").attr("x", function (b) { return x(b) + x.bandwidth() / 2; }).attr("y", 20).attr("text-anchor", "middle")
      .text(function (b) { return SIDE[b]; }).attr("fill", function (b) { return aiBlocC(T, b); });
    svg.append("g").selectAll("text").data(rows).join("text").attr("class", "ai-rowh").attr("x", m.l - 12).attr("y", function (r) { return y(r.id) + y.bandwidth() / 2 + 4; }).attr("text-anchor", "end")
      .text(function (r) { return aiConceptName(r, true) + " · " + r.events; });
    var cells = [];
    rows.forEach(function (r) { B.forEach(function (b) { cells.push({ r: r, b: b, v: r[b] }); }); });
    var c = svg.append("g").selectAll("g").data(cells).join("g").attr("tabindex", 0)
      .attr("data-tip", function (d) { return "<span class='k'>" + esc(aiConceptName(d.r, true)) + " · " + SIDE[d.b] + "</span>" + d.v.k + " / " + d.v.n + " kurum-olay · " + orP(d.v.rate) + "<br>%95 aralık " + orP(d.v.lo) + " – " + orP(d.v.hi); });
    c.append("rect").attr("x", function (d) { return x(d.b); }).attr("y", function (d) { return y(d.r.id); }).attr("width", x.bandwidth()).attr("height", y.bandwidth()).attr("rx", 3)
      .attr("fill", T.np).transition().delay(function (d, i) { return 15 * i; }).duration(450).attr("fill", function (d) { return col(d.v.rate); });
    c.append("text").attr("class", "ai-cell").attr("x", function (d) { return x(d.b) + x.bandwidth() / 2; }).attr("y", function (d) { return y(d.r.id) + y.bandwidth() / 2 + 4; }).attr("text-anchor", "middle")
      .attr("fill", function (d) { return aiLum(col(d.v.rate)) > .55 ? "#1B1813" : "#FBF8F0"; }).text(function (d) { return orP(d.v.rate); });
    box.append(svg.node());
  },
  /* findings per event (both passes), mean with bootstrap 95 % interval, by context */
  where: function (box, T) {
    var Wh = D.AIX.where, groups = [["Konu", Wh.topic], ["Hafta", Wh.week], ["Yüklü dil farkı", Wh.spread], ["Kör nokta", Wh.blind]].filter(function (g) { return g[1].length; });
    var rows = []; groups.forEach(function (g) { rows.push({ head: g[0] }); g[1].forEach(function (r) { rows.push({ g: g[0], r: r }); }); });
    var W = 720, rh = 26, m = { t: 30, r: 70, b: 34, l: 220 }, H = m.t + rows.length * rh + m.b;
    var all = [].concat.apply([], groups.map(function (g) { return g[1]; }));
    var x = d3.scaleLinear([d3.min(all, function (r) { return r.lo; }) - .5, d3.max(all, function (r) { return r.hi; }) + .5], [m.l, W - m.r]).nice();
    var svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).attr("class", "ai-svg");
    svg.append("g").attr("class", "ai-ax").attr("transform", "translate(0," + (H - m.b) + ")").call(d3.axisBottom(x).ticks(6).tickSize(-(H - m.t - m.b)));
    svg.append("text").attr("class", "ai-axt").attr("x", W - m.r).attr("y", H - 4).attr("text-anchor", "end").text("Olay başına AI bulgusu (ortalama, %95 aralık) →");
    var g = svg.append("g").selectAll("g").data(rows).join("g").attr("transform", function (d, i) { return "translate(0," + (m.t + i * rh) + ")"; });
    g.filter(function (d) { return d.head; }).append("text").attr("class", "ai-grp").attr("x", 0).attr("y", 16).text(function (d) { return d.head; });
    var r = g.filter(function (d) { return !d.head; }).attr("tabindex", 0)
      .attr("data-tip", function (d) { return "<span class='k'>" + esc(aiTopic(d.r.k)) + "</span>" + d.r.n + " olay · ortalama " + dec(d.r.mean, 1) + " bulgu<br>%95 aralık " + dec(d.r.lo, 1) + " – " + dec(d.r.hi, 1); });
    r.append("text").attr("class", "ai-rowh").attr("x", m.l - 12).attr("y", 16).attr("text-anchor", "end").text(function (d) { return aiTopic(d.r.k) + " · " + d.r.n; });
    r.append("line").attr("x1", function (d) { return x(d.r.lo); }).attr("x2", function (d) { return x(d.r.hi); }).attr("y1", 12).attr("y2", 12).attr("stroke", T.ink2).attr("stroke-width", 2).attr("stroke-linecap", "round");
    r.append("circle").attr("cx", function (d) { return x(d.r.mean); }).attr("cy", 12).attr("r", 5.5).attr("fill", T.hot).attr("stroke", T.surface || "#fff").attr("stroke-width", 1.5);
    box.append(svg.node());
  }
};

/* ================================================== Örüntüler › Genel bakış: one profile, every measure */
OR_PAGES.genel = ["Genel bakış", "Sitenin bütün ölçüleri, kural tabanlı olanlar ve AI imzalı olanlar, her kurum için yan yana: hangileri birlikte hareket ediyor, bir kurum hangisinde nerede duruyor?"];
SUB["/oruntu"].unshift(["/oruntu", "genel", "Genel bakış"]);

function orFindGenelMatrix() {
  var P = D.AIX && D.AIX.profile; if (!P || !P.outlets.length) return null;
  var key = proKey(), k0 = key[0], tested = P.matrix.filter(function (c) { return c.rho != null; }), sig = tested.filter(proSig);
  if (!PRO_SEL.a && k0) { PRO_SEL.a = k0.a; PRO_SEL.b = k0.b; }
  if (!PRO_SEL.a) { PRO_SEL.a = P.measures[0].k; PRO_SEL.b = P.measures[1].k; }
  var viz = '<div class="ai-mxwrap"><div>' + aiBox("matrix", "Kurum ölçüleri arasındaki sıra korelasyonları") +
    '<p class="or-hint">Dolu kare: anlamlı ilişki; koyuluk ilişkinin gücü, işaret yönü (+ birlikte artıyor, − biri artarken öteki azalıyor). Kesik çizgili kare: anlamlı değil. ' +
    '<span class="ai-key"><i class="k-kural"></i>kural</span><span class="ai-key"><i class="k-ai"></i>AI imzalı</span><span class="ai-key"><i class="k-kayit"></i>kayıt</span></p></div>' +
    "<div>" + aiBox("pair", "Seçili iki ölçünün kurumlara göre saçılımı") + legendHTML([{ c: "var(--left)", t: "sola yerleşik" }, { c: "var(--mid)", t: "merkez" }, { c: "var(--right)", t: "sağa yerleşik" }, { c: "var(--line2)", t: "yerleşimsiz" }], "Kurum") + "</div></div>";
  return { id: "genel-iliski", nopin: true, nocount: true,
    claim: k0 ? P.measures.length + " ölçü arasındaki " + tested.length + " ilişkiden " + sig.length + " tanesi şansla açıklanamayacak kadar güçlü; en güçlüsü: " + esc(proPlain(k0)) + ". " + yzBadge()
      : "Ölçüler arasında şansla açıklanamayacak bir ilişki bulunmadı. " + yzBadge(),
    viz: viz,
    read: "Sol: her kare iki ölçünün " + P.outlets.length + " kurum üzerindeki sıra korelasyonu. Bir kareye " + orTap() + ": sağdaki grafik o iki ölçüyü kurum kurum gösterir; her nokta bir kurum, rengi kayıttaki yerleşimi.",
    means: (key.length ? "Öne çıkan bağlar: " + key.slice(0, 4).map(proSentence).join("; ") + ". " : "") +
      "Kural tabanlı ve AI imzalı ölçüler aynı haritada okununca bir kurumun dili, hızı ve AI’nin onda ne gördüğü birbirinden ayrı soru olmaktan çıkar. " +
      "AI’nin sözcük alıntıları kural tabanlı yüklü dil puanıyla " + (function () { var c = proCell("loaded", "ai_wording"); return c && c.rho != null ? (proSig(c) ? "ilişkili (ρ " + dec(c.rho, 2) + ")" : "anlamlı biçimde ilişkili değil (ρ " + dec(c.rho, 2) + ")") : "karşılaştırılamadı"; })() +
      ": iki yöntem aynı şeyi ölçmüyor. Korelasyon neden-sonuç göstermez; çok olay veren kurumlar birçok ölçüde öne çıkabilir.",
    table: vzTable(["Ölçü A", "Ölçü B", "Kurum", "ρ", "p", "q", "Anlamlı"], tested.slice().sort(function (a, b) { return Math.abs(b.rho) - Math.abs(a.rho); }).map(function (c) {
      return [proM(c.a).label, proM(c.b).label, c.n, dec(c.rho, 2), dec(c.p, 3), dec(c.q, 3), proSig(c) ? "evet" : "hayır"]; })),
    how: orHow(["Birim: AI incelemesinde en az " + D.AIX.minEvents + " olayı olan " + P.outlets.length + " kurum. Her ölçü kurum başına tek bir sayıdır; tanımlar alttaki şeritlerde.",
      "ρ: Spearman sıra korelasyonu (iki ölçünün de bulunduğu kurumlar). p: 2.000 karıştırmalı permütasyon testi. q: " + tested.length + " karşılaştırma için Benjamini-Hochberg düzeltmesi; q < 0,05 ‘anlamlı’ sayılır.",
      "Yerleşim yalnızca kayıt defterinde yeri olan kurumlarda vardır (doğrulanmamış); bu yüzden yerleşimli ilişkiler daha az kuruma dayanır."], "yz") };
}
function orFindGenelStrips() {
  var P = D.AIX && D.AIX.profile; if (!P || !P.outlets.length) return null;
  var big = P.outlets.slice().sort(function (a, b) { return b.n - a.n; })[0];
  if (!PRO_SEL.s) PRO_SEL.s = big.s;
  var opts = P.outlets.slice().sort(function (a, b) { return trCmp(srcName(a.s), srcName(b.s)); })
    .map(function (o) { return '<option value="' + esc(o.s) + '"' + (o.s === PRO_SEL.s ? " selected" : "") + ">" + esc(srcName(o.s)) + "</option>"; }).join("");
  return { id: "genel-kurum", nopin: true, nocount: true,
    claim: "Her kurumun " + P.measures.length + " ölçüdeki yeri tek bakışta: bir kurum seçin, bütün şeritlerde yanar. " + yzBadge(),
    viz: '<div class="or-ctl ai-pickrow"><label class="or-cl" for="ai-pick">Kurum</label><select id="ai-pick">' + opts + "</select>" +
      '<span class="or-hint">ya da bir noktaya ' + orTap() + "</span></div>" + aiBox("strips", "Her ölçüde kurumların dağılımı, seçili kurum vurgulu"),
    read: "Her satır bir ölçü, her nokta bir kurum; sağa gittikçe değer yüksek. Sağdaki sayı seçili kurumun sırası (1 = en yüksek). Satırın altındaki etiket ölçünün kaynağı: kural, kayıt, anlatı kodu ya da AI imzalı.",
    means: "Aynı kurum bir ölçüde başta, ötekinde sonda olabilir: hızlı veren bir kurum sakin bir dil kullanabilir, AI ise onu sık alıntılayabilir. Şeritler bu profilin tek bir “yanlılık puanına” indirgenmemesi için yan yana durur. " +
      "Ölçüler farklı ölçeklerde; her şerit kendi en düşük ve en yüksek değeri arasında çizilir.",
    table: vzTable(["Kurum", "Blok"].concat(P.measures.map(function (m) { return m.label; })), P.outlets.map(function (o) {
      return [srcName(o.s), SIDE[o.bloc] || "yerleşimsiz"].concat(P.measures.map(function (m) { return proFmt(m.k, o.m[m.k]); })); })),
    how: orHow(["Yerleşim: kayıt defteri (0 sol – 100 sağ). Verdiği olay payı: sezondaki olayların kaçını verdiği. Yüklü dil puanı: siyasi başlıkların kural tabanlı ortalaması. Başlık spottan ne kadar sert: başlık puanı eksi spot puanı.",
      "İlk veren olduğu olay payı: Kim önce veriyor sayfasıyla aynı veri. Sorumlu tutma payı: Anlatı haritasında kodlanmış satırlardan ‘sorumlu tutulan’ boş olmayanların payı (kodlamanın bir kısmı AI ile yapıldı).",
      "AI ölçüleri: kurumun başlığının ilgili AI bulgusunun kanıtında alıntılandığı incelenen olay payı. Sözcük teknikleri: duygu yüklü dil, sözcük seçimi, etiketleme."], "yz") };
}
/* Which outlets stand furthest from the middle on all behaviour measures at once (registry placement left out):
   mean absolute z-score over the measures an outlet has. A distance, not a verdict. */
function orFindGenelOutliers() {
  var P = D.AIX && D.AIX.profile; if (!P || P.outlets.length < 5) return null;
  var ms = P.measures.filter(function (m) { return m.kind !== "kayıt"; }), z = {};
  ms.forEach(function (m) {
    var v = P.outlets.map(function (o) { return o.m[m.k]; }).filter(function (x) { return x != null; });
    var mu = v.reduce(function (a, b) { return a + b; }, 0) / v.length, sd = Math.sqrt(v.reduce(function (a, b) { return a + (b - mu) * (b - mu); }, 0) / v.length) || 1;
    z[m.k] = function (x) { return (x - mu) / sd; };
  });
  var rows = P.outlets.map(function (o) {
    var zs = ms.filter(function (m) { return o.m[m.k] != null; }).map(function (m) { return { m: m, z: z[m.k](o.m[m.k]) }; });
    return { o: o, d: zs.reduce(function (a, x) { return a + Math.abs(x.z); }, 0) / zs.length,
      top: zs.slice().sort(function (a, b) { return Math.abs(b.z) - Math.abs(a.z); }).slice(0, 2) };
  }).sort(function (a, b) { return b.d - a.d; });
  var show = rows.slice(0, 10), why = function (r) { return r.top.map(function (x) { return x.m.label.toLocaleLowerCase("tr") + (x.z > 0 ? " yüksek" : " düşük"); }).join(", "); };
  var bars = vzRows(show.map(function (r) {
    return { k: r.o.s, label: srcName(r.o.s), val: dec(r.d, 2), pts: [{ v: r.d, c: "var(--" + (r.o.bloc || "line2") + ")", big: true }],
      tip: "<span class='k'>" + esc(srcName(r.o.s)) + "</span>Ortalamadan uzaklık " + dec(r.d, 2) + "<br>En çok: " + esc(why(r)) };
  }), { min: 0, fmt: function (v) { return dec(v, 1); }, lw: 150, vw: 50, axis: "Ölçüler genelinde ortalamadan uzaklık (standart sapma cinsinden ortalama). 0 tam ortada demektir." });
  var a = show[0], b = show[1], c = show[2];
  return { id: "genel-uzak", nocount: true,
    claim: "Bütün ölçülere birlikte bakınca kurumların ortasından en uzak duran <b>" + esc(srcName(a.o.s)) + "</b>; onu " + esc(srcName(b.o.s)) + " ve " + esc(srcName(c.o.s)) + " izliyor. " + yzBadge(),
    viz: bars,
    read: "Her satır bir kurum; nokta sağa gittikçe kurum ölçülerin çoğunda ötekilerden daha farklı. Renk kayıttaki yerleşim. Bir noktaya " + orTap() + ": kurumu en çok hangi ölçünün ayırdığı görünür.",
    means: esc(srcName(a.o.s)) + " en çok " + esc(why(a)) + " olduğu için, " + esc(srcName(b.o.s)) + " " + esc(why(b)) + " olduğu için öne çıkıyor. " +
      "Uzaklık bir yön söylemez: çok hızlı veren ya da AI’nin hiç alıntılamadığı bir kurum da ortadan uzak düşer. Bir kurumu tek bir sayıyla yargılamak için değil, profiline nereden bakmaya başlanacağını göstermek için.",
    table: vzTable(["Kurum", "Blok", "Uzaklık", "En çok ayıran ölçüler"], rows.map(function (r) { return [srcName(r.o.s), SIDE[r.o.bloc] || "yerleşimsiz", dec(r.d, 2), why(r)]; })),
    how: orHow(["Kayıt yerleşimi dışındaki " + ms.length + " ölçünün her biri kurumlar arasında standartlaştırılır (z-puanı: ortalamadan kaç standart sapma uzakta). Uzaklık, kurumun değeri olan ölçülerdeki mutlak z-puanlarının ortalamasıdır.",
      "Birim: Genel bakıştaki " + P.outlets.length + " kurum. Bu bir sıralama değil, profil özetidir."], "yz") };
}
function orGenel() { return orPage("genel", [orFindGenelMatrix(), orFindGenelStrips(), orFindGenelOutliers()], orExamples("genel")); }

/* ================================================== AI findings, used inside the existing Örüntüler pages */
function orFindYZConcepts() {
  var M = bgm7(), B = bg7(); if (!M && !B) return null;
  var mi = aiItems(M), bi = aiItems(B);
  var rows = function (items, media, g) {
    var by = {}; items.forEach(function (it) { (by[it.f.id] = by[it.f.id] || { f: it.f, ev: {} }).ev[it.x.event] = 1; });
    return Object.keys(by).map(function (k) { var r = by[k]; return { f: r.f, n: Object.keys(r.ev).length, g: g, media: media }; }).sort(function (a, b) { return b.n - a.n; });
  };
  var mr = rows(mi, true, "medya"), br = rows(bi, false, "davranis"), mx = Math.max(1, (mr[0] || {}).n || 0, (br[0] || {}).n || 0);
  var list = function (rs, title, S) {
    return '<div class="ai-cgrp"><h3>' + esc(title) + ' <span class="ai-sub">' + S.completed + " / " + S.planned + " olay incelendi</span></h3><ol class=\"ai-clist\">" + rs.map(function (r) {
      return '<li><a href="#/oruntu?q=yz&g=' + r.g + "&k=" + encodeURIComponent(r.f.id) + '"><span class="ai-cn">' + esc(aiConceptName(r.f, r.media)) + '</span><span class="ai-cbar"><i style="width:' + (100 * r.n / mx) + '%"></i></span><b>' + r.n + "</b></a>" +
        '<p class="ai-ct">' + esc(aiConceptText(r.f, r.media)) + "</p></li>"; }).join("") + "</ol></div>";
  };
  var top = mr[0], withF = M ? M.events.filter(function (x) { return x.status === "review_complete" && bg7Live(x).length; }).length : 0;
  return { id: "dil-yz-kavram", nopin: true, nocount: true,
    claim: M ? "AI, medya tekniklerini incelediği " + M.summary.completed + " olayın " + (withF === M.summary.completed ? "hepsinde" : withF + " tanesinde") + " en az bir teknik buldu; en sık görülen <b>" +
      esc(top ? aiConceptName(top.f, true).toLocaleLowerCase("tr") : "—") + "</b> (" + (top ? top.n : 0) + " olay). " + yzBadge() : "AI incelemesi davranışsal yanlılıkları taradı. " + yzBadge(),
    viz: '<div class="ai-concepts">' + (M ? list(mr, MEDIA_GROUP, M.summary) : "") + (B ? list(br, BEHAVIOURAL_GROUP, B.summary) : "") + "</div>",
    read: "Çubuk, kavramın bulunduğu olay sayısı. Bir kavrama " + orTap() + ": o kavramın bütün bulguları, her biri ne fark ettiği, ne anlama geldiği ve neden kesin olmadığıyla açılır.",
    means: "Medya teknikleri metnin ne yaptığını, davranışsal yanlılıklar başlıkların akıl yürütmesini anlatır. Davranışsal bulguların neredeyse hepsi “bağlam gerekli” düzeyinde kaldı: başlıklar bir kişinin akıl yürütmesini nadiren gösterir. Hiçbir bulgu insan tarafından doğrulanmadı.",
    how: orHow(["İki ayrı AI incelemesi: bir seçici olası kavramları seçer; birbirini görmeyen savunan ve sorgulayan inceleyici her kavramın zorunlu koşullarını tek tek değerlendirir; motor her alıntının başlıkta birebir geçtiğini denetler.",
      "Medya kartları 8.2 deneme sürümü için laboratuvar sınaması beklenmeden canlıya alındı." + (M && M.summary.planned > M.summary.completed ? " " + (M.summary.planned - M.summary.completed) + " olayın medya incelemesi tamamlanmadı." : "")], "yz") };
}
function orFindYZWording() {
  var A = D.AIX && D.AIX.wording; if (!A || !A.outlets.length || A.headlines.auc == null) return null;
  var h = A.headlines, top = A.outlets[0], low = A.outlets[A.outlets.length - 1], d = h.auc - .5;
  var verdict = Math.abs(d) < .05 ? "<b>neredeyse hiç ilişkili değil</b>" : d > 0 ? "<b>ilişkili</b>: yüksek puanlı başlıklar daha sık alıntılanıyor" : "<b>ters yönde ilişkili</b>: düşük puanlı başlıklar daha sık alıntılanıyor";
  return { id: "dil-yz-kural", nopin: true, nocount: true,
    claim: "AI’nin bir başlığı sözcük tekniği için alıntılaması, kural tabanlı yüklü dil puanıyla " + verdict + ": alıntılanan başlıkların ortalama puanı " + dec(h.vCited, 1) +
      ", alıntılanmayanlarınki " + dec(h.vNot, 1) + ". " + yzBadge(),
    viz: aiBox("wording", "Kurumlara göre kural tabanlı yüklü dil puanı ve AI’nin sözcük tekniği alıntılama payı") +
      legendHTML([{ c: "var(--left)", t: "sola yerleşik" }, { c: "var(--mid)", t: "merkez" }, { c: "var(--right)", t: "sağa yerleşik" }, { c: "var(--line2)", t: "yerleşimsiz" }], "Kurum"),
    read: "Her nokta bir kurum (en az " + D.AIX.minEvents + " incelenen olayı olanlar). Sağa gittikçe kural tabanlı puan yüksek, yukarı gittikçe AI daha sık alıntılamış. Dikey çizgi %95 aralık.",
    means: "Kural tabanlı puan sözcüğün kendisine bakar (“vurgun”, “skandal”); AI ise aynı olayı veren başlıkları karşılaştırır ve bir kurumun ötekilerden farklı adlandırdığı yeri işaretler. Kurumlar arasında sıra korelasyonu ρ = " + dec(A.rho, 2) +
      ", başlık düzeyinde AUC " + dec(h.auc, 2) + " (yazı tura 0,50). Birlikte okunduğunda, yüklü sözcük kullanmadan da farklı çerçeveleyen başlıklar görünür olur. En sık alıntılanan " + esc(srcName(top.s)) + " (" + orP(top.rate) + "), en seyrek " + esc(srcName(low.s)) + " (" + orP(low.rate) + ").",
    table: vzTable(["Kurum", "Blok", "İncelenen olay", "AI alıntısı", "Pay", "%95 aralık", "Yüklü dil puanı"], A.outlets.map(function (r) {
      return [srcName(r.s), SIDE[r.bloc] || "yerleşimsiz", r.n, r.k, orP(r.rate), orP(r.lo) + " – " + orP(r.hi), dec(r.v, 1)]; })),
    how: orHow(["Sözcük teknikleri: duygu yüklü dil, sözcük seçimi, etiketleme. Bir kurum, bu tekniklerden birinin kanıtında başlığı alıntılandıysa o olayda ‘alıntılandı’ sayılır.",
      "Yüklü dil puanı: sitenin kural tabanlı puanlayıcısı, kurumun aynı olaylardaki ilk başlıkları üzerinden ortalama.",
      "ρ: Spearman sıra korelasyonu (" + A.outlets.length + " kurum). AUC: alıntılanmış rastgele bir başlığın puanının alıntılanmamış bir başlığınkinden yüksek olma olasılığı; %95 aralık " + dec(h.aucLo, 2) + " – " + dec(h.aucHi, 2) + " (bootstrap, " + orN(h.cited + h.notCited) + " başlık)."], "yz") };
}
function orFindYZHeat() {
  var rows = D.AIX && D.AIX.heat; if (!rows || !rows.length) return null;
  var B = ["left", "mid", "right"], t = rows[0], spread = function (r) { var v = B.map(function (b) { return r[b].rate; }); return Math.max.apply(null, v) - Math.min.apply(null, v); };
  var widest = rows.filter(function (r) { return r.events >= 10; }).sort(function (a, b) { return spread(b) - spread(a); })[0] || t, wide = spread(widest) >= .05;
  var hiB = B.slice().sort(function (a, b) { return widest[b].rate - widest[a].rate; })[0];
  return { id: "dil-yz-blok", nopin: true, nocount: true,
    claim: (wide ? SIDE[hiB] + " kurumlar " + esc(aiConceptName(widest, true).toLocaleLowerCase("tr")) + " tekniğinde öne çıkıyor; ama en sık teknik olan " : "Hiçbir blok AI bulgularında öne çıkmıyor: en sık teknik olan ") +
      esc(aiConceptName(t, true).toLocaleLowerCase("tr")) + " sol, merkez ve sağ kurumlarda " + B.map(function (b) { return "<b>" + orPc(t[b].rate) + "</b>"; }).join(", ") + " oranında. " + yzBadge(),
    viz: aiBox("heat", "Medya teknikleri ve bloklar: AI’nin kurum başlığını alıntıladığı kurum-olay payı"),
    read: "Satır bir teknik (yanındaki sayı, bulunduğu olay), sütun bir blok. Hücre, o bloktaki kurumların bu teknik için alıntılandığı kurum-olay payı; koyu renk daha sık. Son satır davranışsal incelemenin tamamı.",
    means: "Kurum başına hesaplandığından, çok kurumlu blok sırf büyüklüğü yüzünden koyu görünmez. En geniş blok farkı " + esc(aiConceptName(widest, true).toLocaleLowerCase("tr")) + " tekniğinde " + dec(100 * spread(widest), 1) + " puan. " +
      "AI, çerçeveleme farkını yelpazenin bir ucuna değil, olayı veren kurumların arasına yerleştiriyor. Yerleşim kayıt defterinden gelir ve doğrulanmamıştır.",
    table: vzTable(["Teknik", "Olay", "Sol", "Merkez", "Sağ"], rows.map(function (r) { return [aiConceptName(r, true), r.events].concat(B.map(function (b) { return orP(r[b].rate) + " (" + r[b].k + "/" + r[b].n + ")"; })); })),
    how: orHow(["Birim: kurum-olay; incelenen olayda olayı veren her kurum bir kez sayılır. Pay = AI’nin o teknik için kurumun başlığını alıntıladığı kurum-olay / bloktaki kurum-olay.", "Yerleşimsiz kurumlar bu tabloda yok."], "yz") };
}
function orFindYZBlame() {
  var b = D.AIX && D.AIX.blame; if (!b || !b.events || b.kappa == null) return null;
  var n = b.both + b.rule + b.ai + b.neither, ruleN = b.both + b.rule, aiN = b.both + b.ai, k = b.kappa;
  var word = k < .2 ? "<b>neredeyse hiç örtüşmüyor</b>" : k < .4 ? "<b>az örtüşüyor</b>" : k < .6 ? "<b>orta düzeyde örtüşüyor</b>" : "<b>büyük ölçüde örtüşüyor</b>";
  var cell = function (v, cls) { return '<div class="ai-x ' + cls + '"><b>' + orN(v) + "</b><span>" + orP(v / (n || 1)) + "</span></div>"; };
  var viz = '<div class="ai-2x2" role="table" aria-label="Anlatı haritası ile AI sorumluluk bulgularının karşılaştırması">' +
    '<span></span><span class="ai-ch" role="columnheader">AI sorumluluk çerçevesi buldu</span><span class="ai-ch" role="columnheader">AI bulmadı</span>' +
    '<span class="ai-rh" role="rowheader">Anlatı haritası birini sorumlu tutuyor</span>' + cell(b.both, "on") + cell(b.rule, "") +
    '<span class="ai-rh" role="rowheader">Kimseyi sorumlu tutmuyor</span>' + cell(b.ai, "") + cell(b.neither, "") + "</div>";
  return { id: "anlati-yz-sorumlu", nopin: true, nocount: true,
    claim: "Anlatı haritasının “sorumlu tutulan” kodlaması ile AI’nin sorumluluk çerçevesi bulguları " + word + ": " + orN(b.events) + " olayda iki yöntemin uyumu " + (k < .2 ? "şans düzeyine yakın" : "şansın üstünde") + ". " + yzBadge(),
    viz: viz,
    read: "Her hücre bir kurum-olay satırı. Sol üst, iki yöntemin de sorumluluk gördüğü başlıklar; köşegen dışı hücreler ayrıştıkları yer.",
    means: "Anlatı haritası " + orN(ruleN) + " satırda başlığın birini sorumlu tuttuğunu kodladı; AI ise " + orN(aiN) + " satırda sorumluluk çerçevesi gördü ve bunların " + orN(b.both) + " tanesi ortak. " +
      "Uyum ölçüsü Cohen κ = " + dec(k, 2) + " (0 şans düzeyi, 1 tam uyum). İki yöntem farklı soru soruyor: anlatı kodu her başlıkta ‘kim sorumlu gösteriliyor’ diye sorar, AI ise yalnızca kurumların sorumluluğu farklı dağıttığı olayları işaretler. Düşük örtüşme birinin yanlış olduğunu göstermez; sorumluluk atfını ölçmenin tek bir yolu olmadığını gösterir.",
    table: vzTable(["", "AI buldu", "AI bulmadı"], [["Anlatı: sorumlu var", b.both, b.rule], ["Anlatı: sorumlu yok", b.ai, b.neither]]),
    how: orHow(["Birim: hem anlatı haritasında kodlanmış hem medya incelemesi tamamlanmış " + orN(b.events) + " olaydaki kurum satırları (" + orN(n) + ").",
      "Anlatı tarafı: ‘sorumlu tutulan’ boyutu boş değil ve ‘belirtilmiyor’ değil. AI tarafı: kurumun başlığı, sorumluluk atfı çerçevelemesi bulgusunun kanıtında alıntılanmış.",
      "κ: Cohen kappa; 0 şans düzeyinde uyum, 1 tam uyum."], "anlati") };
}
function orFindYZWhere() {
  var W = D.AIX && D.AIX.where; if (!W || !W.topic.length) return null;
  var t = W.topic.slice().sort(function (a, b) { return b.mean - a.mean; }), sp = W.spread, all = [].concat(W.topic, W.week).map(function (r) { return r.mean; });
  var hi = t[0], lo = t[t.length - 1], nb = W.blind.filter(function (r) { return r.k !== "kör nokta yok"; }).reduce(function (s, r) { return s + r.n; }, 0);
  return { id: "secim-yz-nerede", nopin: true, nocount: true,
    claim: "AI bulguları konu ve haftaya göre değişmiyor: olay başına ortalama bulgu " + dec(Math.min.apply(null, all), 1) + " ile " + dec(Math.max.apply(null, all), 1) + " arasında" +
      (sp.length > 1 ? "; kurumların yüklü dil puanı birbirinden çok ayrılan olaylarda " + dec(sp[sp.length - 1].mean, 1) + ", az ayrılanlarda " + dec(sp[0].mean, 1) : "") + ". " + yzBadge(),
    viz: aiBox("where", "Konu, hafta, yüklü dil farkı ve kör noktaya göre olay başına AI bulgusu"),
    read: "Her satır bir olay grubu (yanındaki sayı, gruptaki olay). Nokta ortalama bulgu, çizgi %95 aralık; çizgileri örtüşen gruplar arasındaki fark şansla açıklanabilir.",
    means: "Konular arasında en çok bulgu " + esc(aiTopic(hi.k)) + " (" + dec(hi.mean, 1) + "), en az " + esc(aiTopic(lo.k)) + " (" + dec(lo.mean, 1) + ") olaylarında, ama aralıklar örtüşüyor. " +
      "Kurumların hangi olayı verdiği (bu sayfanın konusu) ile AI’nin o olayda ne gördüğü büyük ölçüde bağımsız." + (nb ? " Kör nokta olayları çok az (" + nb + " olay); bu satıra dayanarak sonuç çıkarmayın." : ""),
    table: vzTable(["Grup", "Değer", "Olay", "Ortalama bulgu", "%95 aralık"], [["Konu", W.topic], ["Hafta", W.week], ["Yüklü dil farkı", W.spread], ["Kör nokta", W.blind]].reduce(function (o, g) {
      return o.concat(g[1].map(function (r) { return [g[0], aiTopic(r.k), r.n, dec(r.mean, 1), dec(r.lo, 1) + " – " + dec(r.hi, 1)]; })); }, [])),
    how: orHow(["Bulgu: iki incelemenin (medya ve davranışsal) bir olaydaki bütün bulguları. Birim: medya incelemesi tamamlanmış " + orN(D.AIX.wording.events) + " olay.",
      "Yüklü dil farkı: olayı veren kurumların ilk başlıklarındaki en yüksek ve en düşük kural tabanlı puan arasındaki fark, olaylar üç eşit gruba bölünerek. %95 aralık: bootstrap.", "Konu: olayın ilk konu etiketi; 5’ten az olayı olan konular gösterilmez."], "yz") };
}

/* one concept's findings: #/oruntu?q=yz&g=medya|davranis&k=<id> */
function orYZDetail(q) {
  var sel = q.g === "davranis" ? [bg7(), false, BEHAVIOURAL_GROUP] : [bgm7(), true, MEDIA_GROUP];
  var items = aiItems(sel[0]).filter(function (it) { return it.f.id === q.k; }).sort(function (a, b) { return b.x.outlets - a.x.outlets; });
  var f0 = items[0] && items[0].f;
  var h = '<div class="wrap page or ai-detail"><nav class="xcrumb" aria-label="Konum"><a href="#/oruntu?q=dil&f=dil-yz-kavram">Nasıl anlatıyor</a><span aria-hidden="true">›</span><span aria-current="page">' + esc(sel[2]) + "</span></nav>";
  if (!f0) return h + '<p class="xempty">Bu kavramda bulgu yok.</p></div>';
  return h + '<div class="phead"><div class="eyebrow">' + esc(sel[2]) + " " + yzBadge() + "</div><h1>" + esc(aiConceptName(f0, sel[1])) + '</h1><p class="lede">' + esc(aiConceptText(f0, sel[1])) +
    ' <span class="ai-sub">' + items.length + " olay</span></p></div>" +
    '<div class="ai-grid">' + items.map(function (it) { return aiCard(it, sel[1], true); }).join("") + "</div></div>";
}

/* ---- 8.2'de yeni ---- */
function pgYeni82() {
  var W = D.W82;
  if (!W) return '<div class="wrap page"><div class="phead"><h1>8.2’de yeni</h1><p class="lede">Bu sürümde karşılaştırma verisi yok.</p></div></div>';
  return '<div class="wrap page v7-yn"><div class="phead"><div class="eyebrow">Çapraz Manşet 8.2</div><h1>8.2’de yeni: güncellenen AI incelemesi neyi değiştirdi?</h1>' +
    '<p class="lede">' + esc(W.lede) + "</p></div>" +
    '<div class="yn-grid">' + W.findings.map(ynCard).join("") + "</div>" +
    '<p class="xsmall">Bütün ölçüler bir arada: <a href="#/oruntu?q=genel">Örüntüler › Genel bakış</a>. 8.1’deki veri değişiklikleri: <a href="#/yenilikler">8.1’de yeni</a>.</p></div>';
}
SECTIONS.push({ p: "/yeni82", label: "8.2’de yeni", fn: pgYeni82 });
DETAIL["/yeni82"] = { fn: pgYeni82, of: "/yeni82" };
