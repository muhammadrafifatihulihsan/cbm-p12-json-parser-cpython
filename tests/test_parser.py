"""Uji parser turunan rekursif."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parser_json import KesalahanJSON, muat, urai  # noqa: E402


class UjiParser(unittest.TestCase):
    def test_dokumen_sederhana(self):
        self.assertEqual(
            muat('{"nama": "Rafi", "nilai": [1, 2.5, true, null]}'),
            {"nama": "Rafi", "nilai": [1, 2.5, True, None]},
        )

    def test_sama_dengan_json_bawaan(self):
        contoh = [
            '{"a": 1}', "[1, 2, 3]", '"teks"', "0", "-0", "1.5e-3",
            '{"a": {"b": [{"c": []}]}}', "[[[[[0]]]]]", '"\\u00e9"',
            '"\\ud83d\\ude00"',
        ]
        for teks in contoh:
            self.assertEqual(muat(teks), json.loads(teks), teks)

    def test_kedalaman_dicatat(self):
        _, info = urai('{"a": [1, {"b": 2}]}')
        self.assertEqual(info.kedalaman_maks, 3)
        self.assertEqual(info.jumlah_objek, 2)
        self.assertEqual(info.jumlah_array, 1)

    def test_dokumen_tidak_sah(self):
        contoh = ["", "][", '{"a": 1,}', "[1,]", '{"a" 1}', "tru", "01",
                  '"abc', '{"a": 1} x', "[1 2]", "{\"a\": }"]
        for teks in contoh:
            with self.assertRaises(KesalahanJSON, msg=teks):
                muat(teks)

    def test_konstanta_nonstandar_ditolak(self):
        for teks in ["NaN", "Infinity", "-Infinity"]:
            with self.assertRaises(KesalahanJSON, msg=teks):
                muat(teks)

    def test_nested_dalam(self):
        n = 100
        nilai = muat("[" * n + "0" + "]" * n)
        for _ in range(n):
            self.assertIsInstance(nilai, list)
            nilai = nilai[0]
        self.assertEqual(nilai, 0)

    def test_posisi_kesalahan(self):
        with self.assertRaises(KesalahanJSON) as ctx:
            muat('{"a": 1,}')
        self.assertEqual(ctx.exception.posisi, 8)
        self.assertEqual(ctx.exception.baris, 1)


if __name__ == "__main__":
    unittest.main()
