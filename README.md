# Firsat API (GitHub Actions Tarama Projesi)

Trendyol, Hepsiburada, N11, CicekSepeti, MediaMarkt, Teknosa, Vatan Bilgisayar ve Amazon sitelerini tarayan, **indirimdeki urunleri ve hatali fiyat girisli urunleri** listeleyen bir GitHub Actions projesidir. Tarama **her 5 dakikada bir** tetiklenir; sonuclar statik JSON olarak GitHub Pages'te yayinlanir ve **API anahtari (X-API-Key) korumali** uc noktalar uzerinden harici projelere sunulur.

Bu proje `firsatapp` Flutter uygulamasindan tamamen bagimsizdir.

## Klasor Yapisi ve Gizlilik

```
github_act/                        <- Actions ana dizini
|-- dist/                          YUKLENIR  (Pyarmor ile obfuscate edilmis, okunamaz)
|-- .github/workflows/scraper.yml  YUKLENIR
|-- docs/                          YUKLENIR  (API JSON + Pages)
|-- worker/                        YUKLENIR  (Cloudflare Worker)
|-- api_server/                    YUKLENIR  (FastAPI)
|-- data/                          YUKLENIR
|-- config.json                    YUKLENIR  (gizli alan yok)
|-- requirements.txt               YUKLENIR
|-- README.md                      YUKLENIR
|-- .env.example                   YUKLENIR
|-- .gitignore                     YUKLENIR
|
|-- run.py            YUKLENMEZ    (ham kaynak)
|-- core/             YUKLENMEZ    (ham kaynak)
|-- scrapers/         YUKLENMEZ    (ham kaynak - site selectors'lari burada)
|-- build.py          YUKLENMEZ    (obfuscate araci)
```

- **Kaynak gizliligi:** `dist/` Pyarmor ile uretilmis obfuscate bundle'dir; `dist/run.py`, `dist/core/`, `dist/scrapers/` olarak yuklenir. `run.py`, `core/`, `scrapers/` dosyalari ise **ham kaynaktir ve asla yuklenmez** — `.gitignore` bunlari git ile push ederken otomatik engeller; web arayuzunden elle yukluyorsan bu 4 girdiyi secme.
- **Sitenin kodlari (selectors, sorgu kelimeleri):** obfuscate edilen `scrapers/*.py` icindedir; public `config.json` yalnizca zararsiz ayarlar tasir.
- **API korumasi:** Cloudflare Worker her istekte `X-API-Key` header'ini kontrol eder; gecersizse **403**. Anahtar kodda degil, ortam degiskenlerindedir.

## Kurulum (GitHub)

1. GitHub'da **public** bir repo olusturun.
2. `github_act/` klasorunun icerigini repoya yukleyin (klasor yapisini koruyarak).
   - **Git ile:** dosyalari `github_act/` icinde `git init` + `git add -A` + push edin — `.gitignore` ham kaynagi otomatik disarida birakir.
   - **Web arayuzu (tek tek):** yuklenmesi gerekenler: `dist/`, `.github/`, `docs/`, `worker/`, `api_server/`, `data/`, `config.json`, `requirements.txt`, `README.md`, `.env.example`, `.gitignore`. **Yukleme:** `run.py`, `core/`, `scrapers/`, `build.py`.
3. Repo > **Settings** > **Secrets and variables** > **Actions**: `API_SECRET_KEY` ekleyin (uzun rastgele anahtar). Opsiyonel: `PROXY_URL`.
4. Repo > **Actions** > **firsat-scan** > **Run workflow** ile ilk taramayi baslatin.
5. Repo > **Settings** > **Pages** > Deploy from a branch > `main` / `/docs` > Save.
6. Cloudflare Worker'i kurun (asagida "API Korumasi").

## Build (Kaynak Gizleme / Yeniden Uretme)

Siteler markup degistirirse `scrapers/*.py` guncellenir ve `dist/` yeniden uretilir:

```bash
pip install pyarmor

# GitHub Actions (ubuntu) hedefi icin - YUKLENECEK SURUM:
python build.py --linux

# yerel test icin (kendi platformunda):
python build.py
python dist/run.py --selftest
```

`build.py` mevcut `dist/` klasorunu silip Pyarmor ile yeniden obfuscate eder. `--linux` kullanilmazsa uretilen `dist/` Windows'ta calisir; GitHub'a linux surumu yuklenmelidir.

## API Korumasi (X-API-Key)

### 1. Cloudflare Worker (onerilen, ucretsiz, 7/24)

1. cloudflare.com > Workers & Pages > Create Worker (ad: `firsat-api`).
2. `worker/worker.js` icerigini yapistirin, Deploy.
3. Worker > Settings > Variables: secret olarak ekleyin:
   - `API_SECRET_KEY` = ana anahtar
   - `API_KEYS` = istemcilere verilecek ek anahtarlar (virgulle, istege bagli)
   - `ORIGIN` = `https://<kullanici>.github.io/<repo>` (plain variable)
4. Kullanim:

```bash
# gecerli anahtar -> 200
curl -H "X-API-Key: <anahtar>" https://<worker>.workers.dev/products

# gecersiz/eksik anahtar -> 403
curl -i https://<worker>.workers.dev/errors
```

Uc noktalar: `/products`, `/discounts`, `/errors`, `/stats`, `/changes`, `/history`, `/stores/<site>`.

### 2. FastAPI (kendi sunucunda, istege bagli)

Ayni guvenlik mantigi (`hmac.compare_digest`, 403) `api_server/` icinde FastAPI olarak mevcuttur:

```bash
API_SECRET_KEY=<anahtar> uvicorn api_server.main:app --host 0.0.0.0 --port 8000
curl -H "X-API-Key: <anahtar>" http://sunucu:8000/products
```

## Ortam Degiskenleri (`.env.example`)

| Degisken | Aciklama |
| --- | --- |
| `API_SECRET_KEY` | Ana API anahtari (Actions secret + Worker secret + FastAPI env) |
| `API_KEYS` | Ek istemci anahtarlari, virgulle ayrilmis |
| `PROXY_URL` | Opsiyonel tarama proxy'si (Actions secret) |
| `DATA_DIR` | FastAPI veri dizini (varsayilan `docs`) |
| `ORIGIN` | Worker'in Pages taban adresi |

Hicbir anahtar koda hardcoded yazilmaz.

## Gizlilik ve Limitler (durtus notlar)

- Pyarmor obfuscation "guclu engel"dir, kriptografik garanti degildir. Kesin gizlilik istiyorsaniz tek yol private repo'dur (ancak o zaman Pages calismaz ve 5 dakikalik cron kotayi ~1 haftada tuketir).
- Fork'lar `secrets` degerlerini **goremez**; workflow yalnizca schedule/manuel/push ile tetiklenir.
- GitHub Actions public repolarda **sinirsiz ucretsiz** dakika verir (github.com/docs).

## Kurallar

| Durum | Kosul |
| --- | --- |
| **Hatali fiyat girisi** (`error`) | Fiyat, diger magazalardaki fiyatina veya onceki fiyatina gore **%60+** dusukse |
| **Indirim** (`discount`) | Indirim **%59 ve alti** ise |
| **Normal** (`normal`) | Anlamli indirim yoksa |

Karsilastirma kaynaklari: `magaza-eski-fiyat`, `diger-magaza-min-fiyat` (token eslesmesi), `onceki-fiyat` (gecmis).

## Yapilandirma (`config.json`)

| Alan | Aciklama |
| --- | --- |
| `errorThreshold` / `discountThreshold` | %60 / %59 sinirlari |
| `matchTokenOverlap` | Urun eslestirme benzerligi (0.6) |
| `sites.<site>.enabled` | Site acik/kapali |
| `sites.<site>.maxPages/delay/timeout/retries` | Tarama davranisi |

## Zamanlama

`cron: '*/5 * * * *'` her 5 dakikada bir calisir. Public repoda kota siniri yoktur.

## Opsiyonel: Coklu Repo Yedekliligi

GitHub cikintilarina, site IP engellerine ve gecici hatalara karsi ayni `github_act/` icerigini 4 ayri public repoya yukleyip cron'u kaydirabilirsiniz: `*/5`, `1-59/5`, `2-59/5`, `3-59/5`. Tuketici tarafinda ilk yanit veren URL kullanilir:

```js
const urls = ["https://kullanici.github.io/firsat-api-1", "https://kullanici.github.io/firsat-api-2"];
async function get(ep, key) {
  for (const u of urls) {
    try {
      const r = await fetch(`${u}/${ep}`, { headers: { "X-API-Key": key }, signal: AbortSignal.timeout(8000) });
      if (r.ok) return r.json();
    } catch (e) { /* sonraki repoya gec */ }
  }
  return null;
}
```

## Teknik Notlar

- **Tolerans:** Tek site hatasi taramayi durdurmaz; tum siteler basarisizsa workflow hata verir.
- **Veri:** `docs/api/*` her taramada commit edilir; degisiklik yoksa commit atlanir. `data/` fiyat gecmisini tasir.
- **Sorumluluk:** Arac e-ticaret sitelerinin kullanim kosullarina tabidir; tarama sikligini ve kapsamini makul tutun.
