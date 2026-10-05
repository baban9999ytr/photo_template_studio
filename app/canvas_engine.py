from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from app.constants import (
    CANVAS_PREVIEW_SIZE,
    MAX_SCALE,
    MIN_SCALE,
    RENDER_DEBOUNCE_MS,
    ZOOM_IN_FACTOR,
    ZOOM_OUT_FACTOR,
)


class CanvasEngine:
    def __init__(self, parent_layout, annotation_engine, on_canvas_click=None):
        self._annotations = annotation_engine
        self._on_canvas_click = on_canvas_click

        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setAlignment(Qt.AlignCenter)
        self._view.setRenderHint(QPainter.Antialiasing, False)
        self._view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self._view.setMouseTracking(True)

        parent_layout.addWidget(self._view)

        self._canvas_size = CANVAS_PREVIEW_SIZE

        self._photo_proxy = None
        self._template_image = None
        self._master_photo_size = None

        self._qpixmap_photo = None
        self._qpixmap_template = None

        self._photo_item = None
        self._template_item = None
        self._crop_box_item = None
        self._crop_text_item = None

        self._photo_offset_x = 0.0
        self._photo_offset_y = 0.0
        self._photo_scale = 1.0

        self._template_offset_x = 0.0
        self._template_offset_y = 0.0
        self._template_scale = 1.0

        self._active_layer = "photo"
        self._mode = "pan_zoom"
        self._tool = "move"
        self._draw_color = "#e94560"
        self._brush_width = 3

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._last_draw_x = 0
        self._last_draw_y = 0

        self._view_offset_x = 0
        self._view_offset_y = 0
        self._view_w = 0
        self._view_h = 0

        self._export_w = 0
        self._export_h = 0

        self._zoom_step = 1.0
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._do_render)
        self._initial_render_done = False

        self._view.resizeEvent = self._on_resize
        self._view.mousePressEvent = self._on_press
        self._view.mouseMoveEvent = self._on_drag
        self._view.mouseReleaseEvent = self._on_release
        self._view.wheelEvent = self._on_scroll

    @property
    def widget(self):
        return self._view

    @property
    def photo_offset_x(self):
        return self._photo_offset_x

    @property
    def photo_offset_y(self):
        return self._photo_offset_y

    @property
    def photo_scale(self):
        return self._photo_scale

    @property
    def template_offset_x(self):
        return self._template_offset_x

    @property
    def template_offset_y(self):
        return self._template_offset_y

    @property
    def template_scale(self):
        return self._template_scale

    @property
    def view_min_dim(self):
        return max(1, min(self._view_w, self._view_h))

    def set_zoom_step(self, step):
        self._zoom_step = step

    def set_active_layer(self, layer):
        self._active_layer = layer
        self.request_render()

    def set_mode(self, mode):
        self._mode = mode
        if mode == "auto_fit":
            self._view.viewport().setCursor(Qt.ArrowCursor)
        elif self._tool == "move":
            self._view.viewport().setCursor(Qt.SizeAllCursor)
        self.request_render()

    def set_tool(self, tool):
        self._tool = tool
        cursors = {
            "move": Qt.SizeAllCursor,
            "draw": Qt.CrossCursor,
            "text": Qt.IBeamCursor,
        }
        if tool == "move":
            self._view.viewport().setCursor(Qt.SizeAllCursor)
        else:
            self._view.viewport().setCursor(cursors.get(tool, Qt.ArrowCursor))

    def set_draw_color(self, color):
        self._draw_color = color

    def set_brush_width(self, width_px):
        self._brush_width = width_px

    def canvas_to_normalized(self, cx, cy):
        """Convert canvas pixel coordinates to normalized (0-1) coordinates."""
        if self._view_w <= 0 or self._view_h <= 0:
            return 0.0, 0.0
        nx = (cx - self._view_offset_x) / self._view_w
        ny = (cy - self._view_offset_y) / self._view_h
        return nx, ny

    def set_photo(self, proxy_image, master_size, template_size):
        self._photo_proxy = proxy_image
        self._master_photo_size = master_size
        if template_size and master_size:
            tw = template_size[0]
            pw = master_size[0]
            self._photo_scale = tw / pw
        self._photo_offset_x = 0.0
        self._photo_offset_y = 0.0
        self.request_render()

    def set_template(self, template_image):
        self._template_image = template_image
        self._template_offset_x = 0.0
        self._template_offset_y = 0.0
        self._template_scale = 1.0
        self.request_render()

    def set_export_size(self, w, h):
        self._export_w = w
        self._export_h = h
        self.request_render()

    def update_photo_proxy(self, proxy_image):
        self._photo_proxy = proxy_image
        self.request_render()

    def request_render(self):
        self._render_timer.start(RENDER_DEBOUNCE_MS)

    def _on_resize(self, event):
        new_size = min(event.size().width(), event.size().height())
        if new_size >= 10:
            self._canvas_size = new_size
            self.request_render()
        QGraphicsView.resizeEvent(self._view, event)

    def _on_press(self, event):
        if self._tool == "move":
            self._drag_start_x = event.position().x()
            self._drag_start_y = event.position().y()
        elif self._tool == "draw":
            self._last_draw_x = event.position().x()
            self._last_draw_y = event.position().y()
        elif self._tool == "text":
            if self._on_canvas_click:
                self._on_canvas_click(event.position().x(), event.position().y())
        QGraphicsView.mousePressEvent(self._view, event)

    def _on_drag(self, event):
        x = event.position().x()
        y = event.position().y()
        if self._tool == "move" and event.buttons() & Qt.LeftButton:
            dx = x - self._drag_start_x
            dy = y - self._drag_start_y
            if self._view_w > 0 and self._template_image:
                tw, th = self._template_image.size
                scale_x = tw / self._view_w
                scale_y = th / self._view_h
                if self._active_layer == "template":
                    self._template_offset_x += dx * scale_x
                    self._template_offset_y += dy * scale_y
                else:
                    self._photo_offset_x += dx * scale_x
                    self._photo_offset_y += dy * scale_y
            self._drag_start_x = x
            self._drag_start_y = y
            self.request_render()
        elif self._tool == "draw" and event.buttons() & Qt.LeftButton:
            if self._view_w > 0 and self._view_h > 0:
                nx1 = (self._last_draw_x - self._view_offset_x) / self._view_w
                ny1 = (self._last_draw_y - self._view_offset_y) / self._view_h
                nx2 = (x - self._view_offset_x) / self._view_w
                ny2 = (y - self._view_offset_y) / self._view_h
                nw = self._brush_width / max(1, self._canvas_size)
                self._annotations.add_stroke(nx1, ny1, nx2, ny2, self._draw_color, nw)
            self._last_draw_x = x
            self._last_draw_y = y
            self.request_render()
        QGraphicsView.mouseMoveEvent(self._view, event)

    def _on_release(self, event):
        QGraphicsView.mouseReleaseEvent(self._view, event)

    def _on_scroll(self, event):
        if self._mode != "pan_zoom" or self._tool != "move":
            return
        if self._active_layer == "photo" and self._photo_proxy is None:
            return
        if self._active_layer == "template" and self._template_image is None:
            return

        delta = event.angleDelta().y()
        factor = 1.0
        if delta < 0:
            factor = 1.0 - (1.0 - ZOOM_OUT_FACTOR) * self._zoom_step
        elif delta > 0:
            factor = 1.0 + (ZOOM_IN_FACTOR - 1.0) * self._zoom_step

        if self._view_w > 0 and self._template_image:
            tw, th = self._template_image.size
            ratio = self._view_w / tw
            sx = event.position().x() - (self._view.width() // 2)
            sy = event.position().y() - (self._view.height() // 2)

            if self._active_layer == "template":
                old_scale = self._template_scale
                new_scale = max(MIN_SCALE, min(MAX_SCALE, old_scale * factor))
                actual_factor = new_scale / old_scale
                self._template_scale = new_scale
                self._template_offset_x += (sx / ratio) * (1 - actual_factor)
                self._template_offset_y += (sy / ratio) * (1 - actual_factor)
            else:
                old_scale = self._photo_scale
                new_scale = max(MIN_SCALE, min(MAX_SCALE, old_scale * factor))
                actual_factor = new_scale / old_scale
                self._photo_scale = new_scale
                self._photo_offset_x += (sx / ratio) * (1 - actual_factor)
                self._photo_offset_y += (sy / ratio) * (1 - actual_factor)

        self.request_render()
        QGraphicsView.wheelEvent(self._view, event)

    def _pil_to_qpixmap(self, pil_image):
        """Convert a PIL Image to QPixmap with safe buffer handling."""
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        bytes_per_line = pil_image.width * 4
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            bytes_per_line,
            QImage.Format_RGBA8888,
        )
        # .copy() deep-copies pixel data so the Python bytes buffer can be freed safely
        return QPixmap.fromImage(qimage.copy())

    def _do_render(self):
        self._scene.clear()

        canvas_w = self._view.width()
        canvas_h = self._view.height()

        if canvas_w < 10 or canvas_h < 10:
            if not self._initial_render_done:
                self._render_timer.start(50)
            return

        self._initial_render_done = True
        self._scene.setSceneRect(0, 0, canvas_w, canvas_h)

        if self._template_image is None:
            text = self._scene.addText("Select a template to begin")
            text.setDefaultTextColor(QColor("#555555"))
            text.setPos(canvas_w // 2 - text.boundingRect().width() / 2, canvas_h // 2)
            return

        tw, th = self._template_image.size
        ratio = min(canvas_w / tw, canvas_h / th) * 0.92
        view_w = max(1, int(tw * ratio))
        view_h = max(1, int(th * ratio))
        self._view_w = view_w
        self._view_h = view_h

        offset_x = (canvas_w - view_w) // 2
        offset_y = (canvas_h - view_h) // 2
        self._view_offset_x = offset_x
        self._view_offset_y = offset_y
        center_x = canvas_w // 2
        center_y = canvas_h // 2

        self._scene.addRect(
            offset_x - 1, offset_y - 1, view_w + 2, view_h + 2, QPen(QColor("#333344"))
        )

        if self._photo_proxy is not None:
            if self._mode == "auto_fit":
                cx = max(0.0, min(1.0, 0.5 - (self._photo_offset_x / max(1, view_w))))
                cy = max(0.0, min(1.0, 0.5 - (self._photo_offset_y / max(1, view_h))))
                fitted = ImageOps.fit(
                    self._photo_proxy,
                    (view_w, view_h),
                    method=Image.Resampling.LANCZOS,
                    centering=(cx, cy),
                )
                self._qpixmap_photo = self._pil_to_qpixmap(fitted)
                self._photo_item = self._scene.addPixmap(self._qpixmap_photo)
                self._photo_item.setPos(center_x - view_w / 2, center_y - view_h / 2)
            else:
                mw, mh = (
                    self._master_photo_size
                    if self._master_photo_size
                    else self._photo_proxy.size
                )
                display_pw = max(1, int(mw * self._photo_scale * ratio))
                display_ph = max(1, int(mh * self._photo_scale * ratio))

                cap = 4000
                if display_pw > cap or display_ph > cap:
                    shrink = cap / max(display_pw, display_ph)
                    display_pw = max(1, int(display_pw * shrink))
                    display_ph = max(1, int(display_ph * shrink))

                preview = self._photo_proxy.resize(
                    (display_pw, display_ph), Image.Resampling.LANCZOS
                )
                self._qpixmap_photo = self._pil_to_qpixmap(preview)
                self._photo_item = self._scene.addPixmap(self._qpixmap_photo)
                draw_x = center_x + int(self._photo_offset_x * ratio) - display_pw / 2
                draw_y = center_y + int(self._photo_offset_y * ratio) - display_ph / 2
                self._photo_item.setPos(draw_x, draw_y)

        display_tw = max(1, int(tw * self._template_scale * ratio))
        display_th = max(1, int(th * self._template_scale * ratio))

        cap = 4000
        if display_tw > cap or display_th > cap:
            shrink = cap / max(display_tw, display_th)
            display_tw = max(1, int(display_tw * shrink))
            display_th = max(1, int(display_th * shrink))

        preview_template = self._template_image.resize(
            (display_tw, display_th), Image.Resampling.LANCZOS
        )
        self._qpixmap_template = self._pil_to_qpixmap(preview_template)
        self._template_item = self._scene.addPixmap(self._qpixmap_template)
        draw_tx = center_x + int(self._template_offset_x * ratio) - display_tw / 2
        draw_ty = center_y + int(self._template_offset_y * ratio) - display_th / 2
        self._template_item.setPos(draw_tx, draw_ty)

        if self._export_w > 0 and self._export_h > 0:
            target_ratio = self._export_w / self._export_h
            template_ratio = tw / th
            if target_ratio > template_ratio:
                crop_w = tw
                crop_h = tw / target_ratio
            else:
                crop_h = th
                crop_w = th * target_ratio

            cw = crop_w * (view_w / tw)
            ch = crop_h * (view_h / th)

            cx1 = center_x - cw / 2
            cy1 = center_y - ch / 2

            pen = QPen(QColor("#f39c12"))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            self._scene.addRect(cx1, cy1, cw, ch, pen)

            text = self._scene.addText("Export Crop Box")
            text.setDefaultTextColor(QColor("#f39c12"))
            text.setPos(cx1 + 4, cy1 + 4)

        self._annotations.render_to_canvas(
            self._scene, view_w, view_h, offset_x, offset_y
        )
