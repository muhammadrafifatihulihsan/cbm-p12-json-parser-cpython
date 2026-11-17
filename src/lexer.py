"""Pemindai token JSON sederhana yang meniru lapisan scanner CPython.

Modul ini memperlihatkan bahwa pengenalan token dapat diselesaikan dengan
ekspresi reguler dan satu keputusan berdasarkan karakter pertama. Modul ini
sengaja tidak memeriksa keseimbangan kurung, karena pekerjaan itu bukan tugas
scanner. Akibatnya aliran token seperti ``] [`` tetap dihasilkan tanpa error.
"""

from dataclasses import dataclass

from pola_regex import NUMBER_RE, STRINGCHUNK, WHITESPACE

JENIS = {
    "{": "KURUNG_BUKA",
    "}": "KURUNG_TUTUP",
    "[": "SIKU_BUKA",
    "]": "SIKU_TUTUP",
    ":": "TITIK_DUA",
    ",": "KOMA",
}

ESCAPE_SAH = set('"\\/bfnrt')


@dataclass(frozen=True)
class Token:
    jenis: str
    nilai: str
    posisi: int


class KesalahanToken(ValueError):
    """Kesalahan saat memindai token."""

    def __init__(self, pesan, posisi):
        super().__init__(f"{pesan} pada posisi {posisi}")
        self.pesan = pesan
        self.posisi = posisi


class LexerJSON:
    """Pemindai token dengan satu karakter sebagai penentu cabang."""

    def __init__(self, teks):
        self.teks = teks
        self.i = 0

    def _lewati_spasi(self):
        self.i = WHITESPACE.match(self.teks, self.i).end()

    def _string(self):
        awal = self.i
        self.i += 1
        while True:
            m = STRINGCHUNK.match(self.teks, self.i)
            if m is None:
                raise KesalahanToken("string tidak ditutup", awal)
            _, akhir = m.groups()
            self.i = m.end()
            if akhir == '"':
                break
            if akhir != "\\":
                raise KesalahanToken("karakter kontrol di dalam string", self.i - 1)
            # lewati karakter escape
            if self.i >= len(self.teks):
                raise KesalahanToken("escape terpotong", self.i)
            esc = self.teks[self.i]
            if esc == "u":
                potongan = self.teks[self.i + 1:self.i + 5]
                if len(potongan) != 4 or any(c not in "0123456789abcdefABCDEF" for c in potongan):
                    raise KesalahanToken("escape \\u tidak sah", self.i)
                self.i += 5
            elif esc in ESCAPE_SAH:
                self.i += 1
            else:
                raise KesalahanToken("escape tidak dikenal", self.i)
        return Token("STRING", self.teks[awal:self.i], awal)

    def _angka(self):
        awal = self.i
        m = NUMBER_RE.match(self.teks, self.i)
        if m is None:
            raise KesalahanToken("angka tidak sah", awal)
        self.i = m.end()
        return Token("NUMBER", m.group(0), awal)

    def token_berikut(self):
        self._lewati_spasi()
        if self.i >= len(self.teks):
            return Token("EOF", "", self.i)
        awal = self.i
        c = self.teks[self.i]
        if c in JENIS:
            self.i += 1
            return Token(JENIS[c], c, awal)
        if c == '"':
            return self._string()
        if c == "t" and self.teks.startswith("true", self.i):
            self.i += 4
            return Token("TRUE", "true", awal)
        if c == "f" and self.teks.startswith("false", self.i):
            self.i += 5
            return Token("FALSE", "false", awal)
        if c == "n" and self.teks.startswith("null", self.i):
            self.i += 4
            return Token("NULL", "null", awal)
        if c == "-" or c.isdigit():
            return self._angka()
        raise KesalahanToken(f"karakter tidak dikenal {c!r}", awal)

    def semua_token(self):
        hasil = []
        while True:
            t = self.token_berikut()
            hasil.append(t)
            if t.jenis == "EOF":
                return hasil


def tokenisasi(teks):
    """Kembalikan daftar Token untuk ``teks``."""
    return LexerJSON(teks).semua_token()
