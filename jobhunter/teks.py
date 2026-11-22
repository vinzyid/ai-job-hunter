"""Fungsi kecil untuk membersihkan dan membandingkan teks."""

import html
import re
from html.parser import HTMLParser

TAG_BARIS_BARU = {"p", "br", "li", "div", "h1", "h2", "h3", "h4", "h5", "tr", "ul", "ol"}


class PembuangTag(HTMLParser):
    """Mengumpulkan teks dari HTML dan membuang tag-nya."""

    def __init__(self):
        """Menyiapkan tempat potongan teks dan penghitung tag script/style yang sedang dibuka."""
        super().__init__()
        self.potongan = []
        self.lewati = 0

    def handle_starttag(self, tag, attrs):
        """Dipanggil HTMLParser untuk tag pembuka. Isi script/style dilewati; tag blok menjadi baris baru."""
        if tag in ("script", "style"):
            self.lewati += 1
        elif tag in TAG_BARIS_BARU:
            self.potongan.append("\n")

    def handle_endtag(self, tag):
        """Dipanggil untuk tag penutup. Menutup script/style, atau menambah baris baru untuk tag blok."""
        if tag in ("script", "style"):
            self.lewati = max(0, self.lewati - 1)
        elif tag in TAG_BARIS_BARU:
            self.potongan.append("\n")

    def handle_data(self, data):
        """Dipanggil untuk teks di antara tag. Disimpan kecuali sedang di dalam script/style."""
        if not self.lewati:
            self.potongan.append(data)


def buang_html(teks):
    """Mengubah deskripsi lowongan berformat HTML menjadi teks biasa."""
    if not teks:
        return ""
    # Sebagian sumber mengirim HTML yang sudah di-escape (&lt;p&gt;), jadi dibuka dulu.
    if "&lt;" in teks:
        teks = html.unescape(teks)
    pembuang = PembuangTag()
    pembuang.feed(teks)
    pembuang.close()
    hasil = html.unescape("".join(pembuang.potongan)).replace("\xa0", " ")
    hasil = re.sub(r"[ \t]+", " ", hasil)
    hasil = re.sub(r" ?\n ?", "\n", hasil)
    return re.sub(r"\n{2,}", "\n", hasil).strip()


def rapikan(teks):
    """Huruf kecil dan satu spasi antarkata, untuk membandingkan dua teks."""
    teks = teks.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    teks = re.sub(r"[–—]", "-", teks)
    return re.sub(r"\s+", " ", teks).strip().lower()


def kutipan_ada(kutipan, sumber):
    """Benar kalau kutipan benar-benar tertulis di sumber, tanpa melihat huruf besar dan spasi."""
    kutipan = rapikan(kutipan or "").strip(" .\"'")
    return len(kutipan) >= 3 and kutipan in rapikan(sumber)


def potong(teks, batas):
    """Memotong teks panjang di batas kata, supaya permintaan ke AI tidak terlalu besar."""
    if len(teks) <= batas:
        return teks
    return teks[:batas].rsplit(" ", 1)[0] + " ..."
