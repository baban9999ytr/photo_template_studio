import tkinter as tk
from PIL import Image, ImageTk, ImageOps
from app.constants import (
    CANVAS_PREVIEW_SIZE,
    ZOOM_IN_FACTOR,
    ZOOM_OUT_FACTOR,
    MIN_SCALE,
    MAX_SCALE,
    RENDER_DEBOUNCE_MS,
)


class CanvasEngine:

    def __init__(self, parent, annotation_engine, on_canvas_click=None):
        self._annotations = annotation_engine
        self._on_canvas_click = on_canvas_click

        self._canvas_size = CANVAS_PREVIEW_SIZE
        self._canvas = tk.Canvas(
            parent,
            bg="#12121f",
            width=self._canvas_size,
            height=self._canvas_size,
            highlightthickness=0,
            cursor="fleur",
        )
        self._canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self._photo_proxy = None
        self._template_image = None
        self._master_photo_size = None

        self._tk_photo = None
        self._tk_template = None

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

        self._render_pending = False
        self._initial_render_done = False

        self._zoom_step = 1.0

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<MouseWheel>", self._on_scroll)
        self._canvas.bind("<Button-4>", self._on_scroll)
        self._canvas.bind("<Button-5>", self._on_scroll)
        self._canvas.bind("<Configure>", self._on_resize)

    @property
    def widget(self):
        return self._canvas

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
            self._canvas.config(cursor="arrow")
        elif self._tool == "move":
            self._canvas.config(cursor="fleur")
        self.request_render()

    def set_tool(self, tool):
        self._tool = tool
        cursors = {"move": "fleur", "draw": "pencil", "text": "crosshair"}
        if tool == "move":
            self._canvas.config(cursor="fleur")
        else:
            self._canvas.config(cursor=cursors.get(tool, "arrow"))

    def set_draw_color(self, color):
        self._draw_color = color

    def set_brush_width(self, width_px):
        self._brush_width = width_px

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
        if not self._render_pending:
            self._render_pending = True
            self._canvas.after(RENDER_DEBOUNCE_MS, self._do_render)

    def canvas_to_normalized(self, cx, cy):
        if self._view_w <= 0 or self._view_h <= 0:
            return 0.0, 0.0
        nx = (cx - self._view_offset_x) / self._view_w
        ny = (cy - self._view_offset_y) / self._view_h
        return nx, ny

    def _on_resize(self, event):
        new_size = min(event.width, event.height)
        if new_size >= 10:
            self._canvas_size = new_size
            self.request_render()

    def _on_press(self, event):
        if self._tool == "move":
            self._drag_start_x = event.x
            self._drag_start_y = event.y
        elif self._tool == "draw":
            self._last_draw_x = event.x
            self._last_draw_y = event.y
        elif self._tool == "text":
            if self._on_canvas_click:
                self._on_canvas_click(event.x, event.y)

    def _on_drag(self, event):
        if self._tool == "move":
            dx = event.x - self._drag_start_x
            dy = event.y - self._drag_start_y
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
            self._drag_start_x = event.x
            self._drag_start_y = event.y
            self.request_render()

        elif self._tool == "draw":
            if self._view_w > 0 and self._view_h > 0:
                nx1 = (self._last_draw_x - self._view_offset_x) / self._view_w
                ny1 = (self._last_draw_y - self._view_offset_y) / self._view_h
                nx2 = (event.x - self._view_offset_x) / self._view_w
                ny2 = (event.y - self._view_offset_y) / self._view_h
                nw = self._brush_width / max(1, self._canvas_size)
                self._annotations.add_stroke(
                    nx1, ny1, nx2, ny2, self._draw_color, nw
                )
            self._last_draw_x = event.x
            self._last_draw_y = event.y
            self.request_render()

    def _on_release(self, event):
        pass

    def _on_scroll(self, event):
        if self._mode != "pan_zoom" or self._tool != "move":
            return
        if self._active_layer == "photo" and self._photo_proxy is None:
            return
        if self._active_layer == "template" and self._template_image is None:
            return

        factor = 1.0
        if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
            factor = 1.0 - (1.0 - ZOOM_OUT_FACTOR) * self._zoom_step
        elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            factor = 1.0 + (ZOOM_IN_FACTOR - 1.0) * self._zoom_step

        if self._view_w > 0 and self._template_image:
            tw, th = self._template_image.size
            ratio = self._view_w / tw
            sx = event.x - (self._canvas.winfo_width() // 2)
            sy = event.y - (self._canvas.winfo_height() // 2)

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

    def _do_render(self):
        self._render_pending = False
        self._canvas.delete("all")

        canvas_w = self._canvas.winfo_width()
        canvas_h = self._canvas.winfo_height()

        if canvas_w < 10 or canvas_h < 10:
            if not self._initial_render_done:
                self._canvas.after(50, self.request_render)
            return

        self._initial_render_done = True

        if self._template_image is None:
            self._canvas.create_text(
                canvas_w // 2, canvas_h // 2,
                text="Select a template to begin",
                fill="#555555",
                font=("Arial", 14),
            )
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

        self._canvas.create_rectangle(
            offset_x - 1, offset_y - 1,
            offset_x + view_w + 1, offset_y + view_h + 1,
            outline="#333344", width=1,
        )

        if self._photo_proxy is not None:
            if self._mode == "auto_fit":
                cx = max(0.0, min(1.0, 0.5 - (self._photo_offset_x / max(1, view_w))))
                cy = max(0.0, min(1.0, 0.5 - (self._photo_offset_y / max(1, view_h))))
                fitted = ImageOps.fit(
                    self._photo_proxy, (view_w, view_h),
                    method=Image.Resampling.LANCZOS,
                    centering=(cx, cy)
                )
                self._tk_photo = ImageTk.PhotoImage(fitted)
                self._canvas.create_image(
                    center_x, center_y,
                    anchor="center", image=self._tk_photo,
                )
            else:
                if self._master_photo_size:
                    mw, mh = self._master_photo_size
                else:
                    mw, mh = self._photo_proxy.size

                display_pw = max(1, int(mw * self._photo_scale * ratio))
                display_ph = max(1, int(mh * self._photo_scale * ratio))

                cap = 4000
                if display_pw > cap or display_ph > cap:
                    shrink = cap / max(display_pw, display_ph)
                    display_pw = max(1, int(display_pw * shrink))
                    display_ph = max(1, int(display_ph * shrink))

                preview = self._photo_proxy.resize(
                    (display_pw, display_ph), Image.Resampling.LANCZOS,
                )
                self._tk_photo = ImageTk.PhotoImage(preview)

                draw_x = center_x + int(self._photo_offset_x * ratio)
                draw_y = center_y + int(self._photo_offset_y * ratio)

                self._canvas.create_image(
                    draw_x, draw_y,
                    anchor="center", image=self._tk_photo,
                )

        display_tw = max(1, int(tw * self._template_scale * ratio))
        display_th = max(1, int(th * self._template_scale * ratio))

        cap = 4000
        if display_tw > cap or display_th > cap:
            shrink = cap / max(display_tw, display_th)
            display_tw = max(1, int(display_tw * shrink))
            display_th = max(1, int(display_th * shrink))

        preview_template = self._template_image.resize(
            (display_tw, display_th), Image.Resampling.LANCZOS,
        )
        self._tk_template = ImageTk.PhotoImage(preview_template)

        draw_tx = center_x + int(self._template_offset_x * ratio)
        draw_ty = center_y + int(self._template_offset_y * ratio)

        self._canvas.create_image(
            draw_tx, draw_ty,
            anchor="center", image=self._tk_template,
        )

        if hasattr(self, "_export_w") and self._export_w > 0 and self._export_h > 0:
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
            cx2 = center_x + cw / 2
            cy2 = center_y + ch / 2
            
            self._canvas.create_rectangle(
                cx1, cy1, cx2, cy2,
                outline="#f39c12", width=2, dash=(6, 4)
            )
            self._canvas.create_text(
                cx1 + 4, cy1 + 4,
                text="Export Crop Box", fill="#f39c12", anchor="nw",
                font=("Arial", 10, "bold")
            )

        self._annotations.render_to_canvas(
            self._canvas, view_w, view_h, offset_x, offset_y,
        )
