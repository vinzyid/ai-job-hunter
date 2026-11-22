# AI Job Hunter: Skill Apa yang Diminta Lowongan IT?

Proyek UTS Praktik Scripting Language (Mini Project: Automation Scripting Language).

**Masalah.** Pencari kerja IT, terutama fresh graduate, sering belajar skill yang belum tentu dicari perusahaan. Membaca ratusan lowongan satu per satu untuk mengetahui skill yang diminta butuh waktu berhari-hari.

**Solusi otomasi.** Program Python ini mengambil lowongan IT dari lima API publik, membuang lowongan yang sudah tutup, membaca skill yang disebut di setiap lowongan, lalu menghitung skill mana yang paling banyak diminta. Hasilnya bisa disaring per wilayah (lokal atau internasional), peran (backend, frontend, data, dan lainnya), dan tingkat (magang sampai pimpinan). Yang menentukan skill adalah isi lowongan, bukan CV pengguna.

## Menyiapkan lingkungan

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # hanya perlu diisi kalau memakai --ai
```

Di Windows (PowerShell): `python -m venv .venv`, lalu `.venv\Scripts\activate`, dan `copy .env.example .env`.

## Menjalankan program

```bash
python main.py ambil                                    # ambil lowongan terbaru dari API publik
python main.py skill                                    # skill yang diminta semua lowongan IT lokal
python main.py skill --wilayah semua --peran backend    # hanya lowongan backend, lokal dan internasional
python main.py skill --peran frontend --tingkat magang junior --wilayah semua
python main.py skill --wilayah semua --peran backend --ai   # ditambah temuan dan kesimpulan AI
python main.py laporan --wilayah semua --peran backend --buka
python main.py semua --wilayah semua --peran data_analyst   # ambil + skill sekaligus
```

Pilihan `--peran`: `backend`, `frontend`, `fullstack`, `mobile`, `data_analyst`, `data_engineer`, `ai_ml`, `devops_cloud`, `qa`, `keamanan`, `ui_ux`, `dukungan_it`, `software_umum`. Pilihan `--tingkat`: `magang`, `junior`, `menengah`, `senior`, `pimpinan`. Keduanya boleh lebih dari satu.

Setiap saringan menghasilkan folder `output/<saringan>/`, misalnya `output/semua-backend/`:

| File | Isi |
|---|---|
| `hasil.json` | seluruh hasil analisis |
| `skill.csv` | tabel skill: jumlah dan persen lowongan, kategori, golongan |
| `skill.xlsx` | tiga lembar Excel: skill, skill yang sering diminta bersama, contoh lowongan |
| `skill.png` | grafik batang skill teratas |
| `laporan.html` | laporan lengkap untuk dibuka di browser |
| `temuan_ai.json` | hanya kalau memakai `--ai` |

Daftar semua laporan ada di `output/index.html`.

## Alur kerja

```
API publik ──► sumber.py ──► data/lowongan/lowongan.json ──► analisis.py ──► output/<saringan>/
 (6 sumber)    ambil, rapikan,                                  saring, hitung,     hasil.json, csv,
               buang yang tutup                                 golongkan            xlsx, png
                                                                     │
                                         temuan_ai.py (--ai) ◄───────┤
                                                                     ▼
                                                                laporan.py ──► laporan.html
```

1. **Ambil** (`sumber.py`). Setiap sumber punya fungsi `ambil_...` yang memanggil API dengan `requests` dan menyamakan bentuk datanya. `lengkapi` membuang tag HTML, menentukan peran dan tingkat dari judul, lalu membaca skill dari deskripsi. `gabungkan` mengenali lowongan kembar dari beberapa sumber. `pilah_tutup` membuang lowongan yang sudah tutup.
2. **Kenali skill** (`skill.py`). Kamus di `konfigurasi/skill_it.yaml` diubah menjadi satu regex per skill. Regex memakai batas kata, jadi "Java" tidak terbaca di dalam "JavaScript" dan "SQL" tidak terbaca di dalam "MySQL".
3. **Analisis** (`analisis.py`). `saring_lowongan` memilih lowongan sesuai saringan. `hitung_skill` menghitung persen lowongan yang menyebut tiap skill, lalu `golongkan` memberi golongan: **wajib dikuasai** (30% lowongan atau lebih), **sering diminta** (10 sampai 30%), atau **nilai tambah**. Ada juga `skill_bersama` (skill pendamping), `tren_skill` (lowongan dua minggu terakhir dibandingkan yang lebih lama), dan `ringkasan_pasar` (peran, tingkat, pengalaman, dan gaji dengan pandas).
4. **AI opsional** (`temuan_ai.py`, pilihan `--ai`). AI membaca enam lowongan terbaru untuk mencari skill di luar kamus. Setiap temuan wajib disertai kutipan, dan ditolak kalau kutipannya tidak ada di lowongan, tidak menyebut skill itu, atau skill-nya sudah ada di kamus. AI juga menulis kesimpulan, yang ditolak kalau memuat angka yang tidak ada di data.
5. **Laporan** (`laporan.py`). Halaman HTML statis tanpa JavaScript. Grafiknya digambar dengan HTML dan CSS, dan semua teks dari lowongan di-escape.

### Lowongan tutup

Setiap `ambil` membuang lowongan yang tutup. Lowongan dianggap tutup kalau salah satu berlaku:

1. tanggal tutup dari sumber sudah lewat;
2. tidak muncul di pengambilan terbaru dan halamannya sudah dihapus (404 atau 410), diperiksa paling banyak 60 halaman per pengambilan;
3. tidak muncul lagi di sumbernya lebih dari 14 hari;
4. dicatat sendiri, lalu barisnya dihapus dari `lowongan_manual.csv`.

Aturan 1 dan 3 juga berlaku saat data dibaca. Lowongan yang dibuang dicatat di `data/lowongan/arsip_tutup.jsonl` beserta alasannya. Setelah `ambil`, semua hasil di `output/` dihitung ulang, jadi laporan dan statistik tidak pernah memuat lowongan yang sudah tutup.

### Lowongan lokal dari halaman karier perusahaan

Sumber `karier_perusahaan` mengambil lowongan di Indonesia langsung dari halaman karier perusahaan yang memakai Lever, Greenhouse, SmartRecruiters, atau Workable. Sistem rekrutmen ini menyediakan API JSON publik supaya lowongannya bisa ditampilkan di situs lain. Daftar perusahaannya ada di `konfigurasi/perusahaan.yaml` (saat ini GoTo Group, Ninja Van, Coda, Xendit, Grab, Cermati, Ajaib, dan Amartha). Untuk menambah perusahaan, buka salah satu lowongannya, lihat alamatnya (misalnya `jobs.lever.co/<kode>/...`), lalu tambahkan kodenya di file itu. Lowongan yang bukan IT tetap dibuang oleh kamus peran.

```bash
python main.py ambil --sumber karier_perusahaan
```

### Menambah lowongan lokal sendiri

Glints, JobStreet, Kalibrr, dan LinkedIn tidak di-scraping karena tidak menyediakan API terbuka dan aturan situsnya melarang. Lowongan dari sana bisa disalin ke `data/lowongan_manual.csv` (kolom: `judul, perusahaan, lokasi, jenis, gaji, tanggal, url, deskripsi`), lalu jalankan `python main.py ambil --sumber manual`.

## Struktur kode

| File | Isi |
|---|---|
| `main.py` | pilihan terminal (argparse) dan empat perintah: `ambil`, `skill`, `laporan`, `semua` |
| `jobhunter/sumber.py` | pengambilan dari API, penyeragaman data, lowongan kembar, aturan lowongan tutup |
| `jobhunter/skill.py` | kamus skill, peran, dan tingkat (regex) |
| `jobhunter/analisis.py` | saringan, hitungan skill, golongan, skill bersama, tren, gambaran pasar, ekspor CSV/Excel/PNG |
| `jobhunter/temuan_ai.py` | fitur AI opsional dan pemeriksaan jawabannya |
| `jobhunter/klien_ai.py` | penghubung ke API AI: tiga model cadangan, cache, log |
| `jobhunter/laporan.py` | laporan HTML dan halaman daftar laporan |
| `jobhunter/berkas.py`, `teks.py`, `pengaturan.py` | baca/tulis file, pembersih teks, lokasi file dan pengaturan |
| `konfigurasi/preferensi.yaml` | wilayah bawaan, batas golongan, jumlah skill, dan lainnya |
| `konfigurasi/skill_it.yaml` | kamus skill, peran, dan tingkat |
| `tests/test_jobhunter.py` | 41 tes otomatis |

Setiap fungsi punya docstring yang menjelaskan peran, parameter, dan nilai kembaliannya.

## Pemakaian AI

Hanya `deepseek-v4.1-flash`, `gemini-4-argon`, dan `glm-5.3` lewat GripHub Router. Model dicoba berurutan: kalau satu gagal atau jawabannya tidak lolos pemeriksaan, model berikutnya dipakai. Jawaban disimpan di `data/cache_ai/` (kuncinya hash SHA-256), dan setiap panggilan dicatat di `output/log_ai.jsonl`. Tanpa `--ai`, program tidak memanggil AI sama sekali dan tidak butuh API key.

## Tes

```bash
python -m pytest
```

Tes tidak butuh internet maupun AI.

## Sumber data

Lowongan berasal dari API publik [Remotive](https://remotive.com), [Arbeitnow](https://www.arbeitnow.com) (hanya yang jarak jauh), [Jobicy](https://jobicy.com), [Himalayas](https://himalayas.app), dan [Remote OK](https://remoteok.com), ditambah API halaman karier perusahaan di Indonesia (Lever, Greenhouse, SmartRecruiters, Workable). Semuanya meminta sumber dicantumkan dan tautan mengarah ke halaman asli. Data ini hanya untuk tugas kuliah.

## Batasan

- Lowongan lokal berasal dari Himalayas (saringan negara Indonesia) dan halaman karier delapan perusahaan teknologi, jumlahnya sekitar seratus. Ini lebih condong ke perusahaan besar dan tingkat senior, jadi belum mewakili seluruh pasar kerja Indonesia; pakai `--wilayah semua` untuk gambaran yang lebih luas.
- Skill dikenali dengan kamus. Skill di luar kamus hanya terlihat lewat `--ai`, dan nama yang mirip bisa ikut terbaca (misalnya "Tailwind CSS" juga terhitung sebagai CSS).
- Peran dan tingkat ditentukan dari judul lowongan. Judul yang tidak biasa bisa salah golongan; judul tanpa kata tingkat dianggap menengah.
- Pemeriksaan kutipan hanya memastikan kutipan ada di teks asli, bukan bahwa kesimpulan AI benar.
