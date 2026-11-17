"""Uji model berhingga untuk bahasa kurung."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from otomat_terbatas import (  # noqa: E402
    DFAKurung, cocok_regex, kedalaman_maks, pola_kurung, uji_batas,
)


class UjiOtomat(unittest.TestCase):
    def test_dfa_menerima_sampai_batas(self):
        for k in (1, 2, 3, 5):
            dfa = DFAKurung(k)
            for n in range(0, k + 1):
                s = "(" * n + ")" * n
                self.assertTrue(dfa.terima(s), f"k={k} n={n}")

    def test_dfa_menolak_di_atas_batas(self):
        for k in (1, 2, 3, 5):
            dfa = DFAKurung(k)
            s = "(" * (k + 1) + ")" * (k + 1)
            self.assertFalse(dfa.terima(s), f"k={k}")

    def test_dfa_menolak_tidak_seimbang(self):
        dfa = DFAKurung(3)
        for s in ["(", ")", "())", "(()", ")("]:
            self.assertFalse(dfa.terima(s), s)

    def test_jumlah_state(self):
        self.assertEqual(DFAKurung(3).jumlah_state(), 5)
        self.assertEqual(DFAKurung(3).jumlah_transisi(), 10)

    def test_regex_setara_dfa(self):
        for k in (0, 1, 2, 3):
            for n in range(0, k + 3):
                s = "(" * n + ")" * n
                self.assertEqual(
                    DFAKurung(k).terima(s), cocok_regex(k, s), f"k={k} n={n}"
                )

    def test_pola_regex_terbentuk(self):
        self.assertEqual(pola_kurung(0), r"[^()]*")

    def test_kedalaman_maks(self):
        self.assertEqual(kedalaman_maks("(()())"), 2)
        self.assertEqual(kedalaman_maks("())"), -1)
        self.assertEqual(kedalaman_maks(""), 0)

    def test_uji_batas(self):
        hasil = uji_batas(2, [1, 2, 3])
        self.assertTrue(hasil[1]["dfa"])
        self.assertFalse(hasil[2]["dfa"])
        self.assertTrue(hasil[2]["seimbang"])


if __name__ == "__main__":
    unittest.main()
