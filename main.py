import os
import shutil
import subprocess
import threading
import re
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DroidLens(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DroidLens")
        self.geometry("560x1")
        self.resizable(True, True)

        # Detectar herramientas automáticamente
        self.adb_path       = shutil.which("adb")
        self.scrcpy_path    = shutil.which("scrcpy")
        self.scrcpy_version = self._detect_scrcpy_version()   # tuple (major, minor, patch) o None
        self.audio_supported = (
            self.scrcpy_version is not None and self.scrcpy_version >= (2, 0, 0)
        )

        self.default_save_dir = os.path.expanduser("~/Movies")
        os.makedirs(self.default_save_dir, exist_ok=True)

        # Variables
        self.devices          = []
        self.selected_device  = ctk.StringVar()
        self.selected_res     = ctk.StringVar()
        self.live_view_var    = ctk.BooleanVar(value=True)
        self.audio_internal   = ctk.BooleanVar(value=True)
        self.audio_mic_cel    = ctk.BooleanVar(value=False)
        self.device_info_text = ctk.StringVar(value="Esperando dispositivo…")
        self.status_var       = ctk.StringVar(value="Listo")

        self._build_ui()
        self._check_tools()
        self.refresh_devices()

        self.update_idletasks()
        self.geometry(f"560x{self.winfo_reqheight()}")
        self.minsize(520, self.winfo_reqheight())

    # ─────────────────────────── Versión scrcpy ───────────────────────────
    def _detect_scrcpy_version(self):
        """Devuelve (major, minor, patch) o None si no se puede detectar."""
        if not self.scrcpy_path:
            return None
        try:
            r = subprocess.run(
                [self.scrcpy_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            # Captura "1.25", "2.3", "2.3.1", etc.
            m = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', r.stdout + r.stderr)
            if m:
                major = int(m.group(1))
                minor = int(m.group(2))
                patch = int(m.group(3)) if m.group(3) else 0
                return (major, minor, patch)
        except Exception:
            pass
        return None

    # ─────────────────────────── Verificación ───────────────────────────
    def _check_tools(self):
        missing = []
        if not self.adb_path:
            missing.append("adb")
        if not self.scrcpy_path:
            missing.append("scrcpy")

        if missing:
            messagebox.showerror(
                "Herramientas no encontradas",
                f"No se encontraron en el sistema: {', '.join(missing)}\n\n"
                "Instálalos y asegúrate de que estén en el PATH.\n"
                "• adb: parte del Android SDK platform-tools\n"
                "• scrcpy: brew install scrcpy"
            )
            if "adb" in missing:
                self.status_var.set("Error: adb no encontrado")
            elif "scrcpy" in missing:
                self.status_var.set("Error: scrcpy no encontrado")
            return

        # Mostrar versión detectada
        if self.scrcpy_version:
            major, minor, patch = self.scrcpy_version
            ver_str = f"v{major}.{minor}.{patch}" if patch else f"v{major}.{minor}"
        else:
            ver_str = "version desconocida"

        if self.audio_supported:
            self.status_var.set(f"scrcpy {ver_str} — audio disponible")
        else:
            self.status_var.set(f"scrcpy {ver_str} — audio no disponible (requiere v2.0+)")

        self._apply_audio_state()

    # ─────────────────────────── UI ───────────────────────────
    def _build_ui(self):
        PAD  = 10
        IPAD = 10
        GAP  = 6

        root = self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # ── Título ──
        ctk.CTkLabel(
            root, text="DroidLens",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=2, pady=(2, 8))

        # ── Dispositivo ──
        self._section_label(root, "DISPOSITIVO")
        dev_card = ctk.CTkFrame(root)
        dev_card.pack(fill="x", pady=(2, GAP))

        dev_row = ctk.CTkFrame(dev_card, fg_color="transparent")
        dev_row.pack(fill="x", padx=IPAD, pady=(IPAD, 4))

        self.device_combo = ctk.CTkComboBox(
            dev_row, variable=self.selected_device,
            state="readonly", command=self.on_device_selected
        )
        self.device_combo.pack(side="left", expand=True, fill="x", padx=(0, 8))

        ctk.CTkButton(
            dev_row, text="Actualizar", width=90,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self.refresh_devices
        ).pack(side="right")

        self.info_lbl = ctk.CTkLabel(
            dev_card, textvariable=self.device_info_text,
            font=ctk.CTkFont(size=11)
        )
        self.info_lbl.pack(anchor="w", padx=IPAD, pady=(0, IPAD))

        # ── Captura + Audio ──
        mid_row = ctk.CTkFrame(root, fg_color="transparent")
        mid_row.pack(fill="x", pady=(0, GAP))
        mid_row.columnconfigure(0, weight=1)
        mid_row.columnconfigure(1, weight=1)

        # — Captura —
        left = ctk.CTkFrame(mid_row)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self._section_label(left, "CAPTURA", pady_top=IPAD)

        res_row = ctk.CTkFrame(left, fg_color="transparent")
        res_row.pack(fill="x", padx=IPAD, pady=(4, 6))
        ctk.CTkLabel(res_row, text="Resolución máx.", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        self.res_combo = ctk.CTkComboBox(res_row, variable=self.selected_res, state="readonly", width=130)
        self.res_combo.pack(side="right")

        ctk.CTkSwitch(
            left, text="Pantalla en vivo",
            variable=self.live_view_var,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=IPAD, pady=(0, IPAD))

        # — Audio —
        right = ctk.CTkFrame(mid_row)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self._section_label(right, "AUDIO", pady_top=IPAD)

        self.sw_audio_internal = ctk.CTkSwitch(
            right, text="Audio interno",
            variable=self.audio_internal,
            font=ctk.CTkFont(size=12)
        )
        self.sw_audio_internal.pack(anchor="w", padx=IPAD, pady=(4, 6))

        self.sw_audio_mic = ctk.CTkSwitch(
            right, text="Mic del celular",
            variable=self.audio_mic_cel,
            font=ctk.CTkFont(size=12)
        )
        self.sw_audio_mic.pack(anchor="w", padx=IPAD, pady=(0, 6))

        self.audio_note_lbl = ctk.CTkLabel(
            right, text="Requiere Android 10+",
            font=ctk.CTkFont(size=10), text_color="gray"
        )
        self.audio_note_lbl.pack(anchor="w", padx=IPAD, pady=(0, IPAD))

        # ── Destino ──
        self._section_label(root, "DESTINO")
        dest_card = ctk.CTkFrame(root)
        dest_card.pack(fill="x", pady=(2, GAP))

        dest_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=IPAD, pady=IPAD)

        self.dest_label = ctk.CTkLabel(
            dest_row, text=self.default_save_dir,
            text_color=("#007AFF", "#0A84FF"),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.dest_label.pack(side="left", expand=True, fill="x")

        ctk.CTkButton(
            dest_row, text="Cambiar", width=80,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            command=self._change_dest
        ).pack(side="right")

        # ── Botón + estado ──
        bottom = ctk.CTkFrame(root, fg_color="transparent")
        bottom.pack(fill="x", pady=(4, 0))

        self.btn_record = ctk.CTkButton(
            bottom, text="Iniciar Grabación",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42, command=self.start_recording_flow
        )
        self.btn_record.pack(fill="x", pady=(0, 4))

        self.status_label = ctk.CTkLabel(
            bottom, textvariable=self.status_var,
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.status_label.pack(anchor="center")

    def _section_label(self, parent, text, pady_top=0):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(pady_top, 0))

    def _apply_audio_state(self):
        """Habilita o deshabilita los controles de audio según la versión de scrcpy."""
        if self.audio_supported:
            self.sw_audio_internal.configure(state="normal")
            self.sw_audio_mic.configure(state="normal")
            self.audio_note_lbl.configure(text="Requiere Android 10+", text_color="gray")
        else:
            # Versión antigua: apagar switches y bloquearlos
            self.audio_internal.set(False)
            self.audio_mic_cel.set(False)
            self.sw_audio_internal.configure(state="disabled")
            self.sw_audio_mic.configure(state="disabled")
            self.audio_note_lbl.configure(
                text="No soportado (scrcpy < v2.0)",
                text_color=("orange", "#FF9F0A")
            )

    # ─────────────────────────── ADB ───────────────────────────
    def run_adb(self, args):
        if not self.adb_path:
            return ""
        try:
            r = subprocess.run(
                [self.adb_path] + args,
                capture_output=True, text=True, timeout=5
            )
            return r.stdout.strip()
        except Exception:
            return ""

    def get_adb_devices(self):
        out = self.run_adb(["devices"])
        if not out:
            return []
        return [
            l.split('\t')[0]
            for l in out.split('\n')[1:]
            if l.strip() and "\tdevice" in l
        ]

    def refresh_devices(self):
        if not self.adb_path:
            self.status_var.set("Error: adb no encontrado en el sistema")
            return

        prev = self.selected_device.get()
        self.devices = self.get_adb_devices()

        if self.devices:
            self.device_combo.configure(values=self.devices)
            idx = self.devices.index(prev) if prev in self.devices else 0
            self.device_combo.set(self.devices[idx])
            self.on_device_selected()
            self.status_var.set("Dispositivos actualizados")
        else:
            self.device_combo.configure(values=[])
            self.selected_device.set("")
            self.device_info_text.set("No se detectaron dispositivos")
            self.res_combo.configure(values=[])
            self.selected_res.set("")
            self.status_var.set("Sin dispositivos — conecta un dispositivo y pulsa Actualizar")
            self.info_lbl.configure(text_color=("red", "#FF6961"))

    def _get_orientation(self, serial, w, h):
        disp = self.run_adb(["-s", serial, "shell", "dumpsys", "display"])
        m = re.search(r'mCurrentOrientation=(\d)', disp)
        if m:
            return "Horizontal" if m.group(1) in ("1", "3") else "Vertical"
        win = self.run_adb(["-s", serial, "shell", "dumpsys", "window"])
        for pat in (r'mLastOrientation=(\d)', r'mRotation=(\d)'):
            m = re.search(pat, win)
            if m:
                return "Horizontal" if m.group(1) in ("1", "3") else "Vertical"
        return "Horizontal" if w > h else "Vertical"

    def on_device_selected(self, event=None):
        serial = self.selected_device.get()
        if not serial:
            return
        self.device_info_text.set("Obteniendo información…")
        self.info_lbl.configure(text_color=("green", "#32D74B"))
        self.update()

        wm = self.run_adb(["-s", serial, "shell", "wm", "size"])
        w, h = 1080, 1920
        for pat in (
            r'Override size:\s*(\d+)x(\d+)',
            r'Physical size:\s*(\d+)x(\d+)',
            r'size:\s*(\d+)x(\d+)'
        ):
            m = re.search(pat, wm)
            if m:
                w, h = int(m.group(1)), int(m.group(2))
                break

        ori = self._get_orientation(serial, w, h)
        nw = max(w, h) if ori == "Horizontal" else min(w, h)
        nh = min(w, h) if ori == "Horizontal" else max(w, h)
        self.device_info_text.set(f"Resolución nativa: {nw}×{nh}  ·  Modo: {ori}")

        top = max(nw, nh)
        opts = [f"{top} (Original)"]
        for val, name in [(1920, "FHD"), (1280, "HD"), (1024, "Medio"), (800, "Bajo")]:
            if top > val:
                opts.append(f"{val} ({name})")

        self.res_combo.configure(values=opts)
        self.res_combo.set(opts[0])

    def _change_dest(self):
        p = filedialog.askdirectory(
            initialdir=self.default_save_dir,
            title="Seleccionar carpeta de destino"
        )
        if p:
            self.default_save_dir = p
            self.dest_label.configure(text=p)

    # ─────────────────────────── scrcpy ───────────────────────────
    def _build_scrcpy_cmd(self, serial, max_size, show_live, out_path):
        cmd = [self.scrcpy_path, "-s", serial, "--max-size", max_size, "--record", out_path]
        if not show_live:
            cmd.append("--no-display")

        # Solo agregar flags de audio si la versión lo soporta
        if self.audio_supported:
            if self.audio_internal.get():
                cmd.append("--audio-source=output")
            elif self.audio_mic_cel.get():
                cmd.append("--audio-source=mic")
            else:
                cmd.append("--no-audio")
        # Si no soporta audio, no se agrega nada — scrcpy antiguo lo ignora solo

        return cmd

    def start_recording_flow(self):
        if not self.scrcpy_path:
            messagebox.showerror("Error", "scrcpy no está instalado.\nEjecuta: brew install scrcpy")
            return

        if not self.selected_device.get():
            messagebox.showwarning("Atención", "Selecciona un dispositivo primero.")
            return

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            initialdir=self.default_save_dir,
            initialfile=f"Captura_{ts}.mp4",
            title="Guardar video",
            defaultextension=".mp4",
            filetypes=[("Video MP4", "*.mp4")]
        )
        if not path:
            return

        self.btn_record.configure(state="disabled", text="Grabando...", fg_color="gray")
        self.status_var.set("Conectando con scrcpy…")
        max_size = self.selected_res.get().split()[0]

        threading.Thread(
            target=self.run_scrcpy,
            args=(self.selected_device.get(), max_size, self.live_view_var.get(), path),
            daemon=True
        ).start()

    def run_scrcpy(self, serial, max_size, show_live, out_path):
        try:
            cmd  = self._build_scrcpy_cmd(serial, max_size, show_live, out_path)
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.after(0, lambda: self.status_var.set("Grabando… cierra scrcpy para detener"))
            out, err = proc.communicate()

            if proc.returncode == 0:
                msg = f"Guardado: {os.path.basename(out_path)}"
            else:
                error_line = err.strip().split('\n')[-1] if err else "Error desconocido"
                msg = f"Error: {error_line[:80]}"

            self.after(0, lambda m=msg: self.status_var.set(m))

        except Exception as e:
            err_txt = str(e)[:80]
            self.after(0, lambda t=err_txt: self.status_var.set(f"Fallo: {t}"))
        finally:
            self.after(0, self._re_enable_btn)

    def _re_enable_btn(self):
        self.btn_record.configure(
            state="normal",
            text="Iniciar Grabación",
            fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )


if __name__ == "__main__":
    app = DroidLens()
    app.mainloop()