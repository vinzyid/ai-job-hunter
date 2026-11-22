"""Lokasi file dan pengaturan yang dipakai semua modul."""

from pathlib import Path

import yaml

AKAR = Path(__file__).resolve().parent.parent

FOLDER_KONFIGURASI = AKAR / "konfigurasi"
FOLDER_DATA = AKAR / "data"
FOLDER_LOWONGAN = FOLDER_DATA / "lowongan"
FOLDER_MENTAH = FOLDER_LOWONGAN / "mentah"
FOLDER_CACHE_AI = FOLDER_DATA / "cache_ai"
FOLDER_OUTPUT = AKAR / "output"

FILE_LOWONGAN = FOLDER_LOWONGAN / "lowongan.json"
FILE_LOWONGAN_MANUAL = FOLDER_DATA / "lowongan_manual.csv"
FILE_LOG_AI = FOLDER_OUTPUT / "log_ai.jsonl"

# Tingkat jabatan, urut dari yang paling awal.
TINGKAT = ["magang", "junior", "menengah", "senior", "pimpinan"]
WILAYAH = ["lokal", "internasional", "semua"]


def baca_yaml(nama):
    """Membaca satu file YAML di folder konfigurasi.

    Parameter: nama file, misalnya "preferensi.yaml".
    Mengembalikan isinya sebagai kamus Python.
    """
    with open(FOLDER_KONFIGURASI / nama, encoding="utf-8") as berkas:
        return yaml.safe_load(berkas)


def baca_preferensi():
    """Membaca preferensi.yaml dan menolak isi yang tidak masuk akal sejak awal.

    Mengembalikan kamus pengaturan. Program berhenti dengan pesan yang jelas kalau
    wilayah tidak dikenal atau ambang golongan skill tidak berurutan.
    """
    preferensi = baca_yaml("preferensi.yaml")
    if preferensi["wilayah"] not in WILAYAH:
        raise SystemExit(f"wilayah di preferensi.yaml harus salah satu dari {WILAYAH}.")
    wajib, sering = preferensi["batas_wajib"], preferensi["batas_sering"]
    if not 0 < sering < wajib <= 100:
        raise SystemExit("Di preferensi.yaml harus berlaku 0 < batas_sering < batas_wajib <= 100.")
    return preferensi


def folder_saringan(nama):
    """Folder hasil untuk satu saringan, misalnya output/lokal-backend-junior/."""
    return FOLDER_OUTPUT / nama
