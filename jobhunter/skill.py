"""Mengenali skill, peran, dan tingkat dari teks dengan kamus di konfigurasi/skill_it.yaml."""

import re
from functools import lru_cache

from jobhunter.pengaturan import baca_yaml

# Alias hanya cocok sebagai kata utuh. Tanda +, #, dan titik ikut dijaga supaya
# "C" tidak cocok di dalam "C++" dan "sql" tidak cocok di dalam "mysql".
SEBELUM = r"(?<![A-Za-z0-9+#.])"
SESUDAH = r"(?![A-Za-z0-9+#])"


@lru_cache(maxsize=1)
def muat_kamus():
    """Membaca kamus sekali saja, lalu menyusun satu regex untuk tiap skill."""
    isi = baca_yaml("skill_it.yaml")
    pola_skill = {}
    kategori_skill = {}
    for kategori, daftar in isi["skill"].items():
        for nama, alias in daftar.items():
            # Alias terpanjang dicoba dulu, supaya "react native" tidak terbaca sebagai "react".
            pilihan = sorted({nama.lower(), *[a.lower() for a in alias or []]}, key=len, reverse=True)
            gabungan = "|".join(re.escape(a).replace(r"\ ", r"[ -]?") for a in pilihan)
            pola_skill[nama] = re.compile(SEBELUM + "(?:" + gabungan + ")" + SESUDAH, re.IGNORECASE)
            kategori_skill[nama] = kategori
    for nama, pola in isi["pola_khusus"].items():
        pola_skill[nama] = re.compile(pola)
        kategori_skill[nama] = isi["kategori_pola_khusus"][nama]

    def susun(kelompok):
        """Menggabungkan daftar pola tiap nama (peran atau tingkat) menjadi satu regex."""
        return {nama: re.compile("|".join(pola), re.IGNORECASE) for nama, pola in kelompok.items()}

    return {
        "skill": pola_skill,
        "kategori": kategori_skill,
        "peran": susun(isi["peran"]),
        "tingkat": susun(isi["tingkat"]),
        "bukan_it": re.compile("|".join(isi["bukan_it"]), re.IGNORECASE),
    }


def ekstrak_skill(teks):
    """Mengembalikan daftar skill yang disebut di teks, urut abjad."""
    kamus = muat_kamus()["skill"]
    return sorted(nama for nama, pola in kamus.items() if pola.search(teks))


def bukti_skill(teks, nama, lebar=60):
    """Mengembalikan potongan teks di sekitar tempat skill disebut, atau None."""
    pola = muat_kamus()["skill"].get(nama)
    cocok = pola.search(teks) if pola else None
    if not cocok:
        return None
    awal, akhir = max(0, cocok.start() - lebar), min(len(teks), cocok.end() + lebar)
    return " ".join(teks[awal:akhir].split())


def kategori_skill(nama):
    """Kategori skill di kamus (bahasa, frontend, basis_data, ...), atau "lainnya" kalau tidak ada."""
    return muat_kamus()["kategori"].get(nama, "lainnya")


def tentukan_peran(judul):
    """Peran pertama yang polanya cocok dengan judul. None berarti bukan lowongan IT."""
    if muat_kamus()["bukan_it"].search(judul):
        return None
    for nama, pola in muat_kamus()["peran"].items():
        if pola.search(judul):
            return nama
    return None


def tentukan_tingkat(judul):
    """Tingkat pertama yang polanya cocok dengan judul. Kalau tidak ada yang cocok, dianggap menengah."""
    for nama, pola in muat_kamus()["tingkat"].items():
        if pola.search(judul):
            return nama
    return "menengah"


def daftar_peran():
    """Nama semua peran di kamus, untuk pilihan --peran di terminal."""
    return list(muat_kamus()["peran"])


def daftar_kategori():
    """Nama kategori skill sesuai urutan di kamus, ditambah kategori pola khusus."""
    isi = baca_yaml("skill_it.yaml")
    return list(dict.fromkeys([*isi["skill"], *isi["kategori_pola_khusus"].values()]))


def tahun_pengalaman(teks):
    """Angka tahun pengalaman terbesar yang diminta, misalnya 5 dari "5+ years of experience"."""
    temuan = re.findall(
        r"(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*)?(?:years?|yrs?|tahun)(?:\s+of)?\s+(?:\w+\s+){0,3}?(?:experience|pengalaman)",
        teks,
        re.IGNORECASE,
    )
    angka = [int(isi) for isi in temuan if int(isi) <= 20]
    return max(angka) if angka else None
