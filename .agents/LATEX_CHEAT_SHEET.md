# 📑 LaTeX & VS Code Cheat Sheet (Template Skripsi UNPAR Lionov v13.1)

Panduan ringkas pintasan (*keyboard shortcuts*), sintaks penting, perintah khusus template UNPAR, serta tips menghindari galat (*errors*) saat menyusun naskah tugas akhir.

---

## ⌨️ 1. Pintasan Keyboard VS Code + LaTeX Workshop

| Pintasan (Windows) | Fungsi | Keterangan |
| :--- | :--- | :--- |
| `Ctrl + S` | **Simpan & Auto-Build** | Jika autoBuild aktif (`onFileChange`), PDF otomatis dikompilasi ulang. |
| `Ctrl + Alt + B` | **Manual Build (Compile)** | Menjalankan resep TeX Live (`pdflatex -> bibtex -> pdflatex*2`). |
| `Ctrl + Alt + V` | **View PDF in Tab** | Membuka pratinjau PDF *side-by-side* langsung di tab VS Code. |
| `Ctrl + Alt + J` | **Forward Sync (SyncTeX)** | Melompat dari baris kursor di editor `.tex` ke lokasi halaman PDF. |
| `Ctrl + Klik` (di PDF) | **Reverse Sync (SyncTeX)** | Klik teks di viewer PDF untuk melompat langsung ke baris kodenya di `.tex`. |
| `Ctrl + Alt + K` | **Kill Compiler Process** | Menghentikan proses kompilasi jika pdflatex macet (*hang* / *infinite loop*). |
| `Shift + Alt + F` | **Format Document** | Merapikan indentasi secara manual menggunakan `latexindent.exe`. |
| `Ctrl + /` | **Toggle Comment** | Memberi / melepas tanda komentar `%` pada baris yang dipilih. |
| `Ctrl + Shift + P` | **Command Palette** | Ketik `LaTeX Workshop` untuk melihat seluruh perintah ekstensi. |

---

## 🏛️ 2. Aturan Emas Template UNPAR Lionov

> [!CAUTION]
> **JANGAN PERNAH MENGEDIT BERKAS `skripsi.tex` SECARA LANGSUNG!**
> Semua konfigurasi metadata, paket tambahan, perintah baru, dan perbaikan tata letak wajib dimasukkan ke dalam **`data.tex`**:
> - **Bagian I**: Penambahan package baru (contoh: `\usepackage{booktabs}`).
> - **Bagian II–XVI**: Konfigurasi identitas (NPM, Nama, Judul, Pembimbing, Abstrak, Prakata).
> - **Bagian XVII**: Perintah kustom, pengaturan PGFPlots, atau *hook* `\AtBeginDocument`.

---

## 📝 3. Struktur Dokumen & Pembagian Bab

Di dalam `data.tex` Bagian VI:
```latex
\vbab{1,2} % Mengaktifkan Bab 1 dan Bab 2 untuk dikompilasi
```
File bab berada di folder `Bab/`:
- `Bab/bab1.tex` : Pendahuluan
- `Bab/bab2.tex` : Landasan Teori
- `Bab/bab3.tex` : Metodologi Penelitian & Perancangan Sistem
- `Bab/bab4.tex` : Implementasi & Pembahasan Hasil Pengujian
- `Bab/bab5.tex` : Kesimpulan & Saran

### Hirarki Judul Seksi (Heading):
```latex
\chapter{Judul Bab}             % Level Bab (Otomatis dibuat oleh skripsi.tex)
\section{Judul Bagian}           % 1.1 Latar Belakang
\subsection{Sub-Bagian}          % 1.1.1 Sub Topik
\subsubsection{Sub-Sub-Bagian}   % 1.1.1.1 Rincian (hindari jika tidak perlu)
```

---

## 🖼️ 4. Cheatcode Gambar (Figures)

Pastikan file gambar diletakkan di dalam folder `Gambar/`.

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.85\textwidth]{Gambar/nama_gambar.png}
    \caption{Keterangan gambar yang jelas dan informatif.}
    \label{fig:nama_label_unik}
\end{figure}
```

### Menyandingkan 2 Gambar Bersebelahan (Subfigures):
```latex
\begin{figure}[htbp]
    \centering
    \begin{subfigure}[b]{0.48\textwidth}
        \centering
        \includegraphics[width=\textwidth]{Gambar/gambar_a.png}
        \caption{Kondisi sebelum segmentasi}
        \label{fig:sub_a}
    \end{subfigure}
    \hfill
    \begin{subfigure}[b]{0.48\textwidth}
        \centering
        \includegraphics[width=\textwidth]{Gambar/gambar_b.png}
        \caption{Hasil segmentasi SNIC}
        \label{fig:sub_b}
    \end{subfigure}
    \caption{Perbandingan visual citra satelit.}
    \label{fig:perbandingan}
\end{figure}
```

---

## 📊 5. Cheatcode Tabel Standar Akademik (Booktabs)

Gunakan paket `booktabs` (garis horizontal rapi tanpa garis vertikal kaku):

```latex
\begin{table}[htbp]
    \centering
    \caption{Perbandingan Metrik Evaluasi Model Klasifikasi}
    \label{tab:evaluasi_model}
    \begin{tabular}{lcccc}
        \toprule
        \textbf{Model / Tahapan} & \textbf{Akurasi (\%)} & \textbf{Presisi} & \textbf{Recall} & \textbf{F1-Score} \\
        \midrule
        Tahap 1 (Sawah vs Non-Sawah)      & 86,0 & 0,88 & 0,85 & 0,86 \\
        Tahap 2 (Rojolele vs Non-Srinuk)  & 82,5 & 0,80 & 0,94 & 0,86 \\
        \midrule
        \textbf{Hierarkis Keseluruhan}   & \textbf{77,1} & \textbf{0,83} & \textbf{0,89} & \textbf{0,86} \\
        \bottomrule
    \end{tabular}
\end{table}
```

> [!TIP]
> Notasi perataan kolom `tabular`:
> - `l` : Rata kiri (*Left*)
> - `c` : Rata tengah (*Center*)
> - `r` : Rata kanan (*Right*)
> - `p{5cm}` : Rata kiri dengan lebar tetap 5 cm (teks otomatis membungkus/*wrap*).

---

## 📐 6. Cheatcode Rumus Matematika (Math Equations)

### 1. Rumus di Dalam Paragraf (*Inline*):
Gunakan tanda dollar tunggal `$ ... $`:
- Nilai EVI berkisar antara $-1 \le \text{EVI} \le 1$.
- Kompleksitas waktu algoritma adalah $\mathcal{O}(M \times N)$.

### 2. Rumus Bernomor (*Display Equation*):
```latex
\begin{equation}
    \text{EVI} = 2{,}5 \times \frac{\text{NIR} - \text{Red}}{\text{NIR} + 6 \times \text{Red} - 7{,}5 \times \text{Blue} + 1}
    \label{eq:formulasi_evi}
\end{equation}
```

### 3. Rumus Multi-Baris / Sistem Persamaan:
```latex
\begin{equation}
    D(i, j) = d(x_i, y_j) + \min \begin{cases}
        D(i-1, j)   & \text{(penyisipan)} \\
        D(i, j-1)   & \text{(penghapusan)} \\
        D(i-1, j-1) & \text{(pencocokan)}
    \end{cases}
    \label{eq:dtw_dp}
\end{equation}
```

---

## 🔗 7. Cheatcode Sitasi & Referensi Silang (Cross-Reference)

| Sasaran | Cara Merujuk di Teks | Contoh Kode |
| :--- | :--- | :--- |
| **Pustaka / Sitasi** | `\cite{bib_key}` | `Vico Pratama~\cite{pratama:25:vegetasi}` |
| **Gambar** | `Gambar~\ref{fig:label}` | `...ditunjukkan pada Gambar~\ref{fig:alur_sistem}.` |
| **Tabel** | `Tabel~\ref{tab:label}` | `...seperti dirangkum pada Tabel~\ref{tab:evaluasi_model}.` |
| **Persamaan** | `Persamaan~\eqref{eq:label}` | `...dihitung melalui Persamaan~\eqref{eq:formulasi_evi}.` |
| **Bab / Seksi** | `Bab~\ref{sec:label}` | `...dibahas lebih lanjut pada Bab~\ref{sec:metodologi}.` |

> [!NOTE]
> Selalu gunakan simbol tilde `~` sebelum `\ref` atau `\cite` (misal: `Gambar~\ref{...}`) agar nomor referensi tidak terpisah ke baris baru saat pergantian baris.

---

## 📚 8. Format Sitasi BibTeX (`referensi.bib`)

Template UNPAR menggunakan style `compj.bst`.
> [!WARNING]
> **DILARANG MENGGUNAKAN TIPE `@online` ATAU `@web`!**
> Kompilasi akan gagal / error. Gunakan `@misc` atau `@article` untuk sumber dokumen daring.

### Contoh Entri BibTeX yang Valid:

#### 1. Jurnal Ilmiah / Prosiding:
```bibtex
@article{achanta:17:snic,
  author  = {Achanta, Radhakrishna and Susstrunk, Sabine},
  title   = {Superpixels and Polygons Using Simple Non-Iterative Clustering},
  journal = {IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  pages   = {4895--4904},
  year    = {2017}
}
```

#### 2. Buku:
```bibtex
@book{lillesand:15:remote,
  author    = {Lillesand, Thomas M. and Kiefer, Ralph W. and Chipman, Jonathan W.},
  title     = {Remote Sensing and Image Interpretation},
  edition   = {7th},
  publisher = {John Wiley \& Sons},
  address   = {New York},
  year      = {2015}
}
```

#### 3. Skripsi / Tugas Akhir:
```bibtex
@misc{pratama:25:vegetasi,
  author       = {Pratama, Vico},
  title        = {Identifikasi Vegetasi Padi Menggunakan Data Satelit Penginderaan Jauh Multispektral Time Series},
  howpublished = {Skripsi Sarjana Informatika, Universitas Katolik Parahyangan, Bandung},
  year         = {2025}
}
```

---

## 🔤 9. Karakter Khusus & Tipografi Bahasa Indonesia

1. **Karakter Terlarang yang Wajib di-Escape**:
   - Persen: `\%` (contoh: `86\%`, bukan `86%`)
   - Garis bawah: `\_` (contoh: `F1\_score`, atau tulis `\textit{F1-score}`)
   - Simbol dan: `\&` (contoh: `PT Telkom \& Indosat`)
   - Dollar: `\$` (contoh: `\$100`)
   - Pagar: `\#` (contoh: `Nomor \#1`)
2. **Tanda Petik Ganda yang Benar**:
   - Salah: `"teks"`
   - Benar: `\`\`teks''` (dua *backtick* di kiri, dua *apostrof* di kanan $\rightarrow$ “teks”)
3. **Kata Serapan / Asing**:
   - Wajib menggunakan miring: `\textit{time series}`, `\textit{ground truth}`, `\textit{superpixel}`.
4. **Desimal Angka Indonesia**:
   - Jika menulis angka desimal di mode matematika, bungkus koma dengan kurung kurawal agar tidak renggang: `$82{,}5\%$` (bukan `$82,5\%$`).

---

## 🛠️ 10. Solusi Galat Umum (Troubleshooting)

| Gejala Galat | Penyebab | Solusi |
| :--- | :--- | :--- |
| **`LaTeX Warning: Citation undefined`** | Cache aux belum sinkron dengan bibtex. | Jalankan build resep lengkap (`pdflatex -> bibtex -> pdflatex*2`) atau tekan `Ctrl + Alt + B`. |
| **Teks `cfttoctitlename` muncul di Daftar Isi** | Bug L3 kernel tocloft di TeX Live 2026. | Sudah diperbaiki via `\AtBeginDocument` di `data.tex`. |
| **Daftar Gambar / Tabel rata kanan** | Peregang `\hfill` ganda terpotong `\unskip`. | Sudah diselaraskan menggunakan `\vdierror` di `data.tex`. |
| **`Please set your LaTeX formatter...`** | VS Code mencoba format-on-save tanpa formatter. | Sudah dimatikan untuk LaTeX via `"[latex]": { "editor.formatOnSave": false }` di `.vscode/settings.json`. |
| **Kompilasi macet berputar terus** | Terjadi *prompt error* di latar belakang. | Tekan `Ctrl + Alt + K` untuk mematikan proses, periksa berkas `.log` pada baris error terakhir. |
