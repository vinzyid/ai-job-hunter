"""Penghubung ke layanan AI GripHub Router (format permintaannya sama dengan OpenAI).

Yang diurus di sini:
- Hanya tiga model yang boleh dipakai. Kalau router mengalihkan ke model lain, jawabannya ditolak.
- Model dicoba berurutan. Kalau satu gagal, model berikutnya dipakai.
- Jawaban disimpan di data/cache_ai/, jadi permintaan yang sama tidak dikirim dua kali.
- Setiap panggilan dicatat di output/log_ai.jsonl.

API key dibaca dari file .env dengan nama GRIPHUB_API_KEY.
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

from jobhunter.berkas import baca_json, simpan_json, tambah_jsonl
from jobhunter.pengaturan import AKAR, FILE_LOG_AI, FOLDER_CACHE_AI

URL_API = "https://griphubrouter.web.id/v1/chat/completions"
# Urutan dari uji 10 November 2026: deepseek menjawab sekitar 2 detik, gemini 13 detik,
# glm-5.3 tidak menjawab dalam 90 detik.
MODEL_DIIZINKAN = ["deepseek-v4.1-flash", "gemini-4-argon", "glm-5.3"]
BATAS_WAKTU_DETIK = 120
SUHU = 0.2  # Suhu rendah membuat jawaban lebih konsisten antarpercobaan.


class GalatAI(Exception):
    """Semua model gagal menjawab, atau jawabannya tidak bisa dipakai."""


def periksa_model(daftar):
    """Memastikan semua model di daftar termasuk tiga model yang diizinkan.

    Mengembalikan daftar itu sendiri, atau menghentikan program kalau ada model asing.
    """
    asing = [nama for nama in daftar if nama not in MODEL_DIIZINKAN]
    if asing:
        raise SystemExit(f"Model tidak diizinkan: {asing}. Pilihan: {MODEL_DIIZINKAN}.")
    return daftar


def ambil_api_key():
    """Membaca GRIPHUB_API_KEY dari file .env. Program berhenti dengan petunjuk kalau belum diisi."""
    load_dotenv(AKAR / ".env")
    api_key = os.getenv("GRIPHUB_API_KEY")
    if not api_key:
        raise SystemExit("GRIPHUB_API_KEY belum ada. Salin .env.example menjadi .env, lalu isi key-nya.")
    return api_key


def kunci_cache(model, pesan):
    """Nama file cache: 24 huruf pertama hash SHA-256 dari model, suhu, dan isi pesan.

    Pertanyaan yang sama persis selalu menghasilkan kunci yang sama, jadi jawabannya bisa dipakai ulang.
    """
    isi = json.dumps({"model": model, "suhu": SUHU, "pesan": pesan}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(isi.encode("utf-8")).hexdigest()[:24]


def model_sama(diminta, penjawab):
    """Benar kalau model yang menjawab adalah model yang diminta.

    Router kadang menulis nama yang sama dengan bentuk lain: menambah akhiran (gemini-4-argon-d),
    awalan penyedia, atau huruf besar (deepseek-ai/DeepSeek-V4.1-Flash-1017). Bagian sebelum "/"
    dibuang dan huruf disamakan, lalu yang diperiksa awalannya. Model lain tetap ditolak.
    """
    nama = penjawab.rsplit("/", 1)[-1].lower()
    return bool(nama) and nama.startswith(diminta.lower())


def panggil_model(model, pesan, api_key):
    """Mengirim satu permintaan ke satu model dan mengembalikan jawabannya."""
    mulai = time.perf_counter()
    respons = requests.post(
        URL_API,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "temperature": SUHU, "messages": pesan},
        timeout=BATAS_WAKTU_DETIK,
    )
    respons.raise_for_status()
    isi = respons.json()
    pilihan = isi["choices"][0]
    penjawab = isi.get("model") or ""
    if not model_sama(model, penjawab):
        raise GalatAI(f"router mengalihkan {model} ke {penjawab or 'model tak dikenal'}")
    teks = pilihan["message"].get("content") or ""
    if not teks.strip():
        raise GalatAI(f"{model} mengembalikan jawaban kosong")
    return {
        "teks": teks,
        "model_diminta": model,
        "model_penjawab": penjawab,
        "alasan_berhenti": pilihan.get("finish_reason"),
        "detik": round(time.perf_counter() - mulai, 1),
        "total_token": isi.get("usage", {}).get("total_tokens"),
    }


def tanya(sistem, pengguna, tugas, model=None, pakai_cache=True):
    """Bertanya ke AI. Mengembalikan kamus berisi teks jawaban dan catatan pemakaiannya."""
    pesan = [{"role": "system", "content": sistem}, {"role": "user", "content": pengguna}]
    daftar_model = periksa_model(model or MODEL_DIIZINKAN)

    if pakai_cache:
        for nama in daftar_model:
            lokasi = FOLDER_CACHE_AI / f"{kunci_cache(nama, pesan)}.json"
            if lokasi.exists():
                return {**baca_json(lokasi), "dari_cache": True}

    api_key = ambil_api_key()
    galat_terakhir = None
    for nama in daftar_model:
        catatan = {"waktu": datetime.now().isoformat(timespec="seconds"), "tugas": tugas, "model_diminta": nama}
        try:
            hasil = panggil_model(nama, pesan, api_key)
        except (requests.RequestException, GalatAI, KeyError, IndexError, ValueError) as galat:
            # API key tidak boleh ikut tercatat kalau muncul di pesan galat.
            galat_terakhir = str(galat).replace(api_key, "***")
            tambah_jsonl(FILE_LOG_AI, {**catatan, "galat": galat_terakhir})
            print(f"    {nama} gagal: {galat_terakhir[:120]}")
            continue
        tambah_jsonl(FILE_LOG_AI, {**catatan, **{k: v for k, v in hasil.items() if k != "teks"}})
        simpan_json(FOLDER_CACHE_AI / f"{kunci_cache(nama, pesan)}.json", hasil)
        return {**hasil, "dari_cache": False}
    raise GalatAI(f"Semua model gagal untuk tugas {tugas}. Galat terakhir: {galat_terakhir}")


def ambil_json(teks):
    """Mengambil objek JSON dari jawaban model, yang kadang dibungkus ```json atau diberi pengantar."""
    teks = re.sub(r"^```(?:json)?\s*|\s*```$", "", teks.strip())
    try:
        return json.loads(teks)
    except json.JSONDecodeError:
        awal, akhir = teks.find("{"), teks.rfind("}")
        if awal == -1 or akhir <= awal:
            raise GalatAI("jawaban model tidak memuat JSON")
        try:
            return json.loads(teks[awal:akhir + 1])
        except json.JSONDecodeError as galat:
            raise GalatAI(f"JSON dari model rusak: {galat}")


def tanya_json(sistem, pengguna, tugas, kunci_wajib, model=None, pemeriksa=None):
    """Seperti tanya(), tetapi jawabannya harus JSON yang memuat semua kunci wajib.

    pemeriksa adalah fungsi yang menerima JSON itu dan mengembalikan bentuk rapinya, atau
    melempar GalatAI kalau isinya tidak bisa dipakai. Kalau jawaban sebuah model tidak
    bisa dipakai, model berikutnya dicoba.
    """
    galat_terakhir = None
    for nama in periksa_model(model or MODEL_DIIZINKAN):
        try:
            hasil = tanya(sistem, pengguna, tugas, model=[nama])
            data = ambil_json(hasil["teks"])
            kurang = [kunci for kunci in kunci_wajib if kunci not in data]
            if kurang:
                raise GalatAI(f"kunci {kurang} tidak ada di jawaban {nama}")
            if pemeriksa:
                data = pemeriksa(data)
        except GalatAI as galat:
            galat_terakhir = galat
            # Jawaban yang tidak bisa dipakai dibuang dari cache supaya bisa diminta ulang.
            pesan = [{"role": "system", "content": sistem}, {"role": "user", "content": pengguna}]
            (FOLDER_CACHE_AI / f"{kunci_cache(nama, pesan)}.json").unlink(missing_ok=True)
            continue
        hasil.pop("teks")
        return data, hasil
    raise GalatAI(f"Tidak ada model yang memberi JSON sah untuk tugas {tugas}: {galat_terakhir}")
