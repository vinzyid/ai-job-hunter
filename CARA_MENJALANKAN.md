# Cara Menjalankan AI Job Hunter dan Melihat Hasilnya

Panduan langkah demi langkah untuk macOS atau Linux. Di Windows (PowerShell), ganti `python3` dengan `python`, `source .venv/bin/activate` dengan `.venv\Scripts\activate`, dan `cp` dengan `copy`. Kalau PowerShell menolak menjalankan skrip aktivasi, jalankan sekali `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 1. Persiapan (sekali saja)

Buka Terminal di folder proyek, lalu:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

File `.env` hanya perlu diisi (`GRIPHUB_API_KEY`) kalau ingin memakai pilihan `--ai`. Tanpa key, semua perintah lain tetap jalan.

Setiap kali membuka Terminal baru, aktifkan lagi lingkungannya:

```bash
source .venv/bin/activate
```

## 2. Cara tercepat: satu perintah

```bash
python main.py semua --wilayah semua --peran backend --buka
```

Perintah ini mengambil lowongan terbaru (sekitar 1 sampai 2 menit), menghitung skill yang diminta lowongan backend, lalu membuka laporannya di browser.

## 3. Cara bertahap

| Langkah | Perintah | Hasil |
|---|---|---|
| 1. Ambil lowongan | `python main.py ambil` | `data/lowongan/lowongan.json` dan `.csv` |
| 2. Hitung skill | `python main.py skill --wilayah semua --peran backend` | tabel di Terminal dan folder `output/semua-backend/` |
| 3. Buka laporan | `python main.py laporan --wilayah semua --peran backend --buka` | laporan HTML di browser |

Saringan lain:

```bash
python main.py skill                                         # semua lowongan IT lokal (bawaan)
python main.py skill --wilayah semua --tingkat magang junior # untuk fresh graduate
python main.py skill --wilayah semua --peran data_analyst ai_ml
python main.py skill --wilayah semua --peran backend --ai    # dengan temuan AI (butuh key)
```

Kalau muncul pesan `Hanya N lowongan yang cocok`, saringannya terlalu sempit. Hapus `--tingkat` atau pakai `--wilayah semua`.

## 4. Membaca hasilnya

### a. Tabel di Terminal

```
68 lowongan cocok dengan saringan semua-backend.
  #  skill            lowongan  persen  golongan        sering bersama
  1  Python                 27   39.7%  wajib dikuasai  AWS, Agile, Java
  2  AWS                    23   33.8%  wajib dikuasai  Python, Java, GCP
```

- **lowongan / persen**: berapa lowongan yang menyebut skill itu.
- **golongan**: wajib dikuasai (30% atau lebih), sering diminta (10 sampai 30%), nilai tambah (di bawah 10%). Batasnya bisa diubah di `konfigurasi/preferensi.yaml`.
- **sering bersama**: skill yang paling sering ikut diminta di lowongan yang sama.

### b. Laporan HTML (yang utama)

Buka `output/<saringan>/laporan.html`, atau `output/index.html` untuk daftar semua laporan. Isinya, dari atas:

1. **Kepala**: skill yang harus dikuasai dulu dan angka ringkas.
2. **Skill yang diminta**: grafik batang dengan golongannya.
3. **Per kategori**: lima teratas di setiap kelompok (bahasa, basis data, cloud, dan lainnya).
4. **Sering diminta bersama**.
5. **Tren**: lowongan dua minggu terakhir dibandingkan yang lebih lama.
6. **Temuan AI** (kalau memakai `--ai`): kesimpulan dan skill di luar kamus beserta kutipan buktinya.
7. **Gambaran lowongan**: peran, tingkat, pengalaman, dan gaji.
8. **Contoh lowongan** dengan tautan ke halaman aslinya, dan **sumber data**.

### c. File di folder `output/<saringan>/`

`hasil.json` (semua angka), `skill.csv` dan `skill.xlsx` (bisa dibuka di Excel atau Google Sheets), `skill.png` (grafik), dan `laporan.html`.

## 5. Memastikan program berjalan benar

```bash
python -m pytest
```

Harus muncul `41 passed`. Tes tidak butuh internet maupun AI.

## 6. Masalah yang sering muncul

| Pesan atau gejala | Penyebab dan cara mengatasinya |
|---|---|
| `Belum ada data lowongan.` | Jalankan `python main.py ambil` dulu. |
| `Hanya N lowongan yang cocok ...` | Saringan terlalu sempit. Hapus `--tingkat` atau pakai `--wilayah semua`. |
| `GRIPHUB_API_KEY belum ada.` | Pilihan `--ai` butuh key di `.env`. Tanpa `--ai`, key tidak diperlukan. |
| `AI gagal: ...` | Layanan AI sedang lambat atau key salah. Coba lagi, atau pakai `--model deepseek-v4.1-flash` (model tercepat). |
| `ModuleNotFoundError` | Lingkungan belum aktif. Jalankan `source .venv/bin/activate`. |
| Lowongan yang kemarin ada sekarang hilang | Lowongan itu sudah tutup dan dibuang otomatis. Alasannya tercatat di `data/lowongan/arsip_tutup.jsonl`. |
