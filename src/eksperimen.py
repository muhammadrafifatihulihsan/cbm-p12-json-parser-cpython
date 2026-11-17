"""Eksperimen utama untuk studi kasus parser JSON CPython.

Seluruh angka yang dipakai laporan berasal dari berkas
``hasil/hasil_eksperimen.json`` yang ditulis modul ini. Tidak ada angka yang
diketik manual ke dalam laporan.

Cara menjalankan dari akar repositori:

    python src/eksperimen.py
"""

import json
import platform
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from otomat_terbatas import DFAKurung, cocok_regex, uji_batas
from parser_json import KesalahanJSON, urai
from pola_regex import (NUMBER_RE, STRINGCHUNK, WHITESPACE, uji_beda_versi,
                        uji_token_angka)
from pumping import periksa, saksi

AKAR = Path(__file__).resolve().parent.parent
HASIL = AKAR / "hasil"
HASIL.mkdir(exist_ok=True)

BENIH = 20261118


def lingkungan():
    """Catat runtime yang benar-benar dipakai saat eksperimen."""
    import json as modul_json
    import json.scanner as pemindai

    return {
        "python": sys.version,
        "implementasi": platform.python_implementation(),
        "platform": platform.platform(),
        "arsitektur": platform.machine(),
        "berkas_json": str(Path(modul_json.__file__).resolve()),
        "modul_scanner": getattr(pemindai.make_scanner, "__module__", "?"),
        "pemindai_c": pemindai.make_scanner is pemindai.c_make_scanner,
        "batas_rekursi": sys.getrecursionlimit(),
        "waktu": datetime.now().isoformat(timespec="seconds"),
    }


def uji_token():
    """Uji pola token yang disalin dari CPython."""
    contoh_angka = [
        "0", "-0", "1", "-12", "1.5", "-0.25", "1e10", "1E+10", "1e-3",
        "01", "+1", ".5", "1.", "1e", "--1", "NaN", "Infinity", "1 2",
    ]
    angka = [uji_token_angka(t) for t in contoh_angka]
    utuh = sum(1 for a in angka if a["utuh"])
    parsial = sum(1 for a in angka if a["cocok"] and a["sisa"])
    spasi = [
        {"teks": repr(t), "panjang": WHITESPACE.match(t).end()}
        for t in ["", " ", "  \t", "\n\r", "x", " \n x"]
    ]
    string = []
    for t in ['"abc"', '"a\\"b"', '"a\\nb"', '"abc', '"a\x01b"']:
        m = STRINGCHUNK.match(t, 1)
        string.append({
            "teks": t.encode("unicode_escape").decode("ascii"),
            "isi": m.group(1) if m else None,
            "akhir": m.group(2) if m else None,
            "posisi_akhir": m.end() if m else None,
        })
    return {
        "angka": angka,
        "jumlah_contoh": len(angka),
        "jumlah_utuh": utuh,
        "jumlah_parsial": parsial,
        "spasi": spasi,
        "string_chunk": string,
    }


KODE_UJI_C = """
import json, sys
n = int(sys.argv[1])
s = "[" * n + "0" + "]" * n
try:
    json.loads(s)
    print("diterima")
except RecursionError:
    print("RecursionError")
except Exception as e:
    print(type(e).__name__)
"""

KODE_UJI_PY = """
import json, json.decoder, json.scanner, sys
n = int(sys.argv[1])
s = "[" * n + "0" + "]" * n
json.scanner.make_scanner = json.scanner.py_make_scanner
d = json.decoder.JSONDecoder()
try:
    d.decode(s)
    print("diterima")
except RecursionError:
    print("RecursionError")
except Exception as e:
    print(type(e).__name__)
"""

KODE_UJI_SENDIRI = """
import sys
sys.path.insert(0, sys.argv[2])
from parser_json import muat
n = int(sys.argv[1])
s = "[" * n + "0" + "]" * n
try:
    muat(s)
    print("diterima")
except RecursionError:
    print("RecursionError")
except Exception as e:
    print(type(e).__name__)
"""


def jalankan_uji(kode, n):
    """Jalankan satu uji kedalaman pada proses terpisah."""
    argumen = [sys.executable, "-c", kode, str(n)]
    if kode == KODE_UJI_SENDIRI:
        argumen.append(str(AKAR / "src"))
    proses = subprocess.run(argumen, capture_output=True, text=True, timeout=180)
    keluaran = (proses.stdout or proses.stderr).strip().splitlines()
    status = keluaran[-1] if keluaran else f"exit {proses.returncode}"
    return {"kedalaman": n, "status": status, "kode_keluar": proses.returncode}


def cari_batas(kode, atas, label):
    """Cari kedalaman terbesar yang masih diterima dengan pencarian biner.

    Batas atas harus benar-benar gagal. Bila batas atas ternyata diterima,
    batas atas dinaikkan sampai ditemukan kegagalan, supaya hasil tidak
    berhenti di batas pencarian.
    """
    hasil_atas_awal = jalankan_uji(kode, atas)
    while hasil_atas_awal["status"] == "diterima":
        atas *= 2
        hasil_atas_awal = jalankan_uji(kode, atas)
        if atas > 100000:
            raise RuntimeError("batas kedalaman tidak ditemukan")
    bawah = 1
    jejak = [hasil_atas_awal]
    while bawah < atas:
        tengah = (bawah + atas + 1) // 2
        hasil = jalankan_uji(kode, tengah)
        jejak.append(hasil)
        if hasil["status"] == "diterima":
            bawah = tengah
        else:
            atas = tengah - 1
    hasil_bawah = jalankan_uji(kode, bawah)
    hasil_atas = jalankan_uji(kode, bawah + 1)
    return {
        "label": label,
        "maks_diterima": bawah,
        "uji_batas": [hasil_bawah, hasil_atas],
        "jejak_pencarian": jejak,
        "status_gagal": hasil_atas["status"],
    }


def uji_kedalaman():
    """Bandingkan batas kedalaman pemindai C, pemindai Python, dan parser sendiri."""
    return {
        "c": cari_batas(KODE_UJI_C, 4000, "pemindai C (_json)"),
        "python": cari_batas(KODE_UJI_PY, 1000, "pemindai Python (py_make_scanner)"),
        "sendiri": cari_batas(KODE_UJI_SENDIRI, 1000, "parser turunan rekursif sendiri"),
    }


def uji_otomat():
    """Uji DFA berbatas dan regex berkedalaman terbatas."""
    rincian = {}
    ringkasan = []
    for k in [1, 2, 3, 4, 5, 6]:
        kedalaman = list(range(0, k + 4))
        hasil = uji_batas(k, kedalaman)
        rincian[str(k)] = hasil
        dfa = DFAKurung(k)
        maks_dfa = max((h["kedalaman"] for h in hasil if h["dfa"]), default=-1)
        maks_regex = max((h["kedalaman"] for h in hasil if h["regex"]), default=-1)
        ringkasan.append({
            "k": k,
            "state_dfa": dfa.jumlah_state(),
            "transisi_dfa": dfa.jumlah_transisi(),
            "kedalaman_maks_dfa": maks_dfa,
            "kedalaman_maks_regex": maks_regex,
            "uji_di_atas_batas": next(h for h in hasil if h["kedalaman"] == k + 1),
        })
    return {"rincian": rincian, "ringkasan": ringkasan}


def uji_pumping():
    """Jalankan demonstrasi Pumping Lemma untuk beberapa nilai p."""
    hasil = [periksa(p) for p in (2, 4, 6, 8, 10)]
    # periksa sifat struktural: seluruh y pada dekomposisi hanya berisi '('
    hanya_buka = True
    for h in hasil:
        w = saksi(h["p"])
        from pumping import dekomposisi

        for _, y, _ in dekomposisi(w, h["p"]):
            if set(y) != {"("}:
                hanya_buka = False
    return {"hasil": hasil, "semua_y_hanya_buka": hanya_buka}


def nilai_acak(rng, level=0):
    pilihan = ["angka", "string", "benar", "salah", "kosong"]
    if level < 3:
        pilihan += ["array", "objek"]
    jenis = rng.choice(pilihan)
    if jenis == "angka":
        return rng.choice([0, 1, -7, 3.5, 1e-3, 123456])
    if jenis == "string":
        return rng.choice(["", "a", "teks", "kata kunci", "baris\nbaru"])
    if jenis == "benar":
        return True
    if jenis == "salah":
        return False
    if jenis == "kosong":
        return None
    if jenis == "array":
        return [nilai_acak(rng, level + 1) for _ in range(rng.randint(0, 4))]
    kunci = ["a", "b", "nama", "nilai", "kunci"]
    return {rng.choice(kunci): nilai_acak(rng, level + 1) for _ in range(rng.randint(0, 4))}


def mutasi(rng, teks):
    """Rusak satu dokumen valid dengan satu perubahan acak."""
    if not teks:
        return "{"
    posisi = rng.randrange(len(teks))
    pilihan = rng.choice(["hapus", "ganti", "tambah", "potong", "tambahan"])
    if pilihan == "hapus":
        return teks[:posisi] + teks[posisi + 1:]
    if pilihan == "ganti":
        pengganti = rng.choice(list("{}[],:\"0123456789x"))
        return teks[:posisi] + pengganti + teks[posisi + 1:]
    if pilihan == "tambah":
        return teks[:posisi] + rng.choice(list("{}[],:")) + teks[posisi:]
    if pilihan == "potong":
        return teks[:posisi]
    return teks + rng.choice(["x", "]", "}", ",", " 0"])


def uji_korpus():
    """Bandingkan parser sendiri dengan json.loads pada korpus eksperimen.

    Status kebenaran ditentukan oleh ``json.loads``. Dokumen valid dibangkitkan
    dengan ``json.dumps``, lalu dirusak satu kali. Sebagian mutasi ternyata
    masih menghasilkan JSON yang sah, sehingga jumlah mutasi yang benar-benar
    tidak sah dihitung terpisah dan tidak dipaksakan menjadi 120.
    """
    rng = random.Random(BENIH)
    valid = [json.dumps(nilai_acak(rng), ensure_ascii=False) for _ in range(120)]
    mutasi_teks = [mutasi(rng, rng.choice(valid)) for _ in range(120)]

    def diterima_json(teks):
        try:
            json.loads(teks)
            return True
        except Exception:
            return False

    def diterima_sendiri(teks):
        from parser_json import muat as muat_sendiri

        try:
            muat_sendiri(teks)
            return True
        except Exception:
            return False

    setuju = 0
    beda = []
    for teks in valid + mutasi_teks:
        kira = diterima_json(teks)
        kita = diterima_sendiri(teks)
        if kira == kita:
            setuju += 1
        else:
            beda.append({"teks": teks, "json_bawaan": kira, "parser_sendiri": kita})

    mutasi_sah = [t for t in mutasi_teks if diterima_json(t)]
    mutasi_tidak_sah = [t for t in mutasi_teks if not diterima_json(t)]
    ditolak_sendiri = [t for t in mutasi_tidak_sah if not diterima_sendiri(t)]
    valid_diterima = [t for t in valid if diterima_sendiri(t)]
    return {
        "jumlah_valid": len(valid),
        "jumlah_mutasi": len(mutasi_teks),
        "mutasi_tetap_sah": len(mutasi_sah),
        "mutasi_tidak_sah": len(mutasi_tidak_sah),
        "mutasi_tidak_sah_ditolak_sendiri": len(ditolak_sendiri),
        "jumlah_total": len(valid) + len(mutasi_teks),
        "setuju": setuju,
        "beda": beda,
        "valid_diterima": len(valid_diterima),
        "invalid_ditolak": len(ditolak_sendiri),
        "benih": BENIH,
        "contoh_valid": valid[:5],
        "contoh_mutasi_sah": mutasi_sah[:5],
        "contoh_mutasi_tidak_sah": mutasi_tidak_sah[:5],
    }


def _diterima(teks):
    from parser_json import muat

    try:
        muat(teks)
        return True
    except Exception:
        return False


def uji_nonstandar():
    """Catat konstanta non-standar yang diterima modul json CPython."""
    hasil = []
    for teks in ["NaN", "Infinity", "-Infinity"]:
        try:
            nilai = json.loads(teks)
            status = f"diterima ({nilai!r})"
        except Exception as e:
            status = f"ditolak ({type(e).__name__})"
        hasil.append({
            "teks": teks,
            "json_cpython": status,
            "parser_sendiri": "diterima" if _diterima(teks) else "ditolak",
        })
    return hasil


def uji_contoh_json():
    """Contoh dokumen dari README dan laporan, diuji dengan kedua parser."""
    contoh = [
        '{"nama": "Rafi", "nilai": [1, 2, 3], "aktif": true}',
        '[[[[0]]]]',
        '{"a": {"b": [{"c": []}]}}',
        '{"a": 1,}',
        '][',
        '',
    ]
    hasil = []
    for teks in contoh:
        try:
            nilai = json.loads(teks)
            status_json = "diterima"
        except Exception as e:
            status_json = f"ditolak ({type(e).__name__})"
            nilai = None
        try:
            _, info = urai(teks)
            status_sendiri = "diterima"
            kedalaman = info.kedalaman_maks
        except Exception as e:
            status_sendiri = f"ditolak ({type(e).__name__})"
            kedalaman = None
        hasil.append({
            "teks": teks,
            "json_cpython": status_json,
            "parser_sendiri": status_sendiri,
            "kedalaman": kedalaman,
        })
    return hasil


def main():
    data = {
        "lingkungan": lingkungan(),
        "token": uji_token(),
        "kedalaman": uji_kedalaman(),
        "otomat": uji_otomat(),
        "pumping": uji_pumping(),
        "korpus": uji_korpus(),
        "nonstandar": uji_nonstandar(),
        "beda_versi": uji_beda_versi(),
        "contoh": uji_contoh_json(),
    }
    tujuan = HASIL / "hasil_eksperimen.json"
    tujuan.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Runtime          :", data["lingkungan"]["python"].split()[0])
    print("Pemindai C aktif :", data["lingkungan"]["pemindai_c"])
    print("Batas rekursi    :", data["lingkungan"]["batas_rekursi"])
    print()
    print("Token angka      :", data["token"]["jumlah_utuh"], "utuh dari",
          data["token"]["jumlah_contoh"], "contoh")
    print("Batas kedalaman  : C =", data["kedalaman"]["c"]["maks_diterima"],
          "| Python =", data["kedalaman"]["python"]["maks_diterima"],
          "| parser sendiri =", data["kedalaman"]["sendiri"]["maks_diterima"])
    print("DFA berbatas     :", ", ".join(
        f"k={r['k']} maks={r['kedalaman_maks_dfa']}" for r in data["otomat"]["ringkasan"]))
    print("Pumping          :", ", ".join(
        f"p={r['p']} gagal={r['jumlah_gagal']}/{r['jumlah_uji']}"
        for r in data["pumping"]["hasil"]))
    print("Korpus           :", data["korpus"]["setuju"], "dari",
          data["korpus"]["jumlah_total"], "dokumen sepakat")
    print("Valid diterima   :", data["korpus"]["valid_diterima"], "dari",
          data["korpus"]["jumlah_valid"])
    print("Mutasi tidak sah :", data["korpus"]["mutasi_tidak_sah"], "| ditolak parser:",
          data["korpus"]["invalid_ditolak"])
    print()
    print("Hasil ditulis    :", tujuan)
    return data


if __name__ == "__main__":
    main()
