"""Tes untuk bagian yang tidak butuh internet maupun AI. Jalankan dengan: python -m pytest"""

import pytest

from jobhunter import analisis, berkas, klien_ai, laporan, skill, sumber, temuan_ai, teks


# Teks

def test_buang_html_membuka_html_yang_di_escape():
    assert teks.buang_html("&lt;p&gt;Python &amp;amp; SQL&lt;/p&gt;&lt;script&gt;x()&lt;/script&gt;") == "Python & SQL"


def test_kutipan_ada_mengabaikan_huruf_besar_dan_spasi():
    cv = "Built REST API endpoints\nwith FastAPI and PostgreSQL."
    assert teks.kutipan_ada("built rest api endpoints with FastAPI", cv)
    assert not teks.kutipan_ada("built GraphQL endpoints", cv)
    assert not teks.kutipan_ada("", cv)


# Skill, peran, dan tingkat

def test_ekstrak_skill_hanya_kata_utuh():
    hasil = skill.ekstrak_skill("We use JavaScript, MySQL and React Native. Scalable systems.")
    assert {"JavaScript", "MySQL", "React Native"} <= set(hasil)
    assert "Java" not in hasil and "SQL" not in hasil and "Scala" not in hasil


def test_ekstrak_skill_alias_dan_tanda_baca():
    hasil = skill.ekstrak_skill("Experience with k8s, C++, C#, .NET, Postgres and Golang.")
    assert {"Kubernetes", "C++", "C#", ".NET", "PostgreSQL", "Go"} <= set(hasil)


def test_kata_biasa_tidak_terbaca_sebagai_skill():
    hasil = skill.ekstrak_skill("Go to the office, excel at your work, and express your ideas.")
    assert not {"Go", "Excel", "Express"} & set(hasil)


@pytest.mark.parametrize("judul, peran, tingkat", [
    ("Senior Backend Engineer (Python)", "backend", "senior"),
    ("Software Engineering Intern", "software_umum", "magang"),
    ("Junior Data Analyst", "data_analyst", "junior"),
    ("Lead DevOps Engineer", "devops_cloud", "pimpinan"),
    ("Full-Stack Developer", "fullstack", "menengah"),
])
def test_peran_dan_tingkat_dari_judul(judul, peran, tingkat):
    assert skill.tentukan_peran(judul) == peran
    assert skill.tentukan_tingkat(judul) == tingkat


def test_judul_bukan_it_tidak_punya_peran():
    assert skill.tentukan_peran("Account Executive") is None
    # Kata teknis di judul tidak menjadikan lowongan penjualan atau anotasi sebagai lowongan IT.
    assert skill.tentukan_peran("Senior Sales Engineer - AI Agents") is None
    assert skill.tentukan_peran("AI Trainer - Video Annotation") is None


def test_kata_ai_tidak_mengalahkan_peran_yang_disebut_di_judul():
    assert skill.tentukan_peran("Senior Backend Engineer Build AI Agents") == "backend"
    assert skill.tentukan_peran("Full Stack Developer (AI-First)") == "fullstack"
    assert skill.tentukan_peran("Senior AI Engineer") == "ai_ml"
    assert skill.tentukan_peran("Machine Learning Engineer (Python)") == "ai_ml"


def test_tahun_pengalaman_mengambil_yang_terbesar():
    assert skill.tahun_pengalaman("3+ years of experience, ideally 5 years of professional experience") == 5
    assert skill.tahun_pengalaman("Founded 10 years ago") is None


# Sumber lowongan

def test_wilayah_lokal_dan_internasional():
    assert sumber.tentukan_wilayah("Jakarta, Indonesia", "himalayas") == "lokal"
    assert sumber.tentukan_wilayah("Indonesia, Malaysia, Singapore, Thailand, Vietnam", "himalayas") == "internasional"
    assert sumber.tentukan_wilayah("Worldwide", "remoteok") == "internasional"
    assert sumber.tentukan_wilayah("", "manual") == "lokal"


def contoh_lowongan(**ubah):
    dasar = {
        "id": "a1", "sumber": "uji", "wilayah": "internasional", "judul": "Junior Backend Developer",
        "perusahaan": "PT Uji", "peran": "backend", "tingkat": "junior", "lokasi": "Worldwide", "url": "https://contoh.test/1",
        "tahun_pengalaman": None, "skill": ["Python", "PostgreSQL", "Docker", "AWS"],
        "deskripsi": "We need a python backend developer who knows postgresql, docker and aws to build rest api services.",
        "pertama_dilihat": "2026-11-01", "terakhir_dilihat": "2026-11-01",
    }
    return {**dasar, **ubah}


def test_gabungkan_mengenali_lowongan_kembar_dan_menjaga_tanggal():
    lama = [contoh_lowongan()]
    baru = [
        contoh_lowongan(pertama_dilihat="2026-11-10", terakhir_dilihat="2026-11-10"),
        contoh_lowongan(id="b2", sumber="lain", judul="junior  backend developer", perusahaan="PT UJI"),
        contoh_lowongan(id="c3", judul="Frontend Developer"),
    ]
    hasil, jumlah_baru, jumlah_kembar = sumber.gabungkan(lama, baru)
    assert (len(hasil), jumlah_baru, jumlah_kembar) == (2, 1, 1)
    asli = next(isi for isi in hasil if isi["id"] == "a1")
    assert asli["pertama_dilihat"] == "2026-11-01" and asli["terakhir_dilihat"] == "2026-11-10"


def test_alasan_tutup_dari_tanggal():
    assert sumber.alasan_tutup(contoh_lowongan(terakhir_dilihat="2026-11-10"), "2026-11-20") is None
    assert "15 hari" in sumber.alasan_tutup(contoh_lowongan(terakhir_dilihat="2026-11-05"), "2026-11-20")
    assert "tanggal tutup" in sumber.alasan_tutup(contoh_lowongan(terakhir_dilihat="2026-11-20", kedaluwarsa="2026-11-19"), "2026-11-20")
    assert sumber.alasan_tutup(contoh_lowongan(terakhir_dilihat="2026-11-20", kedaluwarsa="2026-11-20"), "2026-11-20") is None


def test_pilah_tutup():
    hari_ini = "2026-11-20"
    semua = [
        contoh_lowongan(id="muncul", terakhir_dilihat=hari_ini),
        contoh_lowongan(id="hilang", terakhir_dilihat="2026-11-18", url="https://contoh.test/hilang"),
        contoh_lowongan(id="masih_ada", terakhir_dilihat="2026-11-18", url="https://contoh.test/ada"),
        contoh_lowongan(id="sumber_gagal", sumber="lain", terakhir_dilihat="2026-11-18", url="https://contoh.test/hilang"),
        contoh_lowongan(id="terlalu_lama", sumber="lain", terakhir_dilihat="2026-11-01"),
        contoh_lowongan(id="lewat_tanggal", terakhir_dilihat=hari_ini, kedaluwarsa="2026-11-15"),
        contoh_lowongan(id="manual_dihapus", sumber="manual", terakhir_dilihat="2026-11-19"),
        contoh_lowongan(id="manual_ada", sumber="manual", terakhir_dilihat=hari_ini),
    ]
    diperiksa = []

    def cek_halaman(url):
        diperiksa.append(url)
        return url.endswith("/hilang")

    buka, tutup = sumber.pilah_tutup(semua, hari_ini, {"uji", "manual"}, cek_halaman)
    assert sorted(isi["id"] for isi in buka) == ["manual_ada", "masih_ada", "muncul", "sumber_gagal"]
    assert {isi["id"]: isi["alasan_tutup"].split(" selama ")[0] for isi in tutup} == {
        "hilang": "halaman lowongan sudah dihapus",
        "terlalu_lama": "tidak muncul lagi di sumber",
        "lewat_tanggal": "melewati tanggal tutup dari sumber",
        "manual_dihapus": "dihapus dari lowongan_manual.csv",
    }
    # Hanya lowongan yang tidak muncul hari ini dari sumber yang berhasil diambil yang diperiksa halamannya.
    assert sorted(diperiksa) == ["https://contoh.test/ada", "https://contoh.test/hilang"]
    # Tanpa pemeriksa halaman, lowongan yang tidak muncul tetap dianggap buka sampai masa tunggunya habis.
    buka, _ = sumber.pilah_tutup(semua, hari_ini, {"uji", "manual"}, None)
    assert "hilang" in [isi["id"] for isi in buka]


def test_kembaran_yang_masih_dipasang_memperbarui_tanggal_terlihat():
    lama = [contoh_lowongan(terakhir_dilihat="2026-11-01")]
    kembar = contoh_lowongan(id="b2", sumber="lain", terakhir_dilihat="2026-11-10")
    hasil, _, _ = sumber.gabungkan(lama, [kembar])
    assert [(isi["id"], isi["terakhir_dilihat"]) for isi in hasil] == [("a1", "2026-11-10")]


def test_baca_lowongan_menyaring_yang_tutup(tmp_path, monkeypatch):
    from datetime import date, timedelta
    hari_ini = date.today()
    monkeypatch.setattr(sumber, "FILE_LOWONGAN", tmp_path / "lowongan.json")
    berkas.simpan_json(tmp_path / "lowongan.json", [
        contoh_lowongan(id="buka", terakhir_dilihat=hari_ini.isoformat()),
        contoh_lowongan(id="lama", terakhir_dilihat=(hari_ini - timedelta(days=30)).isoformat()),
        contoh_lowongan(id="lewat", terakhir_dilihat=hari_ini.isoformat(), kedaluwarsa=(hari_ini - timedelta(days=1)).isoformat()),
    ])
    assert [isi["id"] for isi in sumber.baca_lowongan()] == ["buka"]


def test_lengkapi_membuang_lowongan_bukan_it():
    mentah = {"judul": "Sales Manager", "perusahaan": "X", "deskripsi": "<p>Sell things</p>", "url": "u"}
    assert sumber.lengkapi(mentah, "uji", "2026-11-10") is None


def test_segarkan_peran_memakai_kamus_sekarang():
    tersimpan = [
        {"id": "a", "judul": "Senior Backend Engineer Build AI Agents", "peran": "ai_ml", "tingkat": "menengah"},
        {"id": "b", "judul": "Global Sales Director, Energy & AI", "peran": "ai_ml", "tingkat": "pimpinan"},
    ]
    tetap, bukan_it = sumber.segarkan_peran(tersimpan)
    assert [(isi["id"], isi["peran"], isi["tingkat"]) for isi in tetap] == [("a", "backend", "senior")]
    assert [isi["id"] for isi in bukan_it] == ["b"] and "bukan lowongan IT" in bukan_it[0]["alasan_tutup"]


def test_lowongan_manual_dengan_kolom_kurang(tmp_path, monkeypatch):
    berkas_manual = tmp_path / "manual.csv"
    berkas_manual.write_text("judul,perusahaan,lokasi,jenis,gaji,tanggal,url,deskripsi\nBackend Developer,PT A\n", encoding="utf-8")
    monkeypatch.setattr(sumber, "FILE_LOWONGAN_MANUAL", berkas_manual)
    _, hasil = sumber.ambil_manual()
    assert hasil[0]["tanggal"] == "" and hasil[0]["deskripsi"] == ""
    assert sumber.lengkapi(hasil[0], "manual", "2026-11-12")["wilayah"] == "lokal"


def test_ke_tanggal_menerima_milidetik():
    assert sumber.ke_tanggal(1785827515972) == sumber.ke_tanggal(1785827515) == "2026-08-04"


def palsukan_minta(monkeypatch, jawaban):
    """Mengganti sumber.minta: alamat yang memuat kunci di jawaban mendapat isinya. Tanpa internet."""
    dipanggil = []

    def minta_palsu(url, parameter=None):
        dipanggil.append(url)
        for potongan, isi in jawaban.items():
            if potongan in url:
                if isinstance(isi, Exception):
                    raise isi
                return isi
        raise AssertionError(f"alamat tidak terduga: {url}")

    monkeypatch.setattr(sumber, "minta", minta_palsu)
    return dipanggil


def test_ats_hanya_mengambil_lowongan_di_indonesia(monkeypatch):
    palsukan_minta(monkeypatch, {
        "lever.co": [
            {"text": "Backend Engineer", "country": "ID", "categories": {"location": "Jakarta", "commitment": "Permanent"},
             "createdAt": 1785827515972, "hostedUrl": "https://jobs.lever.co/a/1", "description": "<p>Go and Kafka</p>",
             "lists": [{"text": "Requirements", "content": "<li>PostgreSQL</li>"}]},
            {"text": "Backend Engineer", "country": "SG", "categories": {"location": "Singapore"}, "hostedUrl": "u2"},
        ],
        "greenhouse.io": {"jobs": [
            {"title": "Data Analyst", "location": {"name": "Jakarta, Indonesia"}, "absolute_url": "u3",
             "content": "&lt;p&gt;SQL&lt;/p&gt;", "first_published": "2026-11-01T00:00:00Z"},
            {"title": "Data Analyst", "location": {"name": "Manila, Philippines"}, "absolute_url": "u4"},
        ]},
        "workable.com": {"jobs": [
            {"title": "QA Engineer", "locations": [{"city": "Jakarta", "country": "Indonesia"}], "telecommuting": True,
             "url": "u5", "description": "<p>Selenium</p>", "published_on": "2026-11-02"},
            {"title": "QA Engineer", "locations": [{"city": "Berlin", "country": "Germany"}], "url": "u6"},
        ]},
    })
    _, lever = sumber.ats_lever("a", "PT A")
    _, greenhouse = sumber.ats_greenhouse("b", "PT B")
    _, workable = sumber.ats_workable("c", "PT C")
    assert [len(lever), len(greenhouse), len(workable)] == [1, 1, 1]
    assert lever[0]["perusahaan"] == "PT A" and lever[0]["tanggal"] == "2026-08-04"
    assert workable[0]["lokasi"] == "Jakarta, Indonesia (remote)"
    lengkap = [sumber.lengkapi(isi, "karier_perusahaan", "2026-11-22") for isi in lever + greenhouse + workable]
    assert all(isi["wilayah"] == "lokal" for isi in lengkap)
    assert {"Go", "Kafka", "PostgreSQL"} <= set(lengkap[0]["skill"]) and "SQL" in lengkap[1]["skill"]


def test_smartrecruiters_hanya_mengambil_rincian_lowongan_it(monkeypatch):
    dipanggil = palsukan_minta(monkeypatch, {
        "postings/1": {"postingUrl": "https://jobs.smartrecruiters.com/x/1-backend",
                       "jobAd": {"sections": {"companyDescription": {"text": "Kami memakai Java"},
                                              "qualifications": {"title": "Syarat", "text": "<p>Python</p>"}}}},
        "companies/x/postings": {"totalFound": 2, "content": [
            {"id": "1", "name": "Backend Engineer", "ref": "https://api.smartrecruiters.com/v1/companies/x/postings/1",
             "location": {"fullLocation": "Jakarta, , Indonesia"}},
            {"id": "2", "name": "Sales Manager", "ref": "https://api.smartrecruiters.com/v1/companies/x/postings/2",
             "location": {"fullLocation": "Jakarta, , Indonesia"}},
        ]},
    })
    _, hasil = sumber.ats_smartrecruiters("x", "PT X")
    assert len(dipanggil) == 2  # Satu daftar, satu rincian. Lowongan sales tidak diambil rinciannya.
    assert hasil[0]["lokasi"] == "Jakarta, Indonesia" and hasil[0]["url"].endswith("1-backend")
    assert "Python" in hasil[0]["deskripsi"] and "Java" not in hasil[0]["deskripsi"]
    assert sumber.lengkapi(hasil[1], "karier_perusahaan", "2026-11-22") is None


def test_satu_perusahaan_gagal_tidak_menghentikan_yang_lain(monkeypatch):
    monkeypatch.setattr(sumber, "baca_yaml", lambda nama: {"greenhouse": {"rusak": "PT Rusak", "baik": "PT Baik"}})
    palsukan_minta(monkeypatch, {
        "boards/rusak": sumber.requests.ConnectionError("putus"),
        "boards/baik": {"jobs": [{"title": "DevOps Engineer", "location": {"name": "Bandung"}, "absolute_url": "u"}]},
    })
    mentah, hasil = sumber.ambil_karier_perusahaan()
    assert list(mentah) == ["greenhouse/baik"] and hasil[0]["perusahaan"] == "PT Baik"

    monkeypatch.setattr(sumber, "baca_yaml", lambda nama: {"greenhouse": {"rusak": "PT Rusak"}})
    with pytest.raises(ValueError):
        sumber.ambil_karier_perusahaan()



# Analisis skill

PREFERENSI = {
    "wilayah": "semua", "lokasi_diterima": ["worldwide", "indonesia"], "hanya_lokasi_diterima": True,
    "batas_wajib": 30, "batas_sering": 10, "jumlah_skill": 20, "hari_tren": 14, "jumlah_lowongan_ai": 2,
}


def kumpulan_lowongan():
    """Delapan lowongan buatan: enam backend (dua junior) dan dua frontend."""
    return [
        contoh_lowongan(id="b1", skill=["Python", "Docker", "AWS"], tanggal="2026-11-15"),
        contoh_lowongan(id="b2", skill=["Python", "Docker"], tanggal="2026-11-14"),
        contoh_lowongan(id="b3", skill=["Python", "SQL"], tanggal="2026-11-13", tingkat="senior"),
        contoh_lowongan(id="b4", skill=["Go", "Docker"], tanggal="2026-10-20", tingkat="senior"),
        contoh_lowongan(id="b5", skill=["Java"], tanggal="2026-10-19", tingkat="senior"),
        contoh_lowongan(id="b6", skill=["Python"], tanggal="2026-10-18", tingkat="senior", lokasi="United States"),
        contoh_lowongan(id="f1", peran="frontend", skill=["React", "CSS"], tanggal="2026-11-12"),
        contoh_lowongan(id="f2", peran="frontend", skill=["React"], tanggal="2026-10-01", wilayah="lokal", lokasi="Jakarta"),
    ]


def test_nama_saringan():
    assert analisis.nama_saringan("lokal") == "lokal"
    assert analisis.nama_saringan("semua", ["frontend", "backend"], ["senior", "magang"]) == "semua-backend+frontend-magang+senior"


def test_saring_lowongan_menurut_peran_tingkat_dan_lokasi():
    lowongan = kumpulan_lowongan()
    backend = analisis.saring_lowongan(lowongan, PREFERENSI, ["backend"])
    # b6 hanya untuk pelamar di Amerika Serikat, jadi tidak dihitung kalau hanya_lokasi_diterima aktif.
    assert [isi["id"] for isi in backend] == ["b1", "b2", "b3", "b4", "b5"]
    assert [isi["id"] for isi in analisis.saring_lowongan(lowongan, PREFERENSI, ["backend"], ["junior"])] == ["b1", "b2"]
    semua = analisis.saring_lowongan(lowongan, {**PREFERENSI, "hanya_lokasi_diterima": False})
    assert len(semua) == 8


def test_hitung_skill_dan_golongan():
    hasil = {b["skill"]: b for b in analisis.hitung_skill(kumpulan_lowongan()[:5], batas_wajib=50, batas_sering=30)}
    assert hasil["Python"]["jumlah_lowongan"] == 3 and hasil["Python"]["persen_lowongan"] == 60.0
    assert [hasil[n]["golongan"] for n in ["Python", "Docker", "AWS"]] == ["wajib", "wajib", "tambahan"]
    assert hasil["Docker"]["kategori"] == "devops_dan_cloud"
    assert analisis.golongkan(30, 30, 10) == "wajib" and analisis.golongkan(29.9, 30, 10) == "sering"


def test_skill_bersama():
    hasil = analisis.skill_bersama(kumpulan_lowongan()[:5], "Docker")
    # Dari tiga lowongan yang meminta Docker, dua juga meminta Python.
    assert hasil[0] == {"skill": "Python", "persen": 66.7}


def test_tren_skill_hanya_kalau_datanya_cukup():
    lowongan = kumpulan_lowongan()
    assert analisis.tren_skill(lowongan, "2026-11-16", hari=14) is None  # baru 4 lowongan baru
    banyak = lowongan * 2
    tren = analisis.tren_skill(banyak, "2026-11-16", hari=14)
    assert (tren["jumlah_baru"], tren["jumlah_lama"]) == (8, 8)
    python = next(isi for isi in tren["skill"] if isi["skill"] == "Python")
    assert (python["persen_baru"], python["persen_lama"], python["selisih"]) == (75.0, 25.0, 50.0)


def test_analisis_skill_menolak_data_terlalu_sedikit():
    with pytest.raises(SystemExit):
        analisis.analisis_skill(kumpulan_lowongan(), PREFERENSI, {"wilayah": "semua", "peran": ["frontend"], "tingkat": []}, "2026-11-16")


def test_analisis_dan_simpan_hasil(tmp_path, monkeypatch):
    monkeypatch.setattr(analisis, "folder_saringan", lambda nama: tmp_path / nama)
    hasil = analisis.analisis_skill(kumpulan_lowongan(), PREFERENSI, {"wilayah": "semua", "peran": ["backend"], "tingkat": []}, "2026-11-16")
    assert hasil["nama"] == "semua-backend" and hasil["jumlah_lowongan"] == 5
    assert hasil["skill"][0]["skill"] == "Python" and "bersama" in hasil["skill"][0]
    assert list(hasil["per_kategori"])[0] == "bahasa"
    folder = analisis.simpan_hasil(hasil)
    assert {isi.name for isi in folder.iterdir()} == {"hasil.json", "skill.csv", "skill.xlsx", "skill.png"}
    import pandas as pd
    assert pd.read_excel(folder / "skill.xlsx", sheet_name="skill")["skill"].iloc[0] == "Python"


# AI: pemeriksaan jawaban

def test_model_penjawab_dengan_nama_lain_tetap_dikenali():
    assert klien_ai.model_sama("deepseek-v4.1-flash", "deepseek-ai/DeepSeek-V4.1-Flash-1017")
    assert klien_ai.model_sama("gemini-4-argon", "gemini-4-argon-d")
    assert not klien_ai.model_sama("deepseek-v4.1-flash", "gpt-6-luna")
    assert not klien_ai.model_sama("glm-5.3", "")


def test_temuan_ai_hanya_diterima_dengan_kutipan_sah():
    deskripsi = "You will work with JIRA and Confluence. Experience with Python and Kafka is a plus."
    hasil = temuan_ai.periksa_temuan({"skill": [
        {"nama": "Confluence", "kutipan": "work with JIRA and Confluence"},
        {"nama": "Pulumi", "kutipan": "provisioning with Pulumi"},
        {"nama": "Kafka", "kutipan": "Python and Kafka"},
        {"nama": "Lucene", "kutipan": "Experience with Python"},
    ]}, deskripsi)
    assert [isi["nama"] for isi in hasil["diterima"]] == ["Confluence"]
    assert [isi["alasan"] for isi in hasil["ditolak"]] == [
        "kutipan tidak ada di deskripsi", "sudah ada di kamus", "kutipan tidak menyebut skill ini",
    ]
    with pytest.raises(klien_ai.GalatAI):
        temuan_ai.periksa_temuan({"skill": "Confluence"}, deskripsi)


def test_gabung_temuan_menghitung_lowongan_per_skill():
    hasil = temuan_ai.gabung_temuan([
        ("a", "Lowongan A", [{"nama": "Confluence", "kutipan": "x"}]),
        ("b", "Lowongan B", [{"nama": "confluence", "kutipan": "y"}, {"nama": "Lucene", "kutipan": "z"}]),
    ])
    assert [(isi["nama"], isi["jumlah_lowongan"]) for isi in hasil] == [("Confluence", 2), ("Lucene", 1)]


def test_kesimpulan_dengan_angka_karangan_ditolak():
    hasil = {"saringan": {"wilayah": "lokal", "peran": [], "tingkat": []}, "jumlah_lowongan": 68,
             "skill": [{"skill": "Python", "persen_lowongan": 39.7, "golongan": "wajib"}]}
    sah = temuan_ai.angka_sah(hasil)
    assert {"68", "39.7", "40"} <= sah
    teks_baik = "Dari 68 lowongan, Python diminta 39,7% (sekitar 40%), jadi pelajari Python lebih dulu."
    assert temuan_ai.periksa_kesimpulan({"kesimpulan": teks_baik}, sah)["kesimpulan"] == teks_baik
    with pytest.raises(klien_ai.GalatAI):
        temuan_ai.periksa_kesimpulan({"kesimpulan": "Dari 120 lowongan, Python diminta 39,7%. Pelajari Python dulu ya."}, sah)


def test_temuan_dari_lowongan_tutup_dan_kesimpulan_basi_disembunyikan(tmp_path, monkeypatch):
    monkeypatch.setattr(temuan_ai, "folder_saringan", lambda nama: tmp_path)
    berkas.simpan_json(tmp_path / "temuan_ai.json", {
        "tanggal_analisis": "2026-11-16", "jumlah_lowongan": 10, "kesimpulan": "Pelajari Python.", "model": "uji",
        "dibaca": ["a", "b"], "ditolak": [],
        "skill_baru": [{"nama": "Lucene", "jumlah_lowongan": 2, "bukti": [{"id": "a", "judul": "A", "kutipan": "x"}, {"id": "b", "judul": "B", "kutipan": "y"}]},
                       {"nama": "Kanban", "jumlah_lowongan": 1, "bukti": [{"id": "b", "judul": "B", "kutipan": "z"}]}],
    })
    sekarang = temuan_ai.baca_temuan("uji", {"a"}, {"tanggal_analisis": "2026-11-16", "jumlah_lowongan": 10})
    assert [(isi["nama"], isi["jumlah_lowongan"]) for isi in sekarang["skill_baru"]] == [("Lucene", 1)]
    assert sekarang["kesimpulan"] == "Pelajari Python." and sekarang["dibaca"] == 1
    basi = temuan_ai.baca_temuan("uji", {"a"}, {"tanggal_analisis": "2026-11-20", "jumlah_lowongan": 12})
    assert basi["kesimpulan"] is None


def test_jawaban_yang_ditolak_pemeriksa_dibuang_dari_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(klien_ai, "FOLDER_CACHE_AI", tmp_path)
    monkeypatch.setattr(klien_ai, "FILE_LOG_AI", tmp_path / "log.jsonl")
    monkeypatch.setattr(klien_ai, "ambil_api_key", lambda: "kunci")
    monkeypatch.setattr(klien_ai, "panggil_model", lambda model, pesan, api_key: {"teks": '{"skor": "tinggi"}', "model_penjawab": model})

    def pemeriksa(data):
        raise klien_ai.GalatAI("skor bukan angka")

    with pytest.raises(klien_ai.GalatAI):
        klien_ai.tanya_json("s", "p", "uji", ["skor"], model=["deepseek-v4.1-flash"], pemeriksa=pemeriksa)
    assert not list(tmp_path.glob("*.json"))


def test_ambil_json_dari_jawaban_berpagar():
    assert klien_ai.ambil_json('```json\n{"skor": 80}\n```') == {"skor": 80}
    assert klien_ai.ambil_json('Berikut hasilnya: {"skor": 80} semoga membantu') == {"skor": 80}
    with pytest.raises(klien_ai.GalatAI):
        klien_ai.ambil_json("maaf, tidak bisa")


def test_model_di_luar_daftar_ditolak():
    with pytest.raises(SystemExit):
        klien_ai.periksa_model(["gpt-6-luna"])


# File

def test_simpan_dan_baca_json_csv_jsonl(tmp_path):
    berkas.simpan_json(tmp_path / "a" / "data.json", {"nama": "Sari", "skor": 1.5})
    assert berkas.baca_json(tmp_path / "a" / "data.json") == {"nama": "Sari", "skor": 1.5}
    assert berkas.baca_json(tmp_path / "tidak_ada.json", bawaan=[]) == []
    berkas.simpan_csv(tmp_path / "b.csv", [{"id": "1", "judul": "Dev, Senior", "lain": "x"}], ["id", "judul"])
    assert berkas.baca_csv(tmp_path / "b.csv") == [{"id": "1", "judul": "Dev, Senior"}]
    berkas.tambah_jsonl(tmp_path / "c.jsonl", {"n": 1})
    berkas.tambah_jsonl(tmp_path / "c.jsonl", {"n": 2})
    assert berkas.baca_jsonl(tmp_path / "c.jsonl") == [{"n": 1}, {"n": 2}]



# Laporan HTML

def siapkan_laporan(tmp_path, monkeypatch):
    """Hasil analisis tiruan di folder sementara, cukup untuk membuat laporan."""
    for modul in (analisis, laporan, temuan_ai):
        monkeypatch.setattr(modul, "folder_saringan", lambda nama: tmp_path / nama)
    monkeypatch.setattr(laporan, "FOLDER_OUTPUT", tmp_path)
    monkeypatch.setattr(laporan, "FILE_LOG_AI", tmp_path / "log_ai.jsonl")
    lowongan = kumpulan_lowongan()
    lowongan[0] = {**lowongan[0], "judul": "Backend <b>Dev</b>", "url": "javascript:alert(1)"}
    hasil = analisis.analisis_skill(lowongan, PREFERENSI, {"wilayah": "semua", "peran": ["backend"], "tingkat": []}, "2026-11-16")
    analisis.simpan_hasil(hasil)
    return hasil


def test_laporan_html_aman_dan_tanpa_lowongan_tutup(tmp_path, monkeypatch):
    hasil = siapkan_laporan(tmp_path, monkeypatch)
    html = laporan.buat_laporan(hasil["nama"], id_buka={"b1", "b2", "b3", "b4"}).read_text(encoding="utf-8")
    # Teks dari lowongan tidak boleh terbaca sebagai HTML, dan alamat selain http tidak menjadi tautan.
    assert "Backend &lt;b&gt;Dev&lt;/b&gt;" in html and "<b>Dev</b>" not in html
    assert "javascript:" not in html
    # b5 sudah tutup sejak analisis dibuat, jadi tidak boleh tampil sebagai contoh lowongan.
    assert html.count("contoh.test/1") == 3
    assert "Kuasai dulu: Python, Docker" in html
    # Bagian tanpa data (temuan AI) tidak ditulis dan tidak masuk menu.
    assert 'href="#skill"' in html and 'href="#ai"' not in html


def test_indeks_memuat_semua_laporan_tanpa_data_lowongan(tmp_path, monkeypatch):
    hasil = siapkan_laporan(tmp_path, monkeypatch)
    laporan.buat_laporan(hasil["nama"])
    indeks = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'href="semua-backend/laporan.html"' in indeks and "Backend &lt;b&gt;" not in indeks


# Pilihan terminal

def test_pilihan_terminal():
    import main
    args = main.buat_parser().parse_args(["skill", "--peran", "backend", "frontend", "--tingkat", "junior", "--ai"])
    assert (args.peran, args.tingkat, args.ai, args.fungsi) == (["backend", "frontend"], ["junior"], True, main.perintah_skill)
    assert main.baca_saringan(args, PREFERENSI) == {"wilayah": "semua", "peran": ["backend", "frontend"], "tingkat": ["junior"]}
    with pytest.raises(SystemExit):
        main.buat_parser().parse_args(["skill", "--peran", "koki"])
