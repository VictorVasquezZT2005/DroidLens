import os
import subprocess
import threading
import re
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Configuración global del tema
ctk.set_appearance_mode("System")  # Adopta el modo oscuro/claro de macOS automáticamente
ctk.set_default_color_theme("blue")  # Tema de acento (azul tipo macOS)

class DroidLens(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DroidLens")
        self.geometry("520x800")
        self.minsize(520, 600)
        self.resizable(True, True)

        # Rutas fijas con el path exacto que indicaste
        self.adb_dir = "/Users/vvasq/Library/Android/sdk/platform-tools"
        self.adb_path = f"{self.adb_dir}/adb"

        # Dejamos scrcpy como comando global porque macOS ya lo detecta en tu terminal
        self.scrcpy_path = "scrcpy"

        self.default_save_dir = os.path.expanduser("~/Movies")
        os.makedirs(self.default_save_dir, exist_ok=True)

        # Variables
        self.devices = []
        self.selected_device = ctk.StringVar()
        self.selected_res = ctk.StringVar()
        self.live_view_var = ctk.BooleanVar(value=True)

        # Audio Variables (Eliminada la opción del Mic de la Mac que causaba el crasheo)
        self.audio_internal = ctk.BooleanVar(value=True)
        self.audio_mic_cel = ctk.BooleanVar(value=False)

        self.device_info_text = ctk.StringVar(value="Esperando dispositivo…")
        self.status_var = ctk.StringVar(value="Listo")

        self._build_ui()
        self.refresh_devices()

    def _build_ui(self):
        # Frame principal normal sin scroll
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Título
        title = ctk.CTkLabel(self.main_frame, text="DroidLens", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(anchor="w", padx=10, pady=(10, 20))

        # --- SECCIÓN: DISPOSITIVO ---
        ctk.CTkLabel(self.main_frame, text="DISPOSITIVO", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(anchor="w", padx=10)
        dev_frame = ctk.CTkFrame(self.main_frame)
        dev_frame.pack(fill="x", padx=10, pady=(5, 15))

        dev_top_row = ctk.CTkFrame(dev_frame, fg_color="transparent")
        dev_top_row.pack(fill="x", padx=15, pady=(15, 5))

        self.device_combo = ctk.CTkComboBox(dev_top_row, variable=self.selected_device, state="readonly", command=self.on_device_selected)
        self.device_combo.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_refresh = ctk.CTkButton(dev_top_row, text="Actualizar", width=80, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), command=self.refresh_devices)
        btn_refresh.pack(side="right")

        # Banner de Info
        self.info_lbl = ctk.CTkLabel(dev_frame, textvariable=self.device_info_text, font=ctk.CTkFont(size=12))
        self.info_lbl.pack(anchor="w", padx=15, pady=(0, 15))

        # --- SECCIÓN: CONFIGURACIÓN ---
        ctk.CTkLabel(self.main_frame, text="CONFIGURACIÓN DE CAPTURA", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(anchor="w", padx=10)
        conf_frame = ctk.CTkFrame(self.main_frame)
        conf_frame.pack(fill="x", padx=10, pady=(5, 15))

        res_row = ctk.CTkFrame(conf_frame, fg_color="transparent")
        res_row.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(res_row, text="Resolución max.").pack(side="left", padx=(0, 15))
        self.res_combo = ctk.CTkComboBox(res_row, variable=self.selected_res, state="readonly")
        self.res_combo.pack(side="left", expand=True, fill="x")

        ctk.CTkSwitch(conf_frame, text="Mostrar pantalla en vivo mientras graba", variable=self.live_view_var).pack(anchor="w", padx=15, pady=(0, 15))

        # --- SECCIÓN: AUDIO ---
        ctk.CTkLabel(self.main_frame, text="AUDIO", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(anchor="w", padx=10)
        audio_frame = ctk.CTkFrame(self.main_frame)
        audio_frame.pack(fill="x", padx=10, pady=(5, 15))

        ctk.CTkSwitch(audio_frame, text="Grabar audio interno del celular", variable=self.audio_internal).pack(anchor="w", padx=15, pady=(15, 10))
        ctk.CTkSwitch(audio_frame, text="Micrófono del celular", variable=self.audio_mic_cel).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(audio_frame, text="El audio interno requiere Android 10+ y permisos ADB.", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=15, pady=(0, 10))

        # --- SECCIÓN: DESTINO ---
        ctk.CTkLabel(self.main_frame, text="DESTINO", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(anchor="w", padx=10)
        dest_frame = ctk.CTkFrame(self.main_frame)
        dest_frame.pack(fill="x", padx=10, pady=(5, 20))

        dest_row = ctk.CTkFrame(dest_frame, fg_color="transparent")
        dest_row.pack(fill="x", padx=15, pady=15)

        self.dest_label = ctk.CTkLabel(dest_row, text=self.default_save_dir, text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(weight="bold"))
        self.dest_label.pack(side="left", expand=True, anchor="w")

        btn_dest = ctk.CTkButton(dest_row, text="Cambiar", width=80, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), command=self._change_dest)
        btn_dest.pack(side="right")

        # --- BOTÓN PRINCIPAL Y ESTADO ---
        bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom", padx=10, pady=(10, 20))

        self.btn_record = ctk.CTkButton(bottom_frame, text="Iniciar Grabación", font=ctk.CTkFont(size=15, weight="bold"), height=45, command=self.start_recording_flow)
        self.btn_record.pack(fill="x", pady=(0, 5))

        self.status_label = ctk.CTkLabel(bottom_frame, textvariable=self.status_var, font=ctk.CTkFont(size=11), text_color="gray")
        self.status_label.pack(anchor="center")

    # ── ADB y Lógica de Scrcpy ──
    def run_adb(self, args):
        env = os.environ.copy()
        env["PATH"] = f"{self.adb_dir}:{env.get('PATH','')}"
        try:
            r = subprocess.run([self.adb_path] + args, capture_output=True, text=True, env=env, timeout=5)
            return r.stdout.strip()
        except Exception:
            return ""

    def get_adb_devices(self):
        out = self.run_adb(["devices"])
        if not out: return []
        return [l.split('\t')[0] for l in out.split('\n')[1:] if l.strip() and "device" in l]

    def refresh_devices(self):
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
            self.status_var.set("Sin dispositivos")
            self.info_lbl.configure(text_color=("red", "#FF6961"))

    def _get_orientation(self, serial, w, h):
        disp = self.run_adb(["-s", serial, "shell", "dumpsys", "display"])
        m = re.search(r'mCurrentOrientation=(\d)', disp)
        if m: return "Horizontal" if m.group(1) in ("1","3") else "Vertical"
        win = self.run_adb(["-s", serial, "shell", "dumpsys", "window"])
        for pat in (r'mLastOrientation=(\d)', r'mRotation=(\d)'):
            m = re.search(pat, win)
            if m: return "Horizontal" if m.group(1) in ("1","3") else "Vertical"
        return "Horizontal" if w > h else "Vertical"

    def on_device_selected(self, event=None):
        serial = self.selected_device.get()
        if not serial: return
        self.device_info_text.set("Obteniendo información…")
        self.info_lbl.configure(text_color=("green", "#32D74B"))
        self.update()

        wm = self.run_adb(["-s", serial, "shell", "wm", "size"])
        w, h = 1080, 1920
        for pat in (r'Override size:\s*(\d+)x(\d+)', r'Physical size:\s*(\d+)x(\d+)', r'size:\s*(\d+)x(\d+)'):
            m = re.search(pat, wm)
            if m:
                w, h = int(m.group(1)), int(m.group(2)); break

        ori = self._get_orientation(serial, w, h)
        nw, nh = (max(w,h), min(w,h)) if ori == "Horizontal" else (min(w,h), max(w,h))
        self.device_info_text.set(f"Resolución nativa: {nw}x{nh}  ·  Modo: {ori}")

        top = max(nw, nh)
        opts = [f"{top} (Original)"]
        for val, name in [(1920,"FHD"),(1280,"HD"),(1024,"Medio"),(800,"Bajo")]:
            if top > val: opts.append(f"{val} ({name})")

        self.res_combo.configure(values=opts)
        self.res_combo.set(opts[0])

    def _change_dest(self):
        p = filedialog.askdirectory(initialdir=self.default_save_dir, title="Seleccionar carpeta de destino")
        if p:
            self.default_save_dir = p
            self.dest_label.configure(text=p)

    def _build_scrcpy_cmd(self, serial, max_size, show_live, out_path):
        cmd = [self.scrcpy_path, "-s", serial, "-m", max_size, "--record", out_path]

        if not show_live:
            cmd.append("--no-display")

        audio_internal = self.audio_internal.get()
        audio_mic_cel = self.audio_mic_cel.get()

        if not audio_internal and not audio_mic_cel:
            cmd.append("--no-audio")
        else:
            if audio_internal:
                cmd.append("--audio-source=output")
            else:
                cmd.append("--audio-source=mic")

        return cmd

    def start_recording_flow(self):
        if not self.selected_device.get():
            messagebox.showwarning("Atención", "Selecciona un dispositivo primero.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            initialdir=self.default_save_dir,
            initialfile=f"Captura_{ts}.mp4",
            title="Guardar video",
            defaultextension=".mp4",
            filetypes=[("Video MP4", "*.mp4")]
        )
        if not path: return

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
            env = os.environ.copy()
            # Aseguramos que la ruta que diste se incluya en el PATH para que el sistema encuentre las herramientas
            env["PATH"] = f"{self.adb_dir}:{env.get('PATH','')}"
            cmd = self._build_scrcpy_cmd(serial, max_size, show_live, out_path)

            proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.after(0, lambda: self.status_var.set("Grabando… cierra la ventana de scrcpy para detener"))

            out, err = proc.communicate()

            if proc.returncode == 0:
                msg = f"Guardado: {os.path.basename(out_path)}"
            else:
                # Si scrcpy falla por cualquier otra razón, te mostrará el error real abajo
                error_line = err.strip().split('\n')[-1] if err else "Error desconocido"
                msg = f"Error: {error_line[:60]}"

            self.after(0, lambda m=msg: self.status_var.set(m))

        except Exception as e:
            error_text = str(e)[:60]
            self.after(0, lambda err=error_text: self.status_var.set(f"Fallo sistema: {err}"))
        finally:
            self.after(0, self._re_enable_btn)

    def _re_enable_btn(self):
        self.btn_record.configure(state="normal", text="Iniciar Grabación", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

if __name__ == "__main__":
    app = DroidLens()
    app.mainloop()
