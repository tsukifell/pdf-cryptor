<div align="center">
<img src="assets/icons.ico" alt="Fast PDF Encryptor Icon" width="100" height="100" />

# ⬛ Fast PDF Encryptor

**Aplikasi desktop ringan untuk mengenkripsi file PDF — satu per satu maupun massal via CSV.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![Version](https://img.shields.io/badge/Version-1.0-purple?style=flat-square)

</div>

---

## 📋 Daftar Isi

- [Tentang Aplikasi](#-tentang-aplikasi)
- [Fitur](#-fitur)
- [Tangkapan Layar](#-tangkapan-layar)
- [Persyaratan Sistem](#-persyaratan-sistem)
- [Instalasi](#-instalasi)
- [Cara Penggunaan](#-cara-penggunaan)
  - [Mode Batch (Folder + CSV)](#mode-batch-folder--csv)
  - [Mode Single File](#mode-single-file)
  - [Format CSV](#format-csv)
  - [Pengaturan Enkripsi](#pengaturan-enkripsi)
- [Struktur Proyek](#-struktur-proyek)
- [FAQ](#-faq)
- [Lisensi](#-lisensi)

---

## 📌 Tentang Aplikasi

**Fast PDF Encryptor** adalah aplikasi desktop berbasis Python (Tkinter) yang memungkinkan kamu mengenkripsi file PDF dengan password secara cepat. Dirancang untuk kebutuhan produksi — mulai dari mengamankan satu dokumen hingga mengenkripsi ratusan file PDF sekaligus menggunakan daftar CSV.

Enkripsi menggunakan standar **AES-256** melalui library `pikepdf`, yang kompatibel dengan semua pembaca PDF modern (Adobe Acrobat, Foxit, browser, dll).

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| 🗂️ **Batch Enkripsi** | Enkripsi banyak PDF sekaligus dari satu folder menggunakan file CSV |
| 📄 **Single File** | Enkripsi satu PDF dengan input password langsung |
| 🔐 **AES-256** | Standar enkripsi PDF yang kuat dan kompatibel luas |
| 👑 **Owner Password** | Password terpisah untuk kontrol izin dokumen |
| 🚫 **Permission Flags** | Batasi kemampuan print, copy teks, dan modifikasi |
| 🎨 **Dark UI** | Antarmuka modern dengan tema gelap |
| ⚡ **Non-blocking** | Proses berjalan di thread terpisah — UI tidak freeze |
| ❌ **Cancel Batch** | Bisa membatalkan proses batch di tengah jalan |
| ✅ **Validasi CSV** | Cek format CSV sebelum diproses |
| 🏷️ **Prefix / Suffix** | Tambahkan teks di depan/belakang nama file output |
| 💾 **Config Persisten** | Mengingat folder dan pengaturan terakhir |
| 📊 **Ringkasan Hasil** | Laporan jumlah sukses / gagal / dilewati setelah batch |


## 💻 Persyaratan Sistem

- **Python** 3.10 atau lebih baru
- **Sistem Operasi:** Windows 10/11, macOS 11+, atau Linux (dengan Tkinter)
- **RAM:** Minimal 128 MB (rekomendasi 256 MB untuk batch besar)
- Library Python (lihat [Instalasi](#-instalasi)):
  - `pikepdf`
  - `tkinter` *(sudah termasuk dalam Python standar)*

---

## 🚀 Instalasi

### 1. Clone atau Download

```bash
git clone https://github.com/tsukifell/fast-pdf-encryptor.git
cd fast-pdf-encryptor
```

Atau download ZIP langsung dari halaman Releases.

### 2. Buat Virtual Environment *(opsional tapi disarankan)*

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install pikepdf
```

### 4. Jalankan Aplikasi

```bash
python fast_pdf_encryptor.py
```

### Catatan Tkinter

Tkinter biasanya sudah termasuk dalam instalasi Python. Jika tidak:

```bash
# Ubuntu / Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# macOS (via Homebrew)
brew install python-tk
```

---

## 📖 Cara Penggunaan

Aplikasi memiliki dua tab utama: **Enkripsi** dan **Pengaturan**.

---

### Mode Batch (Folder + CSV)

Gunakan mode ini untuk mengenkripsi banyak file PDF sekaligus.

**Langkah-langkah:**

1. Buka aplikasi → pastikan mode **"📁 Folder + CSV (Batch)"** dipilih
2. Klik **Pilih…** di baris *Folder PDF* → pilih folder yang berisi file-file PDF
3. Klik **Pilih…** di baris *File CSV* → pilih file CSV kamu (lihat [Format CSV](#format-csv))
4. *(Opsional)* Klik tombol **Validasi CSV** untuk memverifikasi format file sebelum proses
5. Klik **Pilih…** di baris *Output Folder* → pilih folder tujuan hasil enkripsi
6. Klik **▶ Mulai Enkripsi**
7. Pantau progress dan log di bagian bawah
8. Setelah selesai, akan muncul ringkasan: berhasil / gagal / dilewati

> 💡 Klik **✕ Batalkan** untuk menghentikan proses batch kapan saja.

---

### Mode Single File

Gunakan mode ini untuk mengenkripsi satu file PDF.

**Langkah-langkah:**

1. Pilih mode **"📄 Single File"**
2. Klik **Pilih…** di baris *Single PDF* → pilih file PDF
3. Klik **Pilih…** di baris *Output Folder*
4. Klik **▶ Mulai Enkripsi**
5. Masukkan password pada dialog yang muncul → klik OK
6. File terenkripsi akan tersimpan di folder output

---

### Format CSV

File CSV harus memiliki dua kolom: `filename` dan `password`.

**Contoh isi CSV (`daftar_enkripsi.csv`):**

```csv
filename,password
laporan_keuangan.pdf,Rahasia@2026
kontrak_kerja.pdf,P@ssw0rdKuat
sertifikat_001.pdf,sertif2026!
invoice_jan.pdf,inv_jan_secret
```

**Ketentuan penting:**

- Baris **pertama wajib** berupa header: `filename,password`
- Nama file **relatif** terhadap folder PDF yang dipilih (bukan path penuh)
- Simpan dalam format **UTF-8** (di Excel: *Save As → CSV UTF-8*)
- Tidak boleh ada baris kosong di tengah data
- Password tidak boleh kosong

**Cara membuat CSV di Excel:**

1. Buka Excel → buat dua kolom: `filename` dan `password`
2. Isi data per baris
3. File → Save As → pilih format **"CSV UTF-8 (Comma delimited)"**

---

### Pengaturan Enkripsi

Buka tab **Pengaturan** untuk mengonfigurasi opsi tambahan.

#### Penamaan File Output

| Mode | Contoh Input | Contoh Output |
|---|---|---|
| `prefix` | `dokumen.pdf` | `secured_dokumen.pdf` |
| `suffix` | `dokumen.pdf` | `dokumen_secured.pdf` |
| `none` | `dokumen.pdf` | `dokumen.pdf` |

> Preview nama file ditampilkan secara real-time saat kamu mengetik prefix/suffix.

#### Owner Password

- **User Password** → dibutuhkan untuk *membuka* dokumen
- **Owner Password** → dibutuhkan untuk mengubah *izin* dokumen
- Jika dikosongkan, owner password = user password

#### Permission Flags

| Izin | Fungsi |
|---|---|
| ✅ Boleh Print | Pengguna dapat mencetak dokumen |
| ☐ Boleh Copy Teks | Pengguna dapat menyalin teks |
| ☐ Boleh Modifikasi | Pengguna dapat mengedit dokumen |

> Izin ini hanya berlaku selama pengguna tidak mengetahui owner password.

#### Simpan Pengaturan

Klik **💾 Simpan Pengaturan** untuk menyimpan konfigurasi (folder terakhir, prefix/suffix, mode naming) secara permanen. Pengaturan akan otomatis dimuat saat aplikasi dibuka kembali.

## ❓ FAQ

**Q: File PDF sudah terproteksi password, bisa dienkripsi ulang?**
> Tidak. Aplikasi ini tidak bisa membuka PDF yang sudah terproteksi. Hapus dulu password lamanya menggunakan tools lain, baru enkripsi ulang.

**Q: Apakah file asli akan diubah?**
> Tidak. File asli tidak akan disentuh. Hasil enkripsi selalu disimpan ke folder output sebagai file baru.

**Q: Jika nama file output sudah ada di folder output, apa yang terjadi?**
> Aplikasi otomatis menambahkan timestamp pada nama file output agar tidak menimpa file yang sudah ada. Contoh: `secured_dokumen_20260414_153012.pdf`

**Q: Berapa besar file yang bisa diproses?**
> Tidak ada batasan ukuran dari sisi aplikasi. Batasnya hanya kapasitas RAM dan disk kamu.

**Q: Apakah password tersimpan di suatu tempat?**
> Tidak. Password hanya digunakan saat proses enkripsi dan tidak pernah disimpan ke disk oleh aplikasi ini.

**Q: Kenapa ada file `.pdf_encryptor_config.json` di home folder saya?**
> File ini menyimpan preferensi seperti folder terakhir dan pengaturan naming. Bisa dihapus kapan saja tanpa efek negatif.

---
