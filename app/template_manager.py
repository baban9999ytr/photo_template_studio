import os
import json
from PIL import Image
from app.constants import resolve_template_path, get_app_base_dir


class TemplateManager:

    def __init__(self, json_path):
        self._json_path = json_path
        self._templates = {}
        self._image_cache = {}
        self.load()

    def load(self):
        if os.path.exists(self._json_path):
            try:
                with open(self._json_path, "r", encoding="utf-8") as f:
                    self._templates = json.load(f)
            except Exception:
                self._templates = {}
        self._image_cache.clear()

    def save(self):
        with open(self._json_path, "w", encoding="utf-8") as f:
            json.dump(self._templates, f, ensure_ascii=False, indent=4)

    def get_names(self):
        return list(self._templates.keys())

    def has_templates(self):
        return len(self._templates) > 0

    def add_template(self, name, path):
        try:
            base = get_app_base_dir()
            rel = os.path.relpath(path, base)
            if not rel.startswith(".."):
                store_path = rel.replace("\\", "/")
            else:
                store_path = os.path.abspath(path)
        except ValueError:
            store_path = os.path.abspath(path)

        self._templates[name] = store_path
        self.save()

    def remove_template(self, name):
        self._templates.pop(name, None)
        self._image_cache.pop(name, None)
        self.save()

    def get_template_path(self, name):
        raw = self._templates.get(name)
        if raw is None:
            return None
        return resolve_template_path(raw)

    def get_template_image(self, name):
        if name in self._image_cache:
            return self._image_cache[name].copy()

        path = self.get_template_path(name)
        if path is None or not os.path.exists(path):
            return None

        try:
            img = Image.open(path).convert("RGBA")
            self._image_cache[name] = img
            return img.copy()
        except Exception:
            return None

    def get_template_size(self, name):
        img = self.get_template_image(name)
        if img is None:
            return None
        return img.size

    def validate_template(self, name):
        path = self.get_template_path(name)
        return path is not None and os.path.exists(path)
