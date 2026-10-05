import io
import os
import sys
import webbrowser

from PIL import Image
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app import i18n, theme
from app.annotation_engine import AnnotationEngine
from app.canvas_engine import CanvasEngine
from app.constants import (
    APP_MIN_SIZE,
    APP_WINDOW_TITLE,
    BRUSH_SIZE_DEFAULT,
    BRUSH_SIZE_MAX,
    BRUSH_SIZE_MIN,
    FONT_SIZE_MAX,
    FONT_SIZE_MIN,
    GITHUB_REPO_URL,
    INSTAGRAM_PRESETS,
    SIDEBAR_LEFT_WIDTH,
    SIDEBAR_RIGHT_WIDTH,
    TEXT_LENGTHS,
    TEXT_TONES,
    get_app_base_dir,
    get_env_file_path,
)
from app.i18n import tr
from app.image_processor import ImageProcessor
from app.template_manager import TemplateManager

# Register HEIF opener if available
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass


# ──────────────────────────────────────────────────────
# Background worker for AI text generation
# ──────────────────────────────────────────────────────


class _TextWorker(QThread):
    """Runs text generation in a background thread to keep the UI responsive."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, model_type, model_name, lang, tone, text, length, custom):
        super().__init__()
        self._args = (model_type, model_name, lang, tone, text, length, custom)

    def run(self):
        try:
            from app.text_engine import TextEngine

            result = TextEngine.generate_text(*self._args)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ──────────────────────────────────────────────────────
# Main Application Window
# ──────────────────────────────────────────────────────


class PhotoTemplateStudioPro(QMainWindow):
    """Main application window — orchestrates all UI panels and engines."""

    def __init__(self):
        super().__init__()
        self._dark_mode = True
        self._text_worker = None
        self._init_engines()
        self._build_ui()
        self._wire_signals()
        self._retranslate_ui()
        i18n.on_language_changed(self._retranslate_ui)

    # ──────────────────────────────────────────────────
    #  Engine Initialization
    # ──────────────────────────────────────────────────

    def _init_engines(self):
        """Create backend engines — tolerant of missing optional deps."""
        self._annotations = AnnotationEngine()
        self._image_processor = ImageProcessor()
        templates_path = os.path.join(get_app_base_dir(), "templates.json")
        self._template_manager = TemplateManager(templates_path)

        self._gpu_engine = None
        try:
            from app.gpu_engine import GpuEngine

            self._gpu_engine = GpuEngine()
        except Exception:
            pass

        from app.export_pipeline import ExportPipeline

        self._export_pipeline = ExportPipeline(
            self._gpu_engine, self._image_processor, self._annotations
        )

        self._brightness = 1.0
        self._contrast = 1.0
        self._sharpness = 1.0

    # ──────────────────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle(APP_WINDOW_TITLE)
        self.setMinimumSize(APP_MIN_SIZE[0], APP_MIN_SIZE[1])
        self.resize(1420, 900)

        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tab_widget = QTabWidget()
        root.addWidget(self._tab_widget)

        self._photo_tab = QWidget()
        self._text_tab = QWidget()
        self._vector_tab = QWidget()

        self._tab_widget.addTab(self._photo_tab, "")
        self._tab_widget.addTab(self._text_tab, "")
        self._tab_widget.addTab(self._vector_tab, "")

        self._build_photo_tab()
        self._build_text_tab()
        self._build_vector_tab()

    # ─── Photo Tab ──────────────────────────────────

    def _build_photo_tab(self):
        layout = QHBoxLayout(self._photo_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._build_left_sidebar(layout)
        self._build_center_canvas(layout)
        self._build_right_sidebar(layout)

    # ─── Left Sidebar ──────────────────────────────

    def _build_left_sidebar(self, parent_layout):
        scroll = QScrollArea()
        scroll.setFixedWidth(SIDEBAR_LEFT_WIDTH)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(6)

        # ── App Header ──
        self._lbl_title = QLabel("⬡ Studio Pro")
        self._lbl_title.setProperty("class", "app-title")
        lay.addWidget(self._lbl_title)

        self._lbl_subtitle = QLabel()
        self._lbl_subtitle.setProperty("class", "app-subtitle")
        lay.addWidget(self._lbl_subtitle)
        lay.addWidget(self._sep())

        # ── Template ──
        self._lbl_template = self._header("lbl_template")
        lay.addWidget(self._lbl_template)

        self._combo_template = QComboBox()
        self._refresh_template_list()
        lay.addWidget(self._combo_template)

        self._btn_add_template = QPushButton()
        lay.addWidget(self._btn_add_template)
        lay.addWidget(self._sep())

        # ── Framing Mode ──
        self._lbl_framing = self._header("lbl_framing_mode")
        lay.addWidget(self._lbl_framing)

        self._combo_framing = QComboBox()
        lay.addWidget(self._combo_framing)
        lay.addWidget(self._sep())

        # ── Photo ──
        self._lbl_photo = self._header("lbl_photo")
        lay.addWidget(self._lbl_photo)

        self._btn_load_photo = QPushButton()
        self._btn_load_photo.setProperty("class", "accent")
        lay.addWidget(self._btn_load_photo)

        self._lbl_photo_info = QLabel()
        self._lbl_photo_info.setProperty("class", "info-label")
        lay.addWidget(self._lbl_photo_info)
        lay.addWidget(self._sep())

        # ── Tools ──
        self._lbl_tools = self._header("lbl_tools")
        lay.addWidget(self._lbl_tools)

        # Layer toggle
        lr = QHBoxLayout()
        lr.setSpacing(4)
        self._lbl_layer = QLabel("Layer:")
        lr.addWidget(self._lbl_layer)
        self._combo_layer = QComboBox()
        self._combo_layer.addItems(["Photo", "Template"])
        lr.addWidget(self._combo_layer, 1)
        lay.addLayout(lr)

        # Tool buttons
        tr_ = QHBoxLayout()
        tr_.setSpacing(4)
        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)

        self._btn_move = QPushButton()
        self._btn_move.setCheckable(True)
        self._btn_move.setChecked(True)
        self._btn_move.setProperty("class", "tool-btn")

        self._btn_draw = QPushButton()
        self._btn_draw.setCheckable(True)
        self._btn_draw.setProperty("class", "tool-btn")

        self._btn_text_tool = QPushButton()
        self._btn_text_tool.setCheckable(True)
        self._btn_text_tool.setProperty("class", "tool-btn")

        for btn in (self._btn_move, self._btn_draw, self._btn_text_tool):
            self._tool_group.addButton(btn)
            tr_.addWidget(btn)
        lay.addLayout(tr_)

        # Brush size
        br = QHBoxLayout()
        self._lbl_brush = QLabel()
        br.addWidget(self._lbl_brush)
        self._slider_brush = QSlider(Qt.Horizontal)
        self._slider_brush.setRange(BRUSH_SIZE_MIN, BRUSH_SIZE_MAX)
        self._slider_brush.setValue(BRUSH_SIZE_DEFAULT)
        br.addWidget(self._slider_brush, 1)
        self._lbl_brush_val = QLabel(str(BRUSH_SIZE_DEFAULT))
        self._lbl_brush_val.setProperty("class", "value-label")
        br.addWidget(self._lbl_brush_val)
        lay.addLayout(br)

        # Draw colour picker
        cr = QHBoxLayout()
        cr.addWidget(QLabel("Color:"))
        self._btn_color = QPushButton("  ")
        self._btn_color.setFixedSize(32, 24)
        self._btn_color.setStyleSheet(
            "background-color: #e94560; border-radius: 4px; border: none;"
        )
        cr.addWidget(self._btn_color)
        cr.addStretch()
        lay.addLayout(cr)

        # Text annotation input
        self._txt_annotation = QLineEdit()
        lay.addWidget(self._txt_annotation)

        # Font size
        fr = QHBoxLayout()
        self._lbl_font_size = QLabel()
        fr.addWidget(self._lbl_font_size)
        self._slider_font = QSlider(Qt.Horizontal)
        self._slider_font.setRange(FONT_SIZE_MIN, FONT_SIZE_MAX)
        self._slider_font.setValue(30)
        fr.addWidget(self._slider_font, 1)
        self._lbl_font_val = QLabel("30")
        self._lbl_font_val.setProperty("class", "value-label")
        fr.addWidget(self._lbl_font_val)
        lay.addLayout(fr)

        # Clear annotations
        self._btn_clear = QPushButton()
        lay.addWidget(self._btn_clear)
        lay.addWidget(self._sep())

        # ── Settings ──
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("🌐"))
        self._combo_lang = QComboBox()
        for code in i18n.available_languages():
            self._combo_lang.addItem(i18n.get_display_name(code), code)
        lang_row.addWidget(self._combo_lang, 1)
        lay.addLayout(lang_row)

        self._chk_dark = QCheckBox()
        self._chk_dark.setChecked(True)
        lay.addWidget(self._chk_dark)

        # Spacer pushes credits to the bottom
        lay.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ── Credits ──
        lay.addWidget(self._sep())
        self._lbl_credits = QLabel()
        self._lbl_credits.setProperty("class", "info-label")
        lay.addWidget(self._lbl_credits)

        self._btn_github = QPushButton()
        self._btn_github.setProperty("class", "link-btn")
        lay.addWidget(self._btn_github)

        scroll.setWidget(container)
        parent_layout.addWidget(scroll)

    # ─── Center Canvas ─────────────────────────────

    def _build_center_canvas(self, parent_layout):
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)

        frame = QFrame()
        frame.setObjectName("center_frame")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(4, 4, 4, 4)

        self._canvas_engine = CanvasEngine(
            fl, self._annotations, on_canvas_click=self._on_canvas_click
        )

        wl.addWidget(frame, 1)

        self._lbl_status = QLabel("Ready")
        self._lbl_status.setProperty("class", "status-bar")
        self._lbl_status.setFixedHeight(28)
        wl.addWidget(self._lbl_status)

        parent_layout.addWidget(wrapper, 1)

    # ─── Right Sidebar ─────────────────────────────

    def _build_right_sidebar(self, parent_layout):
        scroll = QScrollArea()
        scroll.setFixedWidth(SIDEBAR_RIGHT_WIDTH)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(6)

        # ── Adjustments ──
        self._lbl_adj = self._header("lbl_adjustments")
        lay.addWidget(self._lbl_adj)

        # Brightness
        self._lbl_brightness, self._slider_brightness, self._lbl_br_val = (
            self._add_slider_row(lay, "lbl_brightness", 0, 200, 100)
        )

        # Contrast
        self._lbl_contrast, self._slider_contrast, self._lbl_co_val = (
            self._add_slider_row(lay, "lbl_contrast", 0, 200, 100)
        )

        # Sharpness
        self._lbl_sharpness, self._slider_sharpness, self._lbl_sh_val = (
            self._add_slider_row(lay, "lbl_sharpness", 0, 200, 100)
        )

        # Zoom Speed
        self._lbl_zoom, self._slider_zoom, self._lbl_zm_val = self._add_slider_row(
            lay, "lbl_zoom_step", 10, 500, 100
        )

        self._btn_reset = QPushButton()
        lay.addWidget(self._btn_reset)
        lay.addWidget(self._sep())

        # ── AI Upscale ──
        self._lbl_ai = self._header("lbl_ai_upscale")
        lay.addWidget(self._lbl_ai)

        self._chk_ai = QCheckBox()
        lay.addWidget(self._chk_ai)

        self._lbl_ai_status = QLabel()
        self._lbl_ai_status.setProperty("class", "info-label")
        lay.addWidget(self._lbl_ai_status)
        self._update_ai_status_label()
        lay.addWidget(self._sep())

        # ── Export ──
        self._lbl_export = self._header("lbl_export")
        lay.addWidget(self._lbl_export)

        self._combo_preset = QComboBox()
        presets = (
            ["Original Size"]
            + [f"{k} ({v[0]}×{v[1]})" for k, v in INSTAGRAM_PRESETS.items()]
            + ["Custom"]
        )
        self._combo_preset.addItems(presets)
        lay.addWidget(self._combo_preset)

        # Custom W×H (hidden by default)
        self._wgt_custom = QWidget()
        cl = QHBoxLayout(self._wgt_custom)
        cl.setContentsMargins(0, 4, 0, 0)
        self._spin_w = QSpinBox()
        self._spin_w.setRange(1, 10000)
        self._spin_w.setValue(1080)
        self._spin_h = QSpinBox()
        self._spin_h.setRange(1, 10000)
        self._spin_h.setValue(1080)
        cl.addWidget(QLabel("W:"))
        cl.addWidget(self._spin_w)
        cl.addWidget(QLabel("H:"))
        cl.addWidget(self._spin_h)
        self._wgt_custom.setVisible(False)
        lay.addWidget(self._wgt_custom)

        self._btn_save = QPushButton()
        self._btn_save.setProperty("class", "accent")
        lay.addWidget(self._btn_save)

        self._btn_batch = QPushButton()
        lay.addWidget(self._btn_batch)

        lay.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        scroll.setWidget(container)
        parent_layout.addWidget(scroll)

    # ─── Text Tab ──────────────────────────────────

    def _build_text_tab(self):
        layout = QHBoxLayout(self._text_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Settings sidebar
        sc = QScrollArea()
        sc.setFixedWidth(SIDEBAR_LEFT_WIDTH)
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(16, 16, 16, 16)
        sl.setSpacing(8)

        self._lbl_provider = QLabel()
        sl.addWidget(self._lbl_provider)
        self._combo_provider = QComboBox()
        self._combo_provider.addItems(["Ollama", "Paid APIs"])
        sl.addWidget(self._combo_provider)

        self._lbl_model_txt = QLabel()
        sl.addWidget(self._lbl_model_txt)
        self._combo_model = QComboBox()
        self._combo_model.addItem("Loading...")
        sl.addWidget(self._combo_model)

        self._btn_env = QPushButton()
        sl.addWidget(self._btn_env)
        sl.addWidget(self._sep())

        self._lbl_tone = QLabel()
        sl.addWidget(self._lbl_tone)
        self._combo_tone = QComboBox()
        self._combo_tone.addItems(TEXT_TONES)
        sl.addWidget(self._combo_tone)

        self._lbl_length = QLabel()
        sl.addWidget(self._lbl_length)
        self._combo_length = QComboBox()
        self._combo_length.addItems(TEXT_LENGTHS)
        self._combo_length.setCurrentIndex(1)
        sl.addWidget(self._combo_length)
        sl.addWidget(self._sep())

        self._lbl_custom = QLabel()
        self._lbl_custom.setWordWrap(True)
        sl.addWidget(self._lbl_custom)
        self._txt_custom = QLineEdit()
        sl.addWidget(self._txt_custom)

        sl.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        sc.setWidget(sw)
        layout.addWidget(sc)

        # Content area
        cw = QWidget()
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(8)

        self._lbl_rough = QLabel()
        cl.addWidget(self._lbl_rough)
        self._txt_input = QTextEdit()
        self._txt_input.setPlaceholderText("Enter your rough text here...")
        cl.addWidget(self._txt_input, 1)

        br = QHBoxLayout()
        self._btn_polish = QPushButton()
        self._btn_polish.setProperty("class", "accent")
        br.addWidget(self._btn_polish)
        br.addStretch()
        cl.addLayout(br)

        self._lbl_polished = QLabel()
        cl.addWidget(self._lbl_polished)
        self._txt_output = QTextEdit()
        self._txt_output.setReadOnly(True)
        cl.addWidget(self._txt_output, 1)

        cr = QHBoxLayout()
        self._btn_copy = QPushButton()
        self._btn_copy.setProperty("class", "success")
        cr.addWidget(self._btn_copy)
        cr.addStretch()
        cl.addLayout(cr)

        layout.addWidget(cw, 1)

    # ─── Vector Tab ────────────────────────────────

    def _build_vector_tab(self):
        layout = QVBoxLayout(self._vector_tab)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Document / Vector Studio\n\nComing soon…")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setProperty("class", "info-label")
        lbl.setStyleSheet("font-size: 16px;")
        layout.addWidget(lbl)

    # ──────────────────────────────────────────────────
    #  Widget Factory Helpers
    # ──────────────────────────────────────────────────

    def _header(self, key):
        """Create a styled section-header QLabel."""
        lbl = QLabel(tr(key))
        lbl.setProperty("class", "section-header")
        return lbl

    def _sep(self):
        """Create a thin horizontal separator line."""
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setProperty("class", "separator")
        f.setFixedHeight(1)
        return f

    def _add_slider_row(self, parent_layout, label_key, lo, hi, default):
        """Add a label + slider + value label row. Returns (label, slider, value_label)."""
        row = QHBoxLayout()
        lbl = QLabel(tr(label_key))
        row.addWidget(lbl)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        row.addWidget(slider, 1)
        val = QLabel(self._fmt_slider(default, lo, hi))
        val.setProperty("class", "value-label")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(val)
        parent_layout.addLayout(row)
        return lbl, slider, val

    @staticmethod
    def _fmt_slider(v, lo, hi):
        """Format a slider value: if the range looks like x100 float, show decimal."""
        if hi == 200 and lo == 0:
            return f"{v / 100.0:.2f}"
        if hi == 500 and lo == 10:
            return f"{v / 100.0:.1f}"
        return str(v)

    # ──────────────────────────────────────────────────
    #  Signal Wiring
    # ──────────────────────────────────────────────────

    def _wire_signals(self):
        # Template
        self._combo_template.currentIndexChanged.connect(self._on_template_changed)
        self._btn_add_template.clicked.connect(self._on_add_template)

        # Framing
        self._combo_framing.currentIndexChanged.connect(self._on_framing_changed)

        # Photo
        self._btn_load_photo.clicked.connect(self._on_load_photo)

        # Tools
        self._tool_group.buttonClicked.connect(self._on_tool_changed)
        self._combo_layer.currentIndexChanged.connect(self._on_layer_changed)
        self._slider_brush.valueChanged.connect(self._on_brush_changed)
        self._slider_font.valueChanged.connect(self._on_font_changed)
        self._btn_color.clicked.connect(self._on_color_pick)
        self._btn_clear.clicked.connect(self._on_clear_annotations)

        # Adjustments
        self._slider_brightness.valueChanged.connect(self._on_brightness)
        self._slider_contrast.valueChanged.connect(self._on_contrast)
        self._slider_sharpness.valueChanged.connect(self._on_sharpness)
        self._slider_zoom.valueChanged.connect(self._on_zoom_speed)
        self._btn_reset.clicked.connect(self._on_reset_adjustments)

        # AI
        self._chk_ai.stateChanged.connect(lambda _: None)

        # Export
        self._combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        self._btn_save.clicked.connect(self._on_save_image)
        self._btn_batch.clicked.connect(self._on_batch_process)

        # Settings
        self._combo_lang.currentIndexChanged.connect(self._on_language_changed)
        self._chk_dark.stateChanged.connect(self._on_theme_toggled)

        # Credits
        self._btn_github.clicked.connect(lambda: webbrowser.open(GITHUB_REPO_URL))

        # Text tab
        self._combo_provider.currentIndexChanged.connect(self._on_provider_changed)
        self._btn_env.clicked.connect(self._on_edit_env)
        self._btn_polish.clicked.connect(self._on_polish_text)
        self._btn_copy.clicked.connect(self._on_copy_output)

        # Initial model list
        self._refresh_model_list()

    # ──────────────────────────────────────────────────
    #  i18n Retranslation
    # ──────────────────────────────────────────────────

    def _retranslate_ui(self):
        """Re-apply every translatable string from the current language.
        Preserves widget state (slider positions, combo selections, etc.)."""
        self.setWindowTitle(APP_WINDOW_TITLE)

        # Tabs
        self._tab_widget.setTabText(0, tr("tab_photo"))
        self._tab_widget.setTabText(1, tr("tab_text"))
        self._tab_widget.setTabText(2, tr("tab_vector"))

        # Left sidebar — photo tab
        self._lbl_subtitle.setText(tr("app_subtitle"))
        self._lbl_template.setText(tr("lbl_template"))
        self._btn_add_template.setText(tr("btn_add_template"))
        self._lbl_framing.setText(tr("lbl_framing_mode"))

        idx = self._combo_framing.currentIndex()
        self._combo_framing.blockSignals(True)
        self._combo_framing.clear()
        self._combo_framing.addItems([tr("mode_pan_zoom"), tr("mode_auto_fit")])
        self._combo_framing.setCurrentIndex(max(0, idx))
        self._combo_framing.blockSignals(False)

        self._lbl_photo.setText(tr("lbl_photo"))
        self._btn_load_photo.setText(tr("btn_load_photo"))
        if not self._image_processor.has_master():
            self._lbl_photo_info.setText(tr("lbl_no_photo"))

        self._lbl_tools.setText(tr("lbl_tools"))
        self._btn_move.setText(tr("btn_move"))
        self._btn_draw.setText(tr("btn_draw"))
        self._btn_text_tool.setText(tr("btn_text"))
        self._lbl_brush.setText(tr("lbl_brush"))
        self._txt_annotation.setPlaceholderText(tr("txt_placeholder"))
        self._lbl_font_size.setText(tr("lbl_font_size"))
        self._btn_clear.setText(tr("btn_clear_annotations"))
        self._chk_dark.setText(tr("switch_dark_mode"))
        self._lbl_credits.setText(tr("lbl_developed_by"))
        self._btn_github.setText(tr("btn_github"))

        # Right sidebar
        self._lbl_adj.setText(tr("lbl_adjustments"))
        self._lbl_brightness.setText(tr("lbl_brightness"))
        self._lbl_contrast.setText(tr("lbl_contrast"))
        self._lbl_sharpness.setText(tr("lbl_sharpness"))
        self._lbl_zoom.setText(tr("lbl_zoom_step"))
        self._btn_reset.setText(tr("btn_reset_all"))
        self._lbl_ai.setText(tr("lbl_ai_upscale"))
        self._chk_ai.setText(tr("switch_enable"))
        self._update_ai_status_label()
        self._lbl_export.setText(tr("lbl_export"))
        self._btn_save.setText(tr("btn_save_image"))
        self._btn_batch.setText(tr("btn_batch_process"))

        # Text tab
        self._lbl_provider.setText(tr("lbl_model_provider"))
        self._lbl_model_txt.setText(tr("lbl_model"))
        self._btn_env.setText(tr("btn_edit_env"))
        self._lbl_tone.setText(tr("lbl_tone"))
        self._lbl_length.setText(tr("lbl_length"))
        self._lbl_custom.setText(tr("lbl_custom_prompt"))
        self._lbl_rough.setText(tr("lbl_rough_input"))
        self._lbl_polished.setText(tr("lbl_polished_output"))
        self._btn_polish.setText(tr("btn_polish_text"))
        self._btn_copy.setText(tr("btn_copy_output"))

    # ──────────────────────────────────────────────────
    #  Event Handlers — Photo Tab
    # ──────────────────────────────────────────────────

    def _on_template_changed(self, index):
        name = self._combo_template.currentText()
        if not name:
            return
        img = self._template_manager.get_template_image(name)
        if img:
            self._canvas_engine.set_template(img)
            self._sync_export_crop()
            self._update_status()

    def _on_add_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Add Template", "", "PNG Images (*.png)"
        )
        if not path:
            return
        name = os.path.splitext(os.path.basename(path))[0]
        self._template_manager.add_template(name, path)
        self._refresh_template_list()
        idx = self._combo_template.findText(name)
        if idx >= 0:
            self._combo_template.setCurrentIndex(idx)

    def _on_framing_changed(self, index):
        self._canvas_engine.set_mode("auto_fit" if index == 1 else "pan_zoom")

    def _on_load_photo(self):
        filt = "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.heic *.pdf *.svg);;All Files (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Load Photo", "", filt)
        if not path:
            return
        try:
            img = self._load_image(path)
            self._image_processor.set_master(img)

            tname = self._combo_template.currentText()
            tsize = self._template_manager.get_template_size(tname)
            proxy = self._image_processor.get_proxy(
                self._brightness, self._contrast, self._sharpness
            )
            msize = self._image_processor.get_master_size()

            self._canvas_engine.set_photo(proxy, msize, tsize)
            w, h = msize
            self._lbl_photo_info.setText(f"{os.path.basename(path)}  ({w}×{h})")
            self._update_status()
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), str(e))

    def _on_tool_changed(self, button):
        tools = {
            self._btn_move: "move",
            self._btn_draw: "draw",
            self._btn_text_tool: "text",
        }
        self._canvas_engine.set_tool(tools.get(button, "move"))

    def _on_layer_changed(self, index):
        self._canvas_engine.set_active_layer("template" if index == 1 else "photo")

    def _on_brush_changed(self, v):
        self._lbl_brush_val.setText(str(v))
        self._canvas_engine.set_brush_width(v)

    def _on_font_changed(self, v):
        self._lbl_font_val.setText(str(v))

    def _on_color_pick(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self._canvas_engine.set_draw_color(c.name())
            self._btn_color.setStyleSheet(
                f"background-color: {c.name()}; border-radius: 4px; border: none;"
            )

    def _on_clear_annotations(self):
        self._annotations.clear()
        self._canvas_engine.request_render()

    def _on_canvas_click(self, x, y):
        text = self._txt_annotation.text().strip() or "Text"
        nx, ny = self._canvas_engine.canvas_to_normalized(x, y)
        nsize = self._slider_font.value() / max(1, self._canvas_engine.view_min_dim)
        self._annotations.add_text(nx, ny, text, "#ffffff", nsize)
        self._canvas_engine.request_render()

    # ─── Adjustments ───────────────────────────────

    def _on_brightness(self, v):
        self._brightness = v / 100.0
        self._lbl_br_val.setText(f"{self._brightness:.2f}")
        self._push_proxy()

    def _on_contrast(self, v):
        self._contrast = v / 100.0
        self._lbl_co_val.setText(f"{self._contrast:.2f}")
        self._push_proxy()

    def _on_sharpness(self, v):
        self._sharpness = v / 100.0
        self._lbl_sh_val.setText(f"{self._sharpness:.2f}")
        self._push_proxy()

    def _on_zoom_speed(self, v):
        step = v / 100.0
        self._lbl_zm_val.setText(f"{step:.1f}")
        self._canvas_engine.set_zoom_step(step)

    def _on_reset_adjustments(self):
        self._slider_brightness.setValue(100)
        self._slider_contrast.setValue(100)
        self._slider_sharpness.setValue(100)
        self._slider_zoom.setValue(100)

    # ─── Export ─────────────────────────────────────

    def _on_preset_changed(self, index):
        n = len(INSTAGRAM_PRESETS)
        self._wgt_custom.setVisible(index == n + 1)
        self._sync_export_crop()

    def _on_save_image(self):
        if not self._image_processor.has_master():
            QMessageBox.warning(self, tr("msg_warning"), tr("lbl_no_photo"))
            return
        tname = self._combo_template.currentText()
        timg = self._template_manager.get_template_image(tname)
        if timg is None:
            QMessageBox.warning(self, tr("msg_warning"), tr("msg_select_template"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, tr("btn_save_image"), "", "JPEG (*.jpg);;PNG (*.png);;HEIC (*.heic)"
        )
        if not path:
            return

        tw, th = self._export_size(timg)
        mode = "auto_fit" if self._combo_framing.currentIndex() == 1 else "pan_zoom"
        try:
            self._export_pipeline.export_single(
                photo_master=self._image_processor.get_master(),
                template_image=timg,
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
                save_path=path,
                use_ai_upscale=self._chk_ai.isChecked(),
            )
            QMessageBox.information(self, tr("msg_success"), tr("msg_done"))
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), str(e))

    def _on_batch_process(self):
        tname = self._combo_template.currentText()
        timg = self._template_manager.get_template_image(tname)
        if timg is None:
            QMessageBox.warning(self, tr("msg_warning"), tr("msg_select_template"))
            return

        in_dir = QFileDialog.getExistingDirectory(self, "Input Directory")
        if not in_dir:
            return
        out_dir = QFileDialog.getExistingDirectory(self, "Output Directory")
        if not out_dir:
            return

        self._lbl_status.setText(tr("msg_batch_starting"))
        QApplication.processEvents()

        def prog(cur, tot):
            self._lbl_status.setText(tr("msg_batch_processing", current=cur, total=tot))
            QApplication.processEvents()

        try:
            n = self._export_pipeline.batch_process(
                input_dir=in_dir,
                output_dir=out_dir,
                template_image=timg,
                template_scale=self._canvas_engine.template_scale,
                template_offset_x=self._canvas_engine.template_offset_x,
                template_offset_y=self._canvas_engine.template_offset_y,
                brightness=self._brightness,
                contrast=self._contrast,
                sharpness=self._sharpness,
                use_ai_upscale=self._chk_ai.isChecked(),
                progress_callback=prog,
            )
            QMessageBox.information(
                self, tr("msg_success"), tr("msg_batch_complete", count=n)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error"), str(e))
        self._lbl_status.setText("Ready")

    # ─── Settings ──────────────────────────────────

    def _on_language_changed(self, index):
        code = self._combo_lang.currentData()
        if code:
            i18n.set_language(code)

    def _on_theme_toggled(self, state):
        self._dark_mode = bool(state)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme.get_theme(self._dark_mode))

    # ─── Text Tab ──────────────────────────────────

    def _on_provider_changed(self, _index):
        self._refresh_model_list()

    def _on_edit_env(self):
        path = get_env_file_path()
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("OPENAI_API_KEY=\nGEMINI_API_KEY=\n")
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')

    def _on_polish_text(self):
        raw = self._txt_input.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, tr("msg_warning"), tr("msg_enter_text"))
            return

        model = self._combo_model.currentText()
        if model in ("Loading...", "No models found"):
            return

        provider = self._combo_provider.currentText()
        mtype = "Ollama" if provider == "Ollama" else "Paid APIs"

        self._btn_polish.setEnabled(False)
        self._btn_polish.setText(tr("msg_generating"))
        self._txt_output.clear()

        self._text_worker = _TextWorker(
            mtype,
            model,
            i18n.get_language(),
            self._combo_tone.currentText(),
            raw,
            self._combo_length.currentText(),
            self._txt_custom.text().strip(),
        )
        self._text_worker.finished.connect(self._on_text_ok)
        self._text_worker.error.connect(self._on_text_err)
        self._text_worker.start()

    def _on_text_ok(self, text):
        self._txt_output.setPlainText(text)
        self._btn_polish.setEnabled(True)
        self._btn_polish.setText(tr("btn_polish_text"))
        self._lbl_status.setText(tr("msg_done"))

    def _on_text_err(self, msg):
        if "API_KEY_MISSING" in msg:
            QMessageBox.warning(self, tr("msg_warning"), tr("msg_api_key_required"))
        else:
            QMessageBox.critical(self, tr("msg_error"), msg)
        self._btn_polish.setEnabled(True)
        self._btn_polish.setText(tr("btn_polish_text"))

    def _on_copy_output(self):
        t = self._txt_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            self._lbl_status.setText(tr("msg_copied"))

    # ──────────────────────────────────────────────────
    #  Internal Helpers
    # ──────────────────────────────────────────────────

    def _push_proxy(self):
        """Push an updated proxy image to the canvas after adjustment changes."""
        if not self._image_processor.has_master():
            return
        proxy = self._image_processor.get_proxy(
            self._brightness, self._contrast, self._sharpness
        )
        if proxy:
            self._canvas_engine.update_photo_proxy(proxy)

    def _load_image(self, path):
        """Load any supported image format and return as RGBA PIL Image."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".svg":
            try:
                import cairosvg

                data = cairosvg.svg2png(url=path)
                return Image.open(io.BytesIO(data)).convert("RGBA")
            except ImportError:
                raise RuntimeError("SVG requires 'cairosvg'.  pip install cairosvg")
        if ext == ".pdf":
            try:
                import fitz

                doc = fitz.open(path)
                pix = doc[0].get_pixmap(dpi=300)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                return img.convert("RGBA")
            except ImportError:
                raise RuntimeError("PDF requires 'PyMuPDF'.  pip install PyMuPDF")
        return Image.open(path).convert("RGBA")

    def _refresh_template_list(self):
        self._combo_template.blockSignals(True)
        self._combo_template.clear()
        names = self._template_manager.get_names()
        if names:
            self._combo_template.addItems(names)
        self._combo_template.blockSignals(False)

    def _refresh_model_list(self):
        self._combo_model.clear()
        prov = self._combo_provider.currentText()
        if prov == "Ollama":
            try:
                from app.text_engine import TextEngine

                models = TextEngine.get_ollama_models()
                self._combo_model.addItems(models if models else ["No models found"])
            except Exception:
                self._combo_model.addItem("No models found")
        else:
            try:
                from app.text_engine import TextEngine

                self._combo_model.addItems(TextEngine.PAID_MODELS)
            except Exception:
                self._combo_model.addItems(["gpt-4o", "gemini-1.5-pro"])

    def _update_ai_status_label(self):
        if self._gpu_engine is None:
            self._lbl_ai_status.setText(tr("msg_cpu_fallback"))
            return
        try:
            import torch  # noqa: F401

            self._lbl_ai_status.setText(tr("msg_torch_fallback"))
        except ImportError:
            self._lbl_ai_status.setText(tr("msg_cpu_fallback"))

    def _export_size(self, template_img):
        """Return (w, h) based on the current export preset selection."""
        idx = self._combo_preset.currentIndex()
        vals = list(INSTAGRAM_PRESETS.values())
        if idx == 0:
            return template_img.size
        if 1 <= idx <= len(vals):
            return vals[idx - 1]
        return self._spin_w.value(), self._spin_h.value()

    def _sync_export_crop(self):
        tname = self._combo_template.currentText()
        timg = self._template_manager.get_template_image(tname)
        if timg is None:
            return
        w, h = self._export_size(timg)
        self._canvas_engine.set_export_size(w, h)

    def _update_status(self):
        parts = []
        if self._image_processor.has_master():
            w, h = self._image_processor.get_master_size()
            parts.append(f"Photo: {w}×{h}")
        tname = self._combo_template.currentText()
        if tname:
            ts = self._template_manager.get_template_size(tname)
            if ts:
                parts.append(f"Template: {ts[0]}×{ts[1]}")
        self._lbl_status.setText("  │  ".join(parts) if parts else "Ready")

    # ──────────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────────

    def run(self):
        """Show the window maximized."""
        self.showMaximized()


if __name__ == "__main__":
    from app import theme as _t

    app = QApplication(sys.argv)
    app.setStyleSheet(_t.get_theme(dark=True))
    win = PhotoTemplateStudioPro()
    win.run()
    sys.exit(app.exec())
