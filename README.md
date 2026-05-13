# ✦ BG Remover Pro

A modern AI-powered desktop background remover built with Python.
Upload any image, remove the background instantly using advanced AI segmentation models, upscale the result, preview transparency in real time, and export high-quality PNG files.

Perfect for:

* 🎨 Graphic designers
* 🛍️ Product photography
* 📸 Portrait editing
* 🎬 Thumbnail creators
* 🧑‍💻 Content creators
* 🤖 AI image workflows

---

# ✨ Features

* ✅ One-click AI background removal
* ✅ Multiple AI segmentation models
* ✅ Transparent PNG export
* ✅ White & black background modes
* ✅ Real-time image preview
* ✅ Image upscaling (×2, ×3, ×4)
* ✅ Modern dark-themed GUI
* ✅ Auto-installs dependencies
* ✅ Fast CPU support
* ✅ Supports multiple image formats

---

# 🛠️ Built With

* Python
* Tkinter
* rembg
* Pillow
* OpenCV
* NumPy

---

# 📦 Supported Formats

Input formats:

* JPG / JPEG
* PNG
* WEBP
* BMP
* TIFF
* GIF
* AVIF
* ICO

Output format:

* PNG

---

# ⚡ Installation

Install Python 3.10+ first.

Then install dependencies:

```bash id="1e1z0p"
pip install rembg[cpu] Pillow opencv-python-headless numpy
```

Or simply run the app once — dependencies install automatically.

---

# ▶️ How To Run

```bash id="c79z1k"
python bg_remover_gui.py
```

The desktop GUI will launch automatically.

---

# 🧠 How It Works

1. Upload an image
2. Choose an AI model
3. Select background mode
4. Optional: upscale image
5. Click “Remove Background”
6. Preview result
7. Save as transparent PNG

---

# 🤖 AI Models

Available processing models:

| Model             | Purpose                   |
| ----------------- | ------------------------- |
| isnet-general-use | Best overall quality      |
| u2net_human_seg   | Best for portraits        |
| u2net             | General purpose           |
| silueta           | Faster processing         |
| u2netp            | Fastest lightweight model |

---

# 📈 Upscaling Options

* None
* ×2
* ×3
* ×4

Uses OpenCV Lanczos scaling for sharper outputs.

---

# 🎨 Background Modes

* Transparent
* White Background
* Black Background

---

# 🖼️ Live Preview

The app includes:

* Input image preview
* Transparent checkerboard preview
* Output comparison
* Real-time processing status

---

# 💾 Export

Outputs are saved as optimized PNG images with transparency support.

---

# 🚀 Future Improvements

* Drag & drop support
* Batch image processing
* GPU acceleration
* Custom background replacement
* Shadow generation
* AI edge refinement

---

# 📜 License

This project is for educational and personal use.

---

# 👨‍💻 Author

Made by SANKHADEEP
