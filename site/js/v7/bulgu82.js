/* 8.2 "AI bulguları": every finding of the two AI passes (D.BGM media techniques, D.BG behavioural biases),
   shown alike, with what it means. "8.2'de yeni": what changed against the 8.0-event review (D.W82). */
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
function yzItems(B) {
  var out = [];
  (B ? B.events : []).forEach(function (x) {
    if (x.status !== "review_complete") return;
    bg7Live(x).forEach(function (f) { out.push({ x: x, f: f }); });
  });
  return out;
}
function yzConceptText(f, media) {
  if (media) return MEDIA_TR[f.id] || f.definition;
  var b = biasBrief(f.id, BREG, bg7k); return b ? b.text : f.definition;
}
function yzConceptName(f, media) {
  if (!media) return f.name;
  var c = MEDIA_CONCEPTS.filter(function (m) { return m.id === f.id; })[0]; return c ? c.tr : f.name;
}
function yzFindingCard(it, media) {
  var f = it.f, x = it.x, e = EV[x.event], t = yzText(f, rev7For(x, f)) || {};
  var qs = (f.evidence || []).slice(0, 3).map(function (q) {
    return "<li>“" + esc(q.q) + "”" + ((q.o || []).length ? " — " + q.o.map(function (o) { return esc(srcName(o)); }).join(", ") : "") + "</li>";
  }).join("");
  return '<article class="v7-yzf yz82-f"><p class="eyebrow">' + esc(yzConceptName(f, media)) + "</p>" +
    '<h4><a class="lnk" href="#/olay?e=' + encodeURIComponent(x.event) + '">' + esc(e ? storyLabel(e, 110) : x.title) + "</a></h4>" +
    (t.noticed ? "<p><b>" + (t.editor ? "Editör notu" : "Ne fark etti") + ".</b> " + esc(t.noticed) + "</p>" : "") +
    (qs ? "<ul>" + qs + "</ul>" : "") +
    "<p><b>Ne anlama geliyor.</b> " + esc(t.means || yzConceptText(f, media)) + "</p>" +
    (t.why ? "<p><b>Neden kesin değil.</b> " + esc(t.why) + "</p>" : "") + "</article>";
}
function pgYZ82(q) {
  q = q || {};
  var groups = [["medya", MEDIA_GROUP, bgm7(), true], ["davranis", BEHAVIOURAL_GROUP, bg7(), false]];
  var h = '<div class="wrap page v7-yz82"><div class="phead"><div class="eyebrow">Çapraz Manşet 8.2 ' + yzBadge() + "</div>" +
    "<h1>AI bulguları: en çok kurumun verdiği olaylarda ne fark edildi?</h1>" +
    '<p class="lede">En çok kurumun verdiği olayların her biri iki ayrı AI incelemesinden geçti: <b>' + MEDIA_GROUP + "</b> metnin ne yaptığına " +
    "(sözcük seçimi, etiketleme, vurgu), <b>" + BEHAVIOURAL_GROUP + "</b> başlıkların akıl yürütmesine bakar. Bulunan her şey burada; " +
    "her bulgunun yanında ne anlama geldiği ve neden kesin olmadığı yazılı. Hiçbiri insan tarafından doğrulanmadı.</p></div>";
  var sel = groups.filter(function (g) { return g[0] === q.g; })[0];
  if (sel && q.k) {
    var items = yzItems(sel[2]).filter(function (it) { return it.f.id === q.k; })
      .sort(function (a, b) { return b.x.outlets - a.x.outlets; });
    var f0 = items[0] && items[0].f;
    h += '<p><a class="lnk" href="#/yz">← Bütün kavramlar</a></p>';
    if (!f0) return h + '<p class="xempty">Bu kavramda bulgu yok.</p></div>';
    h += '<section class="sec"><h2>' + esc(yzConceptName(f0, sel[3])) + " · " + items.length + " olay</h2>" +
      '<p class="lede">' + esc(yzConceptText(f0, sel[3])) + "</p>" +
      items.map(function (it) { return yzFindingCard(it, sel[3]); }).join("") + "</section>";
    return h + "</div>";
  }
  groups.forEach(function (g) {
    var B = g[2], items = yzItems(B), by = {};
    h += '<section class="sec" id="yz-' + g[0] + '"><h2>' + esc(g[1]) + " " + yzBadge() + "</h2>";
    if (!B) { h += '<p class="rv-line">Bu inceleme bu sürümde çalıştırılmadı.</p></section>'; return; }
    var S = B.summary;
    h += '<p class="sub">' + S.completed + " / " + S.planned + " olayın incelemesi tamamlandı · " + items.length + " bulgu · " +
      new Set(items.map(function (it) { return it.x.event; })).size + " olayda en az bir bulgu.</p>";
    items.forEach(function (it) { (by[it.f.id] = by[it.f.id] || { f: it.f, n: 0, o: {} }).n++; (it.f.evidence || []).forEach(function (e) { (e.o || []).forEach(function (o) { by[it.f.id].o[o] = 1; }); }); });
    var rows = Object.keys(by).map(function (k) { return by[k]; }).sort(function (a, b) { return b.n - a.n; });
    h += rows.length ? '<div class="scroller panel"><table class="yn-t"><thead><tr><th>Kavram</th><th>Ne anlama geliyor</th><th class="r">Olay</th><th class="r">Kurum</th></tr></thead><tbody>' +
      rows.map(function (r) {
        return '<tr><td><a href="#/yz?g=' + g[0] + "&k=" + encodeURIComponent(r.f.id) + '">' + esc(yzConceptName(r.f, g[3])) + "</a></td><td>" +
          esc(yzConceptText(r.f, g[3])) + '</td><td class="r num">' + r.n + '</td><td class="r num">' + Object.keys(r.o).length + "</td></tr>";
      }).join("") + "</tbody></table></div>" : '<p class="xsmall">Tamamlanan incelemelerde bulgu yok.</p>';
    var top = items.slice().sort(function (a, b) { return b.x.outlets - a.x.outlets; }).slice(0, 6);
    if (top.length) h += "<h3>En çok kurumun verdiği olaylardan örnekler</h3>" + top.map(function (it) { return yzFindingCard(it, g[3]); }).join("");
    h += "</section>";
  });
  return h + '<p class="xsmall">Kavrama tıklayınca o kavramın bütün bulguları açılır. Bu bulgular metnin ne yaptığını tanımlar; niyet hakkında bir şey söylemez. ' +
    'Yöntem: <a href="#/yontem?s=yz">Nasıl çalışır › YZ</a> · Ne değişti: <a href="#/yeni82">8.2’de yeni</a>.</p></div>';
}
function pgYeni82() {
  var W = D.W82;
  if (!W) return '<div class="wrap page"><div class="phead"><h1>8.2’de yeni</h1><p class="lede">Bu sürümde karşılaştırma verisi yok.</p></div></div>';
  return '<div class="wrap page v7-yn"><div class="phead"><div class="eyebrow">Çapraz Manşet 8.2</div><h1>8.2’de yeni: güncellenen AI incelemesi neyi değiştirdi?</h1>' +
    '<p class="lede">' + esc(W.lede) + "</p></div>" +
    '<div class="yn-grid">' + W.findings.map(ynCard).join("") + "</div>" +
    '<p class="xsmall">Bütün bulgular: <a href="#/yz">AI bulguları</a>. 8.1’deki veri değişiklikleri: <a href="#/yenilikler">8.1’de yeni</a>.</p></div>';
}
SECTIONS.push({ p: "/yz", label: "AI bulguları", fn: pgYZ82 }, { p: "/yeni82", label: "8.2’de yeni", fn: pgYeni82 });
DETAIL["/yz"] = { fn: pgYZ82, of: "/yz" };
DETAIL["/yeni82"] = { fn: pgYeni82, of: "/yeni82" };
NAV.splice(NAV.length - 1, 0, ["/yz", "AI bulguları", []]);
