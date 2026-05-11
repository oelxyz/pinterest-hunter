# 🎯 Pinterest Hunter

> Cari Pinterest username yang sudah **expired/tidak aktif** dan masih punya **backlink** — ideal untuk SEO redirect, brand acquisition, atau riset kompetitor.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Async](https://img.shields.io/badge/Async-aiohttp-orange)
![No API Key](https://img.shields.io/badge/API%20Key-Not%20Required-brightgreen)

---

## 📸 Preview

```
⚙  Preparing username list…
   ✓ 100 usernames queued

🚀 Starting scan…
   Concurrency: 10 | Timeout: 15s | Delay: 0.5s | Backlinks: YES

  ✓ EXPIRED zonereal      | backlinks: 2 | score: 30 💤 LOW
  ✓ EXPIRED gallery2010   | backlinks: 1 | score: 10 💤 LOW
  ✓ EXPIRED shop_aurora   | backlinks: 0 | score: 15 💤 LOW

┏━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃  Rank ┃ Username     ┃ Pinterest URL                       ┃  HTTP  ┃ Backlinks  ┃  Score  ┃ Tier     ┃
┡━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│     1 │ zonereal     │ https://www.pinterest.com/zonereal/ │  200   │     2      │   30    │ 💤 LOW   │
│     2 │ shop_aurora  │ https://www.pinterest.com/shop_...  │  200   │     0      │   15    │ 💤 LOW   │
│     3 │ gallery2010  │ https://www.pinterest.com/galle...  │  200   │     1      │   10    │ 💤 LOW   │
└───────┴──────────────┴─────────────────────────────────────┴────────┴────────────┴─────────┴──────────┘

✔ Full results saved → results.json
✔ Expired CSV saved  → results_expired.csv (18 rows)
```

---

## ✨ Fitur

| Fitur | Detail |
|---|---|
| **Smart Detection** | Pinterest selalu return HTTP 200 — tool ini baca body HTML untuk deteksi akun mati |
| **Wayback Machine** | Cek arsip CDX untuk backlink historis |
| **CommonCrawl Index** | Cek rekaman crawl CC-MAIN terbaru |
| **Value Scorer** | Skor 0–100: backlink count + panjang username + keyword niche |
| **Wordlist Cerdas** | Generator bawaan 4 strategi: old-web, name+year, underscore combo, random short |
| **Wordlist Kustom** | Bisa pakai file wordlist sendiri |
| **Export** | JSON (full data) + CSV (expired only, Excel-ready) |
| **Rich UI** | Progress bar real-time, tabel berwarna, banner ASCII |
| **No API Key** | Semua sumber gratis, tidak butuh akun atau API key apapun |

---

## ⚙️ Instalasi

**Requirement:** Python 3.10+

```bash
# 1. Clone repo
git clone https://github.com/username/pinterest-hunter.git
cd pinterest-hunter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan
python3 pinterest_hunter.py --count 100 --verbose
```

---

## 🚀 Penggunaan

```bash
# Scan 100 username otomatis (default)
python3 pinterest_hunter.py

# Scan lebih banyak dengan output verbose
python3 pinterest_hunter.py --count 300 --verbose

# Pakai wordlist sendiri
python3 pinterest_hunter.py --wordlist usernames.txt

# Scan cepat tanpa cek backlink
python3 pinterest_hunter.py --count 500 --no-backlinks --concurrency 20

# Tambah prefix / suffix ke semua kandidat
python3 pinterest_hunter.py --count 200 --prefix my --suffix shop

# Simpan ke file output kustom
python3 pinterest_hunter.py --count 100 --output hasil.json
```

---

## 🔧 Opsi Lengkap

| Flag | Shorthand | Default | Keterangan |
|---|---|---|---|
| `--wordlist FILE` | `-w` | — | Wordlist kustom, 1 username per baris |
| `--count N` | `-n` | `100` | Jumlah username yang di-generate |
| `--prefix STR` | — | — | Tambah prefix ke semua kandidat |
| `--suffix STR` | — | — | Tambah suffix ke semua kandidat |
| `--length-min N` | — | `3` | Panjang minimum username |
| `--length-max N` | — | `15` | Panjang maksimum username |
| `--concurrency N` | `-c` | `10` | Jumlah request paralel |
| `--timeout SEC` | `-t` | `15` | Timeout per request (detik) |
| `--delay SEC` | `-d` | `0.5` | Jeda antar request per worker |
| `--no-backlinks` | — | — | Skip pengecekan backlink (lebih cepat) |
| `--output FILE` | `-o` | `results.json` | Path output JSON |
| `--verbose` | `-v` | — | Tampilkan hit expired langsung di terminal |

---

## 📊 Output

### `results.json`
Berisi semua data lengkap — aktif, expired, error — beserta detail backlink dan skor.

### `results_expired.csv`
Hanya username yang expired, diurutkan dari skor tertinggi. Selalu dibuat meski 0 hasil.

**Kolom CSV:**

| Kolom | Keterangan |
|---|---|
| `username` | Username Pinterest |
| `url` | URL profil lengkap |
| `http_code` | HTTP status code |
| `status` | `expired` / `active` / `error` / `unknown` |
| `note` | Penjelasan singkat hasil deteksi |
| `backlinks_total` | Total backlink ditemukan |
| `wayback_count` | Jumlah rekaman Wayback Machine |
| `commoncrawl_count` | Jumlah rekaman CommonCrawl |
| `score` | Skor nilai username (0–100) |
| `tier` | HIGH / MEDIUM / LOW |
| `reasons` | Alasan scoring |
| `checked_at` | Waktu pengecekan (UTC) |

---

## 🏆 Sistem Scoring

| Skor | Tier | Kriteria |
|---|---|---|
| 70–100 | 🔥 HIGH | Username pendek (≤6 char) + banyak backlink + keyword niche |
| 40–69 | ⚡ MEDIUM | Ada backlink dan/atau keyword bernilai |
| 0–39 | 💤 LOW | Expired, tapi minim backlink dan tidak ada keyword khusus |

**Faktor scoring:**
- +10–50 poin → jumlah backlink (max 50)
- +20 poin → username ≤ 6 karakter
- +10 poin → username ≤ 10 karakter
- +15 poin → mengandung keyword bernilai (`shop`, `brand`, `travel`, `beauty`, dll.)
- +15 poin → 5+ snapshot di Wayback Machine

---

## 🔍 Cara Deteksi Expired

Pinterest **selalu mengembalikan HTTP 200** untuk semua URL profil, termasuk yang tidak ada.  
Tool ini mendeteksi akun mati dengan cara membaca konten HTML:

- ✅ Ada `"User not found"` di body → **expired**
- ✅ Tidak ada `"username"` + `"full_name"` di data JSON embedded → **expired**
- ✅ Ada teks deaktivasi/suspensi → **expired**
- ❌ Ada data user lengkap → **active**

---

## 🌐 Sumber Backlink

| Sumber | Endpoint | API Key |
|---|---|---|
| **Wayback Machine** | `web.archive.org/cdx/search` | Tidak perlu |
| **CommonCrawl** | `index.commoncrawl.org/CC-MAIN-2024-10-index` | Tidak perlu |

---

## ⚠️ Tips Penggunaan

- Gunakan `--delay 1.0` atau lebih untuk scan jangka panjang agar tidak kena rate limit
- `--concurrency 5` lebih aman daripada default saat scan ratusan username
- Wordlist dari niche spesifik (fashion, food, travel) menghasilkan hit lebih berharga
- Username dengan tahun lama (`2010`–`2015`) dan nama orang memiliki expired rate lebih tinggi
- Jalankan dengan `--no-backlinks` dulu untuk screening cepat, lalu scan ulang yang menarik saja

---

## 📁 Struktur File

```
pinterest-hunter/
├── pinterest_hunter.py   # Tool utama
├── requirements.txt      # Dependencies Python
└── README.md             # Dokumentasi ini
```

---

## 📄 License

MIT — bebas digunakan, dimodifikasi, dan didistribusikan.
