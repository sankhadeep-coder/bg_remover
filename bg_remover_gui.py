"""
BG Eraser Pro — Desktop GUI
Double-click to run. Auto-installs dependencies on first launch.
"""

import sys, os, subprocess, threading

# ── auto-install dependencies ──────────────────────────────────────────────────
REQUIRED = ["rembg[cpu]", "Pillow", "opencv-python-headless"]

def install_deps():
    for pkg in REQUIRED:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "--break-system-packages", pkg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

try:
    from rembg import remove, new_session
    from PIL import Image, ImageTk
    import cv2, numpy as np
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk(); root.withdraw()
    messagebox.showinfo("BG Eraser Pro", "Installing required packages…\nThis only happens once. Please wait.")
    root.destroy()
    install_deps()
    from rembg import remove, new_session
    from PIL import Image, ImageTk
    import cv2, numpy as np

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import io

# ── constants ──────────────────────────────────────────────────────────────────
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif", ".avif", ".ico"}

MODELS = {
    "isnet-general-use": "Best Quality (Recommended)",
    "u2net_human_seg":   "Portraits & People",
    "u2net":             "General Purpose",
    "silueta":           "Fast Processing",
    "u2netp":            "Fastest (Lower Quality)",
}

ACCENT   = "#00D4AA"
ACCENT2  = "#FF6B6B"
BG_DARK  = "#0F1117"
BG_MID   = "#1A1D27"
BG_CARD  = "#22263A"
BG_LIGHT = "#2D3250"
TXT_MAIN = "#E8EAF6"
TXT_DIM  = "#7986CB"
BORDER   = "#3D4466"

# ── checkerboard for transparent preview ──────────────────────────────────────
def make_checker(w, h, size=16):
    img = Image.new("RGB", (w, h))
    px = img.load()
    c1, c2 = (200, 200, 200), (160, 160, 160)
    for y in range(h):
        for x in range(w):
            px[x, y] = c1 if ((x // size) + (y // size)) % 2 == 0 else c2
    return img

def composite_on_checker(rgba: Image.Image, max_w=400, max_h=340) -> Image.Image:
    rgba.thumbnail((max_w, max_h), Image.LANCZOS)
    checker = make_checker(rgba.width, rgba.height)
    checker.paste(rgba, mask=rgba.split()[3])
    return checker

# ── processing logic ───────────────────────────────────────────────────────────
def process_image(img: Image.Image, model: str, upscale: int, bg_mode: str) -> Image.Image:
    img = img.convert("RGBA")
    session = new_session(model)
    result = remove(img, session=session).convert("RGBA")

    if upscale > 1:
        arr = np.array(result)
        h, w = arr.shape[:2]
        arr = cv2.resize(arr, (w * upscale, h * upscale), interpolation=cv2.INTER_LANCZOS4)
        result = Image.fromarray(arr, "RGBA")

    if bg_mode == "white":
        bg = Image.new("RGBA", result.size, (255, 255, 255, 255))
        bg.paste(result, mask=result.split()[3])
        return bg.convert("RGBA")
    elif bg_mode == "black":
        bg = Image.new("RGBA", result.size, (0, 0, 0, 255))
        bg.paste(result, mask=result.split()[3])
        return bg.convert("RGBA")
    return result

# ── main GUI ───────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BG Eraser Pro")
        self.geometry("960x700")
        self.minsize(860, 620)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        self.source_img: Image.Image | None = None
        self.result_img: Image.Image | None = None
        self._tk_src = None
        self._tk_res = None
        self._busy = False

        self._build_ui()

    # ── layout ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # title bar
        hdr = tk.Frame(self, bg=BG_MID, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✦  BG Eraser Pro", font=("Courier", 18, "bold"),
                 fg=ACCENT, bg=BG_MID).pack(side="left", padx=20)
        tk.Label(hdr, text="remove • upscale • export PNG",
                 font=("Courier", 9), fg=TXT_DIM, bg=BG_MID).pack(side="left")

        # main body
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)
        self._build_controls(body)
        self._build_statusbar()

    def _card(self, parent, title, row, col):
        f = tk.Frame(parent, bg=BG_CARD, bd=0, highlightthickness=1,
                     highlightbackground=BORDER)
        f.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        tk.Label(f, text=title, font=("Courier", 9, "bold"),
                 fg=TXT_DIM, bg=BG_CARD).pack(anchor="w", padx=12, pady=(10, 0))
        return f

    def _build_left(self, parent):
        card = self._card(parent, "▸ INPUT IMAGE", 0, 0)
        self.src_canvas = tk.Canvas(card, bg=BG_MID, bd=0, highlightthickness=0,
                                    width=400, height=320)
        self.src_canvas.pack(fill="both", expand=True, padx=12, pady=10)
        self._draw_placeholder(self.src_canvas, "Click  [ Upload Image ]\nor drag & drop here", ACCENT)
        self.src_canvas.bind("<Button-1>", lambda e: self._pick_file())

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", padx=12, pady=(0, 10))
        self._btn(btn_row, "📂  Upload Image", self._pick_file, ACCENT).pack(side="left", expand=True, fill="x", padx=(0,4))
        self._btn(btn_row, "🗑  Clear", self._clear, ACCENT2, dim=True).pack(side="left", expand=True, fill="x", padx=(4,0))

    def _build_right(self, parent):
        card = self._card(parent, "▸ OUTPUT (PNG)", 0, 1)
        self.res_canvas = tk.Canvas(card, bg=BG_MID, bd=0, highlightthickness=0,
                                    width=400, height=320)
        self.res_canvas.pack(fill="both", expand=True, padx=12, pady=10)
        self._draw_placeholder(self.res_canvas, "Result will appear here", TXT_DIM)

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", padx=12, pady=(0, 10))
        self.save_btn = self._btn(btn_row, "💾  Save PNG", self._save, ACCENT, state="disabled")
        self.save_btn.pack(side="left", expand=True, fill="x")

    def _build_controls(self, parent):
        card = tk.Frame(parent, bg=BG_CARD, bd=0, highlightthickness=1,
                        highlightbackground=BORDER)
        card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))
        card.columnconfigure((0,1,2,3,4), weight=1)

        # model
        self._ctrl_label(card, "AI MODEL", 0, 0)
        self.model_var = tk.StringVar(value="isnet-general-use")
        model_frame = tk.Frame(card, bg=BG_CARD)
        model_frame.grid(row=1, column=0, padx=10, pady=(0,12), sticky="ew")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
            fieldbackground=BG_LIGHT, background=BG_LIGHT,
            foreground=TXT_MAIN, selectbackground=BG_LIGHT,
            selectforeground=TXT_MAIN, bordercolor=BORDER,
            arrowcolor=ACCENT, relief="flat")
        cb = ttk.Combobox(model_frame, textvariable=self.model_var,
                          values=list(MODELS.keys()), state="readonly",
                          style="Dark.TCombobox", font=("Courier", 9))
        cb.pack(fill="x")
        cb.bind("<<ComboboxSelected>>", lambda e: self._update_model_desc())
        self.model_desc = tk.Label(card, text=MODELS["isnet-general-use"],
                                   font=("Courier", 8), fg=TXT_DIM, bg=BG_CARD)
        self.model_desc.grid(row=2, column=0, padx=10, pady=(0,8), sticky="w")

        # upscale
        self._ctrl_label(card, "UPSCALE", 0, 1)
        self.upscale_var = tk.IntVar(value=1)
        uf = tk.Frame(card, bg=BG_CARD)
        uf.grid(row=1, column=1, padx=10, pady=(0,12), sticky="ew")
        for val, lbl in [(1, "None"), (2, "×2"), (3, "×3"), (4, "×4")]:
            tk.Radiobutton(uf, text=lbl, variable=self.upscale_var, value=val,
                           bg=BG_CARD, fg=TXT_MAIN, selectcolor=BG_LIGHT,
                           activebackground=BG_CARD, activeforeground=ACCENT,
                           font=("Courier", 9), bd=0).pack(side="left", padx=4)

        # background
        self._ctrl_label(card, "BACKGROUND", 0, 2)
        self.bg_var = tk.StringVar(value="transparent")
        bf = tk.Frame(card, bg=BG_CARD)
        bf.grid(row=1, column=2, padx=10, pady=(0,12), sticky="ew")
        for val, lbl in [("transparent", "Transparent"), ("white", "White"), ("black", "Black")]:
            tk.Radiobutton(bf, text=lbl, variable=self.bg_var, value=val,
                           bg=BG_CARD, fg=TXT_MAIN, selectcolor=BG_LIGHT,
                           activebackground=BG_CARD, activeforeground=ACCENT,
                           font=("Courier", 9), bd=0).pack(side="left", padx=4)

        # process button
        self._ctrl_label(card, "", 0, 3)
        self.process_btn = self._btn(card, "⚡  REMOVE BACKGROUND", self._run,
                                     ACCENT, big=True, state="disabled")
        self.process_btn.grid(row=1, column=3, columnspan=2, padx=14,
                              pady=(0, 12), sticky="ew")

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_MID, height=28)
        bar.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Ready — upload an image to get started.")
        tk.Label(bar, textvariable=self.status_var, font=("Courier", 8),
                 fg=TXT_DIM, bg=BG_MID, anchor="w").pack(side="left", padx=14)
        self.prog = ttk.Progressbar(bar, mode="indeterminate", length=120)
        self.prog.pack(side="right", padx=14, pady=4)

    # ── widget helpers ──────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, color, dim=False, big=False, state="normal"):
        alpha = "#555577" if dim else color
        f = ("Courier", 10, "bold") if big else ("Courier", 9)
        b = tk.Button(parent, text=text, command=cmd, font=f,
                      bg=BG_LIGHT, fg=alpha, activebackground=BG_CARD,
                      activeforeground=color, relief="flat", bd=0,
                      pady=8 if big else 6, cursor="hand2",
                      disabledforeground="#444466", state=state)
        b.bind("<Enter>", lambda e, b=b, c=color: b.config(bg=color, fg=BG_DARK) if b["state"] == "normal" else None)
        b.bind("<Leave>", lambda e, b=b: b.config(bg=BG_LIGHT, fg=alpha))
        return b

    def _ctrl_label(self, parent, text, row, col):
        tk.Label(parent, text=text, font=("Courier", 7, "bold"),
                 fg=TXT_DIM, bg=BG_CARD).grid(row=row, column=col, padx=10,
                                               pady=(10, 2), sticky="w")

    def _draw_placeholder(self, canvas, text, color):
        canvas.delete("all")
        canvas.create_text(canvas.winfo_reqwidth() // 2 or 200,
                           canvas.winfo_reqheight() // 2 or 160,
                           text=text, fill=color, font=("Courier", 11),
                           justify="center")

    # ── actions ─────────────────────────────────────────────────────────────────
    def _pick_file(self):
        filetypes = [("Images", " ".join(f"*{e}" for e in SUPPORTED)), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Choose an image", filetypes=filetypes)
        if not path:
            return
        try:
            p = Path(path)
            if p.suffix.lower() not in SUPPORTED:
                messagebox.showerror("Unsupported", f"Format '{p.suffix}' is not supported.")
                return
            img = Image.open(p)
            if getattr(img, "is_animated", False):
                img.seek(0)
            self.source_img = img.copy()
            self._show_preview(self.src_canvas, self.source_img, "_tk_src")
            self.process_btn.config(state="normal")
            self.save_btn.config(state="disabled")
            self.result_img = None
            self._draw_placeholder(self.res_canvas, "Result will appear here", TXT_DIM)
            self._set_status(f"Loaded: {p.name}  ({img.width}×{img.height})")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _show_preview(self, canvas, img, attr):
        canvas.update_idletasks()
        w = canvas.winfo_width() or 400
        h = canvas.winfo_height() or 320
        preview = composite_on_checker(img.copy().convert("RGBA"), w - 8, h - 8)
        tk_img = ImageTk.PhotoImage(preview)
        setattr(self, attr, tk_img)
        canvas.delete("all")
        canvas.create_image(w // 2, h // 2, anchor="center", image=tk_img)

    def _run(self):
        if self._busy or self.source_img is None:
            return
        self._busy = True
        self.process_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.prog.start(12)
        self._set_status("Processing… this may take a few seconds ⏳")

        model   = self.model_var.get()
        upscale = self.upscale_var.get()
        bg_mode = self.bg_var.get()
        src     = self.source_img.copy()

        def worker():
            try:
                result = process_image(src, model, upscale, bg_mode)
                self.after(0, lambda: self._on_done(result))
            except Exception as ex:
                self.after(0, lambda: self._on_error(str(ex)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, result: Image.Image):
        self.result_img = result
        self._show_preview(self.res_canvas, result, "_tk_res")
        self.save_btn.config(state="normal")
        self.process_btn.config(state="normal")
        self.prog.stop()
        self._busy = False
        self._set_status(f"✅  Done!  Output size: {result.width}×{result.height} px")

    def _on_error(self, msg):
        self.process_btn.config(state="normal")
        self.prog.stop()
        self._busy = False
        self._set_status(f"❌  Error: {msg}")
        messagebox.showerror("Processing Error", msg)

    def _save(self):
        if self.result_img is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Save as PNG",
        )
        if path:
            self.result_img.save(path, format="PNG", optimize=True)
            self._set_status(f"💾  Saved → {path}")

    def _clear(self):
        self.source_img = None
        self.result_img = None
        self._draw_placeholder(self.src_canvas, "Click  [ Upload Image ]\nor drag & drop here", ACCENT)
        self._draw_placeholder(self.res_canvas, "Result will appear here", TXT_DIM)
        self.process_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self._set_status("Cleared.")

    def _update_model_desc(self):
        self.model_desc.config(text=MODELS.get(self.model_var.get(), ""))

    def _set_status(self, msg: str):
        self.status_var.set(msg)

# ── entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
