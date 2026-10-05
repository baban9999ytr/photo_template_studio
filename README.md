# Photo Template Studio Pro (PictureFormatter)

[![Python Support](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/baban9999ytr/PictureFormatter/actions/workflows/build.yml/badge.svg)](https://github.com/baban9999ytr/PictureFormatter/actions/workflows/build.yml)
[![CI Status](https://github.com/baban9999ytr/PictureFormatter/actions/workflows/ci.yml/badge.svg)](https://github.com/baban9999ytr/PictureFormatter/actions/workflows/ci.yml)

**A professional, multi-platform desktop application designed for social media managers and print studios.**

Developed by **Mustafa Göksal**

[View Repository on GitHub](https://github.com/baban9999ytr/PictureFormatter)

---

## Key Features

### Photo Studio (Image Engine)

- **Interactive Framing:** Auto-fit or pan & zoom images perfectly into your custom templates.
- **AI Upscaling:** Hardware-accelerated GPU/CPU upscaling using Real-ESRGAN and PyTorch. Fallbacks gracefully to high-quality Pillow LANCZOS.
- **Batch Exporting:** Process entire directories of photos into templates in a single click.
- **Rich Annotations:** Add resolution-independent text and drawings directly onto the canvas.
- **Image Adjustments:** Real-time brightness, contrast, and sharpness controls.

### Text Studio (AI Polisher)

- **Bilingual Support:** Full UI and AI generation support for both **English (en)** and **Turkish (tr)**.
- **Local Ollama Integration:** Utilize 100% offline local LLMs via Ollama to generate professional social media captions.
- **Paid Cloud APIs:** Easily plug in your OpenAI (`gpt-4o`) or Google Gemini (`gemini-1.5-pro`) keys for top-tier generation.
- **Tone Control:** Automatically convert rough text into "Formal Business", "Casual", or "Energetic" social media posts.

---

## Architecture

This project has been modularized for high performance and maintainability:

- `app/application.py`: Main UI orchestration (**PySide6**) and event wiring.
- `app/canvas_engine.py`: Dual-mode (pan/zoom & auto-fit) rendering engine.
- `app/gpu_engine.py`: Hardware-accelerated (CUDA/MPS) AI upscaling with CPU fallbacks.
- `app/image_processor.py`: Proxy/Master caching and image adjustments.
- `app/text_engine.py`: Handles local Ollama and Paid API integrations for the Text Studio.
- `app/export_pipeline.py`: High-quality batch export and single-image rendering.
- `app/template_manager.py`: JSON-based template registration.

---

## Quick Start & Installation

### 1. Prerequisites

Ensure you have Python 3.11+ installed. Clone the repository and install the requirements:

```bash
git clone https://github.com/baban9999ytr/PictureFormatter.git
cd PictureFormatter
pip install -r requirements.txt
```

_(Note: PyTorch and PySide6 are heavily utilized. Make sure to install the CUDA-specific PyTorch wheels if you have an NVIDIA GPU)._

### 2. .env Configuration (For Paid Models)

The Text Studio requires an `.env` file if you plan to use Paid APIs (OpenAI or Gemini).
On first launch, the application will automatically create an empty `.env` file for you in the root directory.

You can edit this file directly by clicking the **"⚙ Edit .env"** button in the app, or manually add your keys:

```env
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=AIza-your-gemini-key-here
```

_(If you are exclusively using local Ollama models, you do not need API keys)._

### 3. Run the App

```bash
python main.py
```

Alternatively, if installed via setuptools, run:

```bash
photo-studio
```

---

## Cross-Platform Executables

You can easily build a standalone executable for your operating system using `PyInstaller`.

```bash
pip install pyinstaller
```

**Windows Build Command:**

```bash
pyinstaller --noconfirm --onedir --windowed --add-data "app;app/" main.py --name PhotoTemplateStudioPro
```

**macOS / Linux Build Command:**

```bash
pyinstaller --noconfirm --onedir --windowed --add-data "app:app/" main.py --name PhotoTemplateStudioPro
```

### GitHub Actions

This repository is configured with automated GitHub Actions.
Pushing a version tag (e.g., `v2.0.0`) will automatically build `.exe` (Windows), `.app` (macOS), and `.tar.gz` (Linux) bundles and attach them to the GitHub Release.

---

## Privacy & Data Security

**100% Offline Local Processing Guarantee:**
All core photo processing tasks, including image scaling, framing, drawing, and AI image upscaling, happen **entirely offline** on your local hardware.

- No images or project metadata are ever uploaded to the cloud.
- If you use **Ollama**, all text generation occurs securely on your local machine.

For full details, please see our [PRIVACY.md](PRIVACY.md).

---

## License & Legal Disclaimers

This project is licensed under the **MIT License**. Copyright (c) 2026 Mustafa Göksal. See the [LICENSE](LICENSE) file for details.

- **AI Output Disclaimer:** AI-generated text output is provided "as is" without any guarantees regarding factual accuracy, tone appropriateness, or trademark/copyright compliance.
- **Third-Party Trademark Disclaimer:** Photo Template Studio Pro (PictureFormatter) is an independent open-source project. It is not affiliated with, endorsed by, or partnered with OpenAI, Google, Ollama, Meta, Instagram, or Real-ESRGAN.
- **Limitation of Liability:** The software is provided "AS IS". The developer assumes no liability for any data loss, workflow disruption, or hardware stress/damage that may occur during intensive high-resolution photo processing or VRAM scaling tasks.
