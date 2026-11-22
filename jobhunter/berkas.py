"""Membaca dan menulis file JSON, JSONL, dan CSV dengan aman."""

import csv
import json
import os
from pathlib import Path


def baca_json(lokasi, bawaan=None):
    """Membaca file JSON. Kalau filenya belum ada dan bawaan diisi, bawaan yang dikembalikan."""
    lokasi = Path(lokasi)
    if not lokasi.exists() and bawaan is not None:
        return bawaan
    with open(lokasi, encoding="utf-8") as berkas:
        return json.load(berkas)


def simpan_json(lokasi, data):
    """Menulis JSON lewat file sementara, lalu menukarnya.

    Kalau program berhenti di tengah penulisan, file lama tetap utuh.
    """
    lokasi = Path(lokasi)
    lokasi.parent.mkdir(parents=True, exist_ok=True)
    sementara = lokasi.with_name(lokasi.name + ".tmp")
    with open(sementara, "w", encoding="utf-8") as berkas:
        json.dump(data, berkas, indent=2, ensure_ascii=False)
    os.replace(sementara, lokasi)


def tambah_jsonl(lokasi, baris):
    """Menambah satu baris JSON di akhir file, tanpa membaca isi lamanya."""
    lokasi = Path(lokasi)
    lokasi.parent.mkdir(parents=True, exist_ok=True)
    with open(lokasi, "a", encoding="utf-8") as berkas:
        berkas.write(json.dumps(baris, ensure_ascii=False) + "\n")


def baca_jsonl(lokasi):
    """Membaca file berisi satu JSON per baris. File yang belum ada dianggap kosong."""
    lokasi = Path(lokasi)
    if not lokasi.exists():
        return []
    with open(lokasi, encoding="utf-8") as berkas:
        return [json.loads(baris) for baris in berkas if baris.strip()]


def baca_csv(lokasi):
    """Membaca CSV menjadi daftar kamus. File yang belum ada dianggap kosong."""
    lokasi = Path(lokasi)
    if not lokasi.exists():
        return []
    # utf-8-sig membuang tanda BOM yang ditambahkan Excel di awal file.
    with open(lokasi, encoding="utf-8-sig", newline="") as berkas:
        return list(csv.DictReader(berkas))


def simpan_csv(lokasi, baris, kolom):
    """Menulis daftar kamus ke CSV dengan urutan kolom tertentu.

    Parameter: lokasi file, baris (daftar kamus), kolom (nama kolom yang ditulis, berurutan).
    Kunci lain di kamus diabaikan. Seperti simpan_json, file ditulis lewat file sementara.
    """
    lokasi = Path(lokasi)
    lokasi.parent.mkdir(parents=True, exist_ok=True)
    sementara = lokasi.with_name(lokasi.name + ".tmp")
    with open(sementara, "w", encoding="utf-8", newline="") as berkas:
        penulis = csv.DictWriter(berkas, fieldnames=kolom, extrasaction="ignore")
        penulis.writeheader()
        penulis.writerows(baris)
    os.replace(sementara, lokasi)
