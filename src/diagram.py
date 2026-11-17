"""Menggambar diagram dan grafik pendukung laporan.

Gambar ditulis ke folder ``gambar/``. Seluruh angka diambil dari
``hasil/hasil_eksperimen.json`` supaya grafik tidak berbeda dari laporan.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

AKAR = Path(__file__).resolve().parent.parent
GAMBAR = AKAR / "gambar"
GAMBAR.mkdir(exist_ok=True)
DATA = json.loads((AKAR / "hasil" / "hasil_eksperimen.json").read_text(encoding="utf-8"))

BIRU = "#1a1a1a"
BIRU_MUDA = "#ffffff"
HIJAU = "#1a1a1a"
HIJAU_MUDA = "#efefef"
ORANYE = "#1a1a1a"
ABU = "#444444"
MERAH = "#1a1a1a"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": "#444444",
    "axes.labelcolor": "#222222",
    "text.color": "#222222",
    "savefig.facecolor": "white",
})


def kotak(ax, x, y, w, h, teks, warna=BIRU_MUDA, tepi=BIRU, ukuran=10, tebal=False):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.4, edgecolor=tepi, facecolor=warna,
    ))
    ax.text(x, y, teks, ha="center", va="center", fontsize=ukuran,
            color="#111111", fontweight="bold" if tebal else "normal", wrap=True)


def panah(ax, a, b, teks="", rad=0.0, warna=ABU, gaya="-|>", ukuran=9, geser=(0, 0.18)):
    ax.add_patch(FancyArrowPatch(
        a, b, arrowstyle=gaya, mutation_scale=12, linewidth=1.3,
        color=warna, connectionstyle=f"arc3,rad={rad}",
        shrinkA=6, shrinkB=6,
    ))
    if teks:
        ax.text((a[0] + b[0]) / 2 + geser[0], (a[1] + b[1]) / 2 + geser[1],
                teks, ha="center", va="bottom", fontsize=ukuran, color=warna)


def simpan(fig, nama):
    fig.savefig(GAMBAR / nama, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("tulis", nama)


def alur_scan_once():
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.set_xlim(0, 100); ax.set_ylim(0, 68); ax.axis("off")
    kotak(ax, 50, 61, 34, 8, "scan_once(s, idx)\nbaca satu karakter", "#f2f2f2", BIRU, 13, True)

    # bus keluar dari scan_once
    ax.plot([50, 50], [57, 51], color=ABU, linewidth=1.2)
    ax.plot([10, 90], [51, 51], color=ABU, linewidth=1.2)

    cabang = [
        (10, "STRING", '"..."', HIJAU_MUDA, HIJAU),
        (30, "OBJECT", "{", BIRU_MUDA, BIRU),
        (50, "ARRAY", "[", BIRU_MUDA, BIRU),
        (70, "LITERAL", "n/t/f", "#f7f7f7", ORANYE),
        (90, "NUMBER", "regex", HIJAU_MUDA, HIJAU),
    ]
    for x, judul, isi, warna, tepi in cabang:
        ax.plot([x, x], [51, 47], color=ABU, linewidth=1.2)
        kotak(ax, x, 41, 18, 11, f"{judul}\n{isi}", warna, tepi, 12, True)

    # bus masuk ke hasil
    for x, *_ in cabang:
        ax.plot([x, x], [35.5, 32], color=ABU, linewidth=1.2)
    ax.plot([10, 90], [32, 32], color=ABU, linewidth=1.2)
    panah(ax, (50, 32), (50, 27.5), warna=ABU)
    kotak(ax, 50, 22, 34, 8, "nilai + posisi akhir", "#f2f2f2", ABU, 12)

    ax.text(50, 10, "Setiap cabang hanya memeriksa karakter pertama, sehingga lapisan ini berhingga.\n"
                    "Bila tidak ada aturan yang cocok, scanner melempar StopIteration, lalu decoder\n"
                    "mengubahnya menjadi JSONDecodeError.",
            ha="center", va="center", fontsize=11,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f7f7f7", edgecolor="#cccccc"))
    simpan(fig, "alur_scan_once.png")


def arsitektur_lapisan():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.set_xlim(0, 100); ax.set_ylim(0, 72); ax.axis("off")
    lapisan = [
        (60, "Dokumen JSON (str)", "teks masukan", "#f2f2f2"),
        (47, "Scanner token", "WHITESPACE, NUMBER_RE, STRINGCHUNK", "#ffffff"),
        (34, "Parser struktur", "JSONObject, JSONArray, rekursif", "#f2f2f2"),
        (21, "Objek Python", "dict, list, str, int, float, bool", "#ffffff"),
    ]
    for y, judul, isi, warna in lapisan:
        kotak(ax, 50, y, 86, 10, f"{judul}\n{isi}", warna, "#1a1a1a", 12, True)
    for y1, y2 in [(60, 47), (47, 34), (34, 21)]:
        panah(ax, (50, y1 - 5.2), (50, y2 + 5.2), warna="#1a1a1a")
    ax.text(50, 8, "Lapisan token dapat dikenali model berhingga.\n"
                   "Struktur bersarang membutuhkan call stack.",
            ha="center", va="center", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#f7f7f7", edgecolor="#cccccc"))
    simpan(fig, "arsitektur_lapisan.png")


def dfa_angka():
    """Alur tahap pengenalan token angka, disederhanakan dari Tabel 1."""
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    tahap = [
        ("Karakter awal", "angka atau tanda minus", "#ffffff"),
        ("Tanda minus", "opsional, satu karakter", "#f2f2f2"),
        ("Digit bulat", "0, atau 1-9 lalu digit berikutnya", "#ffffff"),
        ("Pecahan", "opsional: titik lalu satu digit atau lebih", "#f2f2f2"),
        ("Eksponen", "opsional: e/E, tanda, lalu digit", "#ffffff"),
    ]
    y = 90
    for i, (judul, isi, warna) in enumerate(tahap):
        kotak(ax, 50, y, 74, 11, f"{judul}\n{isi}", warna, "#1a1a1a", 10.5, True)
        if i < len(tahap) - 1:
            panah(ax, (50, y - 5.6), (50, y - 12.4), warna="#1a1a1a")
        y -= 16
    kotak(ax, 50, 8, 74, 9, "Token selesai\nposisi akhir menjadi awal token berikutnya",
          "#ffffff", "#1a1a1a", 10.5, True)
    panah(ax, (50, 20.5), (50, 13.2), warna="#1a1a1a")
    simpan(fig, "dfa_angka.png")


def dfa_kurung():
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 44); ax.axis("off")
    xs = [14, 38, 62, 86]
    nama = ["q0", "q1", "q2", "q3"]
    for x, n in zip(xs, nama):
        if n == "q0":
            ax.add_patch(plt.Circle((x, 25), 2.9, fill=False, linewidth=1.2, color=BIRU))
        ax.add_patch(plt.Circle((x, 25), 2.4, fill=True, facecolor=HIJAU_MUDA,
                                edgecolor=HIJAU, linewidth=1.5))
        ax.text(x, 25, n, ha="center", va="center", fontsize=11, zorder=5)
    panah(ax, (3, 25), (11.2, 25), "mulai", warna=ABU, geser=(0, 0.5))
    for i in range(3):
        panah(ax, (xs[i] + 2.6, 26.2), (xs[i + 1] - 2.6, 26.2), warna=HIJAU, rad=-0.02)
        ax.text((xs[i] + xs[i + 1]) / 2, 27.6, "(", ha="center", fontsize=12, color=HIJAU)
        panah(ax, (xs[i + 1] - 2.6, 23.8), (xs[i] + 2.6, 23.8), warna=BIRU, rad=-0.02)
        ax.text((xs[i] + xs[i + 1]) / 2, 21.6, ")", ha="center", fontsize=12, color=BIRU)
    ax.text(50, 38, "DFA kurung seimbang dengan batas kedalaman k = 3",
            ha="center", fontsize=12.5, fontweight="bold", color=BIRU)
    ax.text(50, 8, "Transisi '(' dari q3 dan transisi ')' dari q0 menuju state mati "
                   "(tidak digambar).\nString '(((())))' berkedalaman 4 tetap seimbang, "
                   "tetapi ditolak oleh DFA ini.",
            ha="center", va="center", fontsize=10, color="#333333",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f7f7f7", edgecolor="#cccccc"))
    simpan(fig, "dfa_kurung.png")


def grafik_kedalaman():
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    label = ["Pemindai C\n(_json)", "Pemindai Python\n(py_make_scanner)", "Parser sendiri\n(rekursif)"]
    nilai = [DATA["kedalaman"]["c"]["maks_diterima"],
             DATA["kedalaman"]["python"]["maks_diterima"],
             DATA["kedalaman"]["sendiri"]["maks_diterima"]]
    batang = ax.bar(label, nilai, color=["#bdbdbd", "#d9d9d9", "#efefef"], edgecolor="#222222", width=0.55)
    for b, n in zip(batang, nilai):
        ax.text(b.get_x() + b.get_width() / 2, n + 40, f"{n}", ha="center",
                fontsize=10.5, fontweight="bold")
    ax.set_ylabel("Kedalaman array bersarang terbesar")
    ax.set_ylim(0, max(nilai) * 1.18)
    ax.set_title("Batas kedalaman nyata pada Python 3.13.12", fontsize=12, color=BIRU)
    ax.grid(axis="y", linestyle=":", color="#bbbbbb", alpha=0.7)
    ax.set_axisbelow(True)
    ax.text(0.5, -0.28, "Batas rekursi sys.getrecursionlimit() = 1000. Batas bukan sifat teori, "
                        "melainkan batas implementasi.",
            transform=ax.transAxes, ha="center", fontsize=9.5, color="#444444")
    simpan(fig, "grafik_kedalaman.png")


def grafik_otomat():
    ringkas = DATA["otomat"]["ringkasan"]
    k = [r["k"] for r in ringkas]
    state = [r["state_dfa"] for r in ringkas]
    maks = [r["kedalaman_maks_dfa"] for r in ringkas]
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.bar([str(x) for x in k], state, color="#e6e6e6", edgecolor="#222222", width=0.55,
           label="jumlah state DFA")
    ax.plot([str(x) for x in k], maks, marker="o", color="#111111", linewidth=2,
            label="kedalaman maksimum yang diterima")
    for x, n, s in zip(k, maks, state):
        ax.text(str(x), s + 0.25, str(s), ha="center", fontsize=9.5, color=BIRU)
        ax.text(str(x), n - 0.55, str(n), ha="center", fontsize=9.5, color=MERAH)
    ax.set_xlabel("Batas kedalaman k")
    ax.set_ylabel("Jumlah state / kedalaman")
    ax.set_ylim(0, max(state) + 2)
    ax.set_title("DFA berbatas dan regex berkedalaman terbatas", fontsize=12, color=BIRU)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", linestyle=":", color="#bbbbbb", alpha=0.7)
    ax.set_axisbelow(True)
    simpan(fig, "grafik_otomat.png")


def pumping():
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.set_xlim(-2, 104); ax.set_ylim(0, 48); ax.axis("off")
    p = 5
    lebar = 6.2
    mulai = 10
    for i in range(p):
        ax.add_patch(plt.Rectangle((mulai + i * lebar, 28), lebar - 0.4, 7,
                                   facecolor="#ffffff", edgecolor="#1a1a1a"))
        ax.text(mulai + i * lebar + (lebar - 0.4) / 2, 31.5, "(", ha="center",
                va="center", fontsize=13)
        ax.add_patch(plt.Rectangle((mulai + (p + i) * lebar, 28), lebar - 0.4, 7,
                                   facecolor="#efefef", edgecolor="#1a1a1a"))
        ax.text(mulai + (p + i) * lebar + (lebar - 0.4) / 2, 31.5, ")", ha="center",
                va="center", fontsize=13)

    akhir = mulai + 2 * p * lebar
    ax.plot([mulai, mulai + lebar - 0.4], [39, 39], color="#1a1a1a", linewidth=1.2)
    ax.plot([mulai, mulai], [38.4, 39.6], color="#1a1a1a", linewidth=1.2)
    ax.plot([mulai + lebar - 0.4, mulai + lebar - 0.4], [38.4, 39.6], color="#1a1a1a", linewidth=1.2)
    ax.text(mulai + (lebar - 0.4) / 2, 41.2, "y", ha="center", va="bottom", fontsize=11)
    ax.plot([mulai + lebar, akhir - 0.4], [39, 39], color="#1a1a1a", linewidth=1.2)
    ax.text((mulai + lebar + akhir - 0.4) / 2, 41.2, "z", ha="center", va="bottom", fontsize=11)
    ax.text(mulai - 1, 31.5, "x", ha="right", va="center", fontsize=11)

    ax.text(52, 20, "|xy| <= p, maka y hanya berisi tanda buka", ha="center",
            va="center", fontsize=9.5)

    y0 = 7
    for i in range(p - 1):
        ax.add_patch(plt.Rectangle((mulai + i * lebar, y0), lebar - 0.4, 6,
                                   facecolor="#ffffff", edgecolor="#1a1a1a"))
        ax.text(mulai + i * lebar + (lebar - 0.4) / 2, y0 + 3, "(", ha="center",
                va="center", fontsize=12)
    for i in range(p):
        ax.add_patch(plt.Rectangle((mulai + (p - 1 + i) * lebar, y0), lebar - 0.4, 6,
                                   facecolor="#efefef", edgecolor="#1a1a1a"))
        ax.text(mulai + (p - 1 + i) * lebar + (lebar - 0.4) / 2, y0 + 3, ")", ha="center",
                va="center", fontsize=12)
    ax.text(52, 1.5, "Pompa i = 0: satu tanda buka hilang, jumlah tanda tutup tetap.",
            ha="center", va="bottom", fontsize=9)
    simpan(fig, "pumping.png")


def pohon_panggilan():
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 80); ax.axis("off")
    kotak(ax, 50, 73, 30, 7, "scan_once\nposisi 0", "#f2f2f2", "#1a1a1a", 11, True)
    kotak(ax, 50, 59, 30, 9, "JSONObject\n{\"a\": ...}", "#ffffff", "#1a1a1a", 11)
    kotak(ax, 22, 42, 28, 9, "scanstring\nkunci \"a\"", "#ffffff", "#1a1a1a", 11)
    kotak(ax, 78, 42, 28, 9, "scan_once\nnilai", "#f2f2f2", "#1a1a1a", 11)
    kotak(ax, 78, 26, 28, 9, "JSONArray\n[1, {...}]", "#ffffff", "#1a1a1a", 11)
    kotak(ax, 78, 10, 28, 9, "JSONObject\n{\"b\": 2}", "#ffffff", "#1a1a1a", 11)
    panah(ax, (50, 68.6), (50, 63.5), warna="#1a1a1a")
    panah(ax, (39, 54.6), (30, 47), warna="#1a1a1a")
    panah(ax, (61, 54.6), (70, 47), warna="#1a1a1a")
    panah(ax, (78, 37.5), (78, 30.5), warna="#1a1a1a")
    panah(ax, (78, 21.5), (78, 14.5), warna="#1a1a1a")
    ax.text(50, 2, "Kedalaman call stack bertambah setiap objek atau array dibuka.",
            ha="center", va="center", fontsize=9.5)
    simpan(fig, "pohon_panggilan.png")


if __name__ == "__main__":
    alur_scan_once()
    arsitektur_lapisan()
    dfa_angka()
    dfa_kurung()
    grafik_kedalaman()
    grafik_otomat()
    pumping()
    pohon_panggilan()
    print("selesai:", GAMBAR)
