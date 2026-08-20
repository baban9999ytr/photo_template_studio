from PIL import Image, ImageEnhance, ImageOps
from app.constants import PROXY_MAX_DIM


class ImageProcessor:

    def __init__(self):
        self._master = None
        self._adjusted_cache = None
        self._proxy_cache = None
        self._last_adj_key = (1.0, 1.0, 1.0)
        self._last_proxy_key = None

    def set_master(self, image):
        self._master = image.copy() if image else None
        self._adjusted_cache = None
        self._proxy_cache = None
        self._last_adj_key = (1.0, 1.0, 1.0)
        self._last_proxy_key = None

    def get_master(self):
        return self._master

    def has_master(self):
        return self._master is not None

    def get_master_size(self):
        if self._master is None:
            return None
        return self._master.size

    def get_adjusted(self, brightness=1.0, contrast=1.0, sharpness=1.0):
        key = (round(brightness, 4), round(contrast, 4), round(sharpness, 4))
        if self._adjusted_cache is not None and self._last_adj_key == key:
            return self._adjusted_cache

        if self._master is None:
            return None

        img = self._master.copy()

        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)

        self._adjusted_cache = img
        self._last_adj_key = key
        self._proxy_cache = None
        self._last_proxy_key = None
        return img

    def get_proxy(self, brightness=1.0, contrast=1.0, sharpness=1.0, max_dim=None):
        if max_dim is None:
            max_dim = PROXY_MAX_DIM

        adj_key = (round(brightness, 4), round(contrast, 4), round(sharpness, 4))
        proxy_key = (*adj_key, max_dim)

        if self._proxy_cache is not None and self._last_proxy_key == proxy_key:
            return self._proxy_cache

        adjusted = self.get_adjusted(brightness, contrast, sharpness)
        if adjusted is None:
            return None

        w, h = adjusted.size
        if max(w, h) <= max_dim:
            self._proxy_cache = adjusted.copy()
            self._last_proxy_key = proxy_key
            return self._proxy_cache

        ratio = max_dim / max(w, h)
        new_w = max(1, int(w * ratio))
        new_h = max(1, int(h * ratio))
        self._proxy_cache = adjusted.resize(
            (new_w, new_h), Image.Resampling.LANCZOS
        )
        self._last_proxy_key = proxy_key
        return self._proxy_cache

    @staticmethod
    def auto_fit(image, target_size):
        return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)

    def invalidate_cache(self):
        self._adjusted_cache = None
        self._proxy_cache = None
        self._last_proxy_key = None
