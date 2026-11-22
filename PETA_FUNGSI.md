# Peta Fungsi

Semua fungsi di program, dibuat otomatis dari kode dan docstring-nya. Urutannya mengikuti alur program: titik masuk, pengambilan, pengenalan skill, analisis, AI, laporan, lalu modul pendukung.

Jumlah: **125 fungsi** di 10 file.


## `main.py` (14 fungsi)

AI Job Hunter: mencari tahu skill apa yang diminta lowongan kerja IT.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `relatif` | 28 | `lokasi` | Lokasi file relatif terhadap folder proyek, supaya pesan di terminal pendek. |
| `baca_saringan` | 33 | `args, preferensi` | Saringan dari pilihan terminal: wilayah, daftar peran, dan daftar tingkat. Wilayah yang tidak disebut diambil dari preferensi.yaml. Peran dan tingkat kosong berarti semua. |
| `analisis_dan_laporan` | 41 | `saringan, preferensi, pakai_ai=False, model=None` | Menghitung skill untuk satu saringan, menyimpan semua file hasil, lalu menulis laporan HTML. Lowongan selalu dibaca ulang lewat sumber.baca_lowongan, yang sudah membuang lowongan tutup. Mengembalikan (hasil analisis, lokasi laporan). |
| `tampilkan_skill` | 60 | `hasil` | Mencetak tabel skill ke terminal, lengkap dengan golongan dan skill yang sering diminta bersama. |
| `perbarui_semua_hasil` | 70 | `–` | Setelah lowongan diambil ulang, setiap saringan yang pernah dianalisis dihitung ulang dari data baru. Dengan begitu tidak ada laporan lama yang masih memuat lowongan yang sudah tutup. |
| `perintah_ambil` | 85 | `args` | Perintah "ambil": mengambil lowongan dari API, membuang yang tutup, lalu memperbarui semua hasil. |
| `perintah_skill` | 92 | `args` | Perintah "skill": menghitung skill yang diminta untuk saringan yang dipilih dan menampilkannya. |
| `perintah_laporan` | 106 | `args` | Perintah "laporan": menulis ulang laporan satu saringan dari data terbaru, lalu membukanya. |
| `perintah_semua` | 119 | `args` | Perintah "semua": ambil lowongan, lalu jalankan skill dengan saringan yang sama. |
| `buat_parser` | 126 | `–` | Menyusun pilihan terminal dengan argparse: satu subperintah untuk setiap langkah. |
| `tambah_ambil` | 131 | `bagian` | Pilihan untuk mengambil lowongan: sumber mana saja dan apakah halaman diperiksa. |
| `tambah_saringan` | 136 | `bagian` | Pilihan saringan: wilayah, peran, tingkat, dan membuka laporan di browser. |
| `tambah_ai` | 143 | `bagian` | Pilihan AI: menyalakan temuan AI dan memilih model. |
| `main` | 170 | `–` | Titik masuk program: membaca pilihan terminal lalu menjalankan perintah yang dipilih. |

## `jobhunter/sumber.py` (24 fungsi)

Mengambil lowongan dari API publik, lalu menyamakan bentuknya.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `minta` | 51 | `url, parameter=None` | Mengirim satu permintaan GET ke API dan mengembalikan JSON-nya. Parameter: alamat API dan parameter pencarian (kamus, boleh kosong). Kode HTTP 4xx/5xx menjadi galat (raise_for_status). Setelah setiap permintaan program berhenti JEDA_DETIK detik supaya tidak membebani server sumber. |
| `ke_tanggal` | 64 | `nilai` | Menerima detik sejak 1970 atau teks ISO, mengembalikan tanggal berbentuk 2026-11-10. |
| `ke_angka` | 73 | `nilai` | Gaji dari sumber kadang berupa teks, 0, atau kosong. Yang bukan angka positif menjadi None. |
| `ambil_remotive` | 85 | `–` | Lowongan kerja jarak jauh dari Remotive. Mengembalikan (data mentah, daftar lowongan). |
| `ambil_arbeitnow` | 101 | `jumlah_halaman=2` | Hanya lowongan jarak jauh. Sisanya kerja di kantor di Jerman, yang tidak bisa dilamar dari Indonesia. |
| `ambil_jobicy` | 120 | `–` | 100 lowongan terbaru kategori dev dari Jobicy, lengkap dengan gaji kalau dicantumkan. |
| `ambil_himalayas` | 138 | `negara=None` | Tanpa negara: lowongan dari mana saja. Dengan negara: hanya yang menerima pelamar dari negara itu. |
| `ambil_himalayas_indonesia` | 160 | `–` | Lowongan Himalayas yang menerima pelamar dari Indonesia. Sumber utama lowongan lokal. |
| `ambil_remoteok` | 165 | `–` | Lowongan dari Remote OK. Gaji di sumber ini selalu dalam USD per tahun. |
| `ambil_manual` | 183 | `–` | Lowongan yang dicatat sendiri oleh pengguna di data/lowongan_manual.csv. |
| `tentukan_wilayah` | 209 | `lokasi, sumber` | Memilah lowongan menjadi "lokal" (untuk Indonesia) atau "internasional". Lokal berarti lokasinya menyebut Indonesia atau kota di Indonesia dan paling banyak menyebut tiga tempat. Lowongan jarak jauh yang menerima puluhan negara, termasuk Indonesia, tetap dihitung internasional. Lowongan yang dicatat sendiri selalu lokal. |
| `saring_wilayah` | 222 | `lowongan, wilayah` | Hanya lowongan wilayah yang diminta ("lokal" atau "internasional"); "semua" tidak menyaring. |
| `buat_id` | 229 | `sumber, url, judul, perusahaan` | ID pendek yang tetap sama setiap kali lowongan yang sama diambil lagi. |
| `lengkapi` | 235 | `lowongan, sumber, hari_ini` | Membersihkan deskripsi dan menambah peran, tingkat, serta skill. None kalau bukan lowongan IT. |
| `kunci_kembar` | 270 | `lowongan` | Lowongan yang sama sering dipasang di beberapa situs. Judul dan perusahaan dipakai untuk mengenalinya. |
| `gabungkan` | 276 | `lama, baru` | Menggabungkan lowongan baru ke data lama. Lowongan yang sudah ada diperbarui tetapi tanggal pertama dilihat dipertahankan. Lowongan kembar dari sumber lain dilewati. Mengembalikan (hasil, jumlah baru, jumlah kembar). |
| `segarkan_peran` | 302 | `tersimpan` | Menghitung ulang peran dan tingkat lowongan tersimpan dengan kamus yang sekarang. Kamus di skill_it.yaml bisa berubah setelah lowongan disimpan. Mengembalikan (yang tetap, yang dibuang karena judulnya tidak lagi terbaca sebagai lowongan IT). |
| `alasan_tutup` | 318 | `lowongan, hari_ini` | Alasan lowongan dianggap tutup dilihat dari tanggalnya saja, atau None kalau masih buka. |
| `halaman_hilang` | 328 | `url` | Benar kalau halaman lowongan sudah dihapus (404 atau 410). Galat jaringan dan kode lain, misalnya 403 dari situs yang menolak program, tidak dianggap tutup karena belum tentu lowongannya hilang. |
| `pilah_tutup` | 345 | `semua, hari_ini, sumber_berhasil, cek_halaman=None` | Memisahkan lowongan yang masih buka dari yang tutup. Mengembalikan (buka, tutup). Lowongan dianggap tutup kalau salah satu berlaku: 1. tanggal tutup dari sumber sudah lewat; 2. tidak muncul lagi di sumbernya lebih dari BATAS_HARI_TIDAK_TERLIHAT hari; 3. dicatat sendiri, lalu barisnya dihapus dari lowongan_manual.csv; 4. tidak muncul di pengambilan hari ini dan halamannya sudah dihapus. cek_halaman adalah fungsi pemeriksa halaman. Kalau None, aturan 4 dilewati. |
| `arsipkan` | 378 | `tutup, hari_ini` | Mencatat lowongan yang dibuang, tanpa deskripsinya, supaya bisa ditelusuri. |
| `baca_lowongan` | 387 | `–` | Lowongan yang masih buka. Yang tutup menurut tanggal disaring juga di sini, supaya tidak muncul walaupun pengambilan belum dijalankan lagi. |
| `baca_lowongan_wilayah` | 403 | `wilayah` | Lowongan untuk satu pilihan wilayah. Berhenti dengan petunjuk kalau datanya terlalu sedikit. |
| `jalankan` | 415 | `nama_sumber=None, cek_tautan=True` | Mengambil semua sumber yang diminta, lalu membuang lowongan yang sudah tutup. Satu sumber yang gagal tidak menghentikan yang lain, dan lowongan dari sumber yang gagal tidak diperiksa halamannya pada pengambilan ini. |

## `jobhunter/skill.py` (10 fungsi)

Mengenali skill, peran, dan tingkat dari teks dengan kamus di konfigurasi/skill_it.yaml.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `muat_kamus` | 15 | `–` | Membaca kamus sekali saja, lalu menyusun satu regex untuk tiap skill. |
| `susun` | 31 | `kelompok` | Menggabungkan daftar pola tiap nama (peran atau tingkat) menjadi satu regex. |
| `ekstrak_skill` | 44 | `teks` | Mengembalikan daftar skill yang disebut di teks, urut abjad. |
| `bukti_skill` | 50 | `teks, nama, lebar=60` | Mengembalikan potongan teks di sekitar tempat skill disebut, atau None. |
| `kategori_skill` | 60 | `nama` | Kategori skill di kamus (bahasa, frontend, basis_data, ...), atau "lainnya" kalau tidak ada. |
| `tentukan_peran` | 65 | `judul` | Peran pertama yang polanya cocok dengan judul. None berarti bukan lowongan IT. |
| `tentukan_tingkat` | 75 | `judul` | Tingkat pertama yang polanya cocok dengan judul. Kalau tidak ada yang cocok, dianggap menengah. |
| `daftar_peran` | 83 | `–` | Nama semua peran di kamus, untuk pilihan --peran di terminal. |
| `daftar_kategori` | 88 | `–` | Nama kategori skill sesuai urutan di kamus, ditambah kategori pola khusus. |
| `tahun_pengalaman` | 94 | `teks` | Angka tahun pengalaman terbesar yang diminta, misalnya 5 dari "5+ years of experience". |

## `jobhunter/analisis.py` (16 fungsi)

Menghitung skill yang diminta lowongan IT, lalu menyimpan hasilnya ke JSON, CSV, Excel, dan PNG.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `persen` | 39 | `bagian, total` | Persentase dengan satu angka desimal. Total nol menghasilkan 0, bukan galat pembagian. |
| `nama_saringan` | 46 | `wilayah, peran=None, tingkat=None` | Nama folder hasil untuk satu pertanyaan, misalnya "lokal-backend-junior". Parameter peran dan tingkat berupa daftar (boleh kosong). Beberapa pilihan digabung dengan "+". |
| `terbuka_untuk_indonesia` | 59 | `isi, preferensi` | Benar kalau lowongan bisa dilamar dari Indonesia. Lowongan lokal selalu bisa. Lowongan internasional harus menyebut salah satu kata di lokasi_diterima (misalnya worldwide atau asia), kecuali hanya_lokasi_diterima dimatikan. |
| `saring_lowongan` | 71 | `lowongan, preferensi, peran=None, tingkat=None` | Lowongan yang bisa dilamar dari Indonesia dan cocok dengan peran dan tingkat yang diminta. Parameter peran dan tingkat berupa daftar; kosong berarti semua. Mengembalikan daftar baru. |
| `golongkan` | 86 | `nilai_persen, batas_wajib, batas_sering` | Golongan satu skill dari persen lowongan yang memintanya: "wajib", "sering", atau "tambahan". |
| `hitung_skill` | 93 | `lowongan, batas_wajib=30, batas_sering=10` | Semua skill yang disebut lowongan, urut dari yang paling sering. Setiap baris berisi nama skill, kategorinya, jumlah dan persen lowongan yang menyebutnya, serta golongannya. Satu lowongan dihitung sekali per skill walaupun skill-nya disebut berkali-kali, karena isi["skill"] sudah berupa daftar tanpa duplikat. |
| `skill_per_kategori` | 111 | `daftar_skill, jumlah=5` | Mengelompokkan hasil hitung_skill per kategori, paling banyak `jumlah` skill per kategori. Kategori diurutkan seperti di kamus, dan kategori tanpa skill tidak ditulis. |
| `skill_bersama` | 124 | `lowongan, nama_skill, jumlah=JUMLAH_TEMAN` | Skill yang paling sering diminta bersama `nama_skill`. Dari semua lowongan yang meminta nama_skill, dihitung berapa persen yang juga meminta skill lain. Contoh: 60% lowongan yang meminta React juga meminta TypeScript. |
| `tren_skill` | 135 | `lowongan, hari_ini, hari=14, jumlah=8` | Membandingkan lowongan yang dipasang dalam `hari` hari terakhir dengan yang lebih lama. Hanya memakai lowongan yang masih buka, jadi lowongan yang sudah tutup tidak ikut dihitung. Mengembalikan None kalau salah satu kelompok terlalu sedikit untuk dibandingkan. Kalau cukup, mengembalikan skill dengan selisih persen terbesar (naik maupun turun). |
| `gaji_per_peran` | 160 | `tabel` | Median gaji tahunan dalam USD per peran, hanya dari lowongan yang mencantumkannya. Parameter: DataFrame lowongan. Mengembalikan (daftar per peran, jumlah lowongan bergaji). |
| `ringkasan_pasar` | 177 | `lowongan` | Sebaran lowongan per sumber, peran, dan tingkat, ditambah pengalaman dan gaji yang diminta. Memakai pandas: value_counts untuk menghitung, crosstab untuk tabel peran x tingkat, dan groupby untuk median per kelompok. |
| `contoh_lowongan` | 206 | `lowongan, jumlah=JUMLAH_CONTOH` | Lowongan terbaru beserta skill-nya, untuk ditampilkan sebagai bukti di laporan. |
| `analisis_skill` | 213 | `lowongan, preferensi, saringan, hari_ini=None` | Seluruh analisis untuk satu saringan, sebagai kamus yang siap disimpan ke JSON. Parameter: lowongan yang masih buka (sudah disaring wilayahnya), preferensi, saringan (kamus wilayah, peran, tingkat), dan tanggal hari ini (bawaan: hari ini). Program berhenti dengan petunjuk kalau lowongan yang cocok terlalu sedikit. |
| `gambar_skill` | 250 | `hasil, lokasi` | Grafik batang PNG skill teratas, diwarnai menurut golongan, dengan angka persen di ujung batang. |
| `simpan_excel` | 270 | `hasil, lokasi` | Satu file Excel dengan tiga lembar: skill, skill_bersama, dan contoh_lowongan. |
| `simpan_hasil` | 284 | `hasil` | Menulis hasil.json, skill.csv, skill.xlsx, dan skill.png ke output/<saringan>/. Mengembalikan folder tempat hasil disimpan. |

## `jobhunter/klien_ai.py` (8 fungsi)

Penghubung ke layanan AI GripHub Router (format permintaannya sama dengan OpenAI).

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `periksa_model` | 37 | `daftar` | Memastikan semua model di daftar termasuk tiga model yang diizinkan. Mengembalikan daftar itu sendiri, atau menghentikan program kalau ada model asing. |
| `ambil_api_key` | 48 | `–` | Membaca GRIPHUB_API_KEY dari file .env. Program berhenti dengan petunjuk kalau belum diisi. |
| `kunci_cache` | 57 | `model, pesan` | Nama file cache: 24 huruf pertama hash SHA-256 dari model, suhu, dan isi pesan. Pertanyaan yang sama persis selalu menghasilkan kunci yang sama, jadi jawabannya bisa dipakai ulang. |
| `model_sama` | 66 | `diminta, penjawab` | Benar kalau model yang menjawab adalah model yang diminta. Router kadang menulis nama yang sama dengan bentuk lain: menambah akhiran (gemini-4-argon-d), awalan penyedia, atau huruf besar (deepseek-ai/DeepSeek-V4.1-Flash-1017). Bagian sebelum "/" dibuang dan huruf disamakan, lalu yang diperiksa awalannya. Model lain tetap ditolak. |
| `panggil_model` | 77 | `model, pesan, api_key` | Mengirim satu permintaan ke satu model dan mengembalikan jawabannya. |
| `tanya` | 105 | `sistem, pengguna, tugas, model=None, pakai_cache=True` | Bertanya ke AI. Mengembalikan kamus berisi teks jawaban dan catatan pemakaiannya. |
| `ambil_json` | 134 | `teks` | Mengambil objek JSON dari jawaban model, yang kadang dibungkus ```json atau diberi pengantar. |
| `tanya_json` | 149 | `sistem, pengguna, tugas, kunci_wajib, model=None, pemeriksa=None` | Seperti tanya(), tetapi jawabannya harus JSON yang memuat semua kunci wajib. pemeriksa adalah fungsi yang menerima JSON itu dan mengembalikan bentuk rapinya, atau melempar GalatAI kalau isinya tidak bisa dipakai. Kalau jawaban sebuah model tidak bisa dipakai, model berikutnya dicoba. |

## `jobhunter/temuan_ai.py` (11 fungsi)

Fitur AI opsional (pilihan --ai): skill di luar kamus dan kesimpulan untuk pencari kerja.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `pilih_lowongan` | 40 | `lowongan, jumlah` | Lowongan terbaru yang deskripsinya cukup panjang untuk dibaca AI. |
| `periksa_temuan` | 46 | `data, deskripsi` | Memisahkan temuan AI untuk satu lowongan menjadi (diterima, ditolak). Parameter: JSON dari AI dan deskripsi lowongan yang dibaca AI. Setiap temuan yang ditolak diberi alasan. Melempar GalatAI kalau bentuk JSON-nya salah, supaya klien_ai mencoba model berikutnya. |
| `gabung_temuan` | 75 | `per_lowongan` | Menggabungkan temuan dari beberapa lowongan menjadi satu daftar per skill. Nama yang hanya beda huruf besar dianggap sama. Urut dari skill yang disebut paling banyak lowongan. |
| `cari_skill_baru` | 91 | `lowongan, jumlah, model=None` | Meminta AI membaca `jumlah` lowongan terbaru dan mengembalikan skill di luar kamus. Mengembalikan kamus berisi daftar skill baru, jumlah lowongan yang dibaca, dan temuan yang ditolak. |
| `cari_angka` | 109 | `teks` | Semua angka di teks sebagai string. Koma desimal disamakan dengan titik (3,5 menjadi 3.5). |
| `angka_sah` | 114 | `hasil` | Angka yang boleh muncul di kesimpulan: semua angka di data yang dikirim ke AI. Persen juga boleh ditulis bulat, jadi 45.5 menambah 45 dan 46 sebagai angka sah. |
| `data_kesimpulan` | 126 | `hasil` | Ringkasan kecil hasil analisis yang dikirim ke AI: saringan, jumlah lowongan, dan 12 skill teratas. |
| `periksa_kesimpulan` | 135 | `data, sah` | Menolak kesimpulan yang kosong atau memuat angka yang tidak ada di data. Mengembalikan teks kesimpulan yang sudah dirapikan, atau melempar GalatAI. |
| `buat_kesimpulan` | 149 | `hasil, model=None` | Meminta AI menulis kesimpulan dari hasil analisis. Mengembalikan (teks, model yang menjawab). |
| `jalankan` | 159 | `hasil, lowongan, jumlah, model=None` | Menjalankan kedua fitur AI untuk satu hasil analisis dan menyimpannya ke temuan_ai.json. Parameter lowongan adalah lowongan yang sama dengan yang dianalisis (sudah disaring). Temuan diberi tanggal analisis, supaya laporan bisa mengenali temuan yang sudah basi. |
| `baca_temuan` | 173 | `nama, id_buka, hasil` | Temuan AI yang masih berlaku untuk hasil analisis sekarang, atau None. Bukti dari lowongan yang sudah tutup dibuang dan jumlahnya dihitung ulang. Kesimpulan hanya dipakai kalau dibuat dari analisis yang sama (tanggal dan jumlah lowongan sama), karena angkanya berubah setiap kali lowongan diambil ulang. |

## `jobhunter/laporan.py` (25 fungsi)

Menyusun hasil analisis satu saringan menjadi satu halaman HTML statis yang bisa dibuka di browser.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `e` | 343 | `nilai` | Semua teks dari lowongan dan AI di-escape supaya tidak terbaca sebagai HTML. |
| `angka` | 348 | `nilai` | Menulis desimal dengan koma, seperti kebiasaan di Indonesia. None menjadi tanda strip. |
| `tautan` | 355 | `url` | Hanya alamat http atau https yang boleh menjadi tautan; isian lain (misalnya javascript:) diganti. |
| `rapikan` | 361 | `nama` | Nama di kamus memakai garis bawah (dukungan_it); di laporan ditulis dengan spasi. |
| `nama_sumber` | 366 | `kode` | Nama tampilan sumber data, misalnya "remoteok" menjadi "Remote OK". |
| `tanggal_indo` | 371 | `teks` | Mengubah 2026-11-08 menjadi 8 Nov 2026. Teks yang bukan tanggal dikembalikan apa adanya. |
| `judul_saringan` | 380 | `saringan` | Pertanyaan yang dijawab laporan dalam kata-kata, misalnya "backend junior, lowongan lokal". |
| `daftar_tag` | 388 | `nama, kelas=''` | Deretan label kecil, satu per nama. |
| `bungkus` | 393 | `kode, judul, isi, keterangan=''` | Satu bagian laporan. Kodenya menjadi sasaran tautan di menu (#kode). |
| `grafik_batang` | 399 | `baris, maks, satuan='', catatan=False` | Grafik batang mendatar dari HTML. Tiap baris: (label, nilai, kelas batang, teks catatan, keterangan hover). Lebar batang = nilai / maks. Angka ditulis di ujung kanan, jadi grafik tetap terbaca tanpa warna. |
| `kepala_halaman` | 418 | `hasil` | Kesimpulan satu kalimat (skill wajib), sebaran golongan, dan empat angka ringkas. |
| `bagian_skill` | 458 | `hasil` | Grafik semua skill teratas. Warna dan catatan di kanan menunjukkan golongannya. |
| `bagian_kategori` | 471 | `hasil` | Lima skill teratas di setiap kategori, misalnya bahasa pemrograman atau basis data. |
| `bagian_bersama` | 483 | `hasil` | Tabel skill pendamping: kalau lowongan meminta X, skill apa lagi yang biasanya ikut diminta. |
| `bagian_tren` | 497 | `hasil` | Selisih persen antara lowongan baru dan lowongan yang lebih lama. Kosong kalau datanya kurang. |
| `bagian_ai` | 512 | `temuan` | Kesimpulan AI dan skill di luar kamus beserta kutipan buktinya. Kosong kalau --ai belum dipakai. |
| `grafik_peran_tingkat` | 532 | `peran_dan_tingkat` | Batang bertumpuk: jumlah lowongan per peran, dipecah per tingkat dari magang sampai pimpinan. |
| `tabel_pasar` | 550 | `pasar` | Dua tabel kecil: tahun pengalaman yang diminta per tingkat, dan median gaji per peran. |
| `bagian_pasar` | 569 | `hasil` | Sebaran lowongan per peran dan tingkat, pengalaman yang diminta, dan gaji. |
| `bagian_contoh` | 578 | `hasil, id_buka` | Lowongan terbaru sebagai bukti. Lowongan yang sudah tutup sejak analisis dibuat tidak ditampilkan. |
| `bagian_catatan` | 591 | `–` | Sumber data, pemakaian AI, dan batasan analisis. |
| `buat_menu` | 612 | `isi` | Menu hanya memuat bagian yang benar-benar ada, ditambah tautan ke daftar semua laporan. |
| `halaman` | 618 | `judul, kepala, isi, menu=''` | Kerangka HTML yang dipakai laporan dan halaman daftar laporan. |
| `buat_laporan` | 631 | `nama, id_buka=None` | Menulis output/<saringan>/laporan.html dari hasil.json dan mengembalikan lokasinya. id_buka adalah ID semua lowongan yang masih buka. Dipakai untuk menyembunyikan contoh lowongan dan bukti AI dari lowongan yang sudah tutup. |
| `buat_indeks` | 650 | `–` | Menulis output/index.html: daftar semua laporan yang ada, satu kartu per saringan. Halaman ini sengaja tidak memuat data lowongan, hanya nama saringan, jumlah lowongan, dan waktu laporan dibuat, supaya tidak ada lowongan yang sudah tutup tertinggal di sini. |

## `jobhunter/berkas.py` (6 fungsi)

Membaca dan menulis file JSON, JSONL, dan CSV dengan aman.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `baca_json` | 9 | `lokasi, bawaan=None` | Membaca file JSON. Kalau filenya belum ada dan bawaan diisi, bawaan yang dikembalikan. |
| `simpan_json` | 18 | `lokasi, data` | Menulis JSON lewat file sementara, lalu menukarnya. Kalau program berhenti di tengah penulisan, file lama tetap utuh. |
| `tambah_jsonl` | 31 | `lokasi, baris` | Menambah satu baris JSON di akhir file, tanpa membaca isi lamanya. |
| `baca_jsonl` | 39 | `lokasi` | Membaca file berisi satu JSON per baris. File yang belum ada dianggap kosong. |
| `baca_csv` | 48 | `lokasi` | Membaca CSV menjadi daftar kamus. File yang belum ada dianggap kosong. |
| `simpan_csv` | 58 | `lokasi, baris, kolom` | Menulis daftar kamus ke CSV dengan urutan kolom tertentu. Parameter: lokasi file, baris (daftar kamus), kolom (nama kolom yang ditulis, berurutan). Kunci lain di kamus diabaikan. Seperti simpan_json, file ditulis lewat file sementara. |

## `jobhunter/teks.py` (8 fungsi)

Fungsi kecil untuk membersihkan dan membandingkan teks.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `__init__` | 13 | `–` | Menyiapkan tempat potongan teks dan penghitung tag script/style yang sedang dibuka. |
| `handle_starttag` | 19 | `tag, attrs` | Dipanggil HTMLParser untuk tag pembuka. Isi script/style dilewati; tag blok menjadi baris baru. |
| `handle_endtag` | 26 | `tag` | Dipanggil untuk tag penutup. Menutup script/style, atau menambah baris baru untuk tag blok. |
| `handle_data` | 33 | `data` | Dipanggil untuk teks di antara tag. Disimpan kecuali sedang di dalam script/style. |
| `buang_html` | 39 | `teks` | Mengubah deskripsi lowongan berformat HTML menjadi teks biasa. |
| `rapikan` | 55 | `teks` | Huruf kecil dan satu spasi antarkata, untuk membandingkan dua teks. |
| `kutipan_ada` | 62 | `kutipan, sumber` | Benar kalau kutipan benar-benar tertulis di sumber, tanpa melihat huruf besar dan spasi. |
| `potong` | 68 | `teks, batas` | Memotong teks panjang di batas kata, supaya permintaan ke AI tidak terlalu besar. |

## `jobhunter/pengaturan.py` (3 fungsi)

Lokasi file dan pengaturan yang dipakai semua modul.

| Fungsi | Baris | Parameter | Peran dan nilai kembalian |
|---|---|---|---|
| `baca_yaml` | 25 | `nama` | Membaca satu file YAML di folder konfigurasi. Parameter: nama file, misalnya "preferensi.yaml". Mengembalikan isinya sebagai kamus Python. |
| `baca_preferensi` | 35 | `–` | Membaca preferensi.yaml dan menolak isi yang tidak masuk akal sejak awal. Mengembalikan kamus pengaturan. Program berhenti dengan pesan yang jelas kalau wilayah tidak dikenal atau ambang golongan skill tidak berurutan. |
| `folder_saringan` | 50 | `nama` | Folder hasil untuk satu saringan, misalnya output/lokal-backend-junior/. |
