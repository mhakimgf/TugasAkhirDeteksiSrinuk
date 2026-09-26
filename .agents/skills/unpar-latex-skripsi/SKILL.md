---
name: unpar-latex-skripsi
description: "Menulis, menyusun, memformat, dan mengompilasi naskah skripsi LaTeX Program Studi Teknik Informatika FTIS UNPAR sesuai pedoman template resmi Lionov v13.1. Gunakan saat membuat atau mengedit Bab (bab1-5), konfigurasi data.tex, penulisan sitasi referensi.bib, makro dosen.tex, tabel booktabs, gambar, persamaan matematika, dan kompilasi pdflatex."
---

# Skill: UNPAR LaTeX Skripsi (Teknik Informatika FTIS v13.1)

Panduan komprehensif penulisan dan kompilasi naskah Skripsi / Tugas Akhir Program Studi Teknik Informatika, Fakultas Sains, Universitas Katolik Parahyangan (UNPAR) menggunakan Template resmi buatan Lionov (v13.1).

---

## 1. Struktur Direktori Proyek Skripsi

Direktori template skripsi berada di:
`SKRIPSI HAKIM/` (atau root direktori skripsi mahasiswa)
```
SKRIPSI HAKIM/
├── skripsi.tex          # File UTAMA (Halaman sampul, pengesahan, abstrak, TOC, include). JANGAN DIUBAH!
├── data.tex             # Metadata mahasiswa, judul, mode, pembimbing, kata pengantar, abstrak
├── dosen.tex            # Kode makro 3 huruf nama & gelar resmi dosen UNPAR
├── referensi.bib        # Basis data pustaka BibTeX dengan format Computer Journal (compj.bst)
├── .sty/
│   ├── compj.bst        # Style bibliografi resmi FTIS UNPAR
│   └── digsig.sty       # Package digital signature
├── Bab/
│   ├── bab1.tex         # Bab 1: Pendahuluan
│   ├── bab2.tex         # Bab 2: Landasan Teori
│   ├── bab3.tex         # Bab 3: Metodologi Penelitian / Analisis & Perancangan
│   ├── bab4.tex         # Bab 4: Implementasi & Hasil Pengujian / Pembahasan
│   └── bab5.tex         # Bab 5: Kesimpulan dan Saran
├── Gambar/              # Seluruh aset gambar (PNG, JPG, PDF). Otomatis terdeteksi tanpa prefix folder!
└── Lampiran/
    ├── lampA.tex        # Lampiran A
    └── lampB.tex        # Lampiran B
```

---

## 2. Aturan Emas & Pantangan Keras (*Critical Rules*)

> [!CAUTION]
> **ATURAN WAJIB TEKNIK INFORMATIKA UNPAR**:
> 1. **DILARANG MENGUBAH `skripsi.tex`**: File `skripsi.tex` adalah *core engine* template. Seluruh pengaturan dokumen, penambahan package (`\usepackage`), deklarasi perintah kustom, judul, dan data diri **WAJIB** ditulis di file `data.tex`.
> 2. **DILARANG MENGGUNAKAN `@web` DI `referensi.bib`**: Khusus mahasiswa Teknik Informatika, dilarang mencantumkan URL website di daftar pustaka! Untuk merujuk laman web atau dokumentasi online, **GUNAKAN FOOTNOTE** langsung di teks: `\footnote{\url{https://...}}`.
> 3. **DILARANG MENULIS "et al." MANUAL**: Pada `referensi.bib`, tuliskan seluruh nama penulis lengkap dipisahkan dengan kata `and`. Format penyingkatan nama diurus otomatis oleh `compj.bst`.
> 4. **POSISI CAPTION TABEL VS GAMBAR**:
>    - **Gambar**: Judul gambar (*caption*) diletakkan di **BAWAH** gambar.
>    - **Tabel**: Judul tabel (*caption*) diletakkan di **ATAS** tabel.
> 5. **SETIAP GAMBAR & TABEL WAJIB DIACU DALAM TEKS**: Tidak boleh ada gambar/tabel yang berdiri sendiri tanpa kalimat rujukan `Gambar~\ref{fig:...}` atau `Tabel~\ref{tab:...}`.

---

## 3. Konfigurasi `data.tex`

File `data.tex` dibagi menjadi beberapa bagian utama:

### A. Pengaturan Mode Dokumen (Bagian II)
Pilih salah satu mode dengan mengaktifkan baris yang sesuai:
* `\mode{bimbingan}`: Untuk draf bimbingan dosen (hanya mencetak bab yang dipilih, spasi bisa diatur).
* `\mode{sidang}`: Untuk naskah Sidang 1 / Proposal (ada nomor baris, spasi 1.5, tanpa abstrak bahasa Inggris).
* `\mode{sidangakhir}`: Untuk Sidang Akhir / Skripsi 2 (ada nomor baris, spasi 1.5).
* `\mode{final}`: Untuk naskah jilid buku skripsi final (lengkap lembar pengesahan, single spacing, tanpa nomor baris).

### B. Daftar Opsional (Bagian V)
```latex
\gambar{yes}    % Tampilkan Daftar Gambar (yes/no)
\tabel{yes}     % Tampilkan Daftar Tabel (yes/no)
\kode{no}       % Tampilkan Daftar Kode Program (yes/no)
\notasi{no}     % Tampilkan Daftar Simbol/Notasi (yes/no)
```

### C. Data Mahasiswa & Dosen (Bagian VIII)
```latex
\namanpm{MUHAMMAD HAKIM GHIFARI AKIYAT}{6182201096}
\tanggal{20}{3}{2026}         % Format angka: {hari}{bulan}{tahun}
\pembimbing{\VSM}{}           % Pembimbing 1 (kode makro), pembimbing 2 (jika tunggal kosongkan {})
\penguji{\GDK}{\HUH}          % Penguji 1 dan Penguji 2
```

### D. Judul & Abstrak (Bagian IX, X, XI)
* Judul tidak boleh ditulis huruf besar seluruhnya (*all caps*). Gunakan `\texorpdfstring{\\}{}` jika ingin pindah baris.
* Masukkan `\abstrakINA{...}` dan `\abstrakENG{...}`.
* Kata kunci dipisahkan koma: `\kunciINA{Padi Rojolele Srinuk, Sentinel-2, KNN-DTW, Segmentasi SNIC}`.

### E. Penambahan Package & Perintah Kustom (Bagian I & Bagian XVII)
* Tambahkan `\usepackage{...}` di **Bagian I**.
* Tambahkan perintah macro baru atau setting `\hyphenation{...}` di **Bagian XVII**.

---

## 4. Referensi Dosen (`dosen.tex`)

Selalu gunakan kode makro 3 huruf resmi di `data.tex`:
| Kode | Nama & Gelar Dosen Informatika UNPAR |
| :---: | :--- |
| `\VSM` | Dr. Veronica Sri Moertini |
| `\MTA` | Mariskha Tri Adithia, P.D.Eng (Kaprodi IF) |
| `\LNV` | Lionov, Ph.D. |
| `\GDK` | Gede Karya, M.T. |
| `\HUH` | Husnul Hakim, M.T. |
| `\PAN` | Pascal Alfadian Nugroho, M.Comp. |
| `\CEN` | Dr.rer.nat. Cecilia Esti Nugraheni |
| `\RDL` | Rosa De Lima, M.T. |
| `\LCA` | Luciana Abednego, M.T. |
| `\CHW` | Chandra Wijaya, M.T. |
| `\ELH` | Elisati Hulu, M.T. |
| `\VAN` | Vania Natali, M.T. |
| `\RCP` | Raymond Chandra Putra, M.T. |
| `\KAL` | Keenan Adiwijaya Leman, M.T. |
| `\KDH` | Kristopher David Harjono, M.T. |

---

## 5. Standar Penulisan Elemen Naskah

### 5.1 Gambar (*Figure*)
Letakkan file gambar di dalam folder `Gambar/`. Jangan tuliskan kata `Gambar/` di dalam perintah `\includegraphics`.
```latex
Di dalam penginderaan jauh, citra hasil segmentasi superpixel diilustrasikan pada Gambar~\ref{fig:snic_delanggu}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.85\textwidth]{grafik_deret_waktu_srinuk_1988_2026}
    \caption[Profil Deret Waktu EVI Padi Srinuk 1988--2026]{Profil deret waktu EVI padi Rojolele Srinuk di Kecamatan Delanggu dari tahun 1988 hingga 2026 berbasis fusi citra Landsat dan Sentinel-2.}
    \label{fig:snic_delanggu}
\end{figure}
```
*Catatan*: Di perintah `\caption[Teks Daftar Gambar]{Teks Penjelasan Lengkap}`, samakan atau ringkas teks yang ada di dalam tanda kurung siku `[...]`.

### 5.2 Tabel (*Table*) dengan `booktabs`
Keterangan tabel **WAJIB** di atas tabel:
```latex
Perbandingan metrik performa klasifikasi disajikan pada Tabel~\ref{tab:eval_tahap2}.

\begin{table}[H]
    \centering
    \caption{Hasil Evaluasi Model KNN-DTW Tahap 2 (Srinuk vs Pembanding)}
    \label{tab:eval_tahap2}
    \begin{tabular}{lcccc}
        \toprule
        \textbf{Kelas} & \textbf{Presisi} & \textbf{Recall} & \textbf{F1-Score} & \textbf{Support} \\
        \midrule
        Non-Srinuk & 0.67 & 0.33 & 0.44 & 6 \\
        Rojolele Srinuk & 0.79 & 0.94 & 0.86 & 16 \\
        \midrule
        \textbf{Rata-rata Tertimbang} & \textbf{0.76} & \textbf{0.77} & \textbf{0.74} & \textbf{22} \\
        \bottomrule
    \end{tabular}
\end{table}
```

### 5.3 Persamaan Matematika (*Equation*)
```latex
Jarak dinamis DTW antara dua deret waktu dirumuskan pada Persamaan~\eqref{eq:dtw_accum}:

\begin{equation}
    D(i, j) = c(i, j) + \min \Big( D(i-1, j), D(i, j-1), D(i-1, j-1) \Big)
    \label{eq:dtw_accum}
\end{equation}
di mana $c(i, j)$ merupakan jarak lokal antara titik $x_i$ dan $y_j$.
```

### 5.4 Kode Program (*Listings*)
```latex
Struktur ekstraksi nilai rata-rata spektral dapat dilihat pada Kode~\ref{kode:extract_chunk}.

\begin{lstlisting}[language=Python, caption={Fungsi ekstraksi nilai spektral klaster via reduceRegions}, label=kode:extract_chunk]
def extract_chunk(fc_batch, col):
    red = img.reduceRegions(collection=fc_batch, reducer=ee.Reducer.mean(), scale=10)
    return red
\end{lstlisting}
```

---

## 6. Format Bibliografi BibTeX (`referensi.bib`)

Style `compj` mengharuskan format entri yang tepat:

### A. Artikel Jurnal Ilmiah (`@article`)
```bibtex
@article{pratama:25:vegetasi,
    author   = {Vico Pratama and Veronica Sri Moertini},
    title    = {Analisis Data Satelit Historis untuk Memantau Vegetasi Terkait dengan Perubahan Iklim},
    journal  = {Jurnal Informatika UNPAR},
    volume   = {12},
    pages    = {45--58},
    year     = {2025}
}
```

### B. Prosiding Seminar / Konferensi (`@inproceedings`)
> [!IMPORTANT]
> Urutan `month` **HARUS** diletakkan setelah `year`!
```bibtex
@inproceedings{achanta:17:snic,
    author    = {Radhakrishna Achanta and Sabine S{\"{u}}sstrunk},
    title     = {Superpixels and Polygons Using Simple Non-Iterative Clustering},
    booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
    pages     = {4651--4660},
    year      = {2017},
    month     = {21-26 July},
    address   = {Honolulu, USA},
    publisher = {IEEE, Piscataway}
}
```

### C. Buku (`@book`)
```bibtex
@book{lillesand:15:remote,
    author    = {Thomas Lillesand and Ralph W. Kiefer and Jonathan Chipman},
    title     = {Remote Sensing and Image Interpretation},
    edition   = {7th},
    year      = {2015},
    publisher = {John Wiley \& Sons},
    address   = {Hoboken, USA}
}
```

### D. Skripsi / Tesis / Disertasi (`@undergraduatethesis` / `@masterthesis` / `@phdthesis`)
```bibtex
@undergraduatethesis{vico:25:skripsi,
    author  = {Vico Pratama},
    title   = {Analisis Data Satelit Historis untuk Memantau Vegetasi Terkait dengan Perubahan Iklim},
    school  = {Universitas Katolik Parahyangan},
    year    = {2025},
    address = {Indonesia}
}
```

### E. Laman Web / Dokumentasi Resmi (Gunakan Footnote di Teks)
Jangan masukkan ke `referensi.bib`. Tuliskan langsung di naskah:
```latex
Google Cloud Score+ merupakan model deteksi tutupan awan berbasis kecerdasan buatan\footnote{\url{https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_CLOUD_SCORE_PLUS_V1_S2_HARMONIZED}}.
```

---

## 7. Prosedur Kompilasi (CLI & LaTeX Engine)

Untuk menghasilkan file `skripsi.pdf` yang sempurna tanpa referensi tanda tanya `[?]`:

### Di Lingkungan Lokal (PowerShell / Terminal):
Masuk ke direktori `SKRIPSI HAKIM/`:
```powershell
cd "c:\Users\Lenovo\OneDrive - Universitas Katolik Parahyangan\Drive Kuliah\TUGAS AKHIR\PROGRAM\SKRIPSI HAKIM"

# 1. Kompilasi pertama membaca label & struktur
pdflatex -interaction=nonstopmode skripsi.tex

# 2. Proses sitasi dan daftar referensi compj
bibtex skripsi

# 3. Kompilasi kedua mengaitkan nomor referensi
pdflatex -interaction=nonstopmode skripsi.tex

# 4. Kompilasi ketiga memastikan nomor halaman TOC & LOF sinkron
pdflatex -interaction=nonstopmode skripsi.tex
```

### Pembersihan File Sementara (*Temporary Files*):
Jika terjadi error format TOC atau BibTeX macet, hapus file-file cache:
```powershell
Remove-Item *.aux, *.bbl, *.blg, *.log, *.out, *.toc, *.lof, *.lot, *.nlo, *.nls -ErrorAction SilentlyContinue
```
