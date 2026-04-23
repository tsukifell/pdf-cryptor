"""
PDF Cryptor
© 2026 tsukifell. All rights reserved.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import csv
import os
import json
import threading
import pikepdf
from pathlib import Path
from datetime import datetime


APP_NAME = "PDF Cryptor"
APP_VERSION = "1.1"
COPYRIGHT = "© 2026 tsukifell. All rights reserved."
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pdf_encryptor_config.json")

# ---------- Color Palette ----------
CLR = {
    "bg":        "#0f0f13",
    "surface":   "#1a1a24",
    "card":      "#22222f",
    "border":    "#2e2e40",
    "accent":    "#7c6af7",
    "accent2":   "#5ddcb0",
    "danger":    "#f76a6a",
    "warn":      "#f7c46a",
    "success":   "#5ddcb0",
    "text":      "#e8e8f0",
    "muted":     "#7a7a99",
    "entry_bg":  "#14141e",
}


# ============================================================
# Helpers
# ============================================================

def load_config() -> dict:
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data: dict):
    try:
        existing = load_config()
        existing.update(data)
        with open(CONFIG_FILE, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        pass


def validate_pdf(path: str) -> tuple[bool, str]:
    """Returns (ok, error_message). Tries to open the PDF."""
    if not os.path.exists(path):
        return False, "File tidak ditemukan"
    if not path.lower().endswith(".pdf"):
        return False, "Bukan file PDF"
    try:
        with pikepdf.open(path):
            pass
        return True, ""
    except pikepdf.PasswordError:
        return False, "File sudah terproteksi password"
    except Exception as e:
        return False, f"File rusak atau tidak valid: {e}"


def detect_csv_delimiter(path: str) -> str:
    """Auto-detect CSV delimiter by sniffing the first line. Falls back to ','."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        return dialect.delimiter
    except csv.Error:
        # Sniffer failed — count occurrences on the header line as tiebreaker
        try:
            first_line = sample.splitlines()[0] if sample else ""
            counts = {d: first_line.count(d) for d in (",", ";", "|", "\t")}
            return max(counts, key=counts.get)
        except Exception:
            return ","


def validate_csv(path: str) -> tuple[bool, str, list]:
    """Returns (ok, error_message, rows). Auto-detects ',' or ';' delimiter."""
    if not os.path.exists(path):
        return False, "File CSV tidak ditemukan", []
    try:
        delimiter = detect_csv_delimiter(path)
        rows = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames or []
            if "filename" not in headers or "password" not in headers:
                return (
                    False,
                    f"CSV harus punya kolom 'filename' dan 'password'.\n"
                    f"Separator terdeteksi: '{delimiter}'\n"
                    f"Kolom ditemukan: {headers}",
                    [],
                )
            for i, row in enumerate(reader, start=2):
                fname = (row.get("filename") or "").strip()
                pwd = (row.get("password") or "").strip()
                if not fname or not pwd:
                    return False, f"Baris {i} tidak lengkap: {dict(row)}", []
                rows.append({"filename": fname, "password": pwd})
        if not rows:
            return False, "CSV kosong, tidak ada baris data", []
        return True, delimiter, rows          # delimiter returned as second value when ok
    except UnicodeDecodeError:
        return False, "CSV encoding tidak didukung. Simpan sebagai UTF-8.", []
    except Exception as e:
        return False, f"Gagal membaca CSV: {e}", []


# ============================================================
# Tooltip helper
# ============================================================

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self.tw, text=self.text,
            bg="#2a2a3a", fg=CLR["text"],
            font=("Consolas", 8),
            relief="flat", padx=8, pady=4,
            wraplength=280, justify="left"
        )
        lbl.pack()

    def hide(self, _=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


# ============================================================
# Main Application
# ============================================================

class PDFEncryptorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.minsize(780, 620)
        self.root.configure(bg=CLR["bg"])

        self._cancel_flag = False
        self._processing = False

        self._setup_variables()
        self._load_config()
        self._apply_styles()
        self._build_ui()

    # ---- Setup ----

    def _setup_variables(self):
        self.folder_var = tk.StringVar()
        self.csv_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.prefix_var = tk.StringVar(value="secured_")
        self.suffix_var = tk.StringVar(value="_secured")
        self.input_mode_var = tk.StringVar(value="folder")
        self.name_mode_var = tk.StringVar(value="prefix")
        self.single_file_var = tk.StringVar()
        self.owner_pwd_var = tk.StringVar()
        self.allow_print_var = tk.BooleanVar(value=True)
        self.allow_copy_var = tk.BooleanVar(value=False)
        self.allow_modify_var = tk.BooleanVar(value=False)

    def _load_config(self):
        cfg = load_config()
        if cfg.get("last_folder"):
            self.folder_var.set(cfg["last_folder"])
        if cfg.get("last_output"):
            self.output_folder_var.set(cfg["last_output"])
        if cfg.get("prefix"):
            self.prefix_var.set(cfg["prefix"])
        if cfg.get("suffix"):
            self.suffix_var.set(cfg["suffix"])
        if cfg.get("name_mode"):
            self.name_mode_var.set(cfg["name_mode"])

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=CLR["bg"], foreground=CLR["text"],
                         font=("Segoe UI", 9), borderwidth=0)

        style.configure("TFrame", background=CLR["bg"])
        style.configure("Card.TFrame", background=CLR["card"],
                         relief="flat", borderwidth=1)

        style.configure("TLabel", background=CLR["bg"], foreground=CLR["text"],
                         font=("Segoe UI", 9))
        style.configure("Muted.TLabel", foreground=CLR["muted"], font=("Segoe UI", 8))
        style.configure("Title.TLabel", foreground=CLR["text"],
                         font=("Segoe UI", 15, "bold"), background=CLR["bg"])
        style.configure("Section.TLabel", foreground=CLR["accent"],
                         font=("Segoe UI", 9, "bold"), background=CLR["bg"])

        style.configure("TButton",
                         background=CLR["accent"], foreground="#ffffff",
                         font=("Segoe UI", 9, "bold"), padding=(12, 6),
                         relief="flat", borderwidth=0)
        style.map("TButton",
                   background=[("active", "#6658d6"), ("disabled", CLR["border"])],
                   foreground=[("disabled", CLR["muted"])])

        style.configure("Danger.TButton",
                         background=CLR["danger"], foreground="#ffffff",
                         font=("Segoe UI", 9, "bold"), padding=(12, 6))
        style.map("Danger.TButton",
                   background=[("active", "#d94f4f")])

        style.configure("Ghost.TButton",
                         background=CLR["card"], foreground=CLR["muted"],
                         font=("Segoe UI", 8), padding=(8, 4))
        style.map("Ghost.TButton",
                   background=[("active", CLR["border"])],
                   foreground=[("active", CLR["text"])])

        style.configure("TEntry",
                         fieldbackground=CLR["entry_bg"], foreground=CLR["text"],
                         insertcolor=CLR["accent"], relief="flat",
                         borderwidth=1, padding=(6, 4))

        style.configure("TCombobox",
                         fieldbackground=CLR["entry_bg"], foreground=CLR["text"],
                         background=CLR["card"], arrowcolor=CLR["accent"],
                         selectbackground=CLR["accent"], selectforeground="#fff")
        style.map("TCombobox",
                   fieldbackground=[("readonly", CLR["entry_bg"])],
                   foreground=[("readonly", CLR["text"])])

        style.configure("TRadiobutton",
                         background=CLR["bg"], foreground=CLR["text"],
                         font=("Segoe UI", 9))
        style.map("TRadiobutton", background=[("active", CLR["bg"])])

        style.configure("TCheckbutton",
                         background=CLR["bg"], foreground=CLR["text"],
                         font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", CLR["bg"])])

        style.configure("TProgressbar",
                         troughcolor=CLR["border"], background=CLR["accent"],
                         thickness=6)

        style.configure("TSeparator", background=CLR["border"])

        self.root.option_add("*TCombobox*Listbox.background", CLR["card"])
        self.root.option_add("*TCombobox*Listbox.foreground", CLR["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", CLR["accent"])

    # ---- UI Building ----

    def _build_ui(self):
        self._create_menu()

        outer = ttk.Frame(self.root)
        outer.pack(fill="both", expand=True, padx=16, pady=12)

        # Header
        hdr = ttk.Frame(outer)
        hdr.pack(fill="x", pady=(0, 12))
        ttk.Label(hdr, text="⬛ " + APP_NAME, style="Title.TLabel").pack(side="left")
        ttk.Label(hdr, text=f"v{APP_VERSION}", style="Muted.TLabel").pack(side="left", padx=(8, 0), pady=4)

        # Notebook / Tabs
        nb = ttk.Notebook(outer)
        nb.pack(fill="both", expand=True)

        self._tab_main = ttk.Frame(nb, padding=12)
        self._tab_settings = ttk.Frame(nb, padding=12)
        nb.add(self._tab_main, text="  Enkripsi  ")
        nb.add(self._tab_settings, text="  Pengaturan  ")

        self._build_main_tab(self._tab_main)
        self._build_settings_tab(self._tab_settings)

        # Bottom bar
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(8, 0))
        ttk.Label(bottom, text=COPYRIGHT, style="Muted.TLabel").pack(side="left")

    def _create_menu(self):
        menubar = tk.Menu(self.root, bg=CLR["card"], fg=CLR["text"],
                           activebackground=CLR["accent"], activeforeground="#fff",
                           borderwidth=0)
        help_menu = tk.Menu(menubar, tearoff=0, bg=CLR["card"], fg=CLR["text"],
                              activebackground=CLR["accent"], activeforeground="#fff")
        help_menu.add_command(label="Cara Pakai", command=self._show_help)
        help_menu.add_command(label="Format CSV", command=self._show_csv_help)
        help_menu.add_separator()
        help_menu.add_command(label=f"Tentang {APP_NAME}", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def _section(self, parent, title):
        """Create a labeled section separator."""
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=(10, 4))
        ttk.Label(f, text=title, style="Section.TLabel").pack(side="left")
        ttk.Separator(f, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(8, 0), pady=4)
        return f

    def _labeled_browse(self, parent, row, label, var, cmd, tooltip_text, filetypes=None):
        """Row with label + entry + browse button."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=(6, 4), pady=2)
        btn = ttk.Button(parent, text="Pilih…", style="Ghost.TButton", command=cmd)
        btn.grid(row=row, column=2, pady=2)
        Tooltip(entry, tooltip_text)
        Tooltip(btn, tooltip_text)
        return entry

    def _build_main_tab(self, parent):
        # --- Mode ---
        self._section(parent, "Mode Input")
        mode_f = ttk.Frame(parent)
        mode_f.pack(fill="x", pady=(0, 4))
        rb1 = ttk.Radiobutton(mode_f, text="📁  Folder + CSV (Batch)", variable=self.input_mode_var,
                               value="folder", command=self._on_mode_change)
        rb1.pack(side="left", padx=(0, 16))
        Tooltip(rb1, "Enkripsi banyak PDF sekaligus menggunakan file CSV yang berisi nama file dan password.")
        rb2 = ttk.Radiobutton(mode_f, text="📄  Single File", variable=self.input_mode_var,
                               value="single", command=self._on_mode_change)
        rb2.pack(side="left")
        Tooltip(rb2, "Enkripsi satu file PDF dengan password yang dimasukkan manual.")

        # --- Inputs ---
        self._section(parent, "File & Folder")
        grid = ttk.Frame(parent)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        self._folder_entry = self._labeled_browse(
            grid, 0, "Folder PDF", self.folder_var, self._browse_folder,
            "Pilih folder yang berisi file-file PDF yang ingin dienkripsi."
        )
        self._csv_entry = self._labeled_browse(
            grid, 1, "File CSV", self.csv_var, self._browse_csv,
            "File CSV dengan kolom: filename, password\nContoh:\nfilename,password\ndokumen.pdf,rahasia123"
        )
        ttk.Button(grid, text="Validasi CSV", style="Ghost.TButton",
                   command=self._validate_csv_ui).grid(row=1, column=3, padx=(4, 0))

        self._single_entry = self._labeled_browse(
            grid, 2, "Single PDF", self.single_file_var, self._browse_single_file,
            "Pilih satu file PDF untuk dienkripsi."
        )
        self._output_entry = self._labeled_browse(
            grid, 3, "Output Folder", self.output_folder_var, self._browse_output_folder,
            "Folder tempat menyimpan hasil enkripsi. Jika kosong, akan digunakan folder yang sama."
        )

        # --- Progress & Controls ---
        self._section(parent, "Proses")
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", pady=(0, 6))
        self.process_btn = ttk.Button(ctrl, text="▶  Mulai Enkripsi", command=self._run_process)
        self.process_btn.pack(side="left", padx=(0, 8))
        self.cancel_btn = ttk.Button(ctrl, text="✕  Batalkan", style="Danger.TButton",
                                      command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left")
        self.status_label = ttk.Label(ctrl, text="Siap.", style="Muted.TLabel")
        self.status_label.pack(side="right")

        self.progress = ttk.Progressbar(parent, mode="determinate")
        self.progress.pack(fill="x", pady=(4, 6))

        # Log
        log_frame = tk.Frame(parent, bg=CLR["entry_bg"], bd=0)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame, height=10,
            bg=CLR["entry_bg"], fg=CLR["text"],
            insertbackground=CLR["accent"],
            selectbackground=CLR["accent"],
            font=("Consolas", 8),
            relief="flat", padx=8, pady=6,
            wrap="word", state="normal"
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_box.pack(fill="both", expand=True)

        # Log color tags
        self.log_box.tag_configure("success", foreground=CLR["success"])
        self.log_box.tag_configure("error", foreground=CLR["danger"])
        self.log_box.tag_configure("warn", foreground=CLR["warn"])
        self.log_box.tag_configure("info", foreground=CLR["accent"])
        self.log_box.tag_configure("muted", foreground=CLR["muted"])

        self._on_mode_change()

    def _build_settings_tab(self, parent):
        parent.columnconfigure(1, weight=1)

        self._section(parent, "Penamaan File Output")
        grid = ttk.Frame(parent)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        ttk.Label(grid, text="Mode Naming").grid(row=0, column=0, sticky="w", pady=2)
        combo = ttk.Combobox(grid, textvariable=self.name_mode_var,
                              values=["prefix", "suffix", "none"], state="readonly", width=14)
        combo.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=2)
        Tooltip(combo, "prefix: tambah teks di depan\nsuffix: tambah teks di belakang\nnone: nama file sama")

        ttk.Label(grid, text="Prefix").grid(row=1, column=0, sticky="w", pady=2)
        e_prefix = ttk.Entry(grid, textvariable=self.prefix_var, width=20)
        e_prefix.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=2)
        Tooltip(e_prefix, "Contoh: 'secured_' → secured_dokumen.pdf")

        ttk.Label(grid, text="Suffix").grid(row=2, column=0, sticky="w", pady=2)
        e_suffix = ttk.Entry(grid, textvariable=self.suffix_var, width=20)
        e_suffix.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=2)
        Tooltip(e_suffix, "Contoh: '_locked' → dokumen_locked.pdf")

        preview_f = ttk.Frame(parent)
        preview_f.pack(fill="x", pady=4)
        self._preview_label = ttk.Label(preview_f, text="", style="Muted.TLabel")
        self._preview_label.pack(side="left")
        self.name_mode_var.trace_add("write", lambda *_: self._update_name_preview())
        self.prefix_var.trace_add("write", lambda *_: self._update_name_preview())
        self.suffix_var.trace_add("write", lambda *_: self._update_name_preview())
        self._update_name_preview()

        self._section(parent, "Keamanan (Owner Password & Permissions)")

        sec_grid = ttk.Frame(parent)
        sec_grid.pack(fill="x")
        sec_grid.columnconfigure(1, weight=1)

        ttk.Label(sec_grid, text="Owner Password").grid(row=0, column=0, sticky="w", pady=2)
        e_owner = ttk.Entry(sec_grid, textvariable=self.owner_pwd_var, show="●", width=22)
        e_owner.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=2)
        Tooltip(e_owner, "Password owner digunakan untuk mengatur izin.\nJika kosong, owner password = user password.\nOwner password tidak dibatasi.")

        ttk.Label(sec_grid, text="Izin Pengguna").grid(row=1, column=0, sticky="nw", pady=(8, 0))
        perm_f = ttk.Frame(sec_grid)
        perm_f.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(8, 0))

        c1 = ttk.Checkbutton(perm_f, text="Boleh Print", variable=self.allow_print_var)
        c1.grid(row=0, column=0, sticky="w")
        Tooltip(c1, "Izinkan pengguna untuk mencetak dokumen.")

        c2 = ttk.Checkbutton(perm_f, text="Boleh Copy Teks", variable=self.allow_copy_var)
        c2.grid(row=1, column=0, sticky="w")
        Tooltip(c2, "Izinkan pengguna untuk menyalin teks dari dokumen.")

        c3 = ttk.Checkbutton(perm_f, text="Boleh Modifikasi", variable=self.allow_modify_var)
        c3.grid(row=2, column=0, sticky="w")
        Tooltip(c3, "Izinkan pengguna untuk memodifikasi isi dokumen.")

        self._section(parent, "Simpan Konfigurasi")
        ttk.Button(parent, text="💾  Simpan Pengaturan", command=self._save_settings).pack(anchor="w")

    # ---- Mode switching ----

    def _on_mode_change(self):
        mode = self.input_mode_var.get()
        is_folder = mode == "folder"

        state_folder = "normal" if is_folder else "disabled"
        state_single = "disabled" if is_folder else "normal"

        self._folder_entry.configure(state=state_folder)
        self._csv_entry.configure(state=state_folder)
        self._single_entry.configure(state=state_single)

    def _update_name_preview(self):
        example = "dokumen.pdf"
        result = self._generate_name(example)
        self._preview_label.configure(text=f"Preview: {example}  →  {result}")

    # ---- Browse actions ----

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Pilih Folder PDF")
        if path:
            self.folder_var.set(path)

    def _browse_csv(self):
        path = filedialog.askopenfilename(
            title="Pilih File CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            self.csv_var.set(path)

    def _browse_output_folder(self):
        path = filedialog.askdirectory(title="Pilih Folder Output")
        if path:
            self.output_folder_var.set(path)

    def _browse_single_file(self):
        path = filedialog.askopenfilename(
            title="Pilih File PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if path:
            self.single_file_var.set(path)

    # ---- Naming ----

    def _generate_name(self, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        mode = self.name_mode_var.get()
        if mode == "prefix":
            return f"{self.prefix_var.get()}{name}{ext}"
        elif mode == "suffix":
            return f"{name}{self.suffix_var.get()}{ext}"
        return filename

    # ---- Logging ----

    def _log(self, msg: str, tag: str = ""):
        self.log_box.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        full = f"[{ts}] {msg}\n"
        if tag:
            self.log_box.insert(tk.END, full, tag)
        else:
            self.log_box.insert(tk.END, full)
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")
        self.root.update_idletasks()

    def _log_clear(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state="disabled")

    def _set_status(self, text: str):
        self.status_label.configure(text=text)
        self.root.update_idletasks()

    # ---- Validation UI ----

    def _validate_csv_ui(self):
        ok, detail, rows = validate_csv(self.csv_var.get())
        if not ok:
            messagebox.showerror("CSV Tidak Valid", detail)
            self._log(f"Validasi CSV gagal: {detail}", "error")
        else:
            sep_label = {";"  : "titik koma (;)",
                         "\t" : "tab",
                         "|"  : "pipe (|)"}.get(detail, "koma (,)")
            messagebox.showinfo("CSV Valid",
                f"CSV valid!\n{len(rows)} baris ditemukan.\nSeparator terdeteksi: {sep_label}")
            self._log(f"CSV valid: {len(rows)} baris | separator: '{detail}'", "success")

    # ---- Save Settings ----

    def _save_settings(self):
        save_config({
            "last_folder": self.folder_var.get(),
            "last_output": self.output_folder_var.get(),
            "prefix": self.prefix_var.get(),
            "suffix": self.suffix_var.get(),
            "name_mode": self.name_mode_var.get(),
        })
        messagebox.showinfo("Tersimpan", "Pengaturan berhasil disimpan.")

    # ---- Cancel ----

    def _cancel(self):
        if self._processing:
            self._cancel_flag = True
            self._log("⚠ Pembatalan diminta. Menunggu file saat ini selesai…", "warn")
            self._set_status("Membatalkan…")

    # ---- Process entry point ----

    def _run_process(self):
        if self._processing:
            return

        self._log_clear()
        output_folder = self.output_folder_var.get().strip()

        # Validate output folder
        if not output_folder:
            messagebox.showerror("Error", "Pilih folder output terlebih dahulu.")
            return
        if not os.path.isdir(output_folder):
            try:
                os.makedirs(output_folder, exist_ok=True)
                self._log(f"Folder output dibuat: {output_folder}", "info")
            except Exception as e:
                messagebox.showerror("Error", f"Tidak dapat membuat folder output:\n{e}")
                return

        mode = self.input_mode_var.get()
        if mode == "folder":
            if not self.folder_var.get():
                messagebox.showerror("Error", "Pilih folder PDF.")
                return
            if not self.csv_var.get():
                messagebox.showerror("Error", "Pilih file CSV.")
                return
            if not os.path.isdir(self.folder_var.get()):
                messagebox.showerror("Error", "Folder PDF tidak valid.")
                return
            ok, detail, rows = validate_csv(self.csv_var.get())
            if not ok:
                messagebox.showerror("CSV Tidak Valid", detail)
                return
            self._log(f"CSV dimuat | separator: '{detail}' | {len(rows)} baris", "info")
            self._start_thread(lambda: self._encrypt_bulk(rows))
        else:
            file_path = self.single_file_var.get().strip()
            if not file_path:
                messagebox.showerror("Error", "Pilih file PDF.")
                return
            ok, err = validate_pdf(file_path)
            if not ok:
                messagebox.showerror("PDF Tidak Valid", err)
                return
            # Ask password in main thread before spawning thread
            password = simpledialog.askstring(
                "Password", "Masukkan password untuk enkripsi:",
                show="*", parent=self.root
            )
            if not password:
                self._log("Enkripsi dibatalkan (password kosong).", "warn")
                return
            self._start_thread(lambda: self._encrypt_single(file_path, password))

    def _start_thread(self, fn):
        self._processing = True
        self._cancel_flag = False
        self.process_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        t = threading.Thread(target=self._thread_wrapper(fn), daemon=True)
        t.start()

    def _thread_wrapper(self, fn):
        def wrapper():
            try:
                fn()
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error tidak terduga: {e}", "error"))
            finally:
                self.root.after(0, self._on_done)
        return wrapper

    def _on_done(self):
        self._processing = False
        self._cancel_flag = False
        self.process_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self._set_status("Selesai.")

    # ---- Encryption logic ----

    def _build_encryption(self, user_pwd: str) -> pikepdf.Encryption:
        owner_pwd = self.owner_pwd_var.get().strip() or user_pwd
        allow = pikepdf.Permissions(
            print_lowres=self.allow_print_var.get(),
            print_highres=self.allow_print_var.get(),
            extract=self.allow_copy_var.get(),
            modify_other=self.allow_modify_var.get(),
            modify_form=self.allow_modify_var.get(),
        )
        return pikepdf.Encryption(user=user_pwd, owner=owner_pwd, allow=allow)

    def _encrypt_file(self, input_path: str, output_path: str, password: str) -> tuple[bool, str]:
        """Returns (success, message)."""
        try:
            # Check if output already exists
            if os.path.exists(output_path):
                base, ext = os.path.splitext(output_path)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"{base}_{ts}{ext}"

            enc = self._build_encryption(password)
            with pikepdf.open(input_path) as pdf:
                pdf.save(output_path, encryption=enc)
            return True, os.path.basename(output_path)
        except pikepdf.PasswordError:
            return False, "File sudah terproteksi, tidak bisa dibuka"
        except PermissionError:
            return False, "Tidak ada izin tulis ke folder output"
        except OSError as e:
            return False, f"I/O Error: {e}"
        except Exception as e:
            return False, str(e)

    def _encrypt_bulk(self, rows: list):
        folder = self.folder_var.get()
        output_folder = self.output_folder_var.get()

        total = len(rows)
        ok_count = 0
        err_count = 0
        skip_count = 0

        self.root.after(0, lambda: self.progress.configure(maximum=total, value=0))
        self.root.after(0, lambda: self._log(f"Memulai batch enkripsi: {total} file…", "info"))

        for i, row in enumerate(rows, start=1):
            if self._cancel_flag:
                self.root.after(0, lambda: self._log("⚠ Proses dibatalkan oleh pengguna.", "warn"))
                break

            file_name = row["filename"]
            password = row["password"]
            input_path = os.path.join(folder, file_name)

            # Quick validate input
            ok_pdf, err_pdf = validate_pdf(input_path)
            if not ok_pdf:
                msg = f"Skip [{i}/{total}] {file_name}: {err_pdf}"
                self.root.after(0, lambda m=msg: self._log(m, "warn"))
                self.root.after(0, lambda: self._set_status(msg[:60]))
                skip_count += 1
                self.root.after(0, lambda v=i: self.progress.configure(value=v))
                continue

            output_name = self._generate_name(file_name)
            output_path = os.path.join(output_folder, output_name)

            success, detail = self._encrypt_file(input_path, output_path, password)

            if success:
                msg = f"✓ [{i}/{total}] {detail}"
                self.root.after(0, lambda m=msg: self._log(m, "success"))
                ok_count += 1
            else:
                msg = f"✗ [{i}/{total}] {file_name}: {detail}"
                self.root.after(0, lambda m=msg: self._log(m, "error"))
                err_count += 1

            self.root.after(0, lambda v=i: self.progress.configure(value=v))
            self.root.after(0, lambda m=f"[{i}/{total}] Memproses…": self._set_status(m))

        # Summary
        def show_summary():
            self._log("─" * 40, "muted")
            self._log(f"Selesai: {ok_count} berhasil, {err_count} gagal, {skip_count} dilewati", "info")
            if err_count == 0 and skip_count == 0:
                messagebox.showinfo("Selesai", f"✓ Semua {ok_count} file berhasil dienkripsi!")
            else:
                messagebox.showwarning(
                    "Selesai dengan Masalah",
                    f"Berhasil: {ok_count}\nGagal: {err_count}\nDilewati: {skip_count}\n\nCek log untuk detail."
                )

        self.root.after(0, show_summary)

    def _encrypt_single(self, file_path: str, password: str):
        output_folder = self.output_folder_var.get()
        filename = os.path.basename(file_path)
        output_name = self._generate_name(filename)
        output_path = os.path.join(output_folder, output_name)

        self.root.after(0, lambda: self._log(f"Mengenkripsi: {filename}…", "info"))
        self.root.after(0, lambda: self.progress.configure(mode="indeterminate"))
        self.root.after(0, lambda: self.progress.start(10))

        success, detail = self._encrypt_file(file_path, output_path, password)

        self.root.after(0, lambda: self.progress.stop())
        self.root.after(0, lambda: self.progress.configure(mode="determinate", value=0))

        if success:
            self.root.after(0, lambda: self._log(f"✓ Berhasil: {detail}", "success"))
            self.root.after(0, lambda: messagebox.showinfo(
                "Berhasil", f"File berhasil dienkripsi!\n\nOutput: {detail}"
            ))
        else:
            self.root.after(0, lambda: self._log(f"✗ Gagal: {detail}", "error"))
            self.root.after(0, lambda: messagebox.showerror(
                "Gagal", f"Enkripsi gagal:\n{detail}"
            ))

    # ---- Help dialogs ----

    def _show_help(self):
        text = (
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "═══ MODE FOLDER + CSV ═══\n"
            "1. Pilih folder yang berisi file PDF\n"
            "2. Pilih file CSV (lihat menu Help → Format CSV)\n"
            "3. Pilih folder output\n"
            "4. Klik 'Mulai Enkripsi'\n\n"
            "═══ MODE SINGLE FILE ═══\n"
            "1. Pilih satu file PDF\n"
            "2. Pilih folder output\n"
            "3. Klik 'Mulai Enkripsi'\n"
            "4. Masukkan password\n\n"
            "═══ PENGATURAN ═══\n"
            "• Prefix/Suffix: mengubah nama file output\n"
            "• Owner Password: password untuk pengaturan izin\n"
            "• Permissions: batasi apa yang bisa dilakukan pengguna\n"
        )
        messagebox.showinfo("Cara Pakai", text)

    def _show_csv_help(self):
        text = (
            "Format file CSV:\n\n"
            "filename,password\n"
            "dokumen1.pdf,password123\n"
            "laporan.pdf,rahasiaBanget\n"
            "kontrak_2026.pdf,p@ssw0rd!\n\n"
            "Ketentuan:\n"
            "• Baris pertama HARUS header: filename,password\n"
            "• Nama file relatif terhadap folder yang dipilih\n"
            "• Simpan sebagai UTF-8 (Excel: Save As → CSV UTF-8)\n"
            "• Tidak ada baris kosong di tengah"
        )
        messagebox.showinfo("Format CSV", text)

    def _show_about(self):
        messagebox.showinfo(
            f"Tentang {APP_NAME}",
            f"{APP_NAME}\nVersi {APP_VERSION}\n\n{COPYRIGHT}\n\n"
            "Menggunakan pikepdf untuk enkripsi PDF 256-bit AES."
        )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("icon.ico")
    app = PDFEncryptorApp(root)
    root.mainloop()