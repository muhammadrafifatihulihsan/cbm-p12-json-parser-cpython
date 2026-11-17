"""Pola ekspresi reguler yang dipakai CPython untuk memindai token JSON.

Pola di bawah disalin dari CPython v3.13.0, berkas ``Lib/json/scanner.py``
dan ``Lib/json/decoder.py``. Salinan sumber asli tersedia pada folder
``riset/01-sumber`` di luar repositori ini.

Pola ini hanya mengenali token. Pola tidak mengenali struktur dokumen JSON
yang bersarang, karena ekspresi reguler tidak memiliki memori untuk menghitung
kedalaman kurung.
"""

import re

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL

# Lib/json/scanner.py baris 11-13 pada CPython v3.13.0
NUMBER_RE = re.compile(
    r"(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?",
    FLAGS,
)

# Varian yang dipakai runtime Python 3.13.12 (perubahan kecil setelah 3.13.0)
NUMBER_RE_31312 = re.compile(
    r"(-?(?:0|[1-9][0-9]*))(\.[0-9]+)?([eE][-+]?[0-9]+)?",
    FLAGS,
)

# Lib/json/decoder.py baris 132 pada CPython v3.13.0
WHITESPACE = re.compile(r"[ \t\n\r]*", FLAGS)

# Lib/json/decoder.py baris 53 pada CPython v3.13.0
STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])', FLAGS)

# Pola bantu untuk pemeriksaan angka secara utuh. Pola ini tidak ada pada
# CPython, hanya dipakai eksperimen untuk menguji apakah sebuah token angka
# cocok seluruhnya, bukan hanya awalannya.
ANGKA_UTUH = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?")


def cocok_penuh(pola, teks):
    """Kembalikan True bila ``pola`` mencocokkan seluruh ``teks``."""
    m = pola.match(teks)
    return bool(m) and m.end() == len(teks)


def uji_token_angka(teks):
    """Uji satu token angka dengan pola CPython dan pola utuh.

    Mengembalikan kamus berisi potongan yang cocok, sisa karakter, dan
    status kelengkapan. Fungsi ini dipakai eksperimen, bukan oleh parser.
    """
    m = NUMBER_RE.match(teks)
    if m is None:
        return {"teks": teks, "cocok": "", "sisa": teks, "utuh": False}
    cocok = m.group(0)
    sisa = teks[m.end():]
    return {
        "teks": teks,
        "cocok": cocok,
        "sisa": sisa,
        "utuh": sisa == "" and bool(ANGKA_UTUH.fullmatch(teks)),
    }


def uji_beda_versi():
    """Bandingkan pola 3.13.0 dan 3.13.12 pada digit Unicode.

    Pola 3.13.0 memakai \\d yang pada string Python juga cocok dengan digit
    Unicode. Pola 3.13.12 memakai [0-9] yang hanya menerima digit ASCII.
    """
    hasil = []
    for teks in ["1\u0662", "\u0661\u0662", "12"]:
        a = NUMBER_RE.match(teks)
        b = NUMBER_RE_31312.match(teks)
        hasil.append({
            "teks": teks,
            "kode": teks.encode("unicode_escape").decode("ascii"),
            "cocok_3130": a.group(0) if a else None,
            "cocok_31312": b.group(0) if b else None,
        })
    return hasil

