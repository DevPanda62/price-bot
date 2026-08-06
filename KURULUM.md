# KURULUM — kalan adımlar

Repo: https://github.com/DevPanda62/price-bot (public, yükleme tamam)
İlk tarama: BASA̧RILI — her 5 dakikada bir otomatik çalışır (https://github.com/DevPanda62/price-bot/actions)

Kalan 3 adım tarayıcıda yapılır:

## 1) GitHub Secret ekle (API + proxy)

1. https://github.com/DevPanda62/price-bot/settings/secrets/actions
2. "New repository secret" → adı: `API_SECRET_KEY` → değer: güçlü bir anahtar (PowerShell: `[System.BitConverter]::ToString((New-Object byte[] 24)).Replace('-','')` çıktısını kopyala)
3. İkinci secret: `PROXY_URLS` — **Webshare ücretsiz hesaplarından** gelen proxy URL'leri (satır veya virgülle ayrılmış):
   ```
   http://kullanici1:sifre1@host1:port
   http://kullanici2:sifre2@host2:port
   ```
   - Birden çok hesap = otomatik rotasyon: kotası dolan hesap atlanır, sonrakine geçilir (hesap başına ~900 MB, aylık otomatik sıfırlanır)
   - Tek hesap da olur (1 GB/ay); çok hesapla 5 dakika kadansı bile ücretsiz karşılanır
4. Test (PC'de): `$env:PROXY_URLS="http://kullanici:sifre@host:port"` → `python run.py --proxy-test`
5. Add secret

## 2) GitHub Pages aç (verilerin yayınlanması)

1. https://github.com/DevPanda62/price-bot/settings/pages
2. Source: **Deploy from a branch**
3. Branch: `main`, folder: `/docs` → Save
4. ~1 dakika sonra site yayında: `https://devpanda62.github.io/price-bot/`
5. Kontrol: `https://devpanda62.github.io/price-bot/api/products.json` tarayıcıda açılmalı

## 3) Cloudflare Worker (API anahtarı koruması)

1. https://dash.cloudflare.com → ücretsiz hesap aç → **Workers & Pages → Create → Worker** → ad: `firsat-api` → Deploy
2. "Edit code" → mevcut kodu sil → bu repodaki `worker/worker.js` içeriğini yapıştır → Deploy
3. **Settings → Variables**:
   - `ORIGIN` = `https://devpanda62.github.io/price-bot`
   - `API_SECRET_KEY` = 1. adımdaki anahtarın aynısı
   - `API_KEYS` = (opsiyonel) virgülle ayrılmış ek istemci anahtarları — boş bırakılabilir
4. Test:
   - Anahtarsız: `https://firsat-api.<senin-subdomain>.workers.dev/products` → **403** görünmeli
   - Anahtarlı: `https://firsat-api.<senin-subdomain>.workers.dev/products` + Header `X-API-Key: <anahtar>` → **200** ve JSON gelmeli

## Kullanılabilir uçlar (Worker + Pages altında)

| Uç | İçerik |
| --- | --- |
| /products | Tüm ürünler |
| /discounts | İndirimler (%5–%40) |
| /errors | Hatalı fiyatlar (>%40) |
| /stats | Site bazlı sayılar |
| /changes | Son tarama farkları |
| /history | Fiyat geçmişi |
| /stores/{site} | Tek site ürünleri |
| / | Site listesi |

## Güncelleme akışı (site selector değişince)

1. PC'de `scrapers/<site>.py` düzenle
2. `python build.py --linux` (dist/ yeniden şifrelenir)
3. `git add -A` → `git commit` → `git push` (dist/** değiştiği için tarama otomatik tetiklenir)

## Notlar

- Ham kaynak (`run.py`, `core/`, `scrapers/`, `build.py`) **GitHub'a yüklenmedi** — sadece bu PC'de (`C:\firsatapp\github_act`). Onları kaybedersen selector güncelleme yeteneğini kaybedersin; bot çalışmaya devam eder.
- **3 aşamalı tarama:** 1) proxysiz tarama (TLS taklidi + sitemap yedeği ile) → 2) sadece engellenen siteler proxy ile → 3) proxy de açılmazsa **Ultra Trick Mode** (saatte 1: öğrenilmiş/çoklu tarayıcı profili, HTTP/1.1 düşüşü, 2 farklı proxy grubu). İlk UTM denemesi yanıt vermezse site kalıcı olarak pas geçilir (son ürünleri API'de korunur). Sitede o an indirimli ürün olmaması ("0 ürün") engel sayılmaz.
- **Zaman planlı tarama (TR saati, `core/schedule.py` + `config.json` → `schedule`):** cron her 5 dk'da tetiklenir, `run.py` aktif pencereye göre tarama sıklığını belirler:
  - **23:00 – 01:30 (akşam):** 10 dk'da bir, proxy + UTM serbest.
  - **01:30 – 06:30 (gece):** 20 dk'da bir, proxy **KESİNLİKLE kullanılmaz**; engellenen sitede saatlik **proxysiz trick** denemesi yapılır (profil/HTTP-1.1 kandırma taktikleri, proxy harcamadan). Yanıt yoksa site **geçici pasa** girer; 06:30'dan sonra proxy ile yeniden denenir (kalıcı pas DEĞİL).
  - **06:30 – 12:00 (sabah):** 10 dk'da bir, proxy + UTM serbest.
  - **12:00 – 23:00 (gündüz):** 5 dk'da bir, proxy + UTM serbest.
  - Pencere aralığına girmeyen cron tetiklemeleri tarama yapmaz, yalnızca heartbeat günceller (Actions canlı kalır).
- **Proxy kota koruması:** proxy modundaki bir site tam taramayı 5 dk yerine `proxyEveryMinutes` (30 dk) aralığında yapar (`proxy_last` damgası); doğrulama site başı 5 ürün, 30 dakikada bir tekrarlanır (`criticalPerSite` 5, `criticalRecheckMinutes` 30); UTM saatlik denemede en fazla 16 istek (4 profil × 2 grup × 2 http11). Böylece 7 Webshare hesabının (900 MB × 7 ≈ 6.3 GB/ay) tek engelli site tarafından tüketilmesi engellenir.
- **Kategori filtresi (beyaz liste):** yalnızca elektronik (telefon, televizyon, bilgisayar, tablet, oyun konsolu, giyilebilir teknoloji) ile **erkek/unisex** giyim ve ayakkabı ürünleri indexlenir. Kadın giyimi, tüm iç çamaşırı (sütyen, külot, boxer, atlet, slip vb.), kişisel bakım, kozmetik, oyuncak, ev gereçleri ve yiyecek KESİNLİKLE taranmaz/indexlenmez. Filtre üç katmanlıdır: sitemap URL seçiminde, ürün sayfası çıkarımında ve `run.py` son kontrolünde uygulanır (`core/categories.py`). Listedeki "korunan" kategorilere uymayan her ürün (ör. kitap, mobilya) API'ye hiç girmez.
- **Kritik ürün doğrulama katmanı (gelişmiş tarama):** her taramada error (hatalı fiyat girişi) ve indirim adaylarından en kritik ürünler (önce error, sonra fiyatı değişen, sonra yeni giren; site başı en fazla 5, toplam 60) doğrudan ürün sayfasından tek istekle doğrulanır (`core/verify.py`). Ürün sayfasındaki fiyat listeden düşükse **anlık indirim** (sitenin listeye henüz yansıtmadığı indirim) olarak işaretlenir ve fiyat güncellenir; aynı ürün 30 dakikada bir (yeniden) kontrol edilir. Bu adım **proxy kullanmaz** — proxy yalnızca site zaten proxy/utm modundaysa ve gece penceresi değilse devreye girer, böylece minimum proxy harcanır. Sonuçlar `stats.json` → `critical` alanında ve run özetinde görünür.
- **Satıcı güvenilirlik katmanı:** ürün sayfası doğrulaması sırasında satıcı adı ve puanı çekilir (`core/seller.py` — JSON-LD + HTML kalıpları). Puan 5 üzerinden; **≥4.5 = güvenilir** (`seller_reliable`). Satıcısı bilinmeyen ürünler doğrulama önceliğine girer, böylece indirim/hatalı fiyat ürünlerinin tamamı zamanla satıcı bilgisi kazanır. Alanlar: `seller_name`, `seller_rating`, `seller_reliable` (null = bilinmiyor).
- **Heartbeat (uyku engelleme):** her workflow çalışması tarama sonucundan bağımsız olarak `data/heartbeat.json` + `state.json` içine zaman damgası yazar ve değişiklik varsa commit eder (`if: always()`). Böylece tarama hata verse bile run her zaman sonuçlanır ve bir sonraki run için kuyruk asla tıkanmaz.
- Proxy kullanımı API'yi etkilemez: proxy yalnızca tarama isteklerinde kullanılır; API, Pages + Cloudflare Worker üzerinden bağımsız çalışır.
