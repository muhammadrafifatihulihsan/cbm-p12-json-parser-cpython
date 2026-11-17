# Parser JSON CPython dan Batas Finite Automata

Studi kasus Case-Based Method Pertemuan 12, mata kuliah Teori Bahasa dan Automata,
Program Studi Informatika, Universitas Negeri Padang.

Repositori ini membedah implementasi nyata parser JSON pada CPython, lalu menguji
batas model Finite Automata ketika berhadapan dengan struktur bersarang. Objek yang
dianalisis adalah kode sumber resmi CPython v3.13.0, khususnya `Lib/json/decoder.py`,
`Lib/json/scanner.py`, dan akselerator C `Modules/_json.c`. Pengujian dijalankan pada
Python 3.13.12 di Windows.

Repositori bukan parser JSON baru yang menggantikan `json` bawaan. Repositori berisi
alat reproduksi eksperimen, parser turunan rekursif sederhana untuk pembanding,
model DFA berbatas, demonstrasi Pumping Lemma, dan seluruh data hasil pengujian.
Dengan begitu, setiap angka pada laporan dapat diperiksa ulang.

---

## 1. Gambaran proyek

Pertanyaan utama proyek ini sederhana: mengapa pencocokan pola biasa cukup untuk
mengenali token JSON, tetapi tidak cukup untuk memastikan dokumen JSON yang
bersarang seimbang?

Jawabannya tidak berhenti pada kalimat "regex tidak bisa parsing". Proyek ini
menunjukkan tiga hal yang berbeda:

1. Lapisan token pada CPython memang memakai ekspresi reguler, yaitu `NUMBER_RE`,
   `WHITESPACE`, dan `STRINGCHUNK`. Lapisan ini berperilaku seperti model
   berhingga.
2. Lapisan struktur tidak memakai satu DFA. `JSONObject` dan `JSONArray` memanggil
   kembali `scan_once` untuk setiap nilai bersarang. Tumpukan pemanggilan fungsi
   menjadi memori yang menghitung kedalaman.
3. Bahasa kurung seimbang, yang menjadi pola dasar struktur bersarang, bukan bahasa
   reguler. Buktinya memakai Pumping Lemma. Karena itu tidak ada DFA dengan jumlah
   state tetap yang dapat menerima semua kedalaman.

Ketiga hal itu diuji dengan kode yang benar-benar dijalankan. Hasil utamanya:

| Pengujian | Hasil pada mesin ini |
|---|---|
| Kedalaman array bersarang maksimum, pemindai C `_json` | 2.998 |
| Kedalaman maksimum, pemindai Python `py_make_scanner` | 497 |
| Kedalaman maksimum, parser turunan rekursif pembanding | 497 |
| DFA berbatas k | menerima sampai k, menolak k+1 |
| Regex berkedalaman k | menerima sampai k, menolak k+1 |
| Pumping Lemma, p = 8 | 108 dari 108 hasil pompa keluar dari D |
| Korpus 240 dokumen | 240 sepakat dengan `json.loads` |
| Mutasi yang benar-benar tidak sah | 109, seluruhnya ditolak parser |

---

## 2. Latar belakang dan konteks masalah

JSON adalah format pertukaran data yang dipakai hampir di semua layanan web. Dokumen
JSON dapat berisi objek dan array yang bersarang tanpa batas kedalaman yang
ditetapkan oleh spesifikasi. Di sisi lain, perkakas pengolah teks yang paling murah
adalah ekspresi reguler dan DFA. Keduanya tidak memiliki memori tambahan selain
state yang jumlahnya tetap.

Pada praktiknya, banyak orang menyebut "validasi JSON dengan regex". Sebagian
melakukannya untuk memeriksa potongan kecil, misalnya satu angka atau satu string.
Sebagian lain mencoba memvalidasi seluruh dokumen dengan satu pola besar. Pendekatan
kedua gagal pada dokumen bersarang, dan kegagalannya bukan karena pola kurang panjang,
melainkan karena batas kemampuan model.

CPython memberi contoh nyata bagaimana pembagian kerja dilakukan. `Lib/json` memakai
regex untuk token, lalu memakai fungsi rekursif untuk struktur. Pembagian itu bukan
kebetulan. Pembagian itu mengikuti perbedaan antara lexical analysis dan syntactic
analysis yang dikenal pada teori kompilator.

Masalah yang diangkat proyek ini adalah:

- Di bagian mana CPython benar-benar memakai regex?
- Di bagian mana CPython meninggalkan model berhingga dan memakai tumpukan?
- Mengapa perpindahan itu diperlukan?
- Bagaimana membuktikan kebutuhan itu secara formal, bukan hanya dengan contoh?

---

## 3. Tujuan dan ruang lingkup

Tujuan proyek:

1. Menjelaskan alur parser JSON CPython berdasarkan kode sumber resmi.
2. Memetakan elemen teori bahasa formal ke fungsi dan variabel nyata pada kode.
3. Membandingkan pengenalan token dengan pengenalan struktur bersarang.
4. Membuktikan bahwa bahasa kurung seimbang bukan bahasa reguler memakai Pumping
   Lemma.
5. Menguji batas nyata implementasi: kapan pemindai gagal karena kedalaman, dan
   apakah kegagalan itu sifat teori atau batas runtime.
6. Menyediakan data eksperimen yang dapat direproduksi.

Ruang lingkup:

- Versi kode yang dibedah: CPython v3.13.0.
- Runtime pengujian: CPython 3.13.12, Windows 11, AMD64.
- Berkas yang dibedah: `Lib/json/decoder.py`, `Lib/json/scanner.py`,
  `Modules/_json.c`.
- Bahasa formal yang dipakai sebagai alat bukti: D = { "("^n ")"^n | n >= 0 } dan
  varian siku D_s = { "["^n "]"^n | n >= 0 }.
- Pengujian tidak mengukur kecepatan, konsumsi memori, atau keamanan produksi.

Di luar ruang lingkup:

- Membuat parser JSON baru yang siap produksi.
- Mengubah atau menambal CPython.
- Menguji semua implementasi JSON di semua bahasa pemrograman.
- Mengklaim bahwa setiap mesin regex di dunia memiliki perilaku yang sama.

---

## 4. Studi kasus nyata yang digunakan

Seluruh berkas sumber diunduh dari repositori resmi CPython dan diperiksa
checksum-nya. Salinan tersimpan di luar repositori ini, pada folder `riset/01-sumber`
dari paket tugas.

| Berkas | Peran | SHA-256 (awal) |
|---|---|---|
| `Lib/json/decoder.py` v3.13.0 | Parser objek, array, string, dan entry point decode | `0e756ee2194d865d` |
| `Lib/json/scanner.py` v3.13.0 | Pemindai token dan pemilihan cabang | `8604d9d03786d0d5` |
| `Modules/_json.c` v3.13.0 | Akselerator C untuk scanner dan string | `a16459d70d06a864` |

Tautan resmi:

- https://github.com/python/cpython/blob/v3.13.0/Lib/json/decoder.py
- https://github.com/python/cpython/blob/v3.13.0/Lib/json/scanner.py
- https://github.com/python/cpython/blob/v3.13.0/Modules/_json.c
- https://docs.python.org/3.13/library/json.html
- https://docs.python.org/3.13/library/re.html
- https://www.rfc-editor.org/rfc/rfc8259

Perbedaan versi yang ditemukan saat pemeriksaan:

- Pada runtime 3.13.12, `NUMBER_RE` memakai `[0-9]` dan bukan `\d`.
- Perbedaan itu terlihat pada digit Unicode. Pola 3.13.0 mencocokkan `1٢`
  seluruhnya, sedangkan pola 3.13.12 hanya mencocokkan `1`. Pengujian pola
  dilakukan pada `src/pola_regex.py` dan dicatat di `hasil/hasil_eksperimen.json`.
- Pada runtime 3.13.12, `_decode_uXXXX` memakai pola `HEXDIGITS` yang dikompilasi,
  sedangkan versi 3.13.0 memakai pemeriksaan manual.
- Untuk token angka ASCII, kedua pola mengenali bahasa yang sama. Perbedaan hanya
  muncul pada digit Unicode, sehingga catatan ini tidak boleh digeneralisasi menjadi
  "parser 3.13.0 menerima dokumen 1٢".
- Perbedaan itu dicatat supaya pembaca tidak mengira source 3.13.0 identik dengan
  runtime 3.13.12.

Modul `json` yang diuji adalah modul bawaan runtime. Pada mesin ini
`json.scanner.make_scanner` berasal dari modul `_json`, sehingga jalur C yang aktif.

---

## 5. Landasan teori

### 5.1 Bahasa, alfabet, dan string

Sebuah alfabet Σ adalah himpunan simbol. String adalah barisan berhingga simbol.
Bahasa adalah himpunan string atas Σ. Untuk JSON, alfabetnya adalah karakter
Unicode yang muncul pada dokumen, dan bahasa JSON adalah himpunan seluruh dokumen
yang sah menurut RFC 8259.

Notasi yang dipakai:

- Σ* = himpunan semua string atas Σ.
- |w| = panjang string w.
- w^R = pembalikan string w.
- L1 ∪ L2, L1 ∩ L2, dan L1 · L2 = operasi gabungan, irisan, dan konkatenasi.

### 5.2 DFA dan ekspresi reguler

Deterministic Finite Automaton didefinisikan sebagai M = (Q, Σ, δ, q0, F), dengan
Q himpunan state berhingga, δ fungsi transisi, q0 state awal, dan F himpunan state
akhir. DFA membaca string satu simbol per langkah tanpa memori tambahan. Ekspresi
reguler dan DFA mengenali kelas bahasa yang sama, yaitu bahasa reguler.

Sifat penting yang dipakai pada laporan:

- Bahasa reguler tertutup terhadap gabungan, irisan, komplemen, dan konkatenasi.
- Jika L reguler dan R reguler, maka L ∩ R reguler.
- Setiap DFA dengan n state hanya memiliki memori terbatas, yaitu state saat ini.

### 5.3 Pumping Lemma

Jika L bahasa reguler, maka ada konstanta p sehingga setiap string w dalam L dengan
|w| >= p dapat ditulis w = xyz dengan:

1. |xy| <= p,
2. |y| >= 1,
3. untuk setiap i >= 0, string x y^i z juga anggota L.

Lemma ini syarat perlu, bukan syarat cukup. Lemma dipakai untuk menolak
regularitas, bukan untuk membuktikan regularitas.

### 5.4 CFG, PDA, dan recursive descent

Context-Free Grammar memiliki aturan produksi A -> α. Bahasa bebas konteks dapat
mengandung struktur bersarang karena derivasi dapat menyisipkan nonterminal di
tengah. Pushdown Automaton menambahkan stack sebagai memori. Parser turunan
rekursif adalah bentuk praktis dari pengenalan bebas konteks: setiap fungsi
menangani satu konstruksi, dan pemanggilan fungsi bersarang berperan sebagai stack.

### 5.5 Grammar JSON

RFC 8259 mendefinisikan JSON memakai ABNF. Bagian inti:

```
JSON-text = ws value ws
value     = false / null / true / object / array / number / string
object    = begin-object [ member *( value-separator member ) ] end-object
array     = begin-array [ value *( value-separator value ) ] end-array
```

Aturan `value` muncul di dalam `object` dan `array`, sehingga definisinya rekursif.
Rekursi pada grammar inilah yang tidak dapat dipetakan ke satu DFA berukuran tetap.

---

## 6. Analisis implementasi parser JSON CPython

### 6.1 Arsitektur berkas

`json/__init__.py` menyediakan `loads()` dan `load()`. Keduanya memakai
`JSONDecoder` dari `json/decoder.py`. `JSONDecoder.__init__` menyiapkan
`parse_object = JSONObject`, `parse_array = JSONArray`, `parse_string = scanstring`,
lalu memanggil `scanner.make_scanner(self)`.

`scanner.py` memilih implementasi C bila tersedia:

```python
make_scanner = c_make_scanner or py_make_scanner
```

Pada mesin uji, `make_scanner` berasal dari `_json`, sehingga jalur C yang dipakai.
Jalur Python tetap tersedia dan dipakai sebagai pembanding pada eksperimen.

### 6.2 Lapisan token: regex dan pemilihan karakter

`scanner.py` mendefinisikan `NUMBER_RE`:

```python
NUMBER_RE = re.compile(
    r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?',
    (re.VERBOSE | re.MULTILINE | re.DOTALL))
```

Fungsi `_scan_once` memeriksa karakter pertama, lalu memilih aksi:

- `"` memanggil `parse_string`,
- `{` memanggil `parse_object`,
- `[` memanggil `parse_array`,
- `n`, `t`, `f` memeriksa literal `null`, `true`, `false`,
- selain itu mencoba `NUMBER_RE`.

Pemilihan berdasarkan satu karakter adalah keputusan berhingga. Tidak ada tabel
transisi DFA menyeluruh pada berkas ini. Yang ada adalah cabang `if/elif` dan satu
pola regex untuk angka.

`decoder.py` menambahkan dua pola token:

- `WHITESPACE = re.compile(r'[ \t\n\r]*')` untuk melewati spasi,
- `STRINGCHUNK = re.compile(r'(.*?)(["\\\x00-\x1f])')` untuk memecah string
  menjadi potongan dan terminator.

`py_scanstring` memakai `STRINGCHUNK` berulang kali, menangani escape, dan
menggabungkan potongan. Versi C `scanstring` melakukan pekerjaan yang sama.

### 6.3 Lapisan struktur: JSONObject dan JSONArray

`JSONObject` membaca `{`, lalu:

1. Memeriksa apakah objek kosong.
2. Membaca nama anggota memakai `scanstring`.
3. Memeriksa titik dua.
4. Memanggil `scan_once(s, end)` untuk nilai.
5. Mencatat pasangan, lalu memeriksa koma atau penutup.

`JSONArray` melakukan pola yang sama untuk elemen. Yang penting, `scan_once` yang
dipanggil dari dalam `JSONObject` dan `JSONArray` adalah fungsi yang sama, sehingga
nilai berupa objek atau array akan masuk kembali ke `parse_object` atau
`parse_array`. Di sinilah rekursi terjadi.

Rekursi itu bukan rekursi pada grammar secara eksplisit, tetapi efeknya sama:
konteks "sedang di dalam objek" atau "sedang di dalam array" disimpan pada frame
fungsi, bukan pada state DFA.

### 6.4 Entry point dan penolakan

`JSONDecoder.decode` memanggil `raw_decode`, lalu memeriksa sisa spasi. Bila masih
ada karakter setelah dokumen, decoder melempar `JSONDecodeError("Extra data")`.
`raw_decode` memanggil `scan_once` dan mengubah `StopIteration` menjadi
`JSONDecodeError("Expecting value")`.

Pemeriksaan "Extra data" adalah contoh bahwa penerimaan dokumen tidak cukup dengan
token yang cocok. Token `0` pada string `01` cocok dengan `NUMBER_RE`, tetapi
dokumennya ditolak karena masih ada karakter `1`.

### 6.5 Akselerator C dan batas rekursi

`Modules/_json.c` mengimplementasikan `scan_once_unicode` dengan cabang yang sama.
Pada cabang `{` dan `[`, kode memanggil `_Py_EnterRecursiveCall` sebelum masuk ke
`_parse_object_unicode` atau `_parse_array_unicode`. Pemeriksaan itu mencegah
rekursi C yang tidak terkendali dan mengubah kedalaman berlebih menjadi
`RecursionError`.

Kutipan penting dari sumber:

```c
case '{':
    if (_Py_EnterRecursiveCall(" while decoding a JSON object "
                               "from a unicode string"))
        return NULL;
    res = _parse_object_unicode(s, memo, pystr, idx + 1, next_idx_ptr);
    _Py_LeaveRecursiveCall();
```

Konsekuensinya, parser CPython tidak benar-benar menerima kedalaman tak terbatas
pada mesin nyata. Yang tak terbatas adalah model formal. Implementasi selalu
dibatasi resource, dan batas itu dapat diukur.

---

## 7. Penerapan teori pada kasus nyata

| Konsep teori | Bentuk pada CPython | Peran |
|---|---|---|
| Alfabet Σ | Karakter Unicode pada string masukan | Simbol yang dibaca scanner |
| Token | `NUMBER_RE`, `STRINGCHUNK`, literal | Satuan leksikal |
| State pemindai | Posisi indeks dan cabang `if/elif` | Menentukan aksi berikutnya |
| State akhir token | Panjang hasil `match` | Menandai token selesai |
| DFA dokumen | Tidak ada | Struktur tidak dikenali dengan state tetap |
| Stack | Call stack `JSONObject` dan `JSONArray` | Menyimpan konteks bersarang |
| Penolakan | `JSONDecodeError` | Dokumen tidak sah |
| Penerimaan | `decode` selesai dan sisa string kosong | Dokumen sah |

Tabel di atas penting untuk menghindari klaim berlebihan. CPython memakai ide DFA
pada lapisan token, tetapi tidak memakai satu DFA untuk seluruh dokumen.

---

## 8. Mengapa token bisa, struktur tidak

Token seperti angka memiliki bentuk berhingga. Angka JSON dapat dijelaskan dengan
pola:

```
-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?
```

Pola ini hanya perlu mengingat tahap saat ini: tanda, digit awal, pecahan, atau
eksponen. Jumlah tahapnya tetap. Karena itu DFA kecil cukup.

Struktur bersarang berbeda. Untuk memastikan setiap `[` punya `]` pasangan, pemindai
harus mengingat berapa banyak `[` yang belum ditutup. Jumlah itu tidak dibatasi
konstanta. DFA dengan n state hanya dapat menghitung sampai n, lalu kehabisan state.
Menaikkan n tidak menyelesaikan masalah, karena string bersarang yang lebih dalam
selalu dapat dibentuk.

Hal yang sama berlaku untuk `{` dan `}`. Bahasa kurung seimbang karena itu menjadi
contoh minimal dari masalah ini.

---

## 9. Pembuktian non-regularity

Ambil D = { "("^n ")"^n | n >= 0 }. Andaikan D reguler dengan panjang pemompaan p.
Pilih w = "("^p ")"^p. Karena |w| = 2p >= p, lemma berlaku.

Setiap dekomposisi w = xyz dengan |xy| <= p dan |y| >= 1 menempatkan y di dalam
awalan tanda buka. Jadi y = "("^k untuk suatu k >= 1. Ambil i = 0, maka xz memiliki
p - k tanda buka dan p tanda tutup. Jumlahnya tidak sama, sehingga xz bukan anggota
D. Ini melanggar syarat ketiga lemma. Kontradiksi. Maka D tidak reguler.

Karena bahasa reguler tertutup terhadap irisan dengan bahasa reguler, bahasa JSON
juga tidak reguler. Buktinya, irisan bahasa JSON dengan bahasa reguler `"["* "]"*`
adalah D_s = { "["^n "]"^n | n >= 0 }. Bila JSON reguler, D_s akan reguler. Padahal
D_s tidak reguler dengan argumen yang sama. Kontradiksi.

Demonstrasi numerik pada repositori memeriksa seluruh dekomposisi untuk p = 2, 4, 6,
8, dan 10. Untuk p = 8 ada 36 dekomposisi dan 108 hasil pompa (i = 0, 2, 3). Seluruh
hasil pompa keluar dari D. Pemeriksaan ini adalah ilustrasi untuk p kecil, bukan
pengganti bukti umum.

---

## 10. Struktur direktori

```
cbm-p12-json-parser-cpython/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── pola_regex.py        pola token dari CPython
│   ├── lexer.py             pemindai token sederhana
│   ├── parser_json.py       parser turunan rekursif pembanding
│   ├── otomat_terbatas.py   DFA berbatas dan regex berkedalaman terbatas
│   ├── pumping.py           alat bantu demonstrasi Pumping Lemma
│   ├── eksperimen.py        orkestrator seluruh pengujian
│   └── diagram.py           penggambar diagram dan grafik
├── data/
│   ├── contoh_valid.json
│   ├── contoh_nested.json
│   ├── contoh_tidak_valid.json
│   └── contoh_token.txt
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_otomat.py
│   └── test_pumping.py
├── hasil/
│   ├── hasil_eksperimen.json
│   ├── output_eksperimen.txt
│   └── output_tests.txt
└── gambar/
    ├── alur_scan_once.png
    ├── arsitektur_lapisan.png
    ├── dfa_angka.png
    ├── dfa_kurung.png
    ├── grafik_kedalaman.png
    ├── grafik_otomat.png
    ├── pumping.png
    └── pohon_panggilan.png
```

Penjelasan:

- `src/pola_regex.py` menyalin pola CPython dan menyediakan pengujian token.
- `src/lexer.py` menunjukkan bahwa tokenisasi dapat berhasil pada urutan kurung
  yang salah. Ini bukti bahwa scanner bukan validator struktur.
- `src/parser_json.py` adalah pembanding yang meniru strategi CPython. Parser ini
  dipakai untuk memeriksa apakah pemahaman atas kode sesuai dengan perilaku.
- `src/otomat_terbatas.py` membangun DFA eksplisit untuk kedalaman terbatas dan
  pola regex yang ditulis ulang sampai kedalaman tertentu.
- `src/pumping.py` memeriksa dekomposisi dan hasil pompa.
- `src/eksperimen.py` menjalankan semua uji dan menulis satu berkas JSON.
- `src/diagram.py` menggambar seluruh diagram dari data hasil.

---

## 11. Arsitektur dan alur kerja

Alur eksperimen:

```
teks JSON
   |
   v
[1] uji token: NUMBER_RE, WHITESPACE, STRINGCHUNK
   |
   v
[2] parser pembanding mengurai struktur, mencatat kedalaman
   |
   v
[3] uji DFA berbatas dan regex berbatas pada string kurung
   |
   v
[4] uji kedalaman nyata CPython pada proses terpisah
   |
   v
[5] demonstrasi Pumping Lemma
   |
   v
[6] bandingkan parser pembanding dengan json.loads pada korpus
   |
   v
hasil/hasil_eksperimen.json
```

Uji kedalaman dijalankan pada proses terpisah supaya kegagalan rekursi tidak
mematikan proses utama. Setiap proses menerima satu angka kedalaman, membentuk
string `"[" * n + "0" + "]" * n`, lalu melaporkan apakah `json.loads` menerima
atau melempar `RecursionError`.

Pencarian batas memakai pencarian biner. Batas atas diperbesar sampai ditemukan
kegagalan, sehingga hasil tidak berhenti karena batas pencarian yang terlalu kecil.

---

## 12. Requirements dan instalasi

- Python 3.10 atau lebih baru. Pengujian dilakukan pada Python 3.13.12.
- Tidak ada dependensi eksternal untuk menjalankan eksperimen dan pengujian.
- `matplotlib` hanya dibutuhkan untuk membuat ulang diagram.

Instalasi:

```bash
git clone https://github.com/muhammadrafifatihulihsan/cbm-p12-json-parser-cpython.git
cd cbm-p12-json-parser-cpython
python -m pip install -r requirements.txt
```

Isi `requirements.txt`:

```
matplotlib>=3.8
```

---

## 13. Cara menjalankan

Menjalankan seluruh eksperimen:

```bash
python src/eksperimen.py
```

Perintah itu menulis `hasil/hasil_eksperimen.json` dan mencetak ringkasan. Untuk
menyimpan keluaran teks:

```bash
python src/eksperimen.py | tee hasil/output_eksperimen.txt
```

Menjalankan pengujian:

```bash
python -m unittest discover -s tests -v
```

Membuat ulang diagram:

```bash
python src/diagram.py
```

Catatan: modul di `src/` saling mengimpor secara langsung. Jalankan dari akar
repositori, atau tambahkan `src` ke `PYTHONPATH` bila ingin memanggil dari folder
lain.

---

## 14. Contoh penggunaan

### 14.1 Mengurai dokumen

```python
import sys
sys.path.insert(0, "src")

from parser_json import muat, urai

nilai = muat('{"nama": "Rafi", "nilai": [1, 2, 3]}')
print(nilai)

nilai, info = urai('{"a": [1, {"b": 2}]}')
print(nilai)
print(info.kedalaman_maks, info.jumlah_objek, info.jumlah_array)
```

Keluaran:

```
{'nama': 'Rafi', 'nilai': [1, 2, 3]}
{'a': [1, {'b': 2}]}
3 2 1
```

### 14.2 Memeriksa token angka

```python
from pola_regex import uji_token_angka

for teks in ["0", "01", "1.5", "1e", "+1"]:
    print(teks, uji_token_angka(teks))
```

Keluaran yang tercatat:

```
0   {'teks': '0', 'cocok': '0', 'sisa': '', 'utuh': True}
01  {'teks': '01', 'cocok': '0', 'sisa': '1', 'utuh': False}
1.5 {'teks': '1.5', 'cocok': '1.5', 'sisa': '', 'utuh': True}
1e  {'teks': '1e', 'cocok': '1', 'sisa': 'e', 'utuh': False}
+1  {'teks': '+1', 'cocok': '', 'sisa': '+1', 'utuh': False}
```

### 14.3 Menjalankan DFA berbatas

```python
from otomat_terbatas import DFAKurung

dfa = DFAKurung(3)
for s in ["()", "(())", "((()))", "(((())))"]:
    print(s, dfa.terima(s))
```

Keluaran:

```
() True
(()) True
((())) True
(((()))) False
```

---

## 15. Contoh input dan output

`data/contoh_valid.json`:

```json
{
  "nama": "Rafi",
  "nilai": [1, 2, 3],
  "aktif": true,
  "catatan": null
}
```

`data/contoh_nested.json`:

```json
{"a": {"b": [{"c": []}, {"d": [[[0]]]}]}}
```

`data/contoh_tidak_valid.json`:

```json
{"a": 1,}
```

Hasil pengujian contoh:

| Dokumen | `json.loads` | Parser pembanding |
|---|---|---|
| `{"nama": "Rafi", "nilai": [1, 2, 3], "aktif": true}` | diterima | diterima, kedalaman 2 |
| `[[[[0]]]]` | diterima | diterima, kedalaman 4 |
| `{"a": {"b": [{"c": []}]}}` | diterima | diterima, kedalaman 5 |
| `{"a": 1,}` | ditolak `JSONDecodeError` | ditolak `KesalahanJSON` |
| `][` | ditolak `JSONDecodeError` | ditolak `KesalahanJSON` |
| string kosong | ditolak `JSONDecodeError` | ditolak `KesalahanJSON` |

---

## 16. Hasil pengujian dan interpretasi

Seluruh angka di bawah berasal dari `hasil/hasil_eksperimen.json` yang dihasilkan
`src/eksperimen.py` pada 18 November 2026, Python 3.13.12.

### 16.1 Pengujian token

Dari 18 contoh token angka, 9 cocok utuh dan 9 hanya cocok sebagian atau tidak cocok.

| Token | Hasil `NUMBER_RE` | Sisa | Utuh |
|---|---|---|---|
| `0` | `0` | kosong | ya |
| `-0` | `-0` | kosong | ya |
| `1.5` | `1.5` | kosong | ya |
| `1e-3` | `1e-3` | kosong | ya |
| `01` | `0` | `1` | tidak |
| `+1` | kosong | `+1` | tidak |
| `.5` | kosong | `.5` | tidak |
| `1.` | `1` | `.` | tidak |
| `1e` | `1` | `e` | tidak |
| `--1` | kosong | `--1` | tidak |
| `NaN` | kosong | `NaN` | tidak |
| `1 2` | `1` | ` 2` | tidak |

Interpretasi: `NUMBER_RE` adalah pola token, bukan pola dokumen. Pola itu boleh
berhenti di tengah masukan. Pemeriksaan "Extra data" pada `decode` yang menolak
sisa karakter. Ini contoh nyata bahwa pencocokan token dan penerimaan dokumen
adalah dua hal berbeda.

### 16.2 Pengujian DFA berbatas dan regex berbatas

| k | State DFA | Transisi | Kedalaman maksimum DFA | Kedalaman maksimum regex |
|---|---|---|---|---|
| 1 | 3 | 6 | 1 | 1 |
| 2 | 4 | 8 | 2 | 2 |
| 3 | 5 | 10 | 3 | 3 |
| 4 | 6 | 12 | 4 | 4 |
| 5 | 7 | 14 | 5 | 5 |
| 6 | 8 | 16 | 6 | 6 |

Pada setiap k, string `"(" * (k+1) + ")" * (k+1)` tetap seimbang, tetapi ditolak
oleh DFA maupun regex. Hasil ini bukan kegagalan implementasi, melainkan bukti
bahwa batas kedalaman harus dipatok lebih dahulu, dan setiap patokan menambah state
atau panjang pola.

### 16.3 Pengujian kedalaman nyata

| Implementasi | Kedalaman terbesar yang diterima | Kedalaman pertama yang gagal | Gejala |
|---|---|---|---|
| Pemindai C `_json` | 2.998 | 2999 | `RecursionError` |
| Pemindai Python `py_make_scanner` | 497 | 498 | `RecursionError` |
| Parser pembanding | 497 | 498 | `RecursionError` |

Batas rekursi Python pada runtime itu 1000. Pemindai C memiliki anggaran rekursi
sendiri dan berhenti di sekitar 3000. Pemindai Python memakai kira-kira dua frame
per tingkat, sehingga berhenti di sekitar 500.

Interpretasi: pada mesin nyata, semua parser dibatasi resource. Kedalaman 2.998 bukan
sifat bahasa JSON, melainkan batas implementasi. Yang membedakan parser rekursif
dari DFA bukan "tanpa batas", tetapi "batasnya konfigurasi runtime, bukan jumlah
state yang dirancang".

### 16.4 Pumping Lemma

| p | Panjang w | Dekomposisi | Pengujian | Gagal | Contoh |
|---|---|---|---|---|---|
| 2 | 4 | 3 | 9 | 9 | `())` |
| 4 | 8 | 10 | 30 | 30 | `((())))` |
| 6 | 12 | 21 | 63 | 63 | `((((())))))` |
| 8 | 16 | 36 | 108 | 108 | `((((((())))))))` |
| 10 | 20 | 55 | 165 | 165 | `((((((((())))))))))` |

Pada seluruh dekomposisi, `y` hanya berisi `"("`. Pompa turun selalu mengurangi
jumlah tanda buka tanpa mengurangi tanda tutup, sehingga string keluar dari D.

### 16.5 Perbandingan dengan `json.loads`

Korpus berisi 120 dokumen valid dan 120 dokumen hasil mutasi. Sebanyak 11 mutasi
ternyata masih sah, misalnya perubahan di dalam isi string. Dari 109 mutasi yang
benar-benar tidak sah, seluruhnya ditolak parser pembanding. Kesepakatan total
240 dari 240 dokumen.

Ini bukan bukti formal bahwa parser pembanding setara dengan CPython untuk semua
masukan. Ini bukti bahwa pada korpus yang diuji, perilakunya konsisten.

### 16.6 Konstanta non-standar

| Teks | `json.loads` | Parser pembanding |
|---|---|---|
| `NaN` | diterima, menghasilkan `nan` | ditolak |
| `Infinity` | diterima, menghasilkan `inf` | ditolak |
| `-Infinity` | diterima, menghasilkan `-inf` | ditolak |

Perbedaan ini disengaja. `json` CPython menerima tiga konstanta di luar RFC 8259
secara default. Parser pembanding mengikuti RFC 8259 secara ketat. Perbedaan dicatat
sebagai perilaku implementasi, bukan kesalahan.

---

## 17. Analisis kelebihan, keterbatasan, dan temuan

Kelebihan pendekatan CPython:

- Lapisan token murah dan cepat karena memakai regex serta satu keputusan karakter.
- Struktur ditangani kode rekursif yang mudah dibaca dan mengikuti grammar.
- Akselerator C mempercepat jalur umum tanpa mengubah algoritma.
- Pemisahan tanggung jawab jelas: scanner tidak memutuskan keseimbangan dokumen.

Keterbatasan:

- Kedalaman dibatasi call stack, sehingga dokumen sangat dalam dapat gagal.
- Kesalahan pada kedalaman ekstrem muncul sebagai `RecursionError`, bukan pesan
  sintaks yang ramah.
- `json` menerima konstanta non-standar secara default.
- Dokumen dengan banyak pengulangan dapat membebani CPU, dan dokumentasi Python
  mengingatkan agar data dari sumber tidak tepercaya diproses dengan hati-hati.

Temuan penting:

1. Klaim "regex bisa memvalidasi JSON" hanya benar untuk token, bukan dokumen.
2. Tidak ada satu DFA utuh di `decoder.py` atau `scanner.py`. Yang ada adalah
   dispatch karakter dan rekursi.
3. Batas kedalaman nyata berbeda antara jalur C dan jalur Python, meskipun
   keduanya menjalankan algoritma yang sama.
4. Mutasi acak sering tetap sah bila mengenai isi string. Ini menunjukkan bahwa
   pengujian korpus perlu memeriksa status kebenaran, bukan hanya label "invalid".

---

## 18. Kesimpulan

Parser JSON CPython memakai dua lapis pengenalan. Lapisan token memakai ekspresi
reguler dan keputusan berdasarkan karakter pertama. Lapisan struktur memakai
fungsi rekursif yang memanggil pemindai nilai untuk setiap objek atau array
bersarang. Lapisan kedua tidak dapat digantikan oleh DFA berukuran tetap karena
bahasa kurung seimbang bukan bahasa reguler. Pumping Lemma membuktikannya, dan
eksperimen DFA berbatas menunjukkan bahwa setiap penambahan kedalaman menuntut
penambahan state.

Pada mesin nyata, parser tetap memiliki batas. Batas itu berasal dari call stack
dan konfigurasi runtime, bukan dari definisi bahasa. Studi kasus ini menunjukkan
hubungan yang jelas antara teori formal, batas model, dan keputusan implementasi.

---

## 19. Referensi

- Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2007). *Compilers: Principles,
  techniques, and tools* (2nd ed.). Pearson Addison-Wesley.
- Bray, T. (Ed.). (2017). *The JavaScript Object Notation (JSON) Data Interchange
  Format* (RFC 8259). IETF. https://www.rfc-editor.org/rfc/rfc8259
- Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to automata
  theory, languages, and computation* (3rd ed.). Addison-Wesley.
- Python Software Foundation. (2024). *CPython v3.13.0: Lib/json/decoder.py,
  Lib/json/scanner.py, Modules/_json.c*. GitHub.
  https://github.com/python/cpython/tree/v3.13.0
- Python Software Foundation. (2026). *json: JSON encoder and decoder, Python 3.13
  documentation*. https://docs.python.org/3.13/library/json.html
- Python Software Foundation. (2026). *re: Regular expression operations, Python
  3.13 documentation*. https://docs.python.org/3.13/library/re.html
- Sipser, M. (2012). *Introduction to the theory of computation* (3rd ed.).
  Cengage Learning.

---

## 20. Catatan data dan etika

- Seluruh dokumen uji dibangkitkan secara lokal dengan benih `20261118`. Dokumen
  itu data eksperimen, bukan dataset eksternal.
- Tidak ada hasil pengujian yang dikarang. Angka pada README dan laporan berasal
  dari berkas JSON yang dihasilkan skrip.
- Kode sumber CPython tidak disalin ke repositori ini. Berkas asli disimpan pada
  paket tugas di folder `riset/01-sumber`, dan tautan resminya dicantumkan.
- Repositori tidak melakukan push otomatis. Pemilik akun yang mengunggah.
