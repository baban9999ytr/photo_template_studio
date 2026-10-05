import os
import threading
import urllib.request

import numpy as np
from PIL import Image

from app.constants import ESRGAN_MODEL_URLS, get_models_dir


class GPUEngine:

    def __init__(self):
        self._device = "cpu"
        self._torch = None
        self._cuda_available = False
        self._mps_available = False
        self._esrgan_available = False
        self._upscaler = None
        self._current_model_key = None
        self._lock = threading.Lock()
        self._detect_hardware()

    def _detect_hardware(self):
        try:
            import torch

            self._torch = torch
            if torch.cuda.is_available():
                self._device = "cuda"
                self._cuda_available = True
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = "mps"
                self._mps_available = True
        except ImportError:
            pass

        try:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            self._esrgan_available = True
        except ImportError:
            pass

    @property
    def device_name(self):
        if self._cuda_available:
            try:
                return f"CUDA ({self._torch.cuda.get_device_name(0)})"
            except Exception:
                return "CUDA"
        if self._mps_available:
            return "Apple MPS (Metal)"
        return "CPU"

    def has_cuda(self):
        return self._cuda_available

    def has_mps(self):
        return self._mps_available

    def has_gpu(self):
        return self._cuda_available or self._mps_available

    def has_esrgan(self):
        return self._esrgan_available

    def has_torch(self):
        return self._torch is not None

    def upscale(self, image, scale=4, use_esrgan=True):
        if scale not in (2, 4):
            scale = 4

        if use_esrgan and self._esrgan_available:
            try:
                return self._upscale_esrgan(image, scale)
            except Exception:
                pass

        if self._torch is not None:
            try:
                return self._upscale_torch(image, scale)
            except Exception:
                pass

        return self._upscale_pillow(image, scale)

    def _download_model(self, model_key):
        url = ESRGAN_MODEL_URLS.get(model_key)
        if not url:
            return None
        models_dir = get_models_dir()
        filename = f"{model_key}.pth"
        filepath = os.path.join(models_dir, filename)
        if os.path.exists(filepath):
            return filepath
        try:
            urllib.request.urlretrieve(url, filepath)
            return filepath
        except Exception:
            if os.path.exists(filepath):
                os.remove(filepath)
            return None

    def _get_esrgan_upscaler(self, scale):
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        if scale == 2:
            model_key = "RealESRGAN_x2plus"
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=2,
            )
            netscale = 2
        else:
            model_key = "RealESRGAN_x4plus"
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=4,
            )
            netscale = 4

        if self._current_model_key == model_key and self._upscaler is not None:
            return self._upscaler

        model_path = self._download_model(model_key)
        if model_path is None:
            return None

        use_half = self._device != "cpu"
        self._upscaler = RealESRGANer(
            scale=netscale,
            model_path=model_path,
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=use_half,
            device=self._device,
        )
        self._current_model_key = model_key
        return self._upscaler

    def _upscale_esrgan(self, image, scale):
        with self._lock:
            upscaler = self._get_esrgan_upscaler(scale)
            if upscaler is None:
                raise RuntimeError("Failed to load ESRGAN model")
            img_array = np.array(image.convert("RGB"))
            img_bgr = img_array[:, :, ::-1].copy()
            output, _ = upscaler.enhance(img_bgr, outscale=scale)
            output_rgb = output[:, :, ::-1]
            return Image.fromarray(output_rgb)

    def _upscale_torch(self, image, scale):
        torch = self._torch
        img_array = np.array(image.convert("RGB")).astype(np.float32) / 255.0
        tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
        tensor = tensor.to(self._device)
        upscaled = torch.nn.functional.interpolate(
            tensor,
            scale_factor=float(scale),
            mode="bicubic",
            align_corners=False,
        )
        upscaled = upscaled.clamp(0, 1)
        result = upscaled.squeeze(0).permute(1, 2, 0).cpu().numpy()
        result = (result * 255).astype(np.uint8)
        return Image.fromarray(result)

    def _upscale_pillow(self, image, scale):
        w, h = image.size
        return image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

    def clear_vram(self):
        self._upscaler = None
        self._current_model_key = None
        if self._torch is not None and self._cuda_available:
            self._torch.cuda.empty_cache()
