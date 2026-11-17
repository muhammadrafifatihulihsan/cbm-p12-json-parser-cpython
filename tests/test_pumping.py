"""Uji alat bantu Pumping Lemma."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pumping import (  # noqa: E402
    anggota_d, dekomposisi, periksa, pompa, saksi, seimbang,
)


class UjiPumping(unittest.TestCase):
    def test_keanggotaan(self):
        for n in (0, 1, 2, 5):
            self.assertTrue(anggota_d("(" * n + ")" * n))
        for s in ["(", ")", "())", "(()", "()()", "(())("]:
            self.assertFalse(anggota_d(s), s)

    def test_seimbang(self):
        self.assertTrue(seimbang("(()())"))
        self.assertFalse(seimbang("(()"))
        self.assertFalse(seimbang(")("))

    def test_saksi(self):
        self.assertEqual(saksi(3), "((()))")

    def test_jumlah_dekomposisi(self):
        for p in (2, 4, 6, 8):
            self.assertEqual(len(dekomposisi(saksi(p), p)), p * (p + 1) // 2)

    def test_semua_y_hanya_buka(self):
        for p in (2, 4, 6):
            for _, y, _ in dekomposisi(saksi(p), p):
                self.assertEqual(set(y), {"("})

    def test_pompa(self):
        self.assertEqual(pompa("(", "(", "))", 0), "())")
        self.assertEqual(pompa("(", "(", "))", 2), "((())")

    def test_semua_hasil_pompa_gagal(self):
        for p in (2, 4, 6):
            hasil = periksa(p)
            self.assertTrue(hasil["semua_gagal"], p)
            self.assertEqual(hasil["jumlah_gagal"], hasil["jumlah_uji"])
            self.assertFalse(hasil["contoh"]["seimbang"])


if __name__ == "__main__":
    unittest.main()
