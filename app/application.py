import os
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser, simpledialog
from PIL import Image
import webbrowser
import fitz
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

from app.constants import (
    APP_WINDOW_TITLE,
    APP_GEOMETRY,
    APP_MIN_SIZE,
    INSTAGRAM_PRESETS,
    IMAGE_FILETYPES,
    TEMPLATE_FILETYPES,
    EXPORT_FILETYPES,
    ACCENT_COLOR,
    ACCENT_HOVER,
    SIDEBAR_LEFT_WIDTH,
    SIDEBAR_RIGHT_WIDTH,
    SLIDER_MIN,
    SLIDER_MAX,
    SLIDER_DEFAULT,
    BRUSH_SIZE_MIN,
    BRUSH_SIZE_MAX,
    BRUSH_SIZE_DEFAULT,
    FONT_SIZE_MIN,
    FONT_SIZE_MAX,
    FONT_SIZE_DEFAULT,
    ZOOM_STEP_MIN,
    ZOOM_STEP_MAX,
    ZOOM_STEP_DEFAULT,
    ADJUSTMENT_DEBOUNCE_MS,
    SUCCESS_COLOR,
    WARNING_COLOR,
    get_app_base_dir,
    get_env_file_path,
    get_platform,
    TEXT_TONES,
    TEXT_LENGTHS,
    I18N,
    GITHUB_REPO_URL
)
from app.gpu_engine import GPUEngine
from app.template_manager import TemplateManager
from app.image_processor import ImageProcessor
from app.annotation_engine import AnnotationEngine
from app.canvas_engine import CanvasEngine
from app.export_pipeline import ExportPipeline
from app.text_engine import TextEngine


class PhotoTemplateStudioPro(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(APP_WINDOW_TITLE)
        self.geometry(APP_GEOMETRY)
        self.minsize(*APP_MIN_SIZE)

        self._ensure_env_file()
        self._lang = "tr"  # Default language

        self._gpu = GPUEngine()
        base = get_app_base_dir()
        self._templates = TemplateManager(
            os.path.join(base, "templates.json")
        )
        self._processor = ImageProcessor()
        self._annotations = AnnotationEngine()
        self._export = ExportPipeline(
            self._gpu, self._processor, self._annotations
        )

        self._current_template_image = None
        self._ai_upscale_enabled = False
        self._ai_scale = 4
        self._brightness = 1.0
        self._contrast = 1.0
        self._sharpness = 1.0
        self._current_color = ACCENT_COLOR
        self._font_size = FONT_SIZE_DEFAULT
        self._current_tool = "move"
        self._proxy_update_job = None
        
        self._mode_var = ctk.StringVar(value="Pan & Zoom")
        self._active_layer_var = ctk.StringVar(value="Photo")

        self._build_ui()
        self.after(100, self._load_initial_template)

    def _ensure_env_file(self):
        env_path = get_env_file_path()
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("OPENAI_API_KEY=\nGEMINI_API_KEY=\n")

    def _t(self, key):
        return I18N[self._lang].get(key, key)

    def _change_language(self, lang):
        if self._lang == lang:
            return
        self._lang = lang
        
        # Save state before rebuild
        master_img = self._processor.get_master()
        template_name = self._template_var.get() if hasattr(self, "_template_var") else None
        
        for widget in self.winfo_children():
            widget.destroy()
            
        self._build_ui()
        
        if template_name:
            self._template_var.set(template_name)
            self._on_template_change(template_name)
        if master_img:
            self._processor.set_master(master_img)
            self._gpu.clear_vram()
            self._refresh_canvas_photo()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, corner_radius=0)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_photo = self.tabview.add(self._t("tab_photo"))
        self.tab_text = self.tabview.add(self._t("tab_text"))
        self.tab_vector = self.tabview.add(self._t("tab_vector"))

        self.tab_photo.grid_columnconfigure(1, weight=1)
        self.tab_photo.grid_rowconfigure(0, weight=1)

        self._build_left_sidebar(self.tab_photo)
        self._build_center(self.tab_photo)
        self._build_right_sidebar(self.tab_photo)

        self._build_text_studio(self.tab_text)
        self._build_vector_studio(self.tab_vector)

    # ------------------------------------------------------------------ #
    #  LEFT SIDEBAR                                                      #
    # ------------------------------------------------------------------ #

    def _build_left_sidebar(self, parent):
        sidebar = ctk.CTkScrollableFrame(
            parent,
            width=SIDEBAR_LEFT_WIDTH,
            corner_radius=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")

        top_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        top_header.pack(fill="x", padx=16, pady=(18, 2))
        
        ctk.CTkLabel(
            top_header,
            text="⬡  Studio Pro",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        
        lang_seg = ctk.CTkSegmentedButton(
            top_header, values=["tr", "en"],
            command=self._change_language,
            width=60, height=24
        )
        lang_seg.set(self._lang)
        lang_seg.pack(side="right")

        ctk.CTkLabel(
            sidebar,
            text=self._t("app_subtitle"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=16, pady=(0, 18))

        self._section_label(sidebar, self._t("lbl_template"))

        names = self._templates.get_names()
        self._template_var = ctk.StringVar(value=names[0] if names else "")
        self._template_combo = ctk.CTkComboBox(
            sidebar,
            values=names if names else [""],
            variable=self._template_var,
            command=self._on_template_change,
            state="readonly",
            height=32,
        )
        self._template_combo.pack(fill="x", padx=16, pady=(4, 6))

        ctk.CTkButton(
            sidebar,
            text=self._t("btn_add_template"),
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color=ACCENT_COLOR,
            text_color=ACCENT_COLOR,
            hover_color=("#3b3b5c", "#2a2a4c"),
            command=self._on_add_template,
        ).pack(fill="x", padx=16, pady=(0, 12))

        self._section_label(sidebar, self._t("lbl_framing_mode"))

        val_pan = self._t("mode_pan_zoom")
        val_fit = self._t("mode_auto_fit")
        if not self._mode_var.get() in [val_pan, val_fit]:
            self._mode_var.set(val_pan)

        self._mode_seg = ctk.CTkSegmentedButton(
            sidebar,
            values=[val_pan, val_fit],
            variable=self._mode_var,
            command=self._on_mode_change,
        )
        self._mode_seg.pack(fill="x", padx=16, pady=(4, 12))

        self._section_label(sidebar, "Active Layer")
        self._layer_seg = ctk.CTkSegmentedButton(
            sidebar,
            values=["Photo", "Template"],
            variable=self._active_layer_var,
            command=self._on_active_layer_change,
        )
        self._layer_seg.pack(fill="x", padx=16, pady=(4, 12))

        self._section_label(sidebar, self._t("lbl_photo"))

        ctk.CTkButton(
            sidebar,
            text=self._t("btn_load_photo"),
            height=38,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_load_photo,
        ).pack(fill="x", padx=16, pady=(4, 4))

        self._file_label = ctk.CTkLabel(
            sidebar,
            text=self._t("lbl_no_photo"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=SIDEBAR_LEFT_WIDTH - 40,
        )
        self._file_label.pack(anchor="w", padx=16, pady=(0, 12))

        self._section_label(sidebar, self._t("lbl_tools"))

        tools_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        tools_frame.pack(fill="x", padx=16, pady=(4, 6))
        tools_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._move_btn = ctk.CTkButton(
            tools_frame,
            text=self._t("btn_move"),
            width=70,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color=ACCENT_COLOR,
            command=lambda: self._on_tool_change("move"),
        )
        self._move_btn.grid(row=0, column=0, padx=2, sticky="ew")

        self._draw_btn = ctk.CTkButton(
            tools_frame,
            text=self._t("btn_draw"),
            width=70,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            command=lambda: self._on_tool_change("draw"),
        )
        self._draw_btn.grid(row=0, column=1, padx=2, sticky="ew")

        self._text_btn = ctk.CTkButton(
            tools_frame,
            text=self._t("btn_text"),
            width=70,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            command=lambda: self._on_tool_change("text"),
        )
        self._text_btn.grid(row=0, column=2, padx=2, sticky="ew")

        color_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        color_row.pack(fill="x", padx=16, pady=(4, 4))

        self._color_preview = ctk.CTkButton(
            color_row,
            text="",
            width=34,
            height=34,
            fg_color=self._current_color,
            hover_color=self._current_color,
            corner_radius=17,
            border_width=2,
            border_color="#555",
            command=self._on_color_pick,
        )
        self._color_preview.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            color_row,
            text=self._t("lbl_brush"),
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(0, 4))

        self._brush_slider = ctk.CTkSlider(
            color_row,
            from_=BRUSH_SIZE_MIN,
            to=BRUSH_SIZE_MAX,
            number_of_steps=BRUSH_SIZE_MAX - BRUSH_SIZE_MIN,
            width=110,
            command=self._on_brush_change,
        )
        self._brush_slider.set(self._brush_width if hasattr(self, "_brush_width") else BRUSH_SIZE_DEFAULT)
        self._brush_slider.pack(side="left", padx=4, fill="x", expand=True)

        text_input_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        text_input_frame.pack(fill="x", padx=16, pady=(4, 4))
        
        self._text_entry = ctk.CTkEntry(
            text_input_frame,
            placeholder_text=self._t("txt_placeholder"),
            height=32,
        )
        self._text_entry.pack(side="left", fill="x", expand=True)
        self._text_entry.bind("<Return>", lambda e: self._on_add_text_center())

        ctk.CTkButton(
            text_input_frame,
            text="+",
            width=32,
            height=32,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            command=self._on_add_text_center,
        ).pack(side="right", padx=(4, 0))

        font_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        font_row.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            font_row,
            text=self._t("lbl_font_size"),
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(0, 4))

        self._font_val_label = ctk.CTkLabel(
            font_row,
            text=str(self._font_size),
            font=ctk.CTkFont(size=10),
            width=30,
        )
        self._font_val_label.pack(side="right")

        self._font_slider = ctk.CTkSlider(
            font_row,
            from_=FONT_SIZE_MIN,
            to=FONT_SIZE_MAX,
            width=120,
            command=self._on_font_size_change,
        )
        self._font_slider.set(self._font_size)
        self._font_slider.pack(side="right", padx=4, fill="x", expand=True)

        ctk.CTkButton(
            sidebar,
            text=self._t("btn_clear_annotations"),
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            text_color="gray",
            hover_color=("#3b3b5c", "#ddd"),
            command=self._on_clear_annotations,
        ).pack(fill="x", padx=16, pady=(4, 16))

        # Bottom Footer for Branding & Theme Switch
        footer_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=16, pady=(0, 16))

        lbl_author = ctk.CTkLabel(
            footer_frame,
            text=self._t("lbl_developed_by"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        lbl_author.pack(anchor="w")

        btn_github = ctk.CTkButton(
            footer_frame,
            text=self._t("btn_github"),
            height=24,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda: webbrowser.open(GITHUB_REPO_URL),
        )
        btn_github.pack(fill="x", pady=(5, 10))

        theme_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        theme_frame.pack(fill="x")

        ctk.CTkLabel(
            theme_frame,
            text="🌙",
            font=ctk.CTkFont(size=14),
        ).pack(side="left")

        self._theme_switch = ctk.CTkSwitch(
            theme_frame,
            text=self._t("switch_dark_mode"),
            onvalue="dark",
            offvalue="light",
            command=self._on_theme_toggle,
        )
        if ctk.get_appearance_mode().lower() == "dark":
            self._theme_switch.select()
        else:
            self._theme_switch.deselect()
        self._theme_switch.pack(side="left", padx=10)

    # ------------------------------------------------------------------ #
    #  CENTER CANVAS                                                     #
    # ------------------------------------------------------------------ #

    def _build_center(self, parent):
        center = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(0, weight=1)

        self._canvas_engine = CanvasEngine(
            center, self._annotations,
            on_canvas_click=self._on_canvas_click,
        )

    # ------------------------------------------------------------------ #
    #  RIGHT SIDEBAR                                                     #
    # ------------------------------------------------------------------ #

    def _build_right_sidebar(self, parent):
        sidebar = ctk.CTkScrollableFrame(
            parent, width=SIDEBAR_RIGHT_WIDTH, corner_radius=0,
        )
        sidebar.grid(row=0, column=2, sticky="nsew")

        self._section_label(sidebar, self._t("lbl_adjustments"))

        self._brightness_slider = self._build_adj_slider(
            sidebar, self._t("lbl_brightness"), self._on_brightness, self._brightness
        )
        self._contrast_slider = self._build_adj_slider(
            sidebar, self._t("lbl_contrast"), self._on_contrast, self._contrast
        )
        self._sharpness_slider = self._build_adj_slider(
            sidebar, self._t("lbl_sharpness"), self._on_sharpness, self._sharpness
        )

        self._zoom_step_slider = self._build_adj_slider(
            sidebar, self._t("lbl_zoom_step"), self._on_zoom_step, ZOOM_STEP_DEFAULT
        )
        self._zoom_step_slider.configure(from_=ZOOM_STEP_MIN, to=ZOOM_STEP_MAX)

        ctk.CTkButton(
            sidebar, text=self._t("btn_reset_all"), height=26,
            fg_color="transparent", border_width=1, border_color="gray",
            text_color="gray", font=ctk.CTkFont(size=11),
            command=self._on_reset_adjustments,
        ).pack(fill="x", padx=16, pady=(6, 14))

        self._section_label(sidebar, self._t("lbl_ai_upscale"))

        ai_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        ai_row.pack(fill="x", padx=16, pady=(4, 4))

        can_upscale = self._gpu.has_esrgan() or self._gpu.has_torch()
        self._ai_switch = ctk.CTkSwitch(
            ai_row, text=self._t("switch_enable"),
            command=self._on_ai_toggle,
            state="normal",
        )
        if self._ai_upscale_enabled:
            self._ai_switch.select()
        self._ai_switch.pack(side="left")

        self._scale_menu = ctk.CTkOptionMenu(
            ai_row, values=["2x", "4x"], width=68,
            command=self._on_scale_change,
        )
        self._scale_menu.set(f"{self._ai_scale}x")
        self._scale_menu.pack(side="right")

        gpu_color = SUCCESS_COLOR if self._gpu.has_gpu() else "gray"
        ctk.CTkLabel(
            sidebar, text=f"⚡ {self._gpu.device_name}",
            font=ctk.CTkFont(size=11), text_color=gpu_color,
        ).pack(anchor="w", padx=16, pady=(6, 2))

        if self._gpu.has_esrgan():
            status_text = self._t("msg_esrgan_ready")
            status_color = SUCCESS_COLOR
        elif self._gpu.has_torch():
            status_text = self._t("msg_torch_fallback")
            status_color = WARNING_COLOR
        else:
            status_text = self._t("msg_cpu_fallback")
            status_color = "gray"

        ctk.CTkLabel(
            sidebar, text=status_text,
            font=ctk.CTkFont(size=10), text_color=status_color,
        ).pack(anchor="w", padx=16, pady=(0, 14))

        self._section_label(sidebar, self._t("lbl_export"))

        presets_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        presets_frame.pack(fill="x", padx=16, pady=(4, 4))
        presets_frame.grid_columnconfigure((0, 1), weight=1)

        preset_items = list(INSTAGRAM_PRESETS.items())
        for i, (name, (pw, ph)) in enumerate(preset_items):
            ctk.CTkButton(
                presets_frame, text=name, height=30,
                font=ctk.CTkFont(size=10),
                fg_color="transparent", border_width=1, border_color="gray",
                command=lambda w=pw, h=ph: self._on_preset(w, h),
            ).grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")

        idx = len(preset_items)
        ctk.CTkButton(
            presets_frame, text=self._t("btn_original_size"), height=30,
            font=ctk.CTkFont(size=10),
            fg_color="transparent", border_width=1, border_color="gray",
            command=self._on_preset_original,
        ).grid(row=idx // 2, column=idx % 2, padx=2, pady=2, sticky="ew")

        dim_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        dim_frame.pack(fill="x", padx=16, pady=(8, 4))

        ctk.CTkLabel(
            dim_frame, text="W", font=ctk.CTkFont(size=11),
        ).pack(side="left")

        self._width_var = ctk.StringVar(value="1080")
        self._width_var.trace_add("write", self._on_export_dim_change)
        ctk.CTkEntry(
            dim_frame, textvariable=self._width_var,
            width=62, height=30,
        ).pack(side="left", padx=(4, 12))

        ctk.CTkLabel(
            dim_frame, text="H", font=ctk.CTkFont(size=11),
        ).pack(side="left")

        self._height_var = ctk.StringVar(value="1080")
        self._height_var.trace_add("write", self._on_export_dim_change)
        ctk.CTkEntry(
            dim_frame, textvariable=self._height_var,
            width=62, height=30,
        ).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(
            dim_frame, text="px", font=ctk.CTkFont(size=10),
            text_color="gray",
        ).pack(side="left", padx=(4, 0))

        ctk.CTkButton(
            sidebar, text=self._t("btn_save_image"), height=42,
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_save,
        ).pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkButton(
            sidebar, text=self._t("btn_batch_process"), height=36,
            fg_color="transparent", border_width=1,
            border_color=ACCENT_COLOR, text_color=ACCENT_COLOR,
            font=ctk.CTkFont(size=12),
            command=self._on_batch,
        ).pack(fill="x", padx=16, pady=(0, 6))

        self._progress = ctk.CTkProgressBar(sidebar, height=8)
        self._progress.set(0)

        self._progress_label = ctk.CTkLabel(
            sidebar, text="",
            font=ctk.CTkFont(size=10), text_color="gray",
        )

    # ------------------------------------------------------------------ #
    #  VECTOR STUDIO                                                     #
    # ------------------------------------------------------------------ #

    def _build_vector_studio(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Simple layout: top bar for loading, center canvas for rendering
        top_bar = ctk.CTkFrame(parent, height=50)
        top_bar.grid(row=0, column=0, sticky="ew")
        
        ctk.CTkButton(top_bar, text="Load PDF/SVG", command=self._on_load_vector).pack(side="left", padx=10, pady=10)
        self._vector_label = ctk.CTkLabel(top_bar, text="No document loaded")
        self._vector_label.pack(side="left", padx=10)
        
        center = ctk.CTkFrame(parent, fg_color="transparent")
        center.grid(row=1, column=0, sticky="nsew")
        
        self._vector_annotations = AnnotationEngine()
        self._vector_canvas = CanvasEngine(center, self._vector_annotations)
        self._vector_canvas.set_mode("pan_zoom")
        self._vector_canvas.set_tool("draw")
    def _section_label(self, parent, text):
        lbl = ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=12, weight="bold")
            )
        lbl.pack(anchor="w", padx=10, pady=(10, 2))
        return lbl
    def _on_load_vector(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Vector/Document", "*.svg *.pdf")]
            )
        if not filepath:
            return

        self._vector_label.configure(text=os.path.basename(filepath))

        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext in [".pdf", ".svg"]:
                doc = fitz.open(filepath)
                page = doc[0]
                pix = page.get_pixmap(dpi=150)
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(
                    mode, [pix.width, pix.height], pix.samples
                    ).convert("RGBA")
            else:
                img = Image.open(filepath).convert("RGBA")
            self._vector_canvas.set_photo(img, img.size, None)

        except Exception as e:
            messagebox.showerror(
        "Format Error",
        f"Unable to load file: {e}\n\nMake sure PyMuPDF is installed: pip"
        " install PyMuPDF",
    )
    # ------------------------------------------------------------------ #
    #  TEXT STUDIO                                                       #
    # ------------------------------------------------------------------ #

    def _build_text_studio(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(1, weight=1)

        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(top_frame, text=self._t("lbl_model_provider")).pack(side="left", padx=(0, 10))
        
        self._text_provider_var = ctk.StringVar(value="Ollama")
        self._text_provider_seg = ctk.CTkSegmentedButton(
            top_frame, values=["Ollama", "Paid APIs"],
            variable=self._text_provider_var,
            command=self._on_text_provider_change
        )
        self._text_provider_seg.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(top_frame, text=self._t("lbl_model")).pack(side="left", padx=(0, 10))
        
        self._text_model_combo = ctk.CTkComboBox(top_frame, values=["Loading..."], width=180)
        self._text_model_combo.pack(side="left", padx=(0, 20))

        self._edit_env_btn = ctk.CTkButton(
            top_frame, text=self._t("btn_edit_env"),
            fg_color="transparent", border_width=1,
            command=self._on_edit_env
        )
        
        ctk.CTkLabel(top_frame, text=self._t("lbl_tone")).pack(side="left", padx=(20, 10))
        
        self._text_tone_combo = ctk.CTkComboBox(top_frame, values=TEXT_TONES, width=150)
        self._text_tone_combo.set(TEXT_TONES[0])
        self._text_tone_combo.pack(side="left")

        ctk.CTkLabel(top_frame, text=self._t("lbl_length")).pack(side="left", padx=(20, 10))
        
        self._text_length_combo = ctk.CTkComboBox(top_frame, values=TEXT_LENGTHS, width=120)
        self._text_length_combo.set(TEXT_LENGTHS[1])
        self._text_length_combo.pack(side="left")

        self._custom_prompt_entry = ctk.CTkEntry(top_frame, placeholder_text=self._t("lbl_custom_prompt"), width=200)
        self._custom_prompt_entry.pack(side="left", padx=(20, 10))

        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))
        input_frame.grid_rowconfigure(1, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(input_frame, text=self._t("lbl_rough_input"), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self._text_input = ctk.CTkTextbox(input_frame, wrap="word")
        self._text_input.grid(row=1, column=0, sticky="nsew")

        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(output_frame, text=self._t("lbl_polished_output"), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self._text_output = ctk.CTkTextbox(output_frame, wrap="word", state="disabled")
        self._text_output.grid(row=1, column=0, sticky="nsew")

        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))

        self._generate_btn = ctk.CTkButton(
            bottom_frame, text=self._t("btn_polish_text"),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
            command=self._on_generate_text
        )
        self._generate_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bottom_frame, text=self._t("btn_copy_output"),
            fg_color="transparent", border_width=1,
            command=self._on_copy_text
        ).pack(side="left")
        
        self._text_status_label = ctk.CTkLabel(bottom_frame, text="", text_color="gray")
        self._text_status_label.pack(side="right")

        threading.Thread(target=self._fetch_ollama_models, daemon=True).start()

    def _fetch_ollama_models(self):
        models = TextEngine.get_ollama_models()
        self.after(0, lambda: self._update_model_dropdown("Ollama", models))

    def _update_model_dropdown(self, provider, models):
        if self._text_provider_var.get() == provider:
            if models:
                self._text_model_combo.configure(values=models)
                self._text_model_combo.set(models[0])
            else:
                self._text_model_combo.configure(values=["No models found"])
                self._text_model_combo.set("No models found")

    def _on_text_provider_change(self, value):
        if value == "Ollama":
            self._edit_env_btn.pack_forget()
            self._text_model_combo.set("Loading...")
            threading.Thread(target=self._fetch_ollama_models, daemon=True).start()
        else:
            self._edit_env_btn.pack(side="left", padx=(20, 10), after=self._text_model_combo)
            models = TextEngine.PAID_MODELS
            self._text_model_combo.configure(values=models)
            self._text_model_combo.set(models[0])

    def _on_edit_env(self):
        env_path = get_env_file_path()
        try:
            if get_platform() == "windows":
                os.startfile(env_path)
            elif get_platform() == "darwin":
                subprocess.run(["open", env_path])
            else:
                subprocess.run(["xdg-open", env_path])
        except Exception as e:
            messagebox.showerror(self._t("msg_error"), str(e))

    def _on_generate_text(self):
        input_text = self._text_input.get("1.0", "end-1c").strip()
        if not input_text:
            messagebox.showwarning(self._t("msg_warning"), self._t("msg_enter_text"))
            return

        provider = self._text_provider_var.get()
        model = self._text_model_combo.get()
        tone = self._text_tone_combo.get()
        length = self._text_length_combo.get()
        custom_inject = self._custom_prompt_entry.get().strip()

        if model == "No models found" or model == "Loading...":
            messagebox.showwarning(self._t("msg_warning"), "Please select a valid model.")
            return

        self._generate_btn.configure(state="disabled", text=self._t("msg_generating"))
        self._text_status_label.configure(text=self._t("msg_generating"))
        self._text_output.configure(state="normal")
        self._text_output.delete("1.0", "end")
        self._text_output.configure(state="disabled")

        def run():
            try:
                result = TextEngine.generate_text(provider, model, self._lang, tone, input_text, length, custom_inject)
                self.after(0, lambda: self._on_generate_success(result))
            except ValueError as ve:
                if str(ve) == "API_KEY_MISSING":
                    self.after(0, lambda: self._on_generate_error(self._t("msg_api_key_required")))
                else:
                    self.after(0, lambda err=str(ve): self._on_generate_error(err))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_generate_error(err))

        threading.Thread(target=run, daemon=True).start()

    def _on_generate_success(self, text):
        self._text_output.configure(state="normal")
        self._text_output.insert("1.0", text)
        self._text_output.configure(state="disabled")
        self._generate_btn.configure(state="normal", text=self._t("btn_polish_text"))
        self._text_status_label.configure(text=self._t("msg_done"), text_color=SUCCESS_COLOR)
        
    def _on_generate_error(self, err_msg):
        self._generate_btn.configure(state="normal", text=self._t("btn_polish_text"))
        self._text_status_label.configure(text=self._t("msg_error"), text_color=WARNING_COLOR)
        messagebox.showerror(self._t("msg_error"), err_msg)

    def _on_copy_text(self):
        text = self._text_output.get("1.0", "end-1c").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._text_status_label.configure(text=self._t("msg_copied"), text_color=SUCCESS_COLOR)

    # ------------------------------------------------------------------ #
    #  HELPERS                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _section_label(parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        ).pack(anchor="w", padx=16, pady=(12, 2))

    def _build_adj_slider(self, parent, label, callback, default_val=1.0):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=16, pady=3)

        ctk.CTkLabel(
            frame, text=label, font=ctk.CTkFont(size=11),
        ).pack(side="left")

        val_label = ctk.CTkLabel(
            frame, text=f"{default_val:.2f}",
            font=ctk.CTkFont(size=10), width=36,
        )
        val_label.pack(side="right")

        slider = ctk.CTkSlider(
            frame, from_=SLIDER_MIN, to=SLIDER_MAX,
            command=lambda v, cb=callback, vl=val_label: (
                vl.configure(text=f"{v:.2f}"),
                cb(v),
            ),
        )
        slider.set(default_val)
        slider.pack(side="right", fill="x", expand=True, padx=6)
        return slider

    # ------------------------------------------------------------------ #
    #  CALLBACKS                                                         #
    # ------------------------------------------------------------------ #

    def _on_template_change(self, name):
        if not name:
            return
        img = self._templates.get_template_image(name)
        if img is None:
            messagebox.showerror(
                self._t("msg_error"), f"Template file not found for '{name}'."
            )
            return
        self._current_template_image = img
        tw, th = img.size
        self._width_var.set(str(tw))
        self._height_var.set(str(th))
        self._canvas_engine.set_template(img)
        self._refresh_canvas_photo()

    def _on_add_template(self):
        path = filedialog.askopenfilename(filetypes=TEMPLATE_FILETYPES)
        if not path:
            return
        name = simpledialog.askstring(
            "Template Name", "Enter a display name for this template:"
        )
        if not name or not name.strip():
            return
        name = name.strip()
        self._templates.add_template(name, path)
        names = self._templates.get_names()
        self._template_combo.configure(values=names)
        self._template_var.set(name)
        self._on_template_change(name)
        messagebox.showinfo(
            self._t("msg_success"), f"Template '{name}' has been saved."
        )

    def _on_mode_change(self, value):
        mode = "pan_zoom" if value == self._t("mode_pan_zoom") else "auto_fit"
        self._canvas_engine.set_mode(mode)

    def _on_active_layer_change(self, value):
        layer = "photo" if value == "Photo" else "template"
        self._canvas_engine.set_active_layer(layer)

    def _on_load_photo(self):
        path = filedialog.askopenfilename(filetypes=IMAGE_FILETYPES)
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".pdf":
                import fitz
                doc = fitz.open(path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("RGBA")
            elif ext == ".svg":
                import cairosvg
                import io
                png_data = cairosvg.svg2png(url=path)
                img = Image.open(io.BytesIO(png_data)).convert("RGBA")
            else:
                img = Image.open(path).convert("RGBA")
        except Exception as exc:
            messagebox.showerror(self._t("msg_error"), f"Failed to load image:\n{exc}")
            return

        self._processor.set_master(img)
        self._file_label.configure(text=os.path.basename(path))
        self._gpu.clear_vram()

        template_size = None
        if self._current_template_image:
            template_size = self._current_template_image.size

        proxy = self._processor.get_proxy(
            self._brightness, self._contrast, self._sharpness,
        )
        self._canvas_engine.set_photo(proxy, img.size, template_size)

    def _on_tool_change(self, tool):
        self._current_tool = tool
        self._canvas_engine.set_tool(tool)

        btn_map = {
            "move": self._move_btn,
            "draw": self._draw_btn,
            "text": self._text_btn,
        }
        for t, btn in btn_map.items():
            if t == tool:
                btn.configure(fg_color=ACCENT_COLOR, border_width=0)
            else:
                btn.configure(
                    fg_color="transparent",
                    border_width=1, border_color="gray",
                )

    def _on_color_pick(self):
        result = colorchooser.askcolor(
            initialcolor=self._current_color, title="Pick a Color",
        )
        if result and result[1]:
            self._current_color = result[1]
            self._color_preview.configure(
                fg_color=self._current_color,
                hover_color=self._current_color,
            )
            self._canvas_engine.set_draw_color(self._current_color)

    def _on_brush_change(self, value):
        self._brush_width = int(value)
        self._canvas_engine.set_brush_width(self._brush_width)

    def _on_font_size_change(self, value):
        self._font_size = int(value)
        self._font_val_label.configure(text=str(int(value)))

    def _on_canvas_click(self, cx, cy):
        text = self._text_entry.get().strip()
        if not text:
            messagebox.showinfo(
                "Info", "Type some text in the text field first."
            )
            return
        nx, ny = self._canvas_engine.canvas_to_normalized(cx, cy)
        nsize = self._font_size / self._canvas_engine.view_min_dim
        self._annotations.add_text(
            nx, ny, text, self._current_color, nsize,
        )
        self._canvas_engine.request_render()

    def _on_clear_annotations(self):
        self._annotations.clear()
        self._canvas_engine.request_render()

    def _on_export_dim_change(self, *args):
        try:
            w = int(self._width_var.get())
            h = int(self._height_var.get())
            if w > 0 and h > 0:
                self._canvas_engine.set_export_size(w, h)
        except ValueError:
            pass

    def _on_add_text_center(self):
        text = self._text_entry.get().strip()
        if not text:
            messagebox.showinfo(
                "Info", "Type some text in the text field first."
            )
            return
        # Add text to the exact center (0.5, 0.5)
        nsize = self._font_size / self._canvas_engine.view_min_dim
        self._annotations.add_text(
            0.5, 0.5, text, self._current_color, nsize,
        )
        self._canvas_engine.request_render()

    def _on_brightness(self, value):
        self._brightness = value
        self._schedule_proxy_update()

    def _on_contrast(self, value):
        self._contrast = value
        self._schedule_proxy_update()

    def _on_sharpness(self, value):
        self._sharpness = value
        self._schedule_proxy_update()

    def _on_zoom_step(self, value):
        if hasattr(self, '_canvas_engine'):
            self._canvas_engine.set_zoom_step(value)

    def _schedule_proxy_update(self):
        if self._proxy_update_job is not None:
            self.after_cancel(self._proxy_update_job)
        self._proxy_update_job = self.after(
            ADJUSTMENT_DEBOUNCE_MS, self._refresh_canvas_photo,
        )

    def _on_reset_adjustments(self):
        self._brightness = 1.0
        self._contrast = 1.0
        self._sharpness = 1.0
        self._brightness_slider.set(1.0)
        self._contrast_slider.set(1.0)
        self._sharpness_slider.set(1.0)
        self._zoom_step_slider.set(ZOOM_STEP_DEFAULT)
        self._on_zoom_step(ZOOM_STEP_DEFAULT)
        self._refresh_canvas_photo()

    def _on_ai_toggle(self):
        if self._ai_switch.get():
            if not self._gpu.has_torch():
                self._ai_switch.deselect()
                messagebox.showwarning(
                    self._t("msg_warning"), 
                    "PyTorch (torch) is not installed. To use AI Upscaling, please install PyTorch (with CUDA if using an NVIDIA GPU)."
                )
                self._ai_upscale_enabled = False
                return
            self._ai_upscale_enabled = True
        else:
            self._ai_upscale_enabled = False

    def _on_scale_change(self, value):
        self._ai_scale = int(value.replace("x", ""))

    def _on_preset(self, w, h):
        self._width_var.set(str(w))
        self._height_var.set(str(h))

    def _on_preset_original(self):
        if self._current_template_image:
            tw, th = self._current_template_image.size
            self._width_var.set(str(tw))
            self._height_var.set(str(th))

    def _on_theme_toggle(self):
        mode = self._theme_switch.get()
        ctk.set_appearance_mode(mode)
        bg = "#12121f" if mode == "dark" else "#dee2e6"
        self._canvas_engine.widget.configure(bg=bg)

    def _on_save(self):
        if not self._processor.has_master():
            messagebox.showwarning(
                self._t("msg_warning"), self._t("msg_no_photo") if hasattr(self, "_t") else "Please load a photo first.",
            )
            return
        if self._current_template_image is None:
            messagebox.showwarning(
                self._t("msg_warning"), "Please select a template first.",
            )
            return

        try:
            tw = int(self._width_var.get())
            th = int(self._height_var.get())
            if tw <= 0 or th <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                self._t("msg_error"), "Please enter valid positive width and height.",
            )
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg", filetypes=EXPORT_FILETYPES,
        )
        if not save_path:
            return

        mode = (
            "pan_zoom"
            if self._mode_var.get() == self._t("mode_pan_zoom")
            else "auto_fit"
        )

        try:
            self._export.export_single(
                photo_master=self._processor.get_master(),
                template_image=self._current_template_image,
                mode=mode,
                photo_scale=self._canvas_engine.photo_scale,
                photo_offset_x=self._canvas_engine.photo_offset_x,
                photo_offset_y=self._canvas_engine.photo_offset_y,
                template_scale=self._canvas_engine.template_scale,
                template_offset_x=self._canvas_engine.template_offset_x,
                template_offset_y=self._canvas_engine.template_offset_y,
                brightness=self._brightness,
                contrast=self._contrast,
                sharpness=self._sharpness,
                target_w=tw,
                target_h=th,
                save_path=save_path,
                use_ai_upscale=self._ai_upscale_enabled,
                ai_scale=self._ai_scale,
            )
            messagebox.showinfo(
                self._t("msg_success"), "Image saved in full quality!"
            )
        except Exception as exc:
            messagebox.showerror(
                self._t("msg_error"), f"Export failed:\n{exc}"
            )

    def _on_batch(self):
        if self._current_template_image is None:
            messagebox.showwarning(
                self._t("msg_warning"), "Please select a template first.",
            )
            return

        input_dir = filedialog.askdirectory(
            title="Select Input Photo Folder",
        )
        if not input_dir:
            return

        output_dir = filedialog.askdirectory(
            title="Select Output Folder",
        )
        if not output_dir:
            return

        self._progress.pack(fill="x", padx=16, pady=(6, 2))
        self._progress_label.pack(anchor="w", padx=16, pady=(0, 6))
        self._progress.set(0)
        self._progress_label.configure(text=self._t("msg_batch_starting"))

        def run():
            def on_progress(current, total):
                self.after(0, lambda c=current, t=total: (
                    self._progress.set(c / t),
                    self._progress_label.configure(
                        text=self._t("msg_batch_processing").format(current=c, total=t)
                    ),
                ))

            count = self._export.batch_process(
                input_dir=input_dir,
                output_dir=output_dir,
                template_image=self._current_template_image,
                template_scale=self._canvas_engine.template_scale,
                template_offset_x=self._canvas_engine.template_offset_x,
                template_offset_y=self._canvas_engine.template_offset_y,
                brightness=self._brightness,
                contrast=self._contrast,
                sharpness=self._sharpness,
                use_ai_upscale=self._ai_upscale_enabled,
                ai_scale=self._ai_scale,
                progress_callback=on_progress,
            )
            self.after(0, lambda: self._batch_done(count))

        threading.Thread(target=run, daemon=True).start()

    def _batch_done(self, count):
        self._progress.pack_forget()
        self._progress_label.pack_forget()
        messagebox.showinfo(
            self._t("msg_success"),
            self._t("msg_batch_complete").format(count=count),
        )

    # ------------------------------------------------------------------ #
    #  INTERNAL                                                          #
    # ------------------------------------------------------------------ #

    def _refresh_canvas_photo(self):
        self._proxy_update_job = None
        if not self._processor.has_master():
            return
        proxy = self._processor.get_proxy(
            self._brightness, self._contrast, self._sharpness,
        )
        if proxy is not None:
            self._canvas_engine.update_photo_proxy(proxy)

    def _load_initial_template(self):
        if self._templates.has_templates():
            name = self._templates.get_names()[0]
            self._template_var.set(name)
            self._on_template_change(name)