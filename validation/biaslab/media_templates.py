"""Authored Turkish cases for the media-technique concepts ("Medyanın oyunları").

Each variant gives the same invented event twice: once showing the technique ("pos") and once in
plain wording ("plain"). Where the concept compares outlets, a second outlet line ("b_*") is given.
The quoted control is generated: a named speaker says the loaded wording and the outlet reports it.

These cases are invented, not real news. Which rendering a simulated agent gets is decided by the
Mesa mechanism (whether it was active); the wording itself is authored here, so a lab result on these
cases says how the detector handles these sentences and nothing more.
"""
from __future__ import annotations

T = {
 "ad_hominem": [
  {"event": "Bütçe eleştirisi", "speaker": "İktidar sözcüsü",
   "pos": "Sicili bozuk vekil yine konuştu — Geçmişi tartışmalı milletvekili, bütçedeki açığın büyüdüğünü öne sürdü.",
   "plain": "Milletvekili: Bütçe açığı büyüdü — Vekil, açığın geçen yıla göre arttığını söyledi; Bakanlık rakamı doğrulamadı."},
  {"event": "İmar planı tartışması", "speaker": "Muhalefet sözcüsü",
   "pos": "Kendi evi kaçak olan başkan imar dersi veriyor — Başkan, yeni planın yeşil alanı koruyacağını savundu.",
   "plain": "Başkan: Yeni plan yeşil alanı koruyacak — Meclis üyeleri plana ilişkin itirazlarını pazartesi sunacak."}],
 "causal_overclaim": [
  {"event": "Suç istatistikleri açıklandı", "speaker": "Vali yardımcısı",
   "pos": "Yeni kameralar hırsızlığı bitirdi — Kameraların takıldığı ay hırsızlık ihbarları azaldı.",
   "plain": "Kameraların takıldığı ay hırsızlık ihbarları azaldı — Emniyet, düşüşün nedenine ilişkin bir değerlendirme yapmadı."},
  {"event": "Okul başarı verileri", "speaker": "İl müdürü",
   "pos": "Tablet dağıtımı notları yükseltti — Tabletlerin dağıtıldığı dönemde sınav ortalaması arttı.",
   "plain": "Tabletlerin dağıtıldığı dönemde sınav ortalaması arttı — Müdürlük, artışın nedenini henüz incelemediğini bildirdi."}],
 "cherry_picking": [
  {"event": "Aylık ekonomi verileri", "speaker": "Bakan",
   "ctx": "Aynı bültende: ihracat aylık yüzde 4 arttı; ithalat yüzde 9 arttı; dış ticaret açığı yüzde 15 büyüdü.",
   "pos": "Ekonomi uçuşa geçti: ihracat yüzde 4 arttı — Bülten, ekonominin güçlendiğini gösterdi.",
   "plain": "İhracat yüzde 4, ithalat yüzde 9 arttı — Dış ticaret açığı aynı ayda yüzde 15 büyüdü."},
  {"event": "Turizm verileri", "speaker": "Dernek başkanı",
   "ctx": "Aynı raporda: temmuzda ziyaretçi sayısı yüzde 6 arttı; yılın ilk yedi ayında yüzde 8 azaldı.",
   "pos": "Turizm rekora koşuyor: temmuzda ziyaretçi yüzde 6 arttı — Rapor sektörün toparlandığını ortaya koydu.",
   "plain": "Temmuzda ziyaretçi yüzde 6 arttı, yedi ayda yüzde 8 azaldı — Rapor iki rakamı birlikte verdi."}],
 "consequence_framing": [
  {"event": "Merkez Bankası faiz kararı", "speaker": "Ekonomist",
   "pos": "Krediler pahalanacak, ev almak zorlaşacak — Kurul bugün politika faizini bir puan artırdı.",
   "plain": "Merkez Bankası faizi bir puan artırdı — Karar oy çokluğuyla alındı."},
  {"event": "Otoyol ihalesi", "speaker": "Oda başkanı",
   "pos": "Yol bitince bölgeye yatırım yağacak — İhale dün sonuçlandı.",
   "plain": "Otoyol ihalesi sonuçlandı — Yapım süresi üç yıl olarak açıklandı."}],
 "emphasis_framing": [
  {"event": "Asgari ücret açıklandı", "speaker": "Sendika başkanı",
   "pos": "Milyonlarca işçiye zam: asgari ücret yüzde 30 arttı — Yeni ücret ocakta geçerli olacak.",
   "b_pos": "İşverene yeni yük: işçilik maliyeti yüzde 30 arttı — Yeni ücret ocakta geçerli olacak.",
   "plain": "Asgari ücret yüzde 30 arttı — Yeni ücret ocakta geçerli olacak.",
   "b_plain": "Asgari ücret yüzde 30 arttı — Yeni ücret ocakta geçerli olacak."},
  {"event": "Baraj projesi onaylandı", "speaker": "Köy muhtarı",
   "pos": "Baraj 200 bin haneye elektrik sağlayacak — Proje kurulda onaylandı.",
   "b_pos": "Baraj üç köyü sular altında bırakacak — Proje kurulda onaylandı.",
   "plain": "Baraj projesi kurulda onaylandı — Proje 200 bin haneye elektrik sağlayacak, üç köy taşınacak.",
   "b_plain": "Baraj projesi kurulda onaylandı — Proje 200 bin haneye elektrik sağlayacak, üç köy taşınacak."}],
 "episodic_framing": [
  {"event": "Maden kazası", "speaker": "Sendika temsilcisi",
   "ctx": "Kayıtlara göre aynı havzada son beş yılda 14 kaza oldu; denetim raporları üç kez eksiklik bildirdi.",
   "pos": "Madende talihsiz kaza: bir işçi yaralandı — Olay vardiya değişimi sırasında yaşandı.",
   "plain": "Havzada beş yılda 15. kaza: bir işçi yaralandı — Denetim raporları üç kez eksiklik bildirmişti."},
  {"event": "Okul servisi kazası", "speaker": "Veli derneği",
   "ctx": "İl verilerine göre bu yıl servis araçları 22 kazaya karıştı; araçların üçte biri denetimden geçmedi.",
   "pos": "Servis şoförünün dalgınlığı pahalıya patladı — Kazada iki öğrenci hafif yaralandı.",
   "plain": "Bu yıl 23. servis kazası: iki öğrenci hafif yaralandı — Araçların üçte biri denetimden geçmemişti."}],
 "false_dilemma": [
  {"event": "Kentsel dönüşüm tartışması", "speaker": "Belediye başkanı",
   "ctx": "Mecliste üç öneri sunuldu: yıkıp yeniden yapma, güçlendirme ve kademeli taşınma.",
   "pos": "Ya yıkım ya felaket: başka yol yok — Meclis mahalle için karar verecek.",
   "plain": "Meclis üç öneriyi görüşecek — Yıkım, güçlendirme ve kademeli taşınma seçenekleri masada."},
  {"event": "Su kesintisi planı", "speaker": "Genel müdür",
   "ctx": "Kurum raporunda dört önlem yer aldı: kesinti, basınç düşürme, tarımsal kısıtlama ve kaçak onarımı.",
   "pos": "Tek çare kesinti: ya susuz kalacağız ya musluklar kapanacak — Kurum planını açıkladı.",
   "plain": "Kurum dört önlem açıkladı — Kesinti, basınç düşürme, tarımsal kısıtlama ve kaçak onarımı değerlendiriliyor."}],
 "fear_appeal": [
  {"event": "Deprem araştırması yayımlandı", "speaker": "Bir yorumcu",
   "pos": "Kâbus senaryosu: şehir her an yerle bir olabilir — Araştırma, 30 yıl içinde büyük deprem olasılığını yüzde 2 olarak hesapladı.",
   "plain": "Araştırma: 30 yılda büyük deprem olasılığı yüzde 2 — Çalışma üniversitenin yer bilimleri bölümünce yayımlandı."},
  {"event": "Gıda denetimi sonuçları", "speaker": "Dernek sözcüsü",
   "pos": "Sofradaki zehir alarmı: tehlike çanları çalıyor — Denetlenen 400 üründen birinde sınır değer aşıldı.",
   "plain": "400 üründen birinde sınır değer aşıldı — Ürün raflardan toplatıldı."}],
 "labeling": [
  {"event": "İş insanı gözaltına alındı", "speaker": "Savcılık kaynakları",
   "pos": "Holding patronu gözaltında — Soruşturma ihale kayıtlarıyla ilgili.",
   "b_pos": "Saygın iş insanı ifadeye çağrıldı — Soruşturma ihale kayıtlarıyla ilgili.",
   "plain": "Şirketin yönetim kurulu başkanı gözaltına alındı — Soruşturma ihale kayıtlarıyla ilgili.",
   "b_plain": "Şirketin yönetim kurulu başkanı gözaltına alındı — Soruşturma ihale kayıtlarıyla ilgili."},
  {"event": "Yürüyüşe polis müdahalesi", "speaker": "Valilik",
   "pos": "Provokatörler caddeyi kapattı — Yürüyüş öğle saatlerinde başladı.",
   "b_pos": "Hak arayan gençler caddede — Yürüyüş öğle saatlerinde başladı.",
   "plain": "Yürüyüşe katılanlar caddeyi trafiğe kapattı — Yürüyüş öğle saatlerinde başladı.",
   "b_plain": "Yürüyüşe katılanlar caddeyi trafiğe kapattı — Yürüyüş öğle saatlerinde başladı."}],
 "loaded_language": [
  {"event": "Belediye bütçesi görüşüldü", "speaker": "Meclis üyesi",
   "pos": "Skandal bütçe: rezalet rakamlar meclisten geçti — Bütçe 18 kabul, 12 ret oyuyla onaylandı.",
   "plain": "Bütçe 18 kabul, 12 ret oyuyla onaylandı — Görüşmeler dört saat sürdü."},
  {"event": "Yeni hastane açıldı", "speaker": "Parti il başkanı",
   "pos": "Müjde: tarihi eser gibi dev hastane hizmette — 300 yataklı hastane hasta kabulüne başladı.",
   "plain": "300 yataklı hastane hasta kabulüne başladı — Açılış töreni yarın yapılacak."}],
 "metaphorical_framing": [
  {"event": "Döviz kurunda yükseliş", "speaker": "Analist",
   "pos": "Dolar tsunamisi kıyıya vurdu, piyasada savaş hali — Kur gün içinde yüzde 3 yükseldi.",
   "plain": "Dolar kuru gün içinde yüzde 3 yükseldi — Merkez Bankası açıklama yapmadı."},
  {"event": "Sınır kapısında yoğunluk", "speaker": "Dernek başkanı",
   "pos": "Sınırda göç seli: kasaba kuşatma altında — Kapıdan bir haftada 4 bin kişi geçti.",
   "plain": "Sınır kapısından bir haftada 4 bin kişi geçti — Geçişler geçen aya göre arttı."}],
 "responsibility_framing": [
  {"event": "Köprüde çökme", "speaker": "Muhalefet lideri",
   "ctx": "Savcılık soruşturma başlattı; bilirkişi raporu henüz hazırlanmadı.",
   "pos": "Müteahhit köprüyü çökertti — Çökmede iki araç hasar gördü.",
   "plain": "Köprünün bir bölümü çöktü, savcılık soruşturma başlattı — Çökmede iki araç hasar gördü."},
  {"event": "Hastanede yangın", "speaker": "Sendika",
   "ctx": "İtfaiye raporu bekleniyor; idari inceleme sürüyor.",
   "pos": "Başhekimin ihmali yangına yol açtı — Yangında yaralanan olmadı.",
   "plain": "Hastanede yangın çıktı, inceleme sürüyor — Yangında yaralanan olmadı."}],
 "spin": [
  {"event": "İşsizlik verileri açıklandı", "speaker": "Parti sözcüsü",
   "ctx": "Bültende: işsizlik oranı yüzde 9,8'den 9,6'ya indi; genç işsizliği yüzde 17'den 19'a çıktı.",
   "pos": "Müjdeli tablo: başarılı ekonomi yönetimi işsizliği eritti, oran 9,6 — Veriler bugün açıklandı.",
   "b_pos": "İşsizlik yüzde 9,6'ya indi, genç işsizliği yüzde 19'a çıktı — Veriler bugün açıklandı.",
   "plain": "İşsizlik yüzde 9,6'ya indi, genç işsizliği yüzde 19'a çıktı — Veriler bugün açıklandı.",
   "b_plain": "İşsizlik yüzde 9,6'ya indi, genç işsizliği yüzde 19'a çıktı — Veriler bugün açıklandı."},
  {"event": "Toplu ulaşım zammı", "speaker": "Belediye sözcüsü",
   "ctx": "Kararda: tam bilet yüzde 25 arttı; öğrenci bileti değişmedi.",
   "pos": "Beceriksiz yönetimden vatandaşa darbe: fahiş zam yüzde 25 — Karar meclisten geçti.",
   "b_pos": "Tam bilet yüzde 25 arttı, öğrenci bileti değişmedi — Karar meclisten geçti.",
   "plain": "Tam bilet yüzde 25 arttı, öğrenci bileti değişmedi — Karar meclisten geçti.",
   "b_plain": "Tam bilet yüzde 25 arttı, öğrenci bileti değişmedi — Karar meclisten geçti."}],
 "strawman": [
  {"event": "Trafik düzenlemesi önerisi", "speaker": "Esnaf odası başkanı",
   "ctx": "Önerinin metni: Merkezdeki iki caddede hafta sonları araç girişi 10.00–18.00 arasında sınırlandırılsın.",
   "pos": "Arabayı tamamen yasaklamak istiyorlar: esnaf batacak — Öneri mecliste görüşülecek.",
   "plain": "İki caddede hafta sonu araç girişine saat sınırı önerildi — Öneri mecliste görüşülecek."},
  {"event": "Müfredat değişikliği önerisi", "speaker": "Veli temsilcisi",
   "ctx": "Kurul önerisi: Seçmeli derslerin haftalık saati ikiden üçe çıkarılsın.",
   "pos": "Matematiği kaldırıp herkesi seçmeliye mahkûm edecekler — Öneri kurula sunuldu.",
   "plain": "Seçmeli derslerin haftalık saatinin üçe çıkarılması önerildi — Öneri kurula sunuldu."}],
 "thematic_framing": [
  {"event": "Kadın cinayeti davası", "speaker": "Platform sözcüsü",
   "pos": "Bu yıl 280. kadın cinayeti: koruma kararı uygulanmamıştı — Sanık hakkında ağırlaştırılmış müebbet istendi.",
   "plain": "Sanık hakkında ağırlaştırılmış müebbet istendi — Duruşma gelecek aya ertelendi."},
  {"event": "Sel baskını", "speaker": "Meteoroloji uzmanı",
   "pos": "On yılda dördüncü sel: dere yatağındaki yapılaşma sürüyor — Baskında 40 ev su altında kaldı.",
   "plain": "Baskında 40 ev su altında kaldı — Ekipler tahliye çalışması yaptı."}],
 "word_choice": [
  {"event": "Elektrik tarifesi değişti", "speaker": "Kurum başkanı",
   "pos": "Elektriğe zam geldi — Yeni tarife ay başında yürürlüğe girecek.",
   "b_pos": "Elektrikte fiyat güncellemesi yapıldı — Yeni tarife ay başında yürürlüğe girecek.",
   "plain": "Elektrik tarifesi yüzde 12 arttı — Yeni tarife ay başında yürürlüğe girecek.",
   "b_plain": "Elektrik tarifesi yüzde 12 arttı — Yeni tarife ay başında yürürlüğe girecek."},
  {"event": "Gazete binasında arama", "speaker": "Emniyet",
   "pos": "Gazeteye şafak baskını — Arama savcılık talimatıyla yapıldı.",
   "b_pos": "Gazete binasında operasyon — Arama savcılık talimatıyla yapıldı.",
   "plain": "Gazete binasında arama yapıldı — Arama savcılık talimatıyla yapıldı.",
   "b_plain": "Gazete binasında arama yapıldı — Arama savcılık talimatıyla yapıldı."}],
}
