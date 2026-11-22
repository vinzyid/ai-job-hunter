"""Fitur AI opsional (pilihan --ai): skill di luar kamus dan kesimpulan untuk pencari kerja.

Kamus skill hanya mengenali skill yang sudah ditulis di skill_it.yaml. AI membaca beberapa
deskripsi lowongan untuk menemukan skill lain, tetapi setiap temuan wajib disertai kutipan
dari deskripsi itu. Temuan ditolak kalau:
- kutipannya tidak tertulis di deskripsi (AI mengarang),
- kutipannya tidak menyebut nama skill itu, atau
- skill itu sebenarnya sudah ada di kamus (bukan temuan baru).

Kesimpulan ditulis AI dari angka hasil analisis, lalu diperiksa: setiap angka di kesimpulan
harus ada di data. Kalau tidak, jawaban ditolak dan model berikutnya dicoba.
"""

import re
from collections import defaultdict

from jobhunter import klien_ai, skill
from jobhunter.berkas import baca_json, simpan_json
from jobhunter.pengaturan import folder_saringan
from jobhunter.teks import kutipan_ada, potong, rapikan

BATAS_HURUF_DESKRIPSI = 5000
PANJANG_NAMA_MAKS = 40

ATURAN_SKILL = """Kamu membaca satu lowongan kerja IT dan mencatat skill teknis yang diminta.
Jawab hanya dengan JSON: {"skill": [{"nama": "...", "kutipan": "..."}]}
Aturan:
- Hanya skill teknis: bahasa, framework, library, basis data, layanan cloud, alat, atau metode kerja teknis.
- "kutipan" disalin persis dari deskripsi, 3 sampai 15 kata, dan harus memuat nama skill itu.
- Jangan menebak. Kalau tidak ada skill teknis, kembalikan {"skill": []}."""

ATURAN_KESIMPULAN = """Kamu menulis kesimpulan singkat untuk pencari kerja IT di Indonesia, dalam bahasa Indonesia.
Bahanmu hanya data JSON yang diberikan. Jawab hanya dengan JSON: {"kesimpulan": "..."}
Aturan:
- Tiga sampai empat kalimat: skill yang harus dikuasai dulu, skill pendamping, dan saran belajar.
- Setiap angka yang kamu tulis harus ada di data. Tulis persen tanpa desimal kalau datanya bulat.
- Jangan menyebut skill yang tidak ada di data."""


def pilih_lowongan(lowongan, jumlah):
    """Lowongan terbaru yang deskripsinya cukup panjang untuk dibaca AI."""
    cukup = [isi for isi in lowongan if len(isi.get("deskripsi") or "") >= 200]
    return sorted(cukup, key=lambda isi: isi.get("tanggal") or "", reverse=True)[:jumlah]


def periksa_temuan(data, deskripsi):
    """Memisahkan temuan AI untuk satu lowongan menjadi (diterima, ditolak).

    Parameter: JSON dari AI dan deskripsi lowongan yang dibaca AI.
    Setiap temuan yang ditolak diberi alasan. Melempar GalatAI kalau bentuk JSON-nya salah,
    supaya klien_ai mencoba model berikutnya.
    """
    if not isinstance(data.get("skill"), list):
        raise klien_ai.GalatAI("kunci skill bukan daftar")
    diterima, ditolak = [], []
    for isi in data["skill"]:
        if not isinstance(isi, dict):
            continue
        nama, kutipan = str(isi.get("nama") or "").strip(), str(isi.get("kutipan") or "").strip()
        if not nama or len(nama) > PANJANG_NAMA_MAKS:
            alasan = "nama kosong atau terlalu panjang"
        elif skill.ekstrak_skill(nama):
            alasan = "sudah ada di kamus"
        elif not kutipan_ada(kutipan, deskripsi):
            alasan = "kutipan tidak ada di deskripsi"
        elif rapikan(nama) not in rapikan(kutipan):
            alasan = "kutipan tidak menyebut skill ini"
        else:
            diterima.append({"nama": nama, "kutipan": kutipan})
            continue
        ditolak.append({"nama": nama, "kutipan": kutipan, "alasan": alasan})
    return {"diterima": diterima, "ditolak": ditolak}


def gabung_temuan(per_lowongan):
    """Menggabungkan temuan dari beberapa lowongan menjadi satu daftar per skill.

    Nama yang hanya beda huruf besar dianggap sama. Urut dari skill yang disebut paling banyak lowongan.
    """
    kelompok = defaultdict(list)
    nama_asli = {}
    for id_lowongan, judul, temuan in per_lowongan:
        for isi in temuan:
            kunci = rapikan(isi["nama"])
            nama_asli.setdefault(kunci, isi["nama"])
            kelompok[kunci].append({"id": id_lowongan, "judul": judul, "kutipan": isi["kutipan"]})
    hasil = [{"nama": nama_asli[k], "jumlah_lowongan": len({b["id"] for b in v}), "bukti": v} for k, v in kelompok.items()]
    return sorted(hasil, key=lambda isi: (-isi["jumlah_lowongan"], isi["nama"].lower()))


def cari_skill_baru(lowongan, jumlah, model=None):
    """Meminta AI membaca `jumlah` lowongan terbaru dan mengembalikan skill di luar kamus.

    Mengembalikan kamus berisi daftar skill baru, jumlah lowongan yang dibaca, dan temuan yang ditolak.
    """
    per_lowongan, semua_ditolak = [], []
    for isi in pilih_lowongan(lowongan, jumlah):
        deskripsi = potong(isi["deskripsi"], BATAS_HURUF_DESKRIPSI)
        print(f"    AI membaca: {isi['judul'][:60]}")
        data, _ = klien_ai.tanya_json(
            ATURAN_SKILL, f"Judul: {isi['judul']}\n\nDeskripsi:\n{deskripsi}", "skill_lowongan", ["skill"],
            model=model, pemeriksa=lambda jawaban, d=deskripsi: periksa_temuan(jawaban, d),
        )
        per_lowongan.append((isi["id"], isi["judul"], data["diterima"]))
        semua_ditolak += [{**tolak, "id": isi["id"]} for tolak in data["ditolak"]]
    return {"dibaca": [isi[0] for isi in per_lowongan], "skill_baru": gabung_temuan(per_lowongan), "ditolak": semua_ditolak}


def cari_angka(teks):
    """Semua angka di teks sebagai string. Koma desimal disamakan dengan titik (3,5 menjadi 3.5)."""
    return {isi.replace(",", ".") for isi in re.findall(r"\d+(?:[.,]\d+)?", teks)}


def angka_sah(hasil):
    """Angka yang boleh muncul di kesimpulan: semua angka di data yang dikirim ke AI.

    Persen juga boleh ditulis bulat, jadi 45.5 menambah 45 dan 46 sebagai angka sah.
    """
    sah = cari_angka(str(data_kesimpulan(hasil)))
    for isi in list(sah):
        if "." in isi:
            sah |= {str(int(float(isi))), str(round(float(isi)))}
    return sah


def data_kesimpulan(hasil):
    """Ringkasan kecil hasil analisis yang dikirim ke AI: saringan, jumlah lowongan, dan 12 skill teratas."""
    return {
        "saringan": hasil["saringan"], "jumlah_lowongan": hasil["jumlah_lowongan"],
        "skill": [{"skill": b["skill"], "persen": b["persen_lowongan"], "golongan": b["golongan"],
                   "sering_bersama": [t["skill"] for t in b.get("bersama", [])]} for b in hasil["skill"][:12]],
    }


def periksa_kesimpulan(data, sah):
    """Menolak kesimpulan yang kosong atau memuat angka yang tidak ada di data.

    Mengembalikan teks kesimpulan yang sudah dirapikan, atau melempar GalatAI.
    """
    teks = " ".join(str(data.get("kesimpulan") or "").split())
    if len(teks) < 40:
        raise klien_ai.GalatAI("kesimpulan terlalu pendek")
    asing = sorted(cari_angka(teks) - sah)
    if asing:
        raise klien_ai.GalatAI(f"kesimpulan memuat angka yang tidak ada di data: {asing}")
    return {"kesimpulan": teks}


def buat_kesimpulan(hasil, model=None):
    """Meminta AI menulis kesimpulan dari hasil analisis. Mengembalikan (teks, model yang menjawab)."""
    sah = angka_sah(hasil)
    data, catatan = klien_ai.tanya_json(
        ATURAN_KESIMPULAN, str(data_kesimpulan(hasil)), "kesimpulan_skill", ["kesimpulan"],
        model=model, pemeriksa=lambda jawaban: periksa_kesimpulan(jawaban, sah),
    )
    return data["kesimpulan"], catatan.get("model_penjawab")


def jalankan(hasil, lowongan, jumlah, model=None):
    """Menjalankan kedua fitur AI untuk satu hasil analisis dan menyimpannya ke temuan_ai.json.

    Parameter lowongan adalah lowongan yang sama dengan yang dianalisis (sudah disaring).
    Temuan diberi tanggal analisis, supaya laporan bisa mengenali temuan yang sudah basi.
    """
    temuan = cari_skill_baru(lowongan, jumlah, model)
    kesimpulan, penjawab = buat_kesimpulan(hasil, model)
    isi = {"tanggal_analisis": hasil["tanggal_analisis"], "jumlah_lowongan": hasil["jumlah_lowongan"],
           "kesimpulan": kesimpulan, "model": penjawab, **temuan}
    simpan_json(folder_saringan(hasil["nama"]) / "temuan_ai.json", isi)
    return isi


def baca_temuan(nama, id_buka, hasil):
    """Temuan AI yang masih berlaku untuk hasil analisis sekarang, atau None.

    Bukti dari lowongan yang sudah tutup dibuang dan jumlahnya dihitung ulang. Kesimpulan hanya
    dipakai kalau dibuat dari analisis yang sama (tanggal dan jumlah lowongan sama), karena
    angkanya berubah setiap kali lowongan diambil ulang.
    """
    isi = baca_json(folder_saringan(nama) / "temuan_ai.json", bawaan={})
    if not isi:
        return None
    skill_baru = []
    for baris in isi["skill_baru"]:
        bukti = [b for b in baris["bukti"] if b["id"] in id_buka]
        if bukti:
            skill_baru.append({**baris, "bukti": bukti, "jumlah_lowongan": len({b["id"] for b in bukti})})
    sama = isi["tanggal_analisis"] == hasil["tanggal_analisis"] and isi["jumlah_lowongan"] == hasil["jumlah_lowongan"]
    return {
        "skill_baru": skill_baru,
        "dibaca": len([i for i in isi["dibaca"] if i in id_buka]),
        "ditolak": len(isi["ditolak"]),
        "kesimpulan": isi["kesimpulan"] if sama else None,
        "model": isi.get("model"),
    }
