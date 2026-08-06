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
- 7 site GitHub sunucusundan 403/404 alabilir (sunucu IP engeli) — bu normal; `PROXY_URLS` secret ile çözülür. Tarama katmanı: TLS parmak izi taklidi (curl_cffi) → proxy rotasyonu → sitemap yedeği. Site 0 ürün döndürürse son bilinen ürünler API'de korunur.
- Proxy kullanımı API'yi etkilemez: proxy yalnızca tarama isteklerinde kullanılır; API, Pages + Cloudflare Worker üzerinden bağımsız çalışır.
