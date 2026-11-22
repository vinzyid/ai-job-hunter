"""Mengambil lowongan dari API publik, lalu menyamakan bentuknya.

Semua sumber di sini menyediakan API resmi yang boleh dipakai gratis dengan syarat
mencantumkan sumber dan menautkan ke halaman aslinya. Program tidak mengambil data
dari situs yang melarangnya (misalnya JobStreet, Glints, atau LinkedIn). Lowongan dari
situs seperti itu bisa dicatat sendiri di data/lowongan_manual.csv.
"""

import hashlib
import re
import time
from collections import Counter
from datetime import date, datetime, timezone

import requests

from jobhunter import skill
from jobhunter.berkas import baca_csv, baca_json, simpan_csv, simpan_json, tambah_jsonl
from jobhunter.pengaturan import FILE_LOWONGAN, FILE_LOWONGAN_MANUAL, FOLDER_LOWONGAN, FOLDER_MENTAH
from jobhunter.teks import buang_html, rapikan

PENGENAL = {"User-Agent": "ai-job-hunter-uts/1.0 (proyek kuliah, bukan komersial)"}
BATAS_WAKTU_DETIK = 40
# Aturan lowongan tutup. Lowongan yang tutup dibuang dari data dan dicatat di arsip.
BATAS_HARI_TIDAK_TERLIHAT = 14  # Sumber hanya menampilkan lowongan terbaru, jadi diberi masa tunggu.
MAKS_CEK_TAUTAN = 60            # Batas pemeriksaan halaman per pengambilan, supaya tidak membebani situs.
KODE_HALAMAN_HILANG = {404, 410}
FILE_ARSIP_TUTUP = FOLDER_LOWONGAN / "arsip_tutup.jsonl"
MINIMAL_LOWONGAN = 10  # Di bawah ini peringkat dan statistik tidak berarti.
JEDA_DETIK = 1.0  # Jeda antarpermintaan supaya tidak membebani server sumber.

PENCARIAN_HIMALAYAS = [
    "software engineer", "backend developer", "frontend developer", "full stack developer",
    "data analyst", "devops engineer", "junior developer", "software engineer intern",
    # Tambahan untuk fresh graduate, karena lowongan tingkat awal jauh lebih sedikit.
    "graduate software engineer", "entry level developer", "junior data analyst",
]

POLA_INDONESIA = re.compile(
    r"indonesia|jakarta|bandung|surabaya|yogyakarta|jogja|semarang|medan|makassar|denpasar|\bbali\b|"
    r"tangerang|bekasi|depok|bogor|malang|\bsolo\b|surakarta|palembang|balikpapan|batam|pekanbaru",
    re.IGNORECASE,
)

KOLOM_CSV = [
    "id", "sumber", "wilayah", "judul", "perusahaan", "peran", "tingkat", "lokasi", "jenis",
    "gaji_min", "gaji_maks", "mata_uang", "tanggal", "skill", "url",
]


def minta(url, parameter=None):
    """Mengirim satu permintaan GET ke API dan mengembalikan JSON-nya.

    Parameter: alamat API dan parameter pencarian (kamus, boleh kosong).
    Kode HTTP 4xx/5xx menjadi galat (raise_for_status). Setelah setiap permintaan program
    berhenti JEDA_DETIK detik supaya tidak membebani server sumber.
    """
    respons = requests.get(url, params=parameter, headers=PENGENAL, timeout=BATAS_WAKTU_DETIK)
    respons.raise_for_status()
    time.sleep(JEDA_DETIK)
    return respons.json()


def ke_tanggal(nilai):
    """Menerima detik sejak 1970 atau teks ISO, mengembalikan tanggal berbentuk 2026-11-10."""
    if not nilai:
        return ""
    if isinstance(nilai, (int, float)) or str(nilai).isdigit():
        return datetime.fromtimestamp(int(nilai), tz=timezone.utc).date().isoformat()
    return str(nilai)[:10]


def ke_angka(nilai):
    """Gaji dari sumber kadang berupa teks, 0, atau kosong. Yang bukan angka positif menjadi None."""
    try:
        angka = float(nilai)
    except (TypeError, ValueError):
        return None
    return int(angka) if angka > 0 else None


# Tiap fungsi di bawah mengambil satu sumber dan mengembalikan (data mentah, daftar lowongan
# dalam bentuk yang sama). Kunci yang dipakai mengikuti nama asli di API masing-masing.

def ambil_remotive():
    """Lowongan kerja jarak jauh dari Remotive. Mengembalikan (data mentah, daftar lowongan)."""
    mentah = minta("https://remotive.com/api/remote-jobs")
    hasil = [
        {
            "judul": isi["title"], "perusahaan": isi["company_name"],
            "lokasi": isi.get("candidate_required_location") or "", "jenis": isi.get("job_type") or "",
            "tag": isi.get("tags") or [], "gaji_teks": isi.get("salary") or "",
            "tanggal": ke_tanggal(isi.get("publication_date")), "url": isi["url"],
            "deskripsi": isi.get("description"),
        }
        for isi in mentah["jobs"]
    ]
    return mentah, hasil


def ambil_arbeitnow(jumlah_halaman=2):
    """Hanya lowongan jarak jauh. Sisanya kerja di kantor di Jerman, yang tidak bisa dilamar dari Indonesia."""
    mentah, hasil = [], []
    for halaman in range(1, jumlah_halaman + 1):
        isi_halaman = minta("https://www.arbeitnow.com/api/job-board-api", {"page": halaman})["data"]
        mentah.extend(isi_halaman)
        for isi in isi_halaman:
            if not isi.get("remote"):
                continue
            hasil.append({
                "judul": isi["title"], "perusahaan": isi["company_name"],
                "lokasi": f"{isi.get('location') or ''} (remote)",
                "jenis": ", ".join(isi.get("job_types") or []), "tag": isi.get("tags") or [],
                "tanggal": ke_tanggal(isi.get("created_at")), "url": isi["url"],
                "deskripsi": isi.get("description"),
            })
    return mentah, hasil


def ambil_jobicy():
    """100 lowongan terbaru kategori dev dari Jobicy, lengkap dengan gaji kalau dicantumkan."""
    mentah = minta("https://jobicy.com/api/v2/remote-jobs", {"count": 100, "industry": "dev"})
    hasil = [
        {
            "judul": isi["jobTitle"], "perusahaan": isi["companyName"],
            "lokasi": isi.get("jobGeo") or "", "jenis": ", ".join(isi.get("jobType") or []),
            "tag": isi.get("jobIndustry") or [],
            "gaji_min": ke_angka(isi.get("salaryMin")), "gaji_maks": ke_angka(isi.get("salaryMax")),
            "mata_uang": isi.get("salaryCurrency") or "", "periode_gaji": isi.get("salaryPeriod") or "",
            "tanggal": ke_tanggal(isi.get("pubDate")), "url": isi["url"],
            "deskripsi": isi.get("jobDescription"),
        }
        for isi in mentah["jobs"]
    ]
    return mentah, hasil


def ambil_himalayas(negara=None):
    """Tanpa negara: lowongan dari mana saja. Dengan negara: hanya yang menerima pelamar dari negara itu."""
    mentah, hasil = [], []
    for kata in PENCARIAN_HIMALAYAS:
        parameter = {"q": kata, "country": negara} if negara else {"q": kata}
        isi_halaman = minta("https://himalayas.app/jobs/api/search", parameter)["jobs"]
        mentah.extend(isi_halaman)
        for isi in isi_halaman:
            hasil.append({
                "judul": isi["title"], "perusahaan": isi["companyName"],
                "lokasi": ", ".join(isi.get("locationRestrictions") or []) or "Worldwide",
                "jenis": isi.get("employmentType") or "", "tag": isi.get("categories") or [],
                "gaji_min": ke_angka(isi.get("minSalary")), "gaji_maks": ke_angka(isi.get("maxSalary")),
                "mata_uang": isi.get("currency") or "", "periode_gaji": isi.get("salaryPeriod") or "",
                "tanggal": ke_tanggal(isi.get("pubDate")),
                "kedaluwarsa": ke_tanggal(isi.get("expiryDate")),
                "url": isi.get("applicationLink") or isi.get("guid"),
                "deskripsi": isi.get("description"),
            })
    return mentah, hasil


def ambil_himalayas_indonesia():
    """Lowongan Himalayas yang menerima pelamar dari Indonesia. Sumber utama lowongan lokal."""
    return ambil_himalayas(negara="Indonesia")


def ambil_remoteok():
    """Lowongan dari Remote OK. Gaji di sumber ini selalu dalam USD per tahun."""
    mentah = minta("https://remoteok.com/api")
    hasil = [
        {
            "judul": isi["position"], "perusahaan": isi.get("company") or "",
            "lokasi": isi.get("location") or "Worldwide", "jenis": "", "tag": isi.get("tags") or [],
            "gaji_min": ke_angka(isi.get("salary_min")), "gaji_maks": ke_angka(isi.get("salary_max")),
            "mata_uang": "USD", "periode_gaji": "tahunan",
            "tanggal": ke_tanggal(isi.get("date")), "url": isi["url"],
            "deskripsi": isi.get("description"),
        }
        # Elemen pertama berisi ketentuan pemakaian, bukan lowongan.
        for isi in mentah if "position" in isi
    ]
    return mentah, hasil


def ambil_manual():
    """Lowongan yang dicatat sendiri oleh pengguna di data/lowongan_manual.csv."""
    # Baris yang kolomnya kurang berisi None, jadi setiap sel dijadikan teks dulu.
    baris = [{kunci: (nilai or "").strip() for kunci, nilai in isi.items() if kunci} for isi in baca_csv(FILE_LOWONGAN_MANUAL)]
    hasil = [
        {
            "judul": isi["judul"], "perusahaan": isi.get("perusahaan", ""), "lokasi": isi.get("lokasi", ""),
            "jenis": isi.get("jenis", ""), "tag": [], "gaji_teks": isi.get("gaji", ""),
            "tanggal": isi.get("tanggal", ""), "url": isi.get("url", ""), "deskripsi": isi.get("deskripsi", ""),
        }
        for isi in baris if isi.get("judul")
    ]
    return baris, hasil


SUMBER = {
    "remotive": ambil_remotive,
    "arbeitnow": ambil_arbeitnow,
    "jobicy": ambil_jobicy,
    "himalayas": ambil_himalayas,
    "himalayas_indonesia": ambil_himalayas_indonesia,
    "remoteok": ambil_remoteok,
    "manual": ambil_manual,
}


def tentukan_wilayah(lokasi, sumber):
    """Memilah lowongan menjadi "lokal" (untuk Indonesia) atau "internasional".

    Lokal berarti lokasinya menyebut Indonesia atau kota di Indonesia dan paling banyak
    menyebut tiga tempat. Lowongan jarak jauh yang menerima puluhan negara, termasuk
    Indonesia, tetap dihitung internasional. Lowongan yang dicatat sendiri selalu lokal.
    """
    if sumber == "manual":
        return "lokal"
    tempat = [isi for isi in re.split(r"[,;/]", lokasi) if isi.strip()]
    return "lokal" if POLA_INDONESIA.search(lokasi) and len(tempat) <= 3 else "internasional"


def saring_wilayah(lowongan, wilayah):
    """Hanya lowongan wilayah yang diminta ("lokal" atau "internasional"); "semua" tidak menyaring."""
    if wilayah == "semua":
        return lowongan
    return [isi for isi in lowongan if isi["wilayah"] == wilayah]


def buat_id(sumber, url, judul, perusahaan):
    """ID pendek yang tetap sama setiap kali lowongan yang sama diambil lagi."""
    dasar = f"{sumber}|{url or judul + perusahaan}"
    return hashlib.sha1(dasar.encode("utf-8")).hexdigest()[:10]


def lengkapi(lowongan, sumber, hari_ini):
    """Membersihkan deskripsi dan menambah peran, tingkat, serta skill. None kalau bukan lowongan IT."""
    judul = " ".join(str(lowongan["judul"]).split())
    peran = skill.tentukan_peran(judul)
    if peran is None:
        return None
    deskripsi = buang_html(lowongan.get("deskripsi") or "")
    # Tag dari sumber sering memuat skill yang tidak ditulis ulang di deskripsi.
    teks_skill = deskripsi + "\n" + ", ".join(str(isi) for isi in lowongan.get("tag", []))
    return {
        "id": buat_id(sumber, lowongan.get("url"), judul, lowongan.get("perusahaan", "")),
        "sumber": sumber,
        "judul": judul,
        "perusahaan": " ".join(str(lowongan.get("perusahaan") or "").split()),
        "peran": peran,
        "tingkat": skill.tentukan_tingkat(judul),
        "tahun_pengalaman": skill.tahun_pengalaman(deskripsi),
        "lokasi": lowongan.get("lokasi", ""),
        "wilayah": tentukan_wilayah(lowongan.get("lokasi", ""), sumber),
        "jenis": lowongan.get("jenis", ""),
        "gaji_min": lowongan.get("gaji_min"),
        "gaji_maks": lowongan.get("gaji_maks"),
        "mata_uang": lowongan.get("mata_uang", ""),
        "periode_gaji": lowongan.get("periode_gaji", ""),
        "gaji_teks": lowongan.get("gaji_teks", ""),
        "tanggal": lowongan.get("tanggal", ""),
        "kedaluwarsa": lowongan.get("kedaluwarsa", ""),
        "url": lowongan.get("url", ""),
        "skill": skill.ekstrak_skill(teks_skill),
        "deskripsi": deskripsi,
        "pertama_dilihat": hari_ini,
        "terakhir_dilihat": hari_ini,
    }


def kunci_kembar(lowongan):
    """Lowongan yang sama sering dipasang di beberapa situs. Judul dan perusahaan dipakai untuk mengenalinya."""
    bersih = lambda isi: re.sub(r"[^a-z0-9]+", " ", rapikan(isi)).strip()
    return bersih(lowongan["judul"]), bersih(lowongan["perusahaan"])


def gabungkan(lama, baru):
    """Menggabungkan lowongan baru ke data lama.

    Lowongan yang sudah ada diperbarui tetapi tanggal pertama dilihat dipertahankan.
    Lowongan kembar dari sumber lain dilewati. Mengembalikan (hasil, jumlah baru, jumlah kembar).
    """
    hasil = {isi["id"]: isi for isi in lama}
    kunci_ada = {kunci_kembar(isi): isi["id"] for isi in lama}
    jumlah_baru = jumlah_kembar = 0
    for isi in baru:
        kunci = kunci_kembar(isi)
        if isi["id"] in hasil:
            isi["pertama_dilihat"] = hasil[isi["id"]]["pertama_dilihat"]
        elif kunci in kunci_ada:
            # Kembarannya masih dipasang, berarti lowongan yang tersimpan juga masih buka.
            asli = hasil[kunci_ada[kunci]]
            asli["terakhir_dilihat"] = max(asli["terakhir_dilihat"], isi["terakhir_dilihat"])
            jumlah_kembar += 1
            continue
        else:
            jumlah_baru += 1
        hasil[isi["id"]] = isi
        kunci_ada[kunci] = isi["id"]
    return list(hasil.values()), jumlah_baru, jumlah_kembar


def segarkan_peran(tersimpan):
    """Menghitung ulang peran dan tingkat lowongan tersimpan dengan kamus yang sekarang.

    Kamus di skill_it.yaml bisa berubah setelah lowongan disimpan. Mengembalikan
    (yang tetap, yang dibuang karena judulnya tidak lagi terbaca sebagai lowongan IT).
    """
    tetap, bukan_it = [], []
    for isi in tersimpan:
        peran = skill.tentukan_peran(isi["judul"])
        if peran is None:
            bukan_it.append({**isi, "alasan_tutup": "bukan lowongan IT menurut kamus sekarang"})
        else:
            tetap.append({**isi, "peran": peran, "tingkat": skill.tentukan_tingkat(isi["judul"])})
    return tetap, bukan_it


def alasan_tutup(lowongan, hari_ini):
    """Alasan lowongan dianggap tutup dilihat dari tanggalnya saja, atau None kalau masih buka."""
    if lowongan.get("kedaluwarsa") and lowongan["kedaluwarsa"] < hari_ini:
        return "melewati tanggal tutup dari sumber"
    selisih = (date.fromisoformat(hari_ini) - date.fromisoformat(lowongan["terakhir_dilihat"])).days
    if selisih > BATAS_HARI_TIDAK_TERLIHAT:
        return f"tidak muncul lagi di sumber selama {selisih} hari"
    return None


def halaman_hilang(url):
    """Benar kalau halaman lowongan sudah dihapus (404 atau 410).

    Galat jaringan dan kode lain, misalnya 403 dari situs yang menolak program,
    tidak dianggap tutup karena belum tentu lowongannya hilang.
    """
    if not str(url).startswith("http"):
        return False
    try:
        respons = requests.get(url, headers=PENGENAL, timeout=15, stream=True)
        respons.close()
    except requests.RequestException:
        return False
    time.sleep(0.3)
    return respons.status_code in KODE_HALAMAN_HILANG


def pilah_tutup(semua, hari_ini, sumber_berhasil, cek_halaman=None):
    """Memisahkan lowongan yang masih buka dari yang tutup. Mengembalikan (buka, tutup).

    Lowongan dianggap tutup kalau salah satu berlaku:
    1. tanggal tutup dari sumber sudah lewat;
    2. tidak muncul lagi di sumbernya lebih dari BATAS_HARI_TIDAK_TERLIHAT hari;
    3. dicatat sendiri, lalu barisnya dihapus dari lowongan_manual.csv;
    4. tidak muncul di pengambilan hari ini dan halamannya sudah dihapus.
    cek_halaman adalah fungsi pemeriksa halaman. Kalau None, aturan 4 dilewati.
    """
    buka, tutup, perlu_dicek = [], [], []
    for isi in semua:
        alasan = alasan_tutup(isi, hari_ini)
        tidak_muncul = isi["sumber"] in sumber_berhasil and isi["terakhir_dilihat"] < hari_ini
        if not alasan and tidak_muncul and isi["sumber"] == "manual":
            alasan = "dihapus dari lowongan_manual.csv"
        if alasan:
            tutup.append({**isi, "alasan_tutup": alasan})
        elif tidak_muncul and cek_halaman:
            perlu_dicek.append(isi)
        else:
            buka.append(isi)

    # Yang paling lama tidak terlihat diperiksa dulu. Sisanya menunggu pengambilan berikutnya.
    perlu_dicek.sort(key=lambda isi: isi["terakhir_dilihat"])
    for nomor, isi in enumerate(perlu_dicek):
        if nomor < MAKS_CEK_TAUTAN and cek_halaman(isi["url"]):
            tutup.append({**isi, "alasan_tutup": "halaman lowongan sudah dihapus"})
        else:
            buka.append(isi)
    return buka, tutup


def arsipkan(tutup, hari_ini):
    """Mencatat lowongan yang dibuang, tanpa deskripsinya, supaya bisa ditelusuri."""
    for isi in tutup:
        tambah_jsonl(FILE_ARSIP_TUTUP, {
            "tanggal_dibuang": hari_ini,
            **{kunci: isi[kunci] for kunci in ["id", "sumber", "judul", "perusahaan", "url", "pertama_dilihat", "terakhir_dilihat", "alasan_tutup"]},
        })


def baca_lowongan():
    """Lowongan yang masih buka. Yang tutup menurut tanggal disaring juga di sini,
    supaya tidak muncul walaupun pengambilan belum dijalankan lagi."""
    tersimpan = baca_json(FILE_LOWONGAN, bawaan=[])
    if not tersimpan:
        raise SystemExit('Belum ada data lowongan. Jalankan "python main.py ambil" dulu.')
    hari_ini = date.today().isoformat()
    lowongan = [isi for isi in tersimpan if not alasan_tutup(isi, hari_ini)]
    if not lowongan:
        raise SystemExit('Semua lowongan tersimpan sudah terlalu lama. Jalankan "python main.py ambil" untuk memperbarui.')
    # Data yang disimpan sebelum ada pemilahan wilayah dilengkapi saat dibaca.
    for isi in lowongan:
        isi.setdefault("wilayah", tentukan_wilayah(isi["lokasi"], isi["sumber"]))
    return lowongan


def baca_lowongan_wilayah(wilayah):
    """Lowongan untuk satu pilihan wilayah. Berhenti dengan petunjuk kalau datanya terlalu sedikit."""
    lowongan = saring_wilayah(baca_lowongan(), wilayah)
    if len(lowongan) < MINIMAL_LOWONGAN:
        raise SystemExit(
            f"Lowongan wilayah {wilayah} baru {len(lowongan)}, minimal {MINIMAL_LOWONGAN}. "
            "Untuk lokal: jalankan ambil lagi, atau tambahkan lowongan dari Glints, JobStreet, atau Kalibrr "
            "ke data/lowongan_manual.csv."
        )
    return lowongan


def jalankan(nama_sumber=None, cek_tautan=True):
    """Mengambil semua sumber yang diminta, lalu membuang lowongan yang sudah tutup.

    Satu sumber yang gagal tidak menghentikan yang lain, dan lowongan dari sumber
    yang gagal tidak diperiksa halamannya pada pengambilan ini.
    """
    hari_ini = date.today().isoformat()
    semua, bukan_it = segarkan_peran(baca_json(FILE_LOWONGAN, bawaan=[]))
    ringkasan = []
    sumber_berhasil = set()
    for nama in nama_sumber or SUMBER:
        try:
            mentah, daftar = SUMBER[nama]()
        except (requests.RequestException, KeyError, ValueError) as galat:
            print(f"  {nama}: gagal ({type(galat).__name__}: {galat})")
            ringkasan.append({"sumber": nama, "galat": str(galat)})
            continue
        if nama != "manual":
            simpan_json(FOLDER_MENTAH / f"{nama}_{hari_ini}.json", mentah)
        sumber_berhasil.add(nama)
        lengkap = [isi for isi in (lengkapi(lowongan, nama, hari_ini) for lowongan in daftar) if isi]
        # Lowongan yang masih ditampilkan sumber tetapi sudah lewat tanggal tutupnya tidak dimasukkan.
        lengkap = [isi for isi in lengkap if not alasan_tutup(isi, hari_ini)]
        semua, jumlah_baru, jumlah_kembar = gabungkan(semua, lengkap)
        print(f"  {nama}: {len(daftar)} diambil, {len(lengkap)} lowongan IT, {jumlah_baru} baru, {jumlah_kembar} kembar")
        ringkasan.append({
            "sumber": nama, "diambil": len(daftar), "lowongan_it": len(lengkap),
            "baru": jumlah_baru, "kembar": jumlah_kembar,
        })

    semua, tutup = pilah_tutup(semua, hari_ini, sumber_berhasil, halaman_hilang if cek_tautan else None)
    tutup += bukan_it
    arsipkan(tutup, hari_ini)
    # Jumlah hari dibuang dari alasan supaya alasan yang sama terhitung bersama.
    alasan = dict(Counter(isi["alasan_tutup"].split(" selama ")[0] for isi in tutup))
    print(f"  Lowongan yang dibuang: {len(tutup)}" + "".join(f"\n    {nama}: {banyak}" for nama, banyak in alasan.items()))

    semua.sort(key=lambda isi: isi["tanggal"], reverse=True)
    simpan_json(FILE_LOWONGAN, semua)
    simpan_csv(
        FOLDER_LOWONGAN / "lowongan.csv",
        [{**isi, "skill": "; ".join(isi["skill"])} for isi in semua],
        KOLOM_CSV,
    )
    simpan_json(FOLDER_LOWONGAN / "ringkasan_pengambilan.json", {"tanggal": hari_ini, "sumber": ringkasan, "tutup_dibuang": alasan, "total": len(semua)})
    print(f"Total tersimpan: {len(semua)} lowongan IT di {FILE_LOWONGAN.relative_to(FILE_LOWONGAN.parents[2])}")
    return semua
