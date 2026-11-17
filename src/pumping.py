"""Alat bantu demonstrasi Pumping Lemma untuk bahasa kurung seimbang.

Bahasa yang dipakai:

    D = { "("^n ")"^n | n >= 0 }

Bahasa ini bagian dari bahasa kurung seimbang, dan kurung seimbang adalah
pola dasar struktur JSON bersarang. Fungsi di modul ini tidak membuktikan
lemma, tetapi memeriksa seluruh dekomposisi untuk panjang pemompaan kecil.
Pemeriksaan menyeluruh pada satu nilai p adalah ilustrasi, bukan pengganti
bukti untuk semua p.
"""


def seimbang(teks):
    """True bila tanda kurung pada ``teks`` seimbang."""
    dalam = 0
    for c in teks:
        if c == "(":
            dalam += 1
        elif c == ")":
            dalam -= 1
            if dalam < 0:
                return False
        else:
            return False
    return dalam == 0


def anggota_d(teks):
    """True bila ``teks`` berbentuk '('^n ')'^n."""
    if not seimbang(teks):
        return False
    if not teks:
        return True
    tengah = len(teks) // 2
    return teks == "(" * tengah + ")" * tengah and len(teks) % 2 == 0


def saksi(p):
    """String saksi w = '('^p ')'^p untuk panjang pemompaan p."""
    return "(" * p + ")" * p


def dekomposisi(w, p):
    """Semua (x, y, z) dengan w = xyz, |xy| <= p, dan |y| >= 1."""
    hasil = []
    for panjang_y in range(1, p + 1):
        for mulai in range(0, p - panjang_y + 1):
            x = w[:mulai]
            y = w[mulai:mulai + panjang_y]
            z = w[mulai + panjang_y:]
            if len(x) + len(y) <= p:
                hasil.append((x, y, z))
    return hasil


def pompa(x, y, z, i):
    """Bentuk x y^i z."""
    return x + y * i + z


def periksa(p, i_maks=3):
    """Periksa seluruh dekomposisi saksi untuk p tertentu.

    Untuk setiap dekomposisi, string hasil pemompaan dengan i = 0, 2, ..., 
    i_maks diuji keanggotaannya pada D. i = 1 selalu anggota D karena sama
    dengan w. Hasil menyimpan jumlah dekomposisi, jumlah pengujian, dan
    contoh kegagalan pertama.
    """
    w = saksi(p)
    daftar = dekomposisi(w, p)
    jumlah_uji = 0
    jumlah_gagal = 0
    contoh = None
    for x, y, z in daftar:
        for i in range(0, i_maks + 1):
            if i == 1:
                continue
            hasil = pompa(x, y, z, i)
            jumlah_uji += 1
            if not anggota_d(hasil):
                jumlah_gagal += 1
                if contoh is None:
                    contoh = {
                        "x": x,
                        "y": y,
                        "z": z,
                        "i": i,
                        "hasil": hasil,
                        "panjang": len(hasil),
                        "seimbang": seimbang(hasil),
                    }
    return {
        "p": p,
        "w": w,
        "panjang_w": len(w),
        "jumlah_dekomposisi": len(daftar),
        "jumlah_uji": jumlah_uji,
        "jumlah_gagal": jumlah_gagal,
        "semua_gagal": jumlah_gagal == jumlah_uji and jumlah_uji > 0,
        "contoh": contoh,
    }
