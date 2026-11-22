"""Menyusun hasil analisis satu saringan menjadi satu halaman HTML statis yang bisa dibuka di browser.

Halamannya berdiri sendiri: gaya (CSS) ditulis di dalam file dan grafik digambar dengan HTML dan
CSS, jadi laporan.html tetap utuh walaupun dipindah atau dikirim. Tidak ada JavaScript.

Urutan halaman mengikuti pertanyaan pembaca:
1. kesimpulan di kepala halaman: skill apa yang wajib dikuasai,
2. semua skill yang diminta, dikelompokkan wajib / sering / nilai tambah,
3. skill per kategori dan skill yang sering diminta bersama,
4. tren, temuan AI (kalau ada), gambaran pasar, contoh lowongan, dan sumber data.
Setiap bagian dibuat oleh satu fungsi bagian_...() yang mengembalikan potongan HTML.
"""

from collections import Counter
from datetime import datetime
from html import escape

from jobhunter import temuan_ai
from jobhunter.berkas import baca_json, baca_jsonl
from jobhunter.pengaturan import FILE_LOG_AI, FOLDER_OUTPUT, TINGKAT, folder_saringan

SUMBER_DATA = {
    "remotive": ("Remotive", "https://remotive.com"),
    "arbeitnow": ("Arbeitnow", "https://www.arbeitnow.com"),
    "jobicy": ("Jobicy", "https://jobicy.com"),
    "himalayas": ("Himalayas", "https://himalayas.app"),
    "himalayas_indonesia": ("Himalayas (Indonesia)", ""),  # Tautannya sama dengan Himalayas.
    "remoteok": ("Remote OK", "https://remoteok.com"),
    "manual": ("Catatan sendiri", ""),
}
GOLONGAN = ["wajib", "sering", "tambahan"]
LABEL_GOLONGAN = {"wajib": "Wajib dikuasai", "sering": "Sering diminta", "tambahan": "Nilai tambah"}
# Golongan memakai warna yang sama dengan golongan skor di gaya lama: hijau, biru, abu-abu.
KELAS_SEBARAN = {"wajib": "tinggi", "sering": "sedang", "tambahan": "rendah"}
NAMA_KATEGORI = {
    "bahasa": "Bahasa pemrograman", "frontend": "Frontend", "backend": "Backend", "mobile": "Mobile",
    "basis_data": "Basis data", "data_dan_ai": "Data dan AI", "devops_dan_cloud": "DevOps dan cloud",
    "pengujian": "Pengujian", "keamanan": "Keamanan", "alat_dan_cara_kerja": "Alat dan cara kerja", "lainnya": "Lainnya",
}
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

GAYA = """
/* Warna disimpan sebagai variabel, supaya mode gelap cukup mengganti nilainya di satu tempat. */
:root { color-scheme:light;
  --latar:#f3f4f7; --kartu:#ffffff; --kartu2:#f7f8fa; --tinta:#101828; --tinta2:#566074; --redup:#8a93a5;
  --garis:#e3e6ec; --jalur:#e9ecf1;
  --biru:#2a78d6; --biru-muda:#e7f0fc; --biru-teks:#1a4f99;
  --hijau:#14895b; --hijau-muda:#e2f4ec; --hijau-teks:#0d5d3e;
  --jingga:#eb6834; --jingga-muda:#fdeee7; --jingga-teks:#a2400f;
  --kuning-muda:#fff6dc; --kuning-teks:#835b00;
  /* Lima tingkat lowongan, satu warna biru dari terang ke gelap (urutan, bukan kategori). */
  --t1:#86b6ef; --t2:#5598e7; --t3:#2a78d6; --t4:#1c5cab; --t5:#0d366b;
  --kepala1:#0c1730; --kepala2:#16336e; --kepala3:#2363c4;
  --bayang:0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06);
  --bayang-naik:0 10px 28px rgba(16,24,40,.10);
  --keluar:cubic-bezier(0.23, 1, 0.32, 1); }  /* ease-out yang lebih tegas daripada bawaan CSS */
@media (prefers-color-scheme:dark) { :root { color-scheme:dark;
  --latar:#0e1117; --kartu:#161b24; --kartu2:#1c2230; --tinta:#eef1f6; --tinta2:#a9b2c3; --redup:#7d879a;
  --garis:#283041; --jalur:#252c3a;
  --biru:#3987e5; --biru-muda:#16294a; --biru-teks:#9cc3f5;
  --hijau:#1fa872; --hijau-muda:#12301f; --hijau-teks:#8ee0b8;
  --jingga:#e7703f; --jingga-muda:#3a1f12; --jingga-teks:#f6b08f;
  --kuning-muda:#33280b; --kuning-teks:#f0cf7a;
  --t1:#b7d3f6; --t2:#86b6ef; --t3:#5598e7; --t4:#2a78d6; --t5:#1c5cab;
  --kepala1:#070b14; --kepala2:#0f2550; --kepala3:#1a4fa3;
  --bayang:0 0 0 1px rgba(255,255,255,.02); --bayang-naik:0 10px 28px rgba(0,0,0,.45); } }

* { box-sizing:border-box; }
body { margin:0; background:var(--latar); color:var(--tinta);
  font:15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; -webkit-font-smoothing:antialiased; }
h1, h2, h3 { text-wrap:balance; letter-spacing:-0.015em; }
h2 { font-size:20px; margin:0 0 4px; }
h3 { font-size:17px; margin:0; line-height:1.35; }
p { margin:0 0 10px; }
a { color:var(--biru); }
:focus-visible { outline:2px solid var(--biru); outline-offset:2px; border-radius:6px; }
code { font:13px/1.5 ui-monospace, "SF Mono", Menlo, monospace; background:var(--kartu2); border:1px solid var(--garis); border-radius:6px; padding:1px 6px; }
.lebar { max-width:1120px; margin:0 auto; padding:0 16px; }
.kecil { color:var(--tinta2); font-size:13px; }
.redup { color:var(--redup); }
.angka-tabel { font-variant-numeric:tabular-nums; }

/* Kepala halaman: kesimpulan di kiri, sebaran golongan dan angka ringkas di kanan */
header { background:radial-gradient(1200px 400px at 85% -10%, var(--kepala3), transparent 60%), linear-gradient(135deg, var(--kepala1), var(--kepala2));
  color:#fff; padding:36px 0 32px; }
.kepala { display:grid; grid-template-columns:minmax(0, 1.25fr) minmax(0, 1fr); gap:32px; align-items:end; }
.merek { display:flex; align-items:center; gap:10px; font-size:13px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:#bcd0f0; margin-bottom:18px; }
.merek i { width:26px; height:26px; border-radius:8px; background:linear-gradient(135deg, #5fa2ff, #2a78d6); display:grid; place-items:center;
  font-style:normal; color:#fff; font-size:14px; letter-spacing:0; }
header h1 { font-size:34px; line-height:1.15; margin:0 0 10px; }
header .sub { color:#c9d6ee; margin:0 0 16px; max-width:560px; }
.lencana { display:inline-block; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.14); border-radius:999px;
  padding:2px 11px; margin:0 6px 6px 0; font-size:12.5px; color:#e8eefb; }
.panel { background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); border-radius:16px; padding:18px; backdrop-filter:blur(6px); }
.panel small { color:#bcd0f0; font-size:12px; text-transform:uppercase; letter-spacing:.07em; font-weight:600; }
.sebaran { display:flex; gap:2px; height:12px; margin:10px 0 10px; border-radius:6px; overflow:hidden; background:rgba(255,255,255,.08); }
.sebaran i { display:block; min-width:4px; }
.sebaran .tinggi { background:#2fc287; } .sebaran .sedang { background:#5fa2ff; } .sebaran .rendah { background:rgba(255,255,255,.28); }
.legenda-kepala { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:13px; color:#dfe7f6; }
.legenda-kepala span { display:inline-flex; align-items:center; gap:6px; }
.legenda-kepala b { font-variant-numeric:tabular-nums; }
.titik { width:9px; height:9px; border-radius:50%; display:inline-block; }
.titik.tinggi { background:#2fc287; } .titik.sedang { background:#5fa2ff; } .titik.rendah { background:rgba(255,255,255,.4); }
.statistik { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:10px; margin-top:16px; }
.statistik div { border-top:1px solid rgba(255,255,255,.14); padding-top:10px; }
.statistik b { display:block; font-size:22px; line-height:1.2; font-variant-numeric:tabular-nums; }
.statistik span { font-size:12px; color:#bcd0f0; }

/* Menu yang ikut turun saat halaman digulir */
nav { position:sticky; top:0; z-index:3; background:color-mix(in srgb, var(--kartu) 92%, transparent); backdrop-filter:saturate(1.4) blur(10px);
  border-bottom:1px solid var(--garis); }
nav .lebar { display:flex; gap:2px; overflow-x:auto; padding-top:8px; padding-bottom:8px; scrollbar-width:none; }
nav a { white-space:nowrap; text-decoration:none; color:var(--tinta2); font-size:14px; font-weight:500; padding:6px 12px; border-radius:8px;
  transition:background-color 150ms ease, color 150ms ease, transform 160ms var(--keluar); }
nav a:active { transform:scale(0.97); }
nav a.luar { border:1px solid var(--garis); color:var(--tinta); margin-left:4px; }
nav .sela { flex:1; }

main { padding:8px 16px 72px; }
section { background:var(--kartu); border:1px solid var(--garis); border-radius:18px; padding:24px; margin-top:20px;
  box-shadow:var(--bayang); scroll-margin-top:68px; }
.judul-bagian { display:flex; align-items:baseline; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
.judul-bagian p { margin:0; }
.dua-kolom { display:grid; grid-template-columns:minmax(0, 1fr) minmax(0, 1.15fr); gap:20px; align-items:start; }
.dua-kolom > section { margin-top:20px; }
.dua { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:20px; }

/* Tag */
.tag { display:inline-block; background:var(--jalur); color:var(--tinta); border-radius:999px; padding:2px 10px; margin:0 4px 6px 0; font-size:12.5px; line-height:1.6; }
.tag.biru { background:var(--biru-muda); color:var(--biru-teks); }
.tag.hijau { background:var(--hijau-muda); color:var(--hijau-teks); }
.tag.jingga { background:var(--jingga-muda); color:var(--jingga-teks); }

/* Cincin skor: lingkaran yang terisi sesuai skor; warnanya mengikuti golongan */
.tinggi { --warna:var(--hijau); --warna-muda:var(--hijau-muda); --warna-teks:var(--hijau-teks); }
.sedang { --warna:var(--biru); --warna-muda:var(--biru-muda); --warna-teks:var(--biru-teks); }
.rendah { --warna:var(--redup); --warna-muda:var(--jalur); --warna-teks:var(--tinta2); }
.cincin { --u:84px; --tebal:8px; width:var(--u); height:var(--u); flex:none; border-radius:50%; display:grid; place-items:center;
  background:conic-gradient(var(--warna) calc(var(--persen) * 1%), var(--jalur) 0); }
.cincin b { width:calc(var(--u) - 2 * var(--tebal)); height:calc(var(--u) - 2 * var(--tebal)); border-radius:50%; background:var(--kartu);
  display:grid; place-items:center; font-size:21px; font-variant-numeric:tabular-nums; letter-spacing:-0.02em; }
.cincin.kecil { --u:44px; --tebal:5px; } .cincin.kecil b { font-size:13.5px; }
.label-golongan { display:inline-block; font-size:12px; font-weight:600; color:var(--warna-teks); background:var(--warna-muda); border-radius:999px; padding:1px 9px; }

/* Rekomendasi: tiga kartu besar untuk dilamar lebih dulu */
.rekomendasi { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:16px; }
.pilihan { position:relative; display:flex; flex-direction:column; gap:14px; background:var(--kartu); border:1px solid var(--garis);
  border-radius:16px; padding:20px; box-shadow:var(--bayang); transition:box-shadow 200ms ease, transform 200ms var(--keluar); }
.pilihan::before { content:""; position:absolute; inset:0 0 auto 0; height:4px; border-radius:16px 16px 0 0; background:var(--warna); }
.pilihan .atas { display:flex; gap:14px; align-items:center; }
.pilihan .urutan { font-size:12px; font-weight:600; color:var(--redup); text-transform:uppercase; letter-spacing:.07em; }
.pilihan h3 { margin:2px 0 2px; }
.pilihan .tempat { font-size:13.5px; color:var(--tinta2); }
.alasan { list-style:none; margin:0; padding:0; display:grid; gap:6px; font-size:14px; }
.alasan li { display:grid; grid-template-columns:20px minmax(0, 1fr); gap:6px; align-items:start; }
.alasan li::before { content:"✓"; width:18px; height:18px; margin-top:2px; border-radius:50%; display:grid; place-items:center; font-size:11px; font-weight:700;
  background:var(--hijau-muda); color:var(--hijau-teks); }
.alasan li.perlu::before { content:"!"; background:var(--jingga-muda); color:var(--jingga-teks); }
.pilihan .bawah { margin-top:auto; display:flex; align-items:center; justify-content:space-between; gap:10px; padding-top:12px; border-top:1px dashed var(--garis); }

/* Tombol */
.tombol { display:inline-flex; align-items:center; gap:6px; white-space:nowrap; text-decoration:none; background:var(--biru); color:#fff;
  border-radius:10px; padding:8px 14px; font-size:14px; font-weight:600; transition:transform 160ms var(--keluar), filter 150ms ease; }
.tombol:active { transform:scale(0.97); }
.tombol.halus { background:var(--kartu2); color:var(--tinta); border:1px solid var(--garis); }

/* Profil */
.profil-kepala { display:flex; gap:14px; align-items:center; margin-bottom:14px; }
.inisial { width:48px; height:48px; border-radius:14px; flex:none; display:grid; place-items:center; font-size:20px; font-weight:700; color:#fff;
  background:linear-gradient(135deg, #5fa2ff, #1c5cab); }
.fakta { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:10px; margin:14px 0; }
.fakta div { background:var(--kartu2); border:1px solid var(--garis); border-radius:12px; padding:10px 12px; }
.fakta small, .info small { display:block; text-transform:uppercase; letter-spacing:.07em; font-size:11px; font-weight:600; color:var(--redup); }
.fakta b { font-size:15px; }

/* Grafik batang dari HTML: label, jalur, batang, angka. Batang tipis dengan ujung membulat. */
.grafik { display:grid; gap:9px; }
.g-baris { display:grid; grid-template-columns:minmax(80px, 128px) minmax(0, 1fr) 54px; gap:10px; align-items:center; font-size:13.5px; }
.g-baris.dengan-catatan { grid-template-columns:minmax(80px, 128px) minmax(0, 1fr) 54px 64px; }
.g-label { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.g-jalur { height:12px; background:var(--jalur); border-radius:0 4px 4px 0; display:flex; gap:2px; }
.g-jalur i { display:block; height:100%; background:var(--biru); border-radius:0 4px 4px 0; min-width:3px; transition:filter 150ms ease; }
.g-jalur i.belum { background:var(--jingga); }
.g-jalur i.t-magang { background:var(--t1); } .g-jalur i.t-junior { background:var(--t2); } .g-jalur i.t-menengah { background:var(--t3); }
.g-jalur i.t-senior { background:var(--t4); } .g-jalur i.t-pimpinan { background:var(--t5); }
.g-jalur.tumpuk i { border-radius:0; } .g-jalur.tumpuk i:last-child { border-radius:0 4px 4px 0; }
.g-nilai { text-align:right; font-variant-numeric:tabular-nums; font-weight:600; }
.g-catatan { font-size:12px; color:var(--tinta2); }
.legenda { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12.5px; color:var(--tinta2); margin:4px 0 14px; }
.legenda span { display:inline-flex; align-items:center; gap:6px; }
.kotak { width:10px; height:10px; border-radius:3px; display:inline-block; background:var(--biru); }

/* Rencana belajar */
.rencana { display:grid; gap:10px; counter-reset:rencana; margin:0; padding:0; }
.rencana li { list-style:none; display:grid; grid-template-columns:28px minmax(0, 1fr) auto; gap:12px; align-items:center;
  background:var(--kartu2); border:1px solid var(--garis); border-radius:12px; padding:10px 14px; counter-increment:rencana; }
.rencana li::before { content:counter(rencana); width:26px; height:26px; border-radius:8px; display:grid; place-items:center; font-weight:700; font-size:13px;
  background:var(--biru-muda); color:var(--biru-teks); }
.rencana b { font-size:15px; }
.rencana .naik { text-align:right; font-size:13px; color:var(--tinta2); }
.rencana .naik strong { display:block; font-size:16px; color:var(--hijau-teks); font-variant-numeric:tabular-nums; }
.rencana .meter { margin-top:6px; }

/* Langkah berikutnya */
.langkah { margin:0; padding:0; list-style:none; display:grid; gap:10px; }
.langkah li { display:grid; grid-template-columns:minmax(0, 1fr); gap:6px; padding:12px 14px; border:1px solid var(--garis); border-radius:12px; background:var(--kartu2); }
.langkah code { justify-self:start; max-width:100%; white-space:pre-wrap; overflow-wrap:anywhere; }

/* Peringkat: penyaring tanpa JavaScript. Radio yang tersembunyi menentukan baris mana yang tampil. */
.saring-radio { position:absolute; opacity:0; pointer-events:none; }
.tab { display:inline-flex; gap:4px; background:var(--kartu2); border:1px solid var(--garis); border-radius:12px; padding:4px; margin-bottom:12px; flex-wrap:wrap; }
.tab label { cursor:pointer; font-size:13.5px; font-weight:500; color:var(--tinta2); padding:6px 12px; border-radius:9px; user-select:none;
  transition:background-color 150ms ease, color 150ms ease, transform 160ms var(--keluar); }
.tab label:active { transform:scale(0.97); }
.tab label b { font-variant-numeric:tabular-nums; margin-left:4px; color:var(--redup); font-weight:600; }
#s-semua:checked ~ .tab label[for=s-semua], #s-tinggi:checked ~ .tab label[for=s-tinggi],
#s-sedang:checked ~ .tab label[for=s-sedang], #s-rendah:checked ~ .tab label[for=s-rendah] {
  background:var(--kartu); color:var(--tinta); box-shadow:var(--bayang); }
#s-semua:focus-visible ~ .tab label[for=s-semua], #s-tinggi:focus-visible ~ .tab label[for=s-tinggi],
#s-sedang:focus-visible ~ .tab label[for=s-sedang], #s-rendah:focus-visible ~ .tab label[for=s-rendah] { outline:2px solid var(--biru); }
#s-tinggi:checked ~ .daftar .baris:not(.tinggi), #s-sedang:checked ~ .daftar .baris:not(.sedang), #s-rendah:checked ~ .daftar .baris:not(.rendah) { display:none; }
.daftar .kosong { display:none; padding:16px; text-align:center; }
#s-tinggi:checked ~ .daftar .kosong-tinggi, #s-sedang:checked ~ .daftar .kosong-sedang, #s-rendah:checked ~ .daftar .kosong-rendah { display:block; }
.daftar { border:1px solid var(--garis); border-radius:14px; overflow:hidden; }
.baris { border-top:1px solid var(--garis); scroll-margin-top:68px; }
.baris:first-child { border-top:0; }
.baris > summary { list-style:none; cursor:pointer; display:grid; grid-template-columns:30px 44px minmax(0, 1fr) 150px 64px 18px; gap:14px;
  align-items:center; padding:12px 16px; transition:background-color 150ms ease; }
.baris > summary::-webkit-details-marker { display:none; }
.baris .no { font-size:13px; font-weight:600; color:var(--redup); text-align:right; font-variant-numeric:tabular-nums; }
.baris .judul { min-width:0; }
.baris .judul b { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:15px; }
.baris .judul span { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:13px; color:var(--tinta2); }
.meter { font-size:12px; color:var(--tinta2); }
.meter .jalur { height:6px; border-radius:3px; background:var(--jalur); margin-top:4px; overflow:hidden; }
.meter .jalur i { display:block; height:100%; border-radius:3px; background:var(--hijau); }
.meter.lemah .jalur i { background:var(--jingga); }
.chip-ai { justify-self:start; font-size:12px; font-weight:600; border-radius:999px; padding:2px 8px; background:var(--jalur); color:var(--tinta2); white-space:nowrap; }
.chip-ai.ada { background:var(--biru-muda); color:var(--biru-teks); }
.panah { width:8px; height:8px; border-right:2px solid var(--redup); border-bottom:2px solid var(--redup); transform:rotate(-45deg);
  transition:transform 160ms var(--keluar); justify-self:center; }
.baris[open] > summary { background:var(--kartu2); }
.baris[open] .panah, details.lipat[open] > summary::before { transform:rotate(45deg); }
.rincian { padding:4px 16px 18px 104px; background:var(--kartu2); }
.info { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px 20px; margin:6px 0 14px; }
.info b { font-size:14px; font-weight:600; overflow-wrap:anywhere; }
.komponen { display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:12px; margin:0 0 10px; max-width:640px; }
.komponen span { display:block; font-size:12px; color:var(--tinta2); }
.komponen b { color:var(--tinta); font-variant-numeric:tabular-nums; }
.batang { height:6px; background:var(--jalur); border-radius:3px; overflow:hidden; margin-top:4px; }
.batang i { display:block; height:100%; background:var(--biru); border-radius:3px; }
.batang.lemah i { background:var(--jingga); }
.peringatan { background:var(--kuning-muda); color:var(--kuning-teks); border-radius:10px; padding:8px 12px; font-size:13px; margin:10px 0; }
.baris-skill { margin:6px 0 0; font-size:13px; }
.baris-skill > b { display:inline-block; min-width:118px; }
.aksi { display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }

/* Bagian yang bisa dibuka tutup: penilaian AI dan surat */
details.lipat { border-top:1px solid var(--garis); padding:12px 0; scroll-margin-top:68px; }
details.lipat > summary { cursor:pointer; font-weight:600; list-style:none; display:flex; align-items:center; gap:10px; }
details.lipat > summary::-webkit-details-marker { display:none; }
details.lipat > summary::before { content:""; flex:none; width:7px; height:7px; margin:0 2px; border-right:2px solid var(--redup);
  border-bottom:2px solid var(--redup); transform:rotate(-45deg); transition:transform 160ms var(--keluar); }
details.lipat > *:not(summary) { margin-top:12px; }
details[open] > *:not(summary) { animation:muncul 200ms var(--keluar); }
.kuat, .kurang { background:var(--kartu2); border:1px solid var(--garis); border-radius:12px; padding:12px 14px; }
blockquote { margin:4px 0 12px; padding:2px 0 2px 10px; border-left:3px solid var(--garis); color:var(--tinta2); font-size:13px; }
.kuat blockquote { border-color:var(--hijau); } .kurang blockquote { border-color:var(--jingga); }
.surat { background:var(--kartu2); border:1px solid var(--garis); border-radius:12px; padding:20px 22px; max-width:720px; font-size:15px; line-height:1.7; }

/* Lamaran: tahapan seleksi */
.tahapan { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }
.tahapan div { background:var(--kartu2); border:1px solid var(--garis); border-radius:12px; padding:8px 14px; min-width:96px; }
.tahapan b { display:block; font-size:20px; font-variant-numeric:tabular-nums; }
.tahapan span { font-size:12px; color:var(--tinta2); }
.tahapan .nol { opacity:.55; }

/* Tabel */
.gulung { overflow-x:auto; }
table { border-collapse:collapse; width:100%; font-size:14px; }
th, td { text-align:left; padding:9px 10px; border-bottom:1px solid var(--garis); vertical-align:top; }
th { color:var(--tinta2); font-weight:600; font-size:12.5px; white-space:nowrap; }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }

/* Gerak: hanya transform dan opacity, singkat, dan hanya di tempat yang jarang terulang. */
@keyframes muncul { from { opacity:0; transform:translateY(-4px); } }
@keyframes naik { from { opacity:0; transform:translateY(10px); } }
@keyframes pudar { from { opacity:0; } }
.kepala > *, .pilihan { animation:naik 320ms var(--keluar) backwards; }
.kepala > *:nth-child(2) { animation-delay:60ms; }
.pilihan:nth-child(2) { animation-delay:50ms; } .pilihan:nth-child(3) { animation-delay:100ms; }
/* Efek hover hanya untuk perangkat bermouse; di layar sentuh hover menempel setelah diketuk. */
@media (hover:hover) and (pointer:fine) {
  nav a:hover { background:var(--jalur); color:var(--tinta); }
  .tombol:hover { filter:brightness(1.08); }
  .pilihan:hover { box-shadow:var(--bayang-naik); transform:translateY(-2px); }
  .baris > summary:hover { background:var(--kartu2); }
  .tab label:hover { color:var(--tinta); }
  .g-baris:hover .g-jalur i { filter:brightness(1.1); }
}
@media (prefers-reduced-motion:no-preference) { html { scroll-behavior:smooth; } }
/* Pengguna yang meminta gerak dikurangi tetap mendapat pudar, tanpa perpindahan. */
@media (prefers-reduced-motion:reduce) {
  .kepala > *, .pilihan, details[open] > *:not(summary) { animation-name:pudar; }
  .pilihan, .tombol, nav a, .tab label, .panah, details.lipat > summary::before { transition-property:background-color, color, box-shadow; }
}

@media (max-width:860px) {
  .kepala, .dua-kolom { grid-template-columns:1fr; }
  .baris > summary { grid-template-columns:44px minmax(0, 1fr) 18px; }
  .baris .no, .baris .meter, .baris .chip-ai { display:none; }
  .rincian { padding:4px 16px 18px; }
  .komponen { grid-template-columns:repeat(3, minmax(0, 1fr)); }
}
@media (max-width:520px) {
  header h1 { font-size:27px; }
  .statistik { grid-template-columns:repeat(2, minmax(0, 1fr)); }
  .g-baris, .g-baris.dengan-catatan { grid-template-columns:88px minmax(0, 1fr) 46px; }
  .g-catatan { display:none; }
  .fakta { grid-template-columns:1fr; }
}
@media print {
  nav, .tombol, .tab { display:none; }
  .kepala > *, .pilihan { animation:none; }
  header { color:#000; background:none; } header .sub, .statistik span, .panel small, .legenda-kepala, .merek { color:#444; }
  section, .pilihan, .baris { break-inside:avoid; }
}
"""

# Tambahan gaya untuk laporan skill.
GAYA += """
.g-jalur i.sering { background:var(--t1); } .g-jalur i.tambahan { background:var(--redup); }
.kategori { display:grid; grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); gap:14px; }
.kategori > div { background:var(--kartu2); border:1px solid var(--garis); border-radius:14px; padding:14px 16px; }
.kategori ol { margin:8px 0 0; padding-left:20px; } .kategori li { margin:3px 0; }
.kesimpulan { background:var(--biru-muda); color:var(--biru-teks); border-radius:14px; padding:16px 18px; font-size:16px; line-height:1.6; }
.naik { color:var(--hijau-teks); font-weight:600; } .turun { color:var(--jingga-teks); font-weight:600; }
"""


# Penolong kecil

def e(nilai):
    """Semua teks dari lowongan dan AI di-escape supaya tidak terbaca sebagai HTML."""
    return escape(str(nilai if nilai is not None else ""))


def angka(nilai):
    """Menulis desimal dengan koma, seperti kebiasaan di Indonesia. None menjadi tanda strip."""
    if nilai is None:
        return "-"
    return f"{nilai:g}".replace(".", ",") if isinstance(nilai, float) else str(nilai)


def tautan(url):
    """Hanya alamat http atau https yang boleh menjadi tautan; isian lain (misalnya javascript:) diganti."""
    url = str(url or "")
    return e(url) if url.startswith(("http://", "https://")) else "#"


def rapikan(nama):
    """Nama di kamus memakai garis bawah (dukungan_it); di laporan ditulis dengan spasi."""
    return e(str(nama).replace("_", " "))


def nama_sumber(kode):
    """Nama tampilan sumber data, misalnya "remoteok" menjadi "Remote OK"."""
    return e(SUMBER_DATA.get(kode, (kode, ""))[0])


def tanggal_indo(teks):
    """Mengubah 2026-11-08 menjadi 8 Nov 2026. Teks yang bukan tanggal dikembalikan apa adanya."""
    try:
        tanggal = datetime.strptime(str(teks)[:10], "%Y-%m-%d")
    except ValueError:
        return e(teks) or "-"
    return f"{tanggal.day} {BULAN[tanggal.month - 1]} {tanggal.year}"


def judul_saringan(saringan):
    """Pertanyaan yang dijawab laporan dalam kata-kata, misalnya "backend junior, lowongan lokal"."""
    peran = " / ".join(rapikan(p) for p in saringan["peran"]) or "semua peran IT"
    tingkat = " / ".join(e(t) for t in saringan["tingkat"])
    wilayah = {"lokal": "lowongan lokal", "internasional": "lowongan internasional", "semua": "lowongan lokal dan internasional"}
    return f"{peran}{' ' + tingkat if tingkat else ''}, {wilayah.get(saringan['wilayah'], e(saringan['wilayah']))}"


def daftar_tag(nama, kelas=""):
    """Deretan label kecil, satu per nama."""
    return "".join(f'<span class="tag {kelas}">{e(isi)}</span>' for isi in nama)


def bungkus(kode, judul, isi, keterangan=""):
    """Satu bagian laporan. Kodenya menjadi sasaran tautan di menu (#kode)."""
    sub = f'<p class="kecil">{keterangan}</p>' if keterangan else ""
    return f'\n<section id="{kode}">\n  <div class="judul-bagian"><div><h2>{judul}</h2>{sub}</div></div>\n{isi}\n</section>'


def grafik_batang(baris, maks, satuan="", catatan=False):
    """Grafik batang mendatar dari HTML. Tiap baris: (label, nilai, kelas batang, teks catatan, keterangan hover).

    Lebar batang = nilai / maks. Angka ditulis di ujung kanan, jadi grafik tetap terbaca tanpa warna.
    """
    hasil = []
    for label, nilai, kelas, teks_catatan, hover in baris:
        lebar = 100 * nilai / maks if maks else 0
        kolom_catatan = f'<span class="g-catatan">{e(teks_catatan)}</span>' if catatan else ""
        hasil.append(
            f'<div class="g-baris{" dengan-catatan" if catatan else ""}" title="{e(hover)}">'
            f'<span class="g-label">{e(label)}</span><span class="g-jalur"><i class="{kelas}" style="width:{lebar:.1f}%"></i></span>'
            f'<span class="g-nilai">{angka(nilai)}{satuan}</span>{kolom_catatan}</div>'
        )
    return f'<div class="grafik">{"".join(hasil)}</div>'


# Bagian-bagian laporan

def kepala_halaman(hasil):
    """Kesimpulan satu kalimat (skill wajib), sebaran golongan, dan empat angka ringkas."""
    hitung = Counter(baris["golongan"] for baris in hasil["skill"])
    wajib = [baris["skill"] for baris in hasil["skill"] if baris["golongan"] == "wajib"]
    if wajib:
        judul = f"Kuasai dulu: {e(', '.join(wajib[:4]))}"
        sub = (f"Skill ini diminta oleh minimal {hasil['batas']['wajib']}% dari {hasil['jumlah_lowongan']} lowongan "
               f"({judul_saringan(hasil['saringan'])}) yang masih buka.")
    else:
        teratas = ", ".join(b["skill"] for b in hasil["skill"][:3])
        judul = f"Belum ada skill yang diminta {hasil['batas']['wajib']}% lowongan"
        sub = f"Permintaannya menyebar. Yang paling sering: {e(teratas)}. Dari {hasil['jumlah_lowongan']} lowongan ({judul_saringan(hasil['saringan'])})."
    sebaran = "".join(
        f'<i class="{KELAS_SEBARAN[g]}" style="flex-grow:{hitung[g]}" title="{LABEL_GOLONGAN[g]}: {hitung[g]} skill"></i>'
        for g in GOLONGAN if hitung[g]
    )
    legenda = "".join(f'<span><i class="titik {KELAS_SEBARAN[g]}"></i>{LABEL_GOLONGAN[g]} <b>{hitung[g]}</b></span>' for g in GOLONGAN)
    rentang = hasil["pasar"]["rentang_tanggal"]
    return f"""
  <div class="kepala">
    <div>
      <div class="merek"><i>◎</i>AI Job Hunter · laporan kebutuhan skill</div>
      <h1>{judul}</h1>
      <p class="sub">{sub}</p>
      <span class="lencana">Saringan: {e(hasil["nama"])}</span><span class="lencana">Dipasang {tanggal_indo(rentang[0])} – {tanggal_indo(rentang[1])}</span><span class="lencana">Dibuat {datetime.now():%d-%m-%Y %H:%M}</span>
    </div>
    <div class="panel">
      <small>Golongan {len(hasil["skill"])} skill teratas</small>
      <div class="sebaran">{sebaran}</div>
      <div class="legenda-kepala">{legenda}</div>
      <div class="statistik">
        <div><b>{hasil["jumlah_lowongan"]}</b><span>lowongan buka</span></div>
        <div><b>{hasil["jumlah_skill_berbeda"]}</b><span>skill berbeda</span></div>
        <div><b>{angka(hasil["rata_skill_per_lowongan"])}</b><span>skill per lowongan</span></div>
        <div><b>{len(hasil["pasar"]["per_sumber"])}</b><span>sumber data</span></div>
      </div>
    </div>
  </div>"""


def bagian_skill(hasil):
    """Grafik semua skill teratas. Warna dan catatan di kanan menunjukkan golongannya."""
    baris = [
        (b["skill"], b["persen_lowongan"], b["golongan"], LABEL_GOLONGAN[b["golongan"]].lower(),
         f'{b["skill"]}: {b["jumlah_lowongan"]} dari {hasil["jumlah_lowongan"]} lowongan')
        for b in hasil["skill"]
    ]
    batas = hasil["batas"]
    return bungkus("skill", "Skill yang diminta", grafik_batang(baris, max(b[1] for b in baris), "%", catatan=True),
                   f"Persen lowongan yang menyebut skill itu. Wajib dikuasai: {batas['wajib']}% atau lebih; "
                   f"sering diminta: {batas['sering']}% sampai di bawah {batas['wajib']}%; sisanya nilai tambah.")


def bagian_kategori(hasil):
    """Lima skill teratas di setiap kategori, misalnya bahasa pemrograman atau basis data."""
    kotak = "".join(
        f'<div><b>{e(NAMA_KATEGORI.get(kategori, kategori))}</b><ol>'
        + "".join(f'<li>{e(b["skill"])} <span class="kecil">{angka(b["persen_lowongan"])}%</span></li>' for b in daftar)
        + "</ol></div>"
        for kategori, daftar in hasil["per_kategori"].items()
    )
    return bungkus("kategori", "Per kategori", f'<div class="kategori">{kotak}</div>',
                   "Berguna untuk memilih satu dari tiap kelompok, misalnya satu bahasa dan satu basis data.")


def bagian_bersama(hasil):
    """Tabel skill pendamping: kalau lowongan meminta X, skill apa lagi yang biasanya ikut diminta."""
    baris = "".join(
        f"<tr><td><b>{e(b['skill'])}</b></td><td>"
        + ", ".join(f"{e(t['skill'])} <span class='kecil'>{angka(t['persen'])}%</span>" for t in b["bersama"])
        + "</td></tr>"
        for b in hasil["skill"] if b.get("bersama")
    )
    if not baris:
        return ""
    return bungkus("bersama", "Sering diminta bersama", f"<div class='gulung'><table><tr><th>Kalau diminta</th><th>Biasanya juga diminta</th></tr>{baris}</table></div>",
                   "Dari lowongan yang meminta skill di kiri, persen yang juga meminta skill di kanan.")


def bagian_tren(hasil):
    """Selisih persen antara lowongan baru dan lowongan yang lebih lama. Kosong kalau datanya kurang."""
    tren = hasil.get("tren")
    if not tren:
        return ""
    baris = "".join(
        f"<tr><td>{e(t['skill'])}</td><td class='n'>{angka(t['persen_lama'])}%</td><td class='n'>{angka(t['persen_baru'])}%</td>"
        f"<td class='n {'naik' if t['selisih'] > 0 else 'turun'}'>{'+' if t['selisih'] > 0 else ''}{angka(t['selisih'])}</td></tr>"
        for t in tren["skill"]
    )
    return bungkus("tren", "Tren", f"<table><tr><th>Skill</th><th class='n'>Lowongan lama</th><th class='n'>Lowongan baru</th><th class='n'>Selisih (poin)</th></tr>{baris}</table>",
                   f"Lowongan baru: dipasang sejak {tanggal_indo(tren['batas_tanggal'])} ({tren['jumlah_baru']} lowongan). "
                   f"Lowongan lama: sebelum itu dan masih buka ({tren['jumlah_lama']} lowongan).")


def bagian_ai(temuan):
    """Kesimpulan AI dan skill di luar kamus beserta kutipan buktinya. Kosong kalau --ai belum dipakai."""
    if not temuan:
        return ""
    kesimpulan = (f'<div class="kesimpulan">{e(temuan["kesimpulan"])}</div><p class="kecil">Ditulis {e(temuan["model"])}; '
                  "setiap angkanya sudah dicocokkan dengan data.</p>") if temuan["kesimpulan"] else \
        '<p class="kecil">Kesimpulan AI disembunyikan karena dibuat dari data lama. Jalankan lagi dengan --ai.</p>'
    baris = "".join(
        f"<tr><td><b>{e(s['nama'])}</b></td><td class='n'>{s['jumlah_lowongan']}</td><td>"
        + "<br>".join(f"“{e(b['kutipan'])}” <span class='kecil'>({e(b['judul'])})</span>" for b in s["bukti"][:2])
        + "</td></tr>"
        for s in temuan["skill_baru"]
    )
    tabel = f"<div class='gulung'><table><tr><th>Skill</th><th class='n'>Lowongan</th><th>Bukti</th></tr>{baris}</table></div>" if baris else \
        "<p>AI tidak menemukan skill baru yang buktinya sah.</p>"
    return bungkus("ai", "Temuan AI", f"{kesimpulan}<h3 style='margin-top:18px'>Skill di luar kamus</h3>{tabel}",
                   f"AI membaca {temuan['dibaca']} lowongan yang masih buka. {temuan['ditolak']} temuan ditolak karena "
                   "kutipannya tidak ada di lowongan, tidak menyebut skill itu, atau skill-nya sudah ada di kamus.")


def grafik_peran_tingkat(peran_dan_tingkat):
    """Batang bertumpuk: jumlah lowongan per peran, dipecah per tingkat dari magang sampai pimpinan."""
    total = {peran: sum(isi.values()) for peran, isi in peran_dan_tingkat.items()}
    if not total or not max(total.values()):
        return ""
    maks = max(total.values())
    baris = []
    for peran in sorted(total, key=total.get, reverse=True):
        potongan = "".join(
            f'<i class="t-{tingkat}" style="width:{100 * banyak / maks:.1f}%" title="{rapikan(peran)}, {tingkat}: {banyak} lowongan"></i>'
            for tingkat in TINGKAT if (banyak := peran_dan_tingkat[peran].get(tingkat, 0))
        )
        baris.append(f'<div class="g-baris"><span class="g-label">{rapikan(peran)}</span>'
                     f'<span class="g-jalur tumpuk" style="background:none">{potongan}</span><span class="g-nilai">{total[peran]}</span></div>')
    legenda = "".join(f'<span><i class="kotak" style="background:var(--t{nomor})"></i>{tingkat}</span>' for nomor, tingkat in enumerate(TINGKAT, start=1))
    return f'<div><b>Lowongan per peran dan tingkat</b><div class="legenda">{legenda}</div><div class="grafik">{"".join(baris)}</div></div>'


def tabel_pasar(pasar):
    """Dua tabel kecil: tahun pengalaman yang diminta per tingkat, dan median gaji per peran."""
    diminta = pasar.get("median_tahun_pengalaman_diminta", {})
    tahun = "".join(
        f"<tr><td>{e(tingkat)}</td><td class='n'>{angka(diminta[tingkat]['median'])}</td><td class='n'>{diminta[tingkat]['jumlah_lowongan']}</td></tr>"
        for tingkat in TINGKAT if tingkat in diminta
    )
    gaji = "".join(
        f"<tr><td>{rapikan(isi['peran'])}</td><td class='n'>{isi['median_usd_per_tahun']:,}</td><td class='n'>{isi['jumlah_lowongan_bergaji']}</td></tr>".replace(",", ".")
        for isi in pasar["gaji"]["per_peran"]
    )
    kosong = "<p class='kecil'>Datanya terlalu sedikit.</p>"
    return f"""
  <div class="dua">
    <div><b>Pengalaman yang diminta</b>{f"<table><tr><th>Tingkat</th><th class='n'>Median tahun</th><th class='n'>Lowongan</th></tr>{tahun}</table>" if tahun else kosong}</div>
    <div><b>Median gaji (USD per tahun)</b>{f"<table><tr><th>Peran</th><th class='n'>Median</th><th class='n'>Lowongan</th></tr>{gaji}</table>" if gaji else kosong}</div>
  </div>"""


def bagian_pasar(hasil):
    """Sebaran lowongan per peran dan tingkat, pengalaman yang diminta, dan gaji."""
    pasar = hasil["pasar"]
    sumber = ", ".join(f"{nama_sumber(nama)} {banyak}" for nama, banyak in pasar["per_sumber"].items())
    return bungkus("pasar", "Gambaran lowongan", f'{grafik_peran_tingkat(pasar["peran_dan_tingkat"])}<div style="margin-top:22px">{tabel_pasar(pasar)}</div>',
                   f"Per sumber: {sumber}. Gaji dan pengalaman hanya dari lowongan yang mencantumkannya "
                   f"({pasar['gaji']['jumlah_lowongan_bergaji']} lowongan bergaji).")


def bagian_contoh(hasil, id_buka):
    """Lowongan terbaru sebagai bukti. Lowongan yang sudah tutup sejak analisis dibuat tidak ditampilkan."""
    baris = "".join(
        f"<tr><td><a href=\"{tautan(c['url'])}\">{e(c['judul'])}</a><br><span class='kecil'>{e(c['perusahaan'])} · {nama_sumber(c['sumber'])}</span></td>"
        f"<td>{e(c['tingkat'])}</td><td>{tanggal_indo(c['tanggal'])}</td><td>{daftar_tag(c['skill'][:8])}</td></tr>"
        for c in hasil["contoh"] if id_buka is None or c["id"] in id_buka
    )
    if not baris:
        return ""
    return bungkus("contoh", "Contoh lowongan", f"<div class='gulung'><table><tr><th>Lowongan</th><th>Tingkat</th><th>Dipasang</th><th>Skill dikenali</th></tr>{baris}</table></div>",
                   "Lowongan terbaru dari saringan ini. Tautan mengarah ke halaman asli lowongan.")


def bagian_catatan():
    """Sumber data, pemakaian AI, dan batasan analisis."""
    panggilan = baca_jsonl(FILE_LOG_AI)
    berhasil = [isi for isi in panggilan if "galat" not in isi]
    sumber = ", ".join(f'<a href="{url}">{nama}</a>' for nama, url in SUMBER_DATA.values() if url)
    return bungkus("sumber", "Sumber data dan batasan", f"""
  <p>Lowongan diambil dari API publik {sumber}. Lowongan yang sudah tutup dibuang otomatis setiap pengambilan.</p>
  <p>Pemakaian AI sejak awal: {len(berhasil)} panggilan berhasil, {len(panggilan) - len(berhasil)} gagal.</p>
  <p class="kecil">Batasan: (1) sumber didominasi lowongan jarak jauh berbahasa Inggris, jadi belum mewakili seluruh pasar kerja Indonesia;
  (2) skill dikenali dengan kamus, jadi skill di luar kamus hanya terlihat lewat temuan AI;
  (3) pemeriksaan kutipan hanya memastikan kutipan ada di teks asli, bukan bahwa kesimpulan AI benar.</p>""")


# Menyusun halaman

MENU = {
    "skill": "Skill", "kategori": "Kategori", "bersama": "Bersama", "tren": "Tren", "ai": "Temuan AI",
    "pasar": "Gambaran", "contoh": "Contoh lowongan", "sumber": "Sumber data",
}


def buat_menu(isi):
    """Menu hanya memuat bagian yang benar-benar ada, ditambah tautan ke daftar semua laporan."""
    dalam = "".join(f'<a href="#{kode}">{label}</a>' for kode, label in MENU.items() if f'<section id="{kode}"' in isi)
    return f'<nav><div class="lebar">{dalam}<span class="sela"></span><a class="luar" href="../index.html">Semua laporan</a></div></nav>'


def halaman(judul, kepala, isi, menu=""):
    """Kerangka HTML yang dipakai laporan dan halaman daftar laporan."""
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{e(judul)}</title><style>{GAYA}</style></head>
<body>
<header><div class="lebar">{kepala}</div></header>
{menu}
<main class="lebar">{isi}
</main></body></html>"""


def buat_laporan(nama, id_buka=None):
    """Menulis output/<saringan>/laporan.html dari hasil.json dan mengembalikan lokasinya.

    id_buka adalah ID semua lowongan yang masih buka. Dipakai untuk menyembunyikan contoh
    lowongan dan bukti AI dari lowongan yang sudah tutup.
    """
    folder = folder_saringan(nama)
    hasil = baca_json(folder / "hasil.json")
    temuan = temuan_ai.baca_temuan(nama, id_buka if id_buka is not None else set(hasil["id_lowongan"]), hasil)
    isi = "".join([
        bagian_skill(hasil), bagian_kategori(hasil), bagian_bersama(hasil), bagian_tren(hasil),
        bagian_ai(temuan), bagian_pasar(hasil), bagian_contoh(hasil, id_buka), bagian_catatan(),
    ])
    lokasi = folder / "laporan.html"
    lokasi.write_text(halaman(f"AI Job Hunter: {nama}", kepala_halaman(hasil), isi, buat_menu(isi)), encoding="utf-8")
    buat_indeks()
    return lokasi


def buat_indeks():
    """Menulis output/index.html: daftar semua laporan yang ada, satu kartu per saringan.

    Halaman ini sengaja tidak memuat data lowongan, hanya nama saringan, jumlah lowongan, dan
    waktu laporan dibuat, supaya tidak ada lowongan yang sudah tutup tertinggal di sini.
    """
    kartu = []
    for lokasi in sorted(FOLDER_OUTPUT.glob("*/laporan.html")):
        hasil = baca_json(lokasi.parent / "hasil.json", bawaan={})
        if not hasil:
            continue
        kartu.append(f"""
<section>
  <h2>{judul_saringan(hasil["saringan"])}</h2>
  <p class="kecil">{hasil["jumlah_lowongan"]} lowongan · teratas: {e(", ".join(b["skill"] for b in hasil["skill"][:5]))}</p>
  <p><a class="tombol" href="{e(lokasi.parent.name)}/laporan.html">Buka laporan</a>
  <span class="kecil" style="margin-left:8px">diperbarui {datetime.fromtimestamp(lokasi.stat().st_mtime):%d-%m-%Y %H:%M}</span></p>
</section>""")
    kepala = (f'<div class="merek"><i>◎</i>AI Job Hunter</div><h1>Semua laporan</h1>'
              f'<p class="sub">{len(kartu)} saringan · daftar diperbarui {datetime.now():%d-%m-%Y %H:%M}</p>')
    lokasi = FOLDER_OUTPUT / "index.html"
    lokasi.parent.mkdir(parents=True, exist_ok=True)
    lokasi.write_text(halaman("AI Job Hunter: semua laporan", kepala, "".join(kartu)), encoding="utf-8")
    return lokasi
