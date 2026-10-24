# Yeni kurs içeriği — yazım kılavuzu (ajanlar için)

Uygulama "Lingvara": Iskra adlı beyaz yavru ejderhanın krallıkları kurtardığı bir dil öğrenme oyunu. Arayüz Türkçe kaynaklı (sonra 9 dile çevrilir). Rusça kursu hazır (`content_src/<SEVİYE>/*.txt`, örnek olarak bakabilirsin). Şimdi 4 yeni kurs yazılıyor:

| Kod | Dil | Krallık | Klasör |
|---|---|---|---|
| en | İngilizce | Sis Adaları | `content_src/courses/en/` |
| es | İspanyolca | Güneş Krallığı | `content_src/courses/es/` |
| de | Almanca | Orman Kalesi | `content_src/courses/de/` |
| fr | Fransızca | Lavanta Vadisi | `content_src/courses/fr/` |

## Kelime dosyaları: `<kurs>/<SEVİYE>/NN.txt`
```
# UNIT: Türkçe ünite başlığı | Türkçe alt başlık (konular, virgülle)
## Türkçe ders başlığı          ← her ## yeni ders: TAM 10 satır
hedef dil | türkçe anlam | tür | Hedef dilde örnek cümle. | Türkçe çevirisi.
```
- Her dosya = 1 ünite = **10 ders × 10 satır = 100 satır** (A0 hariç, aşağıya bak).
- Alanlar ` | ` ile ayrılır, **tam 5 alan**, hiçbiri boş değil, satırda başka `|` yok.
- Vurgu işareti (`) ve Kiril harf YOK. Hedef dilin kendi harfleri doğru kullanılmalı (é, è, ç, ñ, á, ü, ö, ä, ß, ¿, ¡…).
- **1. alan (kelime):** sözlük biçimi.
  - İsimler artikelle: de `der Hund (die Hunde)`, fr `le chien`, `la maison`, `l'arbre (m)`, es `el perro`, `la casa`, en artikelsiz `dog`.
  - Düzensiz biçimler parantezde: en `go (went, gone)`, `child (children)`; de `gehen (ging, gegangen)`; fr/es gerekirse `faire (fait)`.
  - Başka parantez kullanma. Küçük harf (Almanca isimler ve özel isimler büyük).
- **2. alan:** Türkçe anlam, kısa; iki anlam varsa `;` ile.
- **3. alan (tür), yalnızca şu değerler:** `isim`, `isim (e)`, `isim (d)`, `isim (o)`, `isim (çoğul)`, `fiil`, `fiil · düzensiz`, `fiil · dönüşlü`, `sıfat`, `zarf`, `zamir`, `edat`, `bağlaç`, `ünlem`, `ifade`, `deyim`, `atasözü`, `sayı`, `phrasal verb`, `harf · sesli`, `harf · ünsüz`, `ses`.
  - de/fr/es isimlerinde cinsiyet: (e) eril, (d) dişil, (o) nötr (yalnızca de).
- **4. alan:** doğal, günlük, seviyeye uygun örnek cümle, kelimeyi içerir. A1: 3–7 kelime; B: 7–14; C: 8–18.
- **5. alan:** örneğin doğal Türkçe çevirisi (ç ğ ı İ ö ş ü doğru).
- Kişi adları uluslararası ve çeşitli (Anna, Emre, Maria, Ali, Yuki, Omar, Sofia, Lukas, Camille, Diego…). Gerçek ünlü kişi, marka, siyasi görüş yok. Din/siyaset konularında tarafsız, saygılı. Küfür ve hakaret yok.
- Aynı kurs içinde aynı kelime iki kez geçmesin. Alt seviyelerin temel kelimelerini üst seviyelerde tekrar etme.
- Seviye: CEFR sıklık mantığı (A1 en sık ~800 kelime, A2 sonraki ~1200, B1 ~1500, B2 ~2000, C1 ~2200, C2 ~2300).
- Konular kursun kültürüne uyarlanır (yemekler, şehirler, gelenekler o dilin dünyasından; ama evrensel konular da kalır).

## A0 dosyası: `<kurs>/A0/01.txt` (3 ünite, 12 ders, 120 satır)
1. `# UNIT: <Dil> alfabesi | …` — 3 ders. 1. alan harf (`A a`; dile özgü harfler dahil: ñ, ç, ä/ö/ü/ß, é/è/ê…), 2. alan Türkçe okunuş ipucu, tür `harf · sesli`/`harf · ünsüz`, 4. alan TEK basit örnek kelime (seslendirilen budur), 5. alan anlamı. Harfler 30'u doldurmazsa dile özgü işaretler/aksanlar eklenir.
2. `# UNIT: Zor sesler | …` — 4 ders. 1. alan ses/harf grubu (en: th, w, sh…; de: ch, sch, ei, ie, eu, z…; fr: ou, eau, an/on/in, gn, sessiz son harfler…; es: rr, ll, j, ce/ci, h…), tür `ses`, 4. alan TEK kısa örnek kelime veya 2–3 kelimelik ifade.
3. `# UNIT: İlk kelimeler | …` — 5 ders, normal kelime satırları (sayılar 1–10, renkler, birkaç nesne ve hayvan). Bunlar A1'de tekrar edilmez.

## Diyalog: `<kurs>/dialog/<SEVİYE>.txt` (A0…C2, her biri 4 bölüm × 10 satır)
```
# DIALOG: Türkçe başlık | Türkçe alt başlık | Konuşmacı1 adı | Konuşmacı2 adı
## Türkçe bölüm başlığı
A | hedef dilde cümle | Türkçe çevirisi
B | hedef dilde cümle | Türkçe çevirisi
```
Tam 4 bölüm, her bölüm tam 10 satır, konuşmacı harfi Latin `A` / `B`. Seviyeye uygun uzunluk.

## Dilbilgisi: `<kurs>/grammar/<SEVİYE>.txt` (A0 4 konu, diğerleri 6 konu)
```
# TOPIC: Türkçe konu başlığı | kısa hedef dil örnekleri
> Türkçe açıklama paragrafı (1–3 satır, her biri > ile)
= hedef dil örnek | Türkçe çevirisi       (en az 3)
? Türkçe soru veya boşluklu cümle | DOĞRU cevap | yanlış | yanlış      (tam 5 soru)
```
Soru satırında ilk seçenek doğru olandır; seçenekler birbirinden farklı.

## Dikkat
- Yalnızca sana verilen dosyaları yaz. git çalıştırma, başka dosyaya dokunma.
- Bitince kelime dosyaların için: `python3 tool/check_course.py <kurs> <dosyalar>` → hata kalmayana dek düzelt.
- Kısa rapor: dosyalar, ünite başlıkları.

## Ek kurslar (ikinci dalga)

| Kod | Dil | Krallık | Not |
|---|---|---|---|
| it | İtalyanca | Zeytin Tepeleri | İsimler artikelle: `il gatto`, `la casa`, `l'albero (e)` |
| pt | Portekizce (Brezilya) | Yağmur Ormanı | Brezilya Portekizcesi; `o gato`, `a casa` |
| ja | Japonca | Kiraz Çiçeği Adası | Aşağıya bak |
| ko | Korece | Ay Sarayı Dağları | Aşağıya bak |
| zh | Çince (Mandarin, basitleştirilmiş) | Yeşim Krallığı | Aşağıya bak |
| tr | Türkçe | Peri Bacaları Krallığı | Aşağıya bak |
| ar | Arapça (Modern Standart, fusha) | Çöl Yıldızı Krallığı | Aşağıya bak |

### Latin olmayan yazılar (ja, ko, zh, ar)
- **1. alan:** kelime kendi yazısıyla + parantez içinde okunuş: ja `ありがとう (arigatō)`, kanjili kelimelerde `先生 (sensei)`; ko `감사합니다 (gamsahamnida)`; zh `谢谢 (xièxie)` (pinyin tonlu); ar harekeli `شُكْرًا (shukran)`. Seviye ilerledikçe ja/zh'de kanji/hanzi kullan.
- **4. alan (örnek):** kendi yazısıyla. A0–A2 seviyelerinde örneğin sonuna okunuşu parantezle ekle: `ありがとうございます。(Arigatō gozaimasu.)`. B1 ve üstünde okunuş yok.
- ja: A1'den itibaren temel kanji + furigana yerine okunuş parantezi. ko: hangıl. zh: basitleştirilmiş karakterler. ar: A0–A2'de tam hareke, sonra yalnızca gerektiğinde.
- **A0:** 1. ünite ve 2. ünite yazı kartlarıdır (12 dersin dağılımı: 1. ünite 5 ders, 2. ünite 5 ders, 3. ünite 2 ders olabilir; toplam 12 ders × 10 satır).
  - ja: 1. ünite Hiragana, 2. ünite Katakana, 3. ünite İlk kelimeler.
  - ko: 1. ünite Hangıl sesli harfler ve ünsüzler, 2. ünite Hece blokları ve son ünsüz (batchim), 3. ünite İlk kelimeler.
  - zh: 1. ünite Pinyin ve tonlar, 2. ünite Temel karakterler ve köklər, 3. ünite İlk kelimeler.
  - ar: 1. ünite Harfler (28 harf, başta-ortada-sonda), 2. ünite Harekeler ve uzun ünlüler, 3. ünite İlk kelimeler.
  - Harf/hece kartında 1. alan harf/hece (`あ (a)`, `ㄱ (g/k)`, `mā (1. ton)`, `ب (b)`), 4. alan TEK basit örnek kelime (okunuşuyla).
- Denetim aracı Latin harf istemez; alan/ders sayıları yine denetlenir.

### Türkçe kursu (tr) — ÖZEL
Türkçe kursu Türkçe konuşanlara gösterilmez; dünyaya Türkçe öğretir. Bu yüzden **anlam ve çeviri alanları (2. ve 5. alan) ile ünite/ders başlıkları İNGİLİZCE** yazılır (kaynak dili İngilizce). Tür (3. alan) yine Türkçe listeden. A0: Türk alfabesi (ç, ğ, ı, ö, ş, ü dahil), ünlü uyumu ve özel sesler, ilk kelimeler. Dilbilgisi açıklamaları ve soruları da İngilizce.
