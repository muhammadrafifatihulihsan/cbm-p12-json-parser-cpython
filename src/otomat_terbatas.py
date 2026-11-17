"""Model pengenal terbatas untuk bahasa kurung seimbang.

Dua model dibandingkan:

1. DFA eksplisit dengan batas kedalaman ``k``. Jumlah state bertambah satu
   setiap kali batas kedalaman dinaikkan, dan DFA tetap menolak string
   seimbang yang lebih dalam dari ``k``.
2. Ekspresi reguler yang pola bersarangnya ditulis ulang (unrolled) sampai
   kedalaman ``k``. Pola ini juga berhenti bekerja pada kedalaman ``k + 1``.

Keduanya dipakai untuk menunjukkan bahwa model berhingga hanya dapat
mengenali kedalaman yang dipatok lebih dahulu.
"""


class DFAKurung:
    """DFA yang menerima kurung seimbang dengan kedalaman maksimum ``k``."""

    MATI = "mati"

    def __init__(self, k):
        if k < 0:
            raise ValueError("k harus >= 0")
        self.k = k
        self.state = list(range(k + 1)) + [self.MATI]

    def langkah(self, state, simbol):
        if state == self.MATI:
            return self.MATI
        if simbol == "(":
            return state + 1 if state < self.k else self.MATI
        if simbol == ")":
            return state - 1 if state > 0 else self.MATI
        return self.MATI

    def terima(self, teks):
        state = 0
        for simbol in teks:
            state = self.langkah(state, simbol)
            if state == self.MATI:
                return False
        return state == 0

    def jumlah_state(self):
        return len(self.state)

    def jumlah_transisi(self):
        return len(self.state) * 2


def pola_kurung(k):
    """Pola regex untuk kurung seimbang sampai kedalaman ``k``."""
    if k == 0:
        return r"[^()]*"
    dalam = pola_kurung(k - 1)
    return r"(?:[^()]|\((?:%s)\))*" % dalam


def cocok_regex(k, teks):
    """True bila ``teks`` cocok dengan pola berkedalaman ``k``."""
    import re

    return re.fullmatch(pola_kurung(k), teks) is not None


def kedalaman_maks(teks):
    """Kedalaman kurung terbesar pada ``teks``, atau -1 bila tidak seimbang."""
    dalam = 0
    puncak = 0
    for c in teks:
        if c == "(":
            dalam += 1
            puncak = max(puncak, dalam)
        elif c == ")":
            dalam -= 1
            if dalam < 0:
                return -1
        else:
            return -1
    return puncak if dalam == 0 else -1


def uji_batas(k, kedalaman_uji):
    """Uji DFA dan regex berbatas ``k`` pada string bersarang berbagai depth."""
    hasil = []
    for n in kedalaman_uji:
        s = "(" * n + ")" * n
        hasil.append({
            "kedalaman": n,
            "panjang": len(s),
            "dfa": DFAKurung(k).terima(s),
            "regex": cocok_regex(k, s),
            "seimbang": kedalaman_maks(s) == n,
        })
    return hasil
