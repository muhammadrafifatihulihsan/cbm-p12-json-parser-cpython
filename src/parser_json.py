"""Parser JSON turunan rekursif yang mengikuti strategi CPython.

CPython tidak memakai satu DFA untuk seluruh dokumen. Pada ``Lib/json``,
fungsi ``JSONObject`` dan ``JSONArray`` memanggil kembali pemindai nilai untuk
setiap nilai yang bersarang. Pola itulah yang ditiru modul ini: pemindaian
token bersifat berhingga, sedangkan struktur bersarang ditangani oleh
pemanggilan fungsi yang bertumpuk pada call stack.

Parser ini ketat terhadap RFC 8259. Konstanta non-standar ``NaN``,
``Infinity``, dan ``-Infinity`` yang diterima modul ``json`` CPython secara
default sengaja ditolak, dan perbedaan itu dicatat pada laporan.
"""

import re

POLA_ANGKA = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?")
SPASI = " \t\n\r"


class KesalahanJSON(ValueError):
    """Kesalahan sintaks JSON dengan posisi karakter."""

    def __init__(self, pesan, teks, posisi):
        baris = teks.count("\n", 0, posisi) + 1
        kolom = posisi - teks.rfind("\n", 0, posisi)
        super().__init__(f"{pesan}: baris {baris} kolom {kolom} (karakter {posisi})")
        self.pesan = pesan
        self.posisi = posisi
        self.baris = baris
        self.kolom = kolom


class InfoUrai:
    """Statistik satu proses penguraian."""

    def __init__(self):
        self.kedalaman_maks = 0
        self.panggilan_nilai = 0
        self.jumlah_node = 0
        self.jumlah_objek = 0
        self.jumlah_array = 0

    def sebagai_dict(self):
        return {
            "kedalaman_maks": self.kedalaman_maks,
            "panggilan_nilai": self.panggilan_nilai,
            "jumlah_node": self.jumlah_node,
            "jumlah_objek": self.jumlah_objek,
            "jumlah_array": self.jumlah_array,
        }


class ParserJSON:
    """Parser turunan rekursif untuk dokumen JSON."""

    def __init__(self, teks):
        if not isinstance(teks, str):
            raise TypeError("masukan parser harus str")
        self.teks = teks
        self.i = 0
        self.kedalaman = 0
        self.info = InfoUrai()

    # ------------------------------------------------------------- bantuan
    def _lewati_spasi(self):
        while self.i < len(self.teks) and self.teks[self.i] in SPASI:
            self.i += 1

    def _harap(self, karakter):
        if self.i >= len(self.teks) or self.teks[self.i] != karakter:
            raise KesalahanJSON(f"mengharapkan {karakter!r}", self.teks, self.i)
        self.i += 1

    def _masuk(self):
        self.kedalaman += 1
        if self.kedalaman > self.info.kedalaman_maks:
            self.info.kedalaman_maks = self.kedalaman

    def _keluar(self):
        self.kedalaman -= 1

    # --------------------------------------------------------------- nilai
    def nilai(self):
        self.info.panggilan_nilai += 1
        self._lewati_spasi()
        if self.i >= len(self.teks):
            raise KesalahanJSON("dokumen berakhir saat mengharapkan nilai", self.teks, self.i)
        c = self.teks[self.i]
        if c == "{":
            return self.objek()
        if c == "[":
            return self.array()
        if c == '"':
            return self.string()
        if c == "t" and self.teks.startswith("true", self.i):
            self.i += 4
            self.info.jumlah_node += 1
            return True
        if c == "f" and self.teks.startswith("false", self.i):
            self.i += 5
            self.info.jumlah_node += 1
            return False
        if c == "n" and self.teks.startswith("null", self.i):
            self.i += 4
            self.info.jumlah_node += 1
            return None
        if c == "-" or c.isdigit():
            return self.angka()
        raise KesalahanJSON(f"nilai tidak dikenal {c!r}", self.teks, self.i)

    def objek(self):
        self._harap("{")
        self._masuk()
        self.info.jumlah_objek += 1
        hasil = {}
        self._lewati_spasi()
        if self.i < len(self.teks) and self.teks[self.i] == "}":
            self.i += 1
            self._keluar()
            return hasil
        while True:
            self._lewati_spasi()
            if self.i >= len(self.teks) or self.teks[self.i] != '"':
                raise KesalahanJSON("mengharapkan nama anggota dalam tanda kutip", self.teks, self.i)
            kunci = self.string()
            self._lewati_spasi()
            self._harap(":")
            nilai = self.nilai()
            hasil[kunci] = nilai
            self.info.jumlah_node += 1
            self._lewati_spasi()
            if self.i >= len(self.teks):
                raise KesalahanJSON("objek tidak ditutup", self.teks, self.i)
            if self.teks[self.i] == ",":
                self.i += 1
                continue
            if self.teks[self.i] == "}":
                self.i += 1
                self._keluar()
                return hasil
            raise KesalahanJSON("mengharapkan ',' atau '}'", self.teks, self.i)

    def array(self):
        self._harap("[")
        self._masuk()
        self.info.jumlah_array += 1
        hasil = []
        self._lewati_spasi()
        if self.i < len(self.teks) and self.teks[self.i] == "]":
            self.i += 1
            self._keluar()
            return hasil
        while True:
            hasil.append(self.nilai())
            self.info.jumlah_node += 1
            self._lewati_spasi()
            if self.i >= len(self.teks):
                raise KesalahanJSON("array tidak ditutup", self.teks, self.i)
            if self.teks[self.i] == ",":
                self.i += 1
                continue
            if self.teks[self.i] == "]":
                self.i += 1
                self._keluar()
                return hasil
            raise KesalahanJSON("mengharapkan ',' atau ']'", self.teks, self.i)

    def string(self):
        self._harap('"')
        potongan = []
        while True:
            if self.i >= len(self.teks):
                raise KesalahanJSON("string tidak ditutup", self.teks, self.i)
            c = self.teks[self.i]
            if c == '"':
                self.i += 1
                self.info.jumlah_node += 1
                return "".join(potongan)
            if c == "\\":
                self.i += 1
                if self.i >= len(self.teks):
                    raise KesalahanJSON("escape terpotong", self.teks, self.i)
                esc = self.teks[self.i]
                if esc == "u":
                    potongan.append(self._unicode())
                    continue
                peta = {'"': '"', "\\": "\\", "/": "/", "b": "\b",
                        "f": "\f", "n": "\n", "r": "\r", "t": "\t"}
                if esc not in peta:
                    raise KesalahanJSON(f"escape tidak dikenal {esc!r}", self.teks, self.i)
                potongan.append(peta[esc])
                self.i += 1
                continue
            if ord(c) < 0x20:
                raise KesalahanJSON("karakter kontrol di dalam string", self.teks, self.i)
            potongan.append(c)
            self.i += 1

    def _unicode(self):
        awal = self.i
        potongan = self.teks[self.i + 1:self.i + 5]
        if len(potongan) != 4 or any(c not in "0123456789abcdefABCDEF" for c in potongan):
            raise KesalahanJSON("escape \\u tidak sah", self.teks, awal)
        nilai = int(potongan, 16)
        self.i += 5
        if 0xD800 <= nilai <= 0xDBFF and self.teks.startswith("\\u", self.i):
            pasangan = self.teks[self.i + 2:self.i + 6]
            if len(pasangan) == 4 and all(c in "0123456789abcdefABCDEF" for c in pasangan):
                rendah = int(pasangan, 16)
                if 0xDC00 <= rendah <= 0xDFFF:
                    nilai = 0x10000 + (((nilai - 0xD800) << 10) | (rendah - 0xDC00))
                    self.i += 6
        return chr(nilai)

    def angka(self):
        m = POLA_ANGKA.match(self.teks, self.i)
        if m is None:
            raise KesalahanJSON("angka tidak sah", self.teks, self.i)
        teks = m.group(0)
        self.i = m.end()
        self.info.jumlah_node += 1
        if any(c in teks for c in ".eE"):
            return float(teks)
        return int(teks)

    # ---------------------------------------------------------------- API
    def urai(self):
        """Urai seluruh dokumen dan kembalikan pasangan (nilai, info)."""
        self._lewati_spasi()
        hasil = self.nilai()
        self._lewati_spasi()
        if self.i != len(self.teks):
            raise KesalahanJSON("data tambahan setelah dokumen", self.teks, self.i)
        return hasil, self.info


def muat(teks):
    """Urai ``teks`` dan kembalikan nilai Python."""
    return ParserJSON(teks).urai()[0]


def urai(teks):
    """Urai ``teks`` dan kembalikan (nilai, InfoUrai)."""
    return ParserJSON(teks).urai()
