"""Uji lapisan pemindai token."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lexer import KesalahanToken, tokenisasi  # noqa: E402


class UjiLexer(unittest.TestCase):
    def test_token_struktur(self):
        t = tokenisasi('{"a": [1, true, null]}')
        jenis = [x.jenis for x in t]
        self.assertEqual(jenis, [
            "KURUNG_BUKA", "STRING", "TITIK_DUA",
            "SIKU_BUKA", "NUMBER", "KOMA", "TRUE", "KOMA", "NULL",
            "SIKU_TUTUP", "KURUNG_TUTUP", "EOF",
        ])

    def test_string_dengan_escape(self):
        t = tokenisasi('"a\\"b\\n"')
        self.assertEqual(t[0].jenis, "STRING")
        self.assertEqual(t[0].nilai, '"a\\"b\\n"')

    def test_escape_tidak_sah(self):
        with self.assertRaises(KesalahanToken):
            tokenisasi('"a\\qb"')

    def test_angka_memakai_awalan_terpanjang(self):
        # Pola CPython menerima awalan "0" dari "01", lalu "1" menjadi token lain.
        t = tokenisasi("01")
        self.assertEqual([x.nilai for x in t], ["0", "1", ""])

    def test_token_tidak_menjaga_keseimbangan(self):
        # Scanner tidak boleh menolak urutan kurung yang salah.
        t = tokenisasi("][")
        self.assertEqual([x.jenis for x in t], ["SIKU_TUTUP", "SIKU_BUKA", "EOF"])

    def test_karakter_asing(self):
        with self.assertRaises(KesalahanToken):
            tokenisasi("@")

    def test_string_kontrol_ditolak(self):
        with self.assertRaises(KesalahanToken):
            tokenisasi('"a\x01b"')


if __name__ == "__main__":
    unittest.main()
