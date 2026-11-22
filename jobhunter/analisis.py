"""Menghitung skill yang diminta lowongan IT, lalu menyimpan hasilnya ke JSON, CSV, Excel, dan PNG.

Alurnya:
1. saring_lowongan  : pilih lowongan sesuai wilayah, peran, dan tingkat yang ditanyakan;
2. hitung_skill     : berapa persen lowongan yang menyebut tiap skill;
3. golongkan        : wajib dikuasai, sering diminta, atau nilai tambah;
4. skill_bersama, tren_skill, ringkasan_pasar : keterangan tambahan;
5. simpan_hasil     : menulis semuanya ke folder output/<saringan>/.

Angka di sini hanya menggambarkan lowongan yang berhasil diambil dari sumber program ini
(kebanyakan lowongan jarak jauh berbahasa Inggris), bukan seluruh pasar kerja.
"""

from collections import Counter
from datetime import date, timedelta

import matplotlib

matplotlib.use("Agg")  # Menggambar ke file tanpa membuka jendela.
import matplotlib.pyplot as plt
import pandas as pd

from jobhunter import skill
from jobhunter.berkas import simpan_csv, simpan_json
from jobhunter.pengaturan import TINGKAT, folder_saringan
from jobhunter.teks import rapikan

MINIMAL_LOWONGAN = 5        # Di bawah ini persentase tidak berarti.
MINIMAL_DATA_GAJI = 5
JUMLAH_CONTOH = 10          # Contoh lowongan yang ditampilkan di laporan.
JUMLAH_TEMAN = 3            # Skill pendamping yang ditampilkan untuk tiap skill teratas.
LABEL_GOLONGAN = {"wajib": "wajib dikuasai", "sering": "sering diminta", "tambahan": "nilai tambah"}

# Warna grafik PNG, sama dengan laporan HTML.
PERMUKAAN, TINTA, TINTA_KEDUA, GARIS = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9"
WARNA_GOLONGAN = {"wajib": "#2a78d6", "sering": "#86b6ef", "tambahan": "#c9ced8"}


def persen(bagian, total):
    """Persentase dengan satu angka desimal. Total nol menghasilkan 0, bukan galat pembagian."""
    return round(100 * bagian / total, 1) if total else 0.0


# 1. Menyaring lowongan

def nama_saringan(wilayah, peran=None, tingkat=None):
    """Nama folder hasil untuk satu pertanyaan, misalnya "lokal-backend-junior".

    Parameter peran dan tingkat berupa daftar (boleh kosong). Beberapa pilihan digabung dengan "+".
    """
    bagian = [wilayah]
    if peran:
        bagian.append("+".join(sorted(peran)))
    if tingkat:
        bagian.append("+".join(sorted(tingkat, key=TINGKAT.index)))
    return "-".join(bagian)


def terbuka_untuk_indonesia(isi, preferensi):
    """Benar kalau lowongan bisa dilamar dari Indonesia.

    Lowongan lokal selalu bisa. Lowongan internasional harus menyebut salah satu kata di
    lokasi_diterima (misalnya worldwide atau asia), kecuali hanya_lokasi_diterima dimatikan.
    """
    if isi["wilayah"] == "lokal" or not preferensi.get("hanya_lokasi_diterima", True):
        return True
    lokasi = rapikan(isi.get("lokasi") or "")
    return any(rapikan(kata) in lokasi for kata in preferensi["lokasi_diterima"])


def saring_lowongan(lowongan, preferensi, peran=None, tingkat=None):
    """Lowongan yang bisa dilamar dari Indonesia dan cocok dengan peran dan tingkat yang diminta.

    Parameter peran dan tingkat berupa daftar; kosong berarti semua. Mengembalikan daftar baru.
    """
    return [
        isi for isi in lowongan
        if terbuka_untuk_indonesia(isi, preferensi)
        and (not peran or isi["peran"] in peran)
        and (not tingkat or isi["tingkat"] in tingkat)
    ]


# 2 dan 3. Menghitung dan menggolongkan skill

def golongkan(nilai_persen, batas_wajib, batas_sering):
    """Golongan satu skill dari persen lowongan yang memintanya: "wajib", "sering", atau "tambahan"."""
    if nilai_persen >= batas_wajib:
        return "wajib"
    return "sering" if nilai_persen >= batas_sering else "tambahan"


def hitung_skill(lowongan, batas_wajib=30, batas_sering=10):
    """Semua skill yang disebut lowongan, urut dari yang paling sering.

    Setiap baris berisi nama skill, kategorinya, jumlah dan persen lowongan yang menyebutnya,
    serta golongannya. Satu lowongan dihitung sekali per skill walaupun skill-nya disebut berkali-kali,
    karena isi["skill"] sudah berupa daftar tanpa duplikat.
    """
    hitungan = Counter(nama for isi in lowongan for nama in isi["skill"])
    hasil = []
    for nama, banyak in hitungan.most_common():
        nilai = persen(banyak, len(lowongan))
        hasil.append({
            "skill": nama, "kategori": skill.kategori_skill(nama), "jumlah_lowongan": banyak,
            "persen_lowongan": nilai, "golongan": golongkan(nilai, batas_wajib, batas_sering),
        })
    return hasil


def skill_per_kategori(daftar_skill, jumlah=5):
    """Mengelompokkan hasil hitung_skill per kategori, paling banyak `jumlah` skill per kategori.

    Kategori diurutkan seperti di kamus, dan kategori tanpa skill tidak ditulis.
    """
    hasil = {}
    for kategori in skill.daftar_kategori() + ["lainnya"]:
        isi = [baris for baris in daftar_skill if baris["kategori"] == kategori][:jumlah]
        if isi:
            hasil[kategori] = isi
    return hasil


def skill_bersama(lowongan, nama_skill, jumlah=JUMLAH_TEMAN):
    """Skill yang paling sering diminta bersama `nama_skill`.

    Dari semua lowongan yang meminta nama_skill, dihitung berapa persen yang juga meminta
    skill lain. Contoh: 60% lowongan yang meminta React juga meminta TypeScript.
    """
    dengan = [isi for isi in lowongan if nama_skill in isi["skill"]]
    hitungan = Counter(lain for isi in dengan for lain in isi["skill"] if lain != nama_skill)
    return [{"skill": lain, "persen": persen(banyak, len(dengan))} for lain, banyak in hitungan.most_common(jumlah)]


def tren_skill(lowongan, hari_ini, hari=14, jumlah=8):
    """Membandingkan lowongan yang dipasang dalam `hari` hari terakhir dengan yang lebih lama.

    Hanya memakai lowongan yang masih buka, jadi lowongan yang sudah tutup tidak ikut dihitung.
    Mengembalikan None kalau salah satu kelompok terlalu sedikit untuk dibandingkan. Kalau cukup,
    mengembalikan skill dengan selisih persen terbesar (naik maupun turun).
    """
    batas = (date.fromisoformat(hari_ini) - timedelta(days=hari)).isoformat()
    baru = [isi for isi in lowongan if isi.get("tanggal") and isi["tanggal"] >= batas]
    lama = [isi for isi in lowongan if isi.get("tanggal") and isi["tanggal"] < batas]
    if len(baru) < MINIMAL_LOWONGAN or len(lama) < MINIMAL_LOWONGAN:
        return None
    persen_baru = {b["skill"]: b["persen_lowongan"] for b in hitung_skill(baru)}
    persen_lama = {b["skill"]: b["persen_lowongan"] for b in hitung_skill(lama)}
    selisih = [
        {"skill": nama, "persen_baru": persen_baru.get(nama, 0.0), "persen_lama": persen_lama.get(nama, 0.0),
         "selisih": round(persen_baru.get(nama, 0.0) - persen_lama.get(nama, 0.0), 1)}
        for nama in set(persen_baru) | set(persen_lama)
    ]
    selisih.sort(key=lambda isi: abs(isi["selisih"]), reverse=True)
    return {"batas_tanggal": batas, "jumlah_baru": len(baru), "jumlah_lama": len(lama), "skill": selisih[:jumlah]}


# 4. Gambaran pasar

def gaji_per_peran(tabel):
    """Median gaji tahunan dalam USD per peran, hanya dari lowongan yang mencantumkannya.

    Parameter: DataFrame lowongan. Mengembalikan (daftar per peran, jumlah lowongan bergaji).
    """
    tahunan = tabel["periode_gaji"].fillna("").str.lower().str.contains("year|annual|tahun")
    ada = tabel[(tabel["mata_uang"] == "USD") & tahunan & tabel["gaji_min"].notna() & tabel["gaji_maks"].notna()].copy()
    ada["tengah"] = (ada["gaji_min"] + ada["gaji_maks"]) / 2
    # Angka di bawah 10.000 hampir pasti gaji per jam atau per bulan yang salah label.
    ada = ada[ada["tengah"].between(10_000, 500_000)]
    hasil = []
    for peran, kelompok in ada.groupby("peran"):
        if len(kelompok) >= MINIMAL_DATA_GAJI:
            hasil.append({"peran": peran, "jumlah_lowongan_bergaji": len(kelompok), "median_usd_per_tahun": int(kelompok["tengah"].median())})
    return sorted(hasil, key=lambda isi: isi["median_usd_per_tahun"], reverse=True), len(ada)


def ringkasan_pasar(lowongan):
    """Sebaran lowongan per sumber, peran, dan tingkat, ditambah pengalaman dan gaji yang diminta.

    Memakai pandas: value_counts untuk menghitung, crosstab untuk tabel peran x tingkat,
    dan groupby untuk median per kelompok.
    """
    tabel = pd.DataFrame(lowongan)
    for kolom in ["periode_gaji", "mata_uang", "gaji_min", "gaji_maks", "tahun_pengalaman"]:
        if kolom not in tabel:
            tabel[kolom] = None
    per_peran = tabel["peran"].value_counts()
    silang = pd.crosstab(tabel["peran"], tabel["tingkat"]).reindex(columns=TINGKAT, fill_value=0).loc[per_peran.index]
    gaji, jumlah_bergaji = gaji_per_peran(tabel)
    tahun = tabel.dropna(subset=["tahun_pengalaman"]).groupby("tingkat")["tahun_pengalaman"]
    tanggal = [isi for isi in tabel["tanggal"].fillna("") if isi]
    return {
        "rentang_tanggal": [min(tanggal), max(tanggal)] if tanggal else ["", ""],
        "per_sumber": tabel["sumber"].value_counts().to_dict(),
        "per_peran": per_peran.to_dict(),
        "per_tingkat": tabel["tingkat"].value_counts().reindex(TINGKAT, fill_value=0).to_dict(),
        "peran_dan_tingkat": {peran: baris.to_dict() for peran, baris in silang.iterrows()},
        "median_tahun_pengalaman_diminta": {
            tingkat: {"median": float(kelompok.median()), "jumlah_lowongan": int(kelompok.count())}
            for tingkat, kelompok in tahun if tingkat in TINGKAT
        },
        "gaji": {"jumlah_lowongan_bergaji": jumlah_bergaji, "per_peran": gaji},
    }


def contoh_lowongan(lowongan, jumlah=JUMLAH_CONTOH):
    """Lowongan terbaru beserta skill-nya, untuk ditampilkan sebagai bukti di laporan."""
    terbaru = sorted(lowongan, key=lambda isi: isi.get("tanggal") or "", reverse=True)[:jumlah]
    kunci = ["id", "judul", "perusahaan", "peran", "tingkat", "lokasi", "sumber", "tanggal", "url", "skill"]
    return [{k: isi.get(k) for k in kunci} for isi in terbaru]


def analisis_skill(lowongan, preferensi, saringan, hari_ini=None):
    """Seluruh analisis untuk satu saringan, sebagai kamus yang siap disimpan ke JSON.

    Parameter: lowongan yang masih buka (sudah disaring wilayahnya), preferensi, saringan
    (kamus wilayah, peran, tingkat), dan tanggal hari ini (bawaan: hari ini).
    Program berhenti dengan petunjuk kalau lowongan yang cocok terlalu sedikit.
    """
    hari_ini = hari_ini or date.today().isoformat()
    terpilih = saring_lowongan(lowongan, preferensi, saringan["peran"], saringan["tingkat"])
    if len(terpilih) < MINIMAL_LOWONGAN:
        raise SystemExit(
            f"Hanya {len(terpilih)} lowongan yang cocok dengan saringan ini (minimal {MINIMAL_LOWONGAN}). "
            "Longgarkan saringan, misalnya hapus --tingkat atau pakai --wilayah semua."
        )
    daftar = hitung_skill(terpilih, preferensi["batas_wajib"], preferensi["batas_sering"])
    jumlah = preferensi.get("jumlah_skill", 20)
    for baris in daftar[:10]:
        baris["bersama"] = skill_bersama(terpilih, baris["skill"])
    return {
        "saringan": saringan,
        "nama": nama_saringan(saringan["wilayah"], saringan["peran"], saringan["tingkat"]),
        "tanggal_analisis": hari_ini,
        "jumlah_lowongan": len(terpilih),
        "jumlah_skill_berbeda": len(daftar),
        "rata_skill_per_lowongan": round(sum(len(isi["skill"]) for isi in terpilih) / len(terpilih), 1),
        "batas": {"wajib": preferensi["batas_wajib"], "sering": preferensi["batas_sering"]},
        "skill": daftar[:jumlah],
        "per_kategori": skill_per_kategori(daftar),
        "tren": tren_skill(terpilih, hari_ini, preferensi.get("hari_tren", 14)),
        "pasar": ringkasan_pasar(terpilih),
        "contoh": contoh_lowongan(terpilih),
        "id_lowongan": sorted(isi["id"] for isi in terpilih),
    }


# 5. Menyimpan hasil

def gambar_skill(hasil, lokasi):
    """Grafik batang PNG skill teratas, diwarnai menurut golongan, dengan angka persen di ujung batang."""
    data = hasil["skill"][:15][::-1]
    gambar, sumbu = plt.subplots(figsize=(8, 0.42 * len(data) + 1.8), facecolor=PERMUKAAN)
    sumbu.set_facecolor(PERMUKAAN)
    for sisi in ["top", "right", "left"]:
        sumbu.spines[sisi].set_visible(False)
    sumbu.tick_params(colors=TINTA_KEDUA, length=0, labelsize=10)
    sumbu.xaxis.grid(True, color=GARIS, linewidth=0.8)
    sumbu.set_axisbelow(True)
    batang = sumbu.barh([b["skill"] for b in data], [b["persen_lowongan"] for b in data],
                        color=[WARNA_GOLONGAN[b["golongan"]] for b in data], height=0.62)
    sumbu.bar_label(batang, labels=[f"{b['persen_lowongan']:.0f}%" for b in data], padding=4, color=TINTA, fontsize=9)
    sumbu.set_xlabel("Persen lowongan yang menyebut skill ini", color=TINTA_KEDUA)
    sumbu.set_title(f"Skill yang diminta: {hasil['nama']} ({hasil['jumlah_lowongan']} lowongan)", color=TINTA, loc="left", fontsize=13, pad=12)
    lokasi.parent.mkdir(parents=True, exist_ok=True)
    gambar.savefig(lokasi, dpi=160, facecolor=PERMUKAAN, bbox_inches="tight")
    plt.close(gambar)


def simpan_excel(hasil, lokasi):
    """Satu file Excel dengan tiga lembar: skill, skill_bersama, dan contoh_lowongan."""
    skill_tabel = pd.DataFrame([{k: v for k, v in baris.items() if k != "bersama"} for baris in hasil["skill"]])
    bersama = pd.DataFrame([
        {"skill": baris["skill"], "diminta_bersama": teman["skill"], "persen": teman["persen"]}
        for baris in hasil["skill"] if "bersama" in baris for teman in baris["bersama"]
    ])
    contoh = pd.DataFrame([{**isi, "skill": ", ".join(isi["skill"])} for isi in hasil["contoh"]])
    with pd.ExcelWriter(lokasi, engine="openpyxl") as penulis:
        skill_tabel.to_excel(penulis, sheet_name="skill", index=False)
        bersama.to_excel(penulis, sheet_name="skill_bersama", index=False)
        contoh.to_excel(penulis, sheet_name="contoh_lowongan", index=False)


def simpan_hasil(hasil):
    """Menulis hasil.json, skill.csv, skill.xlsx, dan skill.png ke output/<saringan>/.

    Mengembalikan folder tempat hasil disimpan.
    """
    folder = folder_saringan(hasil["nama"])
    simpan_json(folder / "hasil.json", hasil)
    simpan_csv(folder / "skill.csv", hasil["skill"], ["skill", "kategori", "jumlah_lowongan", "persen_lowongan", "golongan"])
    simpan_excel(hasil, folder / "skill.xlsx")
    gambar_skill(hasil, folder / "skill.png")
    return folder
