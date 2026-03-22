import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
import shlex

# ==============================================================================
# DATA
# ==============================================================================

HASH_TYPES = [
    ("MD5",                "0"),
    ("SHA-1",              "100"),
    ("SHA-256",            "1400"),
    ("SHA-512",            "1700"),
    ("NTLM",               "1000"),
    ("bcrypt",             "3200"),
    ("WPA-PBKDF2",         "22000"),
    ("MD5 (APR)",          "1600"),
    ("sha512crypt ($6$)",  "1800"),
    ("sha256crypt ($5$)",  "7400"),
]

ATTACK_MODES = [
    ("Dictionary",          "0"),
    ("Combination",         "1"),
    ("Brute-force / Mask",  "3"),
    ("Hybrid Dict+Mask",    "6"),
    ("Hybrid Mask+Dict",    "7"),
]

WORKLOAD = [
    ("1  Low",       "1"),
    ("2  Default",   "2"),
    ("3  High",      "3"),
    ("4  Nightmare", "4"),
]

MASK_TOKENS = [
    ("?l", "lowercase  a-z"),
    ("?u", "uppercase  A-Z"),
    ("?d", "digits  0-9"),
    ("?s", "special  !@#..."),
    ("?a", "all printable"),
]

C = {
    "bg":      "#0a0a0a",
    "panel":   "#111111",
    "border":  "#222222",
    "accent":  "#e8420a",
    "text":    "#d0d0d0",
    "dim":     "#555555",
    "green":   "#39ff14",
    "yellow":  "#ffd700",
    "red":     "#ff4500",
    "cyan":    "#00e5ff",
}

# ==============================================================================
# APP
# ==============================================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("cracksmoker")
        self.geometry("920x720")
        self.minsize(800, 600)
        self.configure(bg=C["bg"])

        self.process = None
        self.stop_event = threading.Event()
        self.hashcat_path = shutil.which("hashcat")

        self._ui()
        self._update_cmd()

    # --------------------------------------------------------------------------
    # UI
    # --------------------------------------------------------------------------

    def _ui(self):
        # Header
        hdr = tk.Frame(self, bg=C["bg"])
        hdr.pack(fill=tk.X, padx=16, pady=(10, 0))
        tk.Label(hdr, text="CRACKSMOKER", font=("Courier", 20, "bold"),
                 bg=C["bg"], fg=C["accent"]).pack(side=tk.LEFT)
        status_text = f"● {self.hashcat_path}" if self.hashcat_path else "⚠  hashcat not in PATH"
        status_color = C["green"] if self.hashcat_path else C["yellow"]
        tk.Label(hdr, text=status_text, font=("Courier", 9),
                 bg=C["bg"], fg=status_color).pack(side=tk.RIGHT, pady=6)

        tk.Frame(self, bg=C["border"], height=1).pack(fill=tk.X, padx=16, pady=6)

        # Body: left config + right log
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        left = tk.Frame(body, bg=C["bg"], width=420)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 8))
        left.pack_propagate(False)

        right = tk.Frame(body, bg=C["bg"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, p):
        self._lbl(p, "TARGET HASH")
        self.hash_var = tk.StringVar()
        self.hash_var.trace_add("write", lambda *_: self._update_cmd())
        e = self._entry(p, textvariable=self.hash_var)
        e.pack(fill=tk.X, pady=(0, 6))

        self._lbl(p, "HASH TYPE  -m")
        self.htype_var = tk.StringVar(value="0")
        combo = ttk.Combobox(p, textvariable=self.htype_var, state="readonly",
                              values=[f"{n}  [{v}]" for n, v in HASH_TYPES])
        combo.current(0)
        combo.pack(fill=tk.X, pady=(0, 6))
        combo.bind("<<ComboboxSelected>>", lambda e: self._update_cmd())
        self._style_combo()

        self._lbl(p, "ATTACK MODE  -a")
        self.mode_var = tk.StringVar(value="0")
        for label, val in ATTACK_MODES:
            tk.Radiobutton(p, text=label, variable=self.mode_var, value=val,
                           bg=C["bg"], fg=C["text"], selectcolor=C["panel"],
                           activebackground=C["bg"], activeforeground=C["accent"],
                           font=("Courier", 10), command=self._update_cmd).pack(anchor=tk.W)

        self._lbl(p, "WORDLIST  (dict / hybrid modes)")
        wf = tk.Frame(p, bg=C["bg"])
        wf.pack(fill=tk.X, pady=(0, 6))
        self.wl_var = tk.StringVar()
        self.wl_var.trace_add("write", lambda *_: self._update_cmd())
        self._entry(wf, textvariable=self.wl_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(wf, "…", lambda: self._pick_file(self.wl_var)).pack(side=tk.LEFT, padx=(3, 0))

        self._lbl(p, "MASK  (brute-force / hybrid modes)")
        mf = tk.Frame(p, bg=C["bg"])
        mf.pack(fill=tk.X, pady=(0, 2))
        self.mask_var = tk.StringVar()
        self.mask_var.trace_add("write", lambda *_: self._update_cmd())
        self._entry(mf, textvariable=self.mask_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(mf, "✕", lambda: self.mask_var.set(""), fg=C["dim"]).pack(side=tk.LEFT, padx=(3, 0))

        tok_row = tk.Frame(p, bg=C["bg"])
        tok_row.pack(fill=tk.X, pady=(0, 6))
        for tok, tip in MASK_TOKENS:
            b = tk.Button(tok_row, text=tok, font=("Courier", 9, "bold"),
                          bg=C["panel"], fg=C["cyan"],
                          activebackground=C["accent"], activeforeground="white",
                          relief=tk.FLAT, padx=6, pady=3, cursor="hand2",
                          command=lambda t=tok: self.mask_var.set(self.mask_var.get() + t))
            b.pack(side=tk.LEFT, padx=2)
            self._tip(b, tip)

        # Min/max len
        lf = tk.Frame(p, bg=C["bg"])
        lf.pack(fill=tk.X, pady=(0, 6))
        tk.Label(lf, text="min:", font=("Courier", 9), bg=C["bg"], fg=C["dim"]).pack(side=tk.LEFT)
        self.min_var = tk.StringVar(value="1")
        self.min_var.trace_add("write", lambda *_: self._update_cmd())
        tk.Spinbox(lf, from_=1, to=32, width=4, textvariable=self.min_var,
                   bg=C["panel"], fg=C["text"], relief=tk.FLAT,
                   font=("Courier", 9), insertbackground=C["text"]).pack(side=tk.LEFT, padx=(3, 10))
        tk.Label(lf, text="max:", font=("Courier", 9), bg=C["bg"], fg=C["dim"]).pack(side=tk.LEFT)
        self.max_var = tk.StringVar(value="8")
        self.max_var.trace_add("write", lambda *_: self._update_cmd())
        tk.Spinbox(lf, from_=1, to=32, width=4, textvariable=self.max_var,
                   bg=C["panel"], fg=C["text"], relief=tk.FLAT,
                   font=("Courier", 9), insertbackground=C["text"]).pack(side=tk.LEFT, padx=(3, 0))

        self._lbl(p, "RULES FILE  -r  [optional]")
        rf = tk.Frame(p, bg=C["bg"])
        rf.pack(fill=tk.X, pady=(0, 6))
        self.rules_var = tk.StringVar()
        self.rules_var.trace_add("write", lambda *_: self._update_cmd())
        self._entry(rf, textvariable=self.rules_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(rf, "…", lambda: self._pick_file(self.rules_var)).pack(side=tk.LEFT, padx=(3, 0))

        self._lbl(p, "OUTPUT FILE  -o  [optional]")
        of = tk.Frame(p, bg=C["bg"])
        of.pack(fill=tk.X, pady=(0, 6))
        self.out_var = tk.StringVar()
        self.out_var.trace_add("write", lambda *_: self._update_cmd())
        self._entry(of, textvariable=self.out_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(of, "…", lambda: self._pick_save(self.out_var)).pack(side=tk.LEFT, padx=(3, 0))

        self._lbl(p, "WORKLOAD  -w")
        wl_row = tk.Frame(p, bg=C["bg"])
        wl_row.pack(fill=tk.X, pady=(0, 6))
        self.workload_var = tk.StringVar(value="2")
        self.workload_var.trace_add("write", lambda *_: self._update_cmd())
        for label, val in WORKLOAD:
            tk.Radiobutton(wl_row, text=label, variable=self.workload_var, value=val,
                           bg=C["bg"], fg=C["text"], selectcolor=C["panel"],
                           activebackground=C["bg"], activeforeground=C["accent"],
                           font=("Courier", 9), command=self._update_cmd).pack(side=tk.LEFT, padx=4)

        self._lbl(p, "EXTRA FLAGS  [optional]")
        self.extra_var = tk.StringVar()
        self.extra_var.trace_add("write", lambda *_: self._update_cmd())
        self._entry(p, textvariable=self.extra_var).pack(fill=tk.X)

    def _build_right(self, p):
        # Command preview box
        cmd_box = tk.Frame(p, bg=C["panel"], pady=6, padx=8)
        cmd_box.pack(fill=tk.X, pady=(0, 6))
        tk.Label(cmd_box, text="GENERATED COMMAND", font=("Courier", 8, "bold"),
                 bg=C["panel"], fg=C["dim"]).pack(anchor=tk.W)
        self.cmd_label = tk.Label(cmd_box, text="", font=("Courier", 10),
                                   bg=C["panel"], fg=C["cyan"],
                                   anchor=tk.W, wraplength=440, justify=tk.LEFT)
        self.cmd_label.pack(fill=tk.X)

        # Buttons
        btn_row = tk.Frame(p, bg=C["bg"])
        btn_row.pack(fill=tk.X, pady=(0, 6))

        self.run_btn = tk.Button(btn_row, text="▶  RUN",
                                  font=("Courier", 12, "bold"),
                                  bg=C["accent"], fg="white",
                                  activebackground="#c73508", activeforeground="white",
                                  relief=tk.FLAT, padx=20, pady=7,
                                  cursor="hand2", command=self.run)
        self.run_btn.pack(side=tk.LEFT)

        self.stop_btn = tk.Button(btn_row, text="■  STOP",
                                   font=("Courier", 12, "bold"),
                                   bg=C["border"], fg=C["dim"],
                                   relief=tk.FLAT, padx=20, pady=7,
                                   cursor="hand2", state=tk.DISABLED,
                                   command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.status_lbl = tk.Label(btn_row, text="idle",
                                    font=("Courier", 10), bg=C["bg"], fg=C["dim"])
        self.status_lbl.pack(side=tk.LEFT, padx=12)

        # Log
        log_wrap = tk.Frame(p, bg=C["panel"])
        log_wrap.pack(fill=tk.BOTH, expand=True)

        self.log_txt = tk.Text(log_wrap, bg=C["panel"], fg=C["text"],
                                font=("Courier", 9), state=tk.DISABLED,
                                relief=tk.FLAT, padx=8, pady=6,
                                insertbackground=C["text"])
        sb = tk.Scrollbar(log_wrap, command=self.log_txt.yview, bg=C["border"], troughcolor=C["bg"])
        self.log_txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_txt.pack(fill=tk.BOTH, expand=True)

        for tag, color in [("g", C["green"]), ("r", C["red"]),
                            ("y", C["yellow"]), ("c", C["cyan"]), ("d", C["dim"])]:
            self.log_txt.tag_config(tag, foreground=color)

    # --------------------------------------------------------------------------
    # WIDGET HELPERS
    # --------------------------------------------------------------------------

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, font=("Courier", 8, "bold"),
                 bg=C["bg"], fg=C["dim"]).pack(anchor=tk.W, pady=(8, 1))

    def _entry(self, parent, textvariable=None, **kw):
        return tk.Entry(parent, textvariable=textvariable,
                        font=("Courier", 10), bg=C["panel"], fg=C["text"],
                        insertbackground=C["text"], relief=tk.FLAT,
                        highlightthickness=1, highlightbackground=C["border"],
                        highlightcolor=C["accent"], **kw)

    def _btn(self, parent, text, cmd, fg=None):
        return tk.Button(parent, text=text, font=("Courier", 9),
                         bg=C["panel"], fg=fg or C["text"],
                         activebackground=C["border"], activeforeground=C["accent"],
                         relief=tk.FLAT, padx=6, pady=2,
                         cursor="hand2", command=cmd)

    def _tip(self, widget, text):
        tip = [None]
        def show(e):
            tip[0] = tk.Toplevel(self)
            tip[0].wm_overrideredirect(True)
            tip[0].wm_geometry(f"+{e.x_root+12}+{e.y_root+22}")
            tk.Label(tip[0], text=text, font=("Courier", 9),
                     bg="#1a1a1a", fg=C["cyan"], padx=6, pady=3).pack()
        def hide(e):
            if tip[0]:
                tip[0].destroy()
                tip[0] = None
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _style_combo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                         fieldbackground=C["panel"], background=C["panel"],
                         foreground=C["text"], selectbackground=C["accent"],
                         selectforeground="white", font=("Courier", 10))

    def _pick_file(self, var):
        p = filedialog.askopenfilename(filetypes=(("All", "*.*"),))
        if p:
            var.set(p)

    def _pick_save(self, var):
        p = filedialog.asksaveasfilename(defaultextension=".txt")
        if p:
            var.set(p)

    # --------------------------------------------------------------------------
    # COMMAND BUILDER
    # --------------------------------------------------------------------------

    def _htype_val(self):
        sel = self.htype_var.get()
        try:
            return sel.split("[")[1].rstrip("]")
        except Exception:
            return "0"

    def _build_cmd(self):
        hc   = self.hashcat_path or "hashcat"
        mode = self.mode_var.get()
        m    = self._htype_val()
        w    = self.workload_var.get()
        tgt  = self.hash_var.get().strip()
        wl   = self.wl_var.get().strip()
        mask = self.mask_var.get().strip()
        rules= self.rules_var.get().strip()
        out  = self.out_var.get().strip()
        extra= self.extra_var.get().strip()

        cmd = [hc, "-m", m, "-a", mode, "-w", w]

        if out:
            cmd += ["-o", out]
        if rules:
            cmd += ["-r", rules]

        # Length increment flags for brute mode
        if mode == "3":
            try:
                mn = int(self.min_var.get())
                mx = int(self.max_var.get())
                cmd += ["--increment", "--increment-min", str(mn), "--increment-max", str(mx)]
            except ValueError:
                pass

        if extra:
            try:
                cmd += shlex.split(extra)
            except ValueError:
                cmd += extra.split()

        # Positional args (order matters for hashcat)
        if tgt:
            cmd.append(tgt)

        if mode == "0":               # dictionary
            if wl:  cmd.append(wl)
        elif mode == "1":             # combination — needs two wordlists
            if wl:
                cmd.append(wl)
                cmd.append(wl)
        elif mode == "3":             # brute/mask
            cmd.append(mask or "?a?a?a?a?a?a?a?a")
        elif mode == "6":             # hybrid dict + mask
            if wl:  cmd.append(wl)
            cmd.append(mask or "?a?a?a?a")
        elif mode == "7":             # hybrid mask + dict
            cmd.append(mask or "?a?a?a?a")
            if wl:  cmd.append(wl)

        return cmd

    def _update_cmd(self):
        cmd = self._build_cmd()
        self.cmd_label.config(text=" ".join(cmd))

    # --------------------------------------------------------------------------
    # RUN / STOP
    # --------------------------------------------------------------------------

    def run(self):
        if not self.hashcat_path:
            messagebox.showerror("hashcat not found",
                                  "hashcat is not installed or not in your PATH.\n\n"
                                  "Get it at https://hashcat.net")
            return
        if not self.hash_var.get().strip():
            messagebox.showerror("Error", "Target hash is empty.")
            return

        self.stop_event.clear()
        self._log_clear()
        self._set_state(running=True)

        cmd = self._build_cmd()
        self._log(f"$ {' '.join(cmd)}\n\n", "d")
        threading.Thread(target=self._worker, args=(cmd,), daemon=True).start()

    def _worker(self, cmd):
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for line in self.process.stdout:
                if self.stop_event.is_set():
                    break
                self._classify_log(line)
            self.process.wait()
            rc = self.process.returncode

            if self.stop_event.is_set():
                self._log("\n■  stopped\n", "y")
            elif rc == 0:
                self._log("\n✓  finished\n", "g")
            else:
                self._log(f"\n✗  exit {rc}\n", "r")
        except Exception as ex:
            self._log(f"\n[error] {ex}\n", "r")
        finally:
            self.after(0, lambda: self._set_state(running=False))

    def _classify_log(self, line):
        l = line.lower()
        if any(k in l for k in ("cracked", "found", "status.........: cracked")):
            tag = "g"
        elif any(k in l for k in ("error", "failed", "warning")):
            tag = "r"
        elif any(k in l for k in ("speed", "progress", "status", "time")):
            tag = "c"
        else:
            tag = None
        self._log(line, tag)

    def stop(self):
        self.stop_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.stop_btn.config(state=tk.DISABLED)

    def _set_state(self, running):
        if running:
            self.run_btn.config(state=tk.DISABLED, bg=C["border"], fg=C["dim"])
            self.stop_btn.config(state=tk.NORMAL, bg="#8b1a00", fg="white")
            self.status_lbl.config(text="running", fg=C["green"])
        else:
            self.run_btn.config(state=tk.NORMAL, bg=C["accent"], fg="white")
            self.stop_btn.config(state=tk.DISABLED, bg=C["border"], fg=C["dim"])
            self.status_lbl.config(text="idle", fg=C["dim"])

    def _log(self, text, tag=None):
        def _w():
            self.log_txt.config(state=tk.NORMAL)
            self.log_txt.insert(tk.END, text, tag or "")
            self.log_txt.config(state=tk.DISABLED)
            self.log_txt.see(tk.END)
        self.after(0, _w)

    def _log_clear(self):
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.delete(1.0, tk.END)
        self.log_txt.config(state=tk.DISABLED)


if __name__ == "__main__":
    App().mainloop()
