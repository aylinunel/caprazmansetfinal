# Temel modeller: anlatı kodlaması (mlbench)

İnsan kodlamasına karşı 5 katlı, olay bazında gruplanmış çapraz doğrulama; ajan sabit tahmin olarak puanlanır.

| Etiket | Model | n | Doğruluk | Makro F1 |
|---|---|---|---|---|
| blame_level | majority | 657 | 0.627 | 0.257 |
| blame_level | tfidf_logreg | 657 | 0.591 | 0.367 |
| blame_level | agent | 657 | 0.705 | 0.463 |
| frame_category | majority | 657 | 0.364 | 0.048 |
| frame_category | tfidf_logreg | 657 | 0.478 | 0.244 |
| frame_category | agent | 657 | 0.181 | 0.137 |

Çerçeve kod kitabı henüz onaylı değil (approved=false). Ajanın 657 çerçevesinden 475 tanesi kod kitabının dışında; bunlar Diğer sayılır, dolayısıyla ajanın çerçeve sayısı çoğunlukla sözcük dağarcığını yansıtır.
