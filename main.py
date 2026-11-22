"""AI Job Hunter: mencari tahu skill apa yang diminta lowongan kerja IT.

Program mengambil lowongan IT dari API publik, membuang yang sudah tutup, membaca skill yang
disebut di setiap lowongan, lalu menghitung skill mana yang paling banyak diminta.

Urutan pemakaian:
    python main.py ambil                                   mengambil lowongan terbaru dari API publik
    python main.py skill                                   skill yang diminta semua lowongan IT lokal
    python main.py skill --peran backend --tingkat junior  hanya lowongan backend tingkat junior
    python main.py skill --peran frontend --ai             ditambah temuan dan kesimpulan AI
    python main.py laporan --buka                          membuka laporan HTML di browser
    python main.py semua --peran data_analyst              ambil + skill + laporan sekaligus

Pilihan --wilayah lokal (lowongan untuk Indonesia), internasional, atau semua. Bawaannya dari
konfigurasi/preferensi.yaml. Hasil setiap saringan disimpan di output/<saringan>/ sebagai
hasil.json, skill.csv, skill.xlsx, skill.png, dan laporan.html. Daftar semua laporan ada di
output/index.html. Setelah "ambil", semua hasil yang sudah ada dihitung ulang dari data terbaru.
"""

import argparse
import webbrowser

from jobhunter import analisis, klien_ai, laporan, skill, sumber, temuan_ai
from jobhunter.berkas import baca_json
from jobhunter.pengaturan import AKAR, FOLDER_OUTPUT, TINGKAT, WILAYAH, baca_preferensi


def relatif(lokasi):
    """Lokasi file relatif terhadap folder proyek, supaya pesan di terminal pendek."""
    return lokasi.relative_to(AKAR)


def baca_saringan(args, preferensi):
    """Saringan dari pilihan terminal: wilayah, daftar peran, dan daftar tingkat.

    Wilayah yang tidak disebut diambil dari preferensi.yaml. Peran dan tingkat kosong berarti semua.
    """
    return {"wilayah": args.wilayah or preferensi["wilayah"], "peran": args.peran or [], "tingkat": args.tingkat or []}


def analisis_dan_laporan(saringan, preferensi, pakai_ai=False, model=None):
    """Menghitung skill untuk satu saringan, menyimpan semua file hasil, lalu menulis laporan HTML.

    Lowongan selalu dibaca ulang lewat sumber.baca_lowongan, yang sudah membuang lowongan tutup.
    Mengembalikan (hasil analisis, lokasi laporan).
    """
    semua = sumber.baca_lowongan()
    lowongan = sumber.saring_wilayah(semua, saringan["wilayah"])
    hasil = analisis.analisis_skill(lowongan, preferensi, saringan)
    folder = analisis.simpan_hasil(hasil)
    if pakai_ai:
        terpilih = analisis.saring_lowongan(lowongan, preferensi, saringan["peran"], saringan["tingkat"])
        print(f"  AI membaca {preferensi['jumlah_lowongan_ai']} lowongan terbaru dan menulis kesimpulan...")
        temuan_ai.jalankan(hasil, terpilih, preferensi["jumlah_lowongan_ai"], model)
    lokasi = laporan.buat_laporan(hasil["nama"], {isi["id"] for isi in semua})
    print(f"  Hasil di {relatif(folder)}/ (hasil.json, skill.csv, skill.xlsx, skill.png, laporan.html)")
    return hasil, lokasi


def tampilkan_skill(hasil):
    """Mencetak tabel skill ke terminal, lengkap dengan golongan dan skill yang sering diminta bersama."""
    print(f"\n{hasil['jumlah_lowongan']} lowongan cocok dengan saringan {hasil['nama']}.")
    print(f"{'#':>3}  {'skill':<16} {'lowongan':>8} {'persen':>7}  {'golongan':<15} sering bersama")
    for nomor, baris in enumerate(hasil["skill"], start=1):
        teman = ", ".join(t["skill"] for t in baris.get("bersama", []))
        print(f"{nomor:>3}  {baris['skill']:<16} {baris['jumlah_lowongan']:>8} {baris['persen_lowongan']:>6.1f}%  "
              f"{analisis.LABEL_GOLONGAN[baris['golongan']]:<15} {teman}")


def perbarui_semua_hasil():
    """Setelah lowongan diambil ulang, setiap saringan yang pernah dianalisis dihitung ulang dari data baru.

    Dengan begitu tidak ada laporan lama yang masih memuat lowongan yang sudah tutup.
    """
    preferensi = baca_preferensi()
    for lokasi in sorted(FOLDER_OUTPUT.glob("*/hasil.json")):
        saringan = baca_json(lokasi)["saringan"]
        try:
            hasil, _ = analisis_dan_laporan(saringan, preferensi)
            print(f"  Diperbarui: {hasil['nama']} ({hasil['jumlah_lowongan']} lowongan)")
        except SystemExit as alasan:
            print(f"  Dilewati: {lokasi.parent.name} ({alasan})")


def perintah_ambil(args):
    """Perintah "ambil": mengambil lowongan dari API, membuang yang tutup, lalu memperbarui semua hasil."""
    print("Mengambil lowongan...")
    sumber.jalankan(args.sumber, cek_tautan=not args.lewati_cek_tautan)
    perbarui_semua_hasil()


def perintah_skill(args):
    """Perintah "skill": menghitung skill yang diminta untuk saringan yang dipilih dan menampilkannya."""
    preferensi = baca_preferensi()
    hasil, lokasi = analisis_dan_laporan(baca_saringan(args, preferensi), preferensi, args.ai, args.model)
    tampilkan_skill(hasil)
    temuan = temuan_ai.baca_temuan(hasil["nama"], set(hasil["id_lowongan"]), hasil) if args.ai else None
    if temuan:
        print(f"\nKesimpulan AI: {temuan['kesimpulan']}")
        print(f"Skill di luar kamus: {', '.join(s['nama'] for s in temuan['skill_baru']) or 'tidak ada'}")
    print(f"\nLaporan HTML: {relatif(lokasi)}")
    if args.buka:
        webbrowser.open(lokasi.as_uri())


def perintah_laporan(args):
    """Perintah "laporan": menulis ulang laporan satu saringan dari data terbaru, lalu membukanya."""
    preferensi = baca_preferensi()
    saringan = baca_saringan(args, preferensi)
    nama = analisis.nama_saringan(saringan["wilayah"], saringan["peran"], saringan["tingkat"])
    if not (FOLDER_OUTPUT / nama / "hasil.json").exists():
        raise SystemExit(f'Belum ada hasil untuk {nama}. Jalankan "python main.py skill" dengan saringan yang sama dulu.')
    _, lokasi = analisis_dan_laporan(saringan, preferensi)
    print(f"Laporan HTML: {relatif(lokasi)}\nDaftar semua laporan: {relatif(FOLDER_OUTPUT / 'index.html')}")
    if args.buka:
        webbrowser.open(lokasi.as_uri())


def perintah_semua(args):
    """Perintah "semua": ambil lowongan, lalu jalankan skill dengan saringan yang sama."""
    if not args.lewati_ambil:
        perintah_ambil(args)
    perintah_skill(args)


def buat_parser():
    """Menyusun pilihan terminal dengan argparse: satu subperintah untuk setiap langkah."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    perintah = parser.add_subparsers(dest="perintah", required=True)

    def tambah_ambil(bagian):
        """Pilihan untuk mengambil lowongan: sumber mana saja dan apakah halaman diperiksa."""
        bagian.add_argument("--sumber", nargs="+", choices=list(sumber.SUMBER), help="Bawaan: semua sumber.")
        bagian.add_argument("--lewati-cek-tautan", action="store_true", help="Jangan memeriksa halaman lowongan yang tidak muncul lagi.")

    def tambah_saringan(bagian):
        """Pilihan saringan: wilayah, peran, tingkat, dan membuka laporan di browser."""
        bagian.add_argument("--wilayah", choices=WILAYAH, help="Bawaan: dari preferensi.yaml.")
        bagian.add_argument("--peran", nargs="+", choices=skill.daftar_peran(), help="Satu atau beberapa peran. Bawaan: semua.")
        bagian.add_argument("--tingkat", nargs="+", choices=TINGKAT, help="Satu atau beberapa tingkat. Bawaan: semua.")
        bagian.add_argument("--buka", action="store_true", help="Langsung membuka laporan di browser.")

    def tambah_ai(bagian):
        """Pilihan AI: menyalakan temuan AI dan memilih model."""
        bagian.add_argument("--ai", action="store_true", help="Tambahkan temuan skill di luar kamus dan kesimpulan dari AI.")
        bagian.add_argument("--model", nargs="+", choices=klien_ai.MODEL_DIIZINKAN, help="Model AI yang dicoba, berurutan.")

    bagian = perintah.add_parser("ambil", help="Mengambil lowongan dari API publik.")
    bagian.set_defaults(fungsi=perintah_ambil)
    tambah_ambil(bagian)

    bagian = perintah.add_parser("skill", help="Skill yang diminta lowongan sesuai saringan.")
    bagian.set_defaults(fungsi=perintah_skill)
    tambah_saringan(bagian)
    tambah_ai(bagian)

    bagian = perintah.add_parser("laporan", help="Menulis ulang laporan HTML satu saringan.")
    bagian.set_defaults(fungsi=perintah_laporan)
    tambah_saringan(bagian)

    bagian = perintah.add_parser("semua", help="ambil + skill sekaligus.")
    bagian.set_defaults(fungsi=perintah_semua)
    tambah_ambil(bagian)
    tambah_saringan(bagian)
    tambah_ai(bagian)
    bagian.add_argument("--lewati-ambil", action="store_true", help="Pakai lowongan yang sudah tersimpan.")
    return parser


def main():
    """Titik masuk program: membaca pilihan terminal lalu menjalankan perintah yang dipilih."""
    args = buat_parser().parse_args()
    try:
        args.fungsi(args)
    except klien_ai.GalatAI as galat:
        raise SystemExit(f"AI gagal: {galat}")


if __name__ == "__main__":
    main()
