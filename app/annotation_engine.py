import os
from PIL import ImageDraw, ImageFont
from PySide6.QtGui import QPen, QColor, QFont
from PySide6.QtCore import Qt

from app.constants import FONT_FALLBACK_CHAIN

class AnnotationEngine:
    def __init__(self):
        self._strokes = []
        self._texts = []
        self._resolved_font_path = None

    def add_stroke(self, nx1, ny1, nx2, ny2, color, normalized_width):
        self._strokes.append(
            (nx1, ny1, nx2, ny2, color, normalized_width)
        )

    def add_text(self, nx, ny, text, color, normalized_size):
        self._texts.append(
            (nx, ny, text, color, normalized_size)
        )

    def clear(self):
        self._strokes.clear()
        self._texts.clear()

    def has_annotations(self):
        return len(self._strokes) > 0 or len(self._texts) > 0

    def stroke_count(self):
        return len(self._strokes)

    def text_count(self):
        return len(self._texts)

    def render_to_canvas(self, scene, view_w, view_h, offset_x, offset_y):
        ref = max(1, min(view_w, view_h))

        for nx1, ny1, nx2, ny2, color, nw in self._strokes:
            x1 = offset_x + nx1 * view_w
            y1 = offset_y + ny1 * view_h
            x2 = offset_x + nx2 * view_w
            y2 = offset_y + ny2 * view_h
            w = max(1, int(nw * ref))
            
            pen = QPen(QColor(color))
            pen.setWidth(w)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            scene.addLine(x1, y1, x2, y2, pen)

        for nx, ny, text, color, nsize in self._texts:
            x = offset_x + nx * view_w
            y = offset_y + ny * view_h
            size = max(8, int(nsize * ref))
            
            text_item = scene.addText(text)
            text_item.setDefaultTextColor(QColor(color))
            font = QFont("Arial", size, QFont.Bold)
            text_item.setFont(font)
            text_item.setPos(x, y)

    def render_to_export(self, draw, export_w, export_h):
        ref = max(1, min(export_w, export_h))

        for nx1, ny1, nx2, ny2, color, nw in self._strokes:
            x1 = nx1 * export_w
            y1 = ny1 * export_h
            x2 = nx2 * export_w
            y2 = ny2 * export_h
            w = max(1, int(nw * ref))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=w)

        for nx, ny, text, color, nsize in self._texts:
            x = nx * export_w
            y = ny * export_h
            size = max(8, int(nsize * ref))
            font = self._resolve_font(size)
            draw.text((x, y), text, fill=color, font=font)

    def _resolve_font(self, size):
        if self._resolved_font_path:
            try:
                return ImageFont.truetype(self._resolved_font_path, size=size)
            except Exception:
                self._resolved_font_path = None

        for candidate in FONT_FALLBACK_CHAIN:
            try:
                font = ImageFont.truetype(candidate, size=size)
                self._resolved_font_path = candidate
                return font
            except Exception:
                continue

        return ImageFont.load_default()
