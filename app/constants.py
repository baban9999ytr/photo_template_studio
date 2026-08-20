import os
import sys
import platform

APP_NAME = "PhotoTemplateStudioPro"
APP_VERSION = "2.0.0"
APP_WINDOW_TITLE = "Photo Template Studio Pro"
APP_GEOMETRY = "1420x900"
APP_MIN_SIZE = (1200, 750)

AUTHOR_NAME = "Mustafa Göksal"
GITHUB_REPO_URL = "https://github.com/baban9999ytr/PictureFormatter"

CANVAS_PREVIEW_SIZE = 700
PROXY_MAX_DIM = 1200
DEFAULT_EXPORT_QUALITY = 100
ZOOM_IN_FACTOR = 1.02
ZOOM_OUT_FACTOR = 1.0 / 1.02
MIN_SCALE = 0.05
MAX_SCALE = 20.0
RENDER_DEBOUNCE_MS = 16
ADJUSTMENT_DEBOUNCE_MS = 50
SLIDER_MIN = 0.0
SLIDER_MAX = 2.0
SLIDER_DEFAULT = 1.0
BRUSH_SIZE_MIN = 1
BRUSH_SIZE_MAX = 20
BRUSH_SIZE_DEFAULT = 3
FONT_SIZE_MIN = 10
FONT_SIZE_MAX = 120
FONT_SIZE_DEFAULT = 30

ZOOM_STEP_MIN = 0.1
ZOOM_STEP_MAX = 5.0
ZOOM_STEP_DEFAULT = 1.0

SIDEBAR_LEFT_WIDTH = 280
SIDEBAR_RIGHT_WIDTH = 260

INSTAGRAM_PRESETS = {
    "IG Square": (1080, 1080),
    "IG Portrait": (1080, 1350),
    "IG Story": (1080, 1920),
}

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".pdf", ".svg"}

IMAGE_FILETYPES = [
    ("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.heic *.pdf *.svg"),
    ("PNG", "*.png"),
    ("JPEG", "*.jpg *.jpeg"),
    ("HEIC", "*.heic"),
    ("PDF", "*.pdf"),
    ("SVG", "*.svg"),
    ("WebP", "*.webp"),
]

TEMPLATE_FILETYPES = [("PNG Images", "*.png")]

EXPORT_FILETYPES = [
    ("JPEG Image", "*.jpg"),
    ("PNG Image", "*.png"),
    ("HEIC Image", "*.heic"),
]

ACCENT_COLOR = "#e94560"
ACCENT_HOVER = "#c73e54"
SUCCESS_COLOR = "#2ecc71"
WARNING_COLOR = "#f39c12"

FONT_FALLBACK_CHAIN = [
    "arial.ttf",
    "Arial.ttf",
    "Arial",
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNSText.ttf",
]

ESRGAN_MODEL_URLS = {
    "RealESRGAN_x4plus": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.1.0/RealESRGAN_x4plus.pth"
    ),
    "RealESRGAN_x2plus": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.1/RealESRGAN_x2plus.pth"
    ),
    "RealESRGAN_x4plus_anime_6B": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
    ),
}

OLLAMA_API_URL = "http://localhost:11434"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

TEXT_TONES = ["Formal Business", "Casual", "Energetic"]
TEXT_LENGTHS = ["Short", "Medium", "Long"]

I18N = {
    "en": {
        "tab_photo": "Photo Studio",
        "tab_text": "Text Studio",
        "tab_vector": "Document / Vector",
        "app_subtitle": "Photo Template Engine v2.0",
        "lbl_template": "TEMPLATE",
        "btn_add_template": "＋  Add Template",
        "lbl_framing_mode": "FRAMING MODE",
        "mode_pan_zoom": "Pan & Zoom",
        "mode_auto_fit": "Auto Fit",
        "lbl_photo": "PHOTO",
        "btn_load_photo": "📷   Load Photo",
        "lbl_no_photo": "No photo loaded",
        "lbl_tools": "TOOLS",
        "btn_move": "✥  Move",
        "btn_draw": "✏  Draw",
        "btn_text": "T  Text",
        "lbl_brush": "Brush",
        "txt_placeholder": "Type annotation text…",
        "lbl_font_size": "Font size",
        "btn_clear_annotations": "Clear Annotations",
        "lbl_developed_by": f"Developed by {AUTHOR_NAME}",
        "btn_github": "View on GitHub",
        "switch_dark_mode": "Dark Mode",
        "lbl_adjustments": "ADJUSTMENTS",
        "lbl_brightness": "Brightness",
        "lbl_contrast": "Contrast",
        "lbl_sharpness": "Sharpness",
        "lbl_zoom_step": "Zoom Speed",
        "btn_reset_all": "↺  Reset All",
        "lbl_ai_upscale": "AI UPSCALE",
        "switch_enable": "Enable",
        "msg_esrgan_ready": "✓  Real-ESRGAN ready",
        "msg_torch_fallback": "△  Torch bicubic (no ESRGAN)",
        "msg_cpu_fallback": "○  CPU / Pillow fallback",
        "lbl_export": "EXPORT",
        "btn_original_size": "Original Size",
        "btn_save_image": "Save Image",
        "btn_batch_process": "Batch Process Directory",
        "lbl_model_provider": "Model Provider:",
        "lbl_model": "Model:",
        "btn_edit_env": "⚙ Edit .env",
        "lbl_tone": "Tone:",
        "lbl_length": "Length:",
        "lbl_custom_prompt": "Custom Instruction (Optional):",
        "lbl_rough_input": "Rough Text Input",
        "lbl_polished_output": "Polished Output",
        "btn_polish_text": "Polish Text",
        "btn_copy_output": "Copy Output",
        "msg_select_template": "Select a template to begin",
        "msg_error": "Error",
        "msg_success": "Success",
        "msg_warning": "Warning",
        "msg_enter_text": "Please enter some text to polish.",
        "msg_api_key_required": "API Key is required for Paid APIs. Please click 'Edit .env' to add it.",
        "msg_generating": "Generating...",
        "msg_done": "Done!",
        "msg_copied": "Copied to clipboard!",
        "msg_batch_starting": "Starting batch…",
        "msg_batch_processing": "Processing {current} / {total}…",
        "msg_batch_complete": "Successfully processed {count} image(s)!",
        "tone_prompt_formal": (
            "You are an expert social media manager for a corporate brand. "
            "Your task is to take informal, rough text and rewrite it into a highly professional, "
            "formal business paragraph in English. It must be polished, grammatically perfect, "
            "and optimized for Instagram posts or Reels descriptions. "
            "Maintain all original facts and details, but elevate the language to be corporate and respectable."
        ),
        "tone_prompt_casual": (
            "You are a friendly social media manager. "
            "Take the rough input text and rewrite it into a casual, engaging, and friendly paragraph in English, "
            "perfect for Instagram posts or Reels. Use emojis tastefully and keep it easy to read."
        ),
        "tone_prompt_energetic": (
            "You are a high-energy, exciting social media influencer. "
            "Take the rough input text and rewrite it into an enthusiastic, energetic, and captivating paragraph "
            "in English for Instagram or Reels. Use exciting language, emojis, and strong hooks!"
        ),
    },
    "tr": {
        "tab_photo": "Fotoğraf Stüdyosu",
        "tab_text": "Metin Stüdyosu",
        "tab_vector": "Belge / Vektör",
        "app_subtitle": "Fotoğraf Şablon Motoru v2.0",
        "lbl_template": "ŞABLON",
        "btn_add_template": "＋  Şablon Ekle",
        "lbl_framing_mode": "ÇERÇEVE MODU",
        "mode_pan_zoom": "Kaydır ve Yakınlaştır",
        "mode_auto_fit": "Otomatik Sığdır",
        "lbl_photo": "FOTOĞRAF",
        "btn_load_photo": "📷   Fotoğraf Yükle",
        "lbl_no_photo": "Fotoğraf yüklenmedi",
        "lbl_tools": "ARAÇLAR",
        "btn_move": "✥  Taşı",
        "btn_draw": "✏  Çiz",
        "btn_text": "T  Metin",
        "lbl_brush": "Fırça",
        "txt_placeholder": "Ek açıklama metni yazın…",
        "lbl_font_size": "Yazı boyutu",
        "btn_clear_annotations": "Ek Açıklamaları Temizle",
        "lbl_developed_by": f"{AUTHOR_NAME} Tarafından Geliştirildi",
        "btn_github": "GitHub'da Görüntüle",
        "switch_dark_mode": "Karanlık Mod",
        "lbl_adjustments": "AYARLAMALAR",
        "lbl_brightness": "Parlaklık",
        "lbl_contrast": "Kontrast",
        "lbl_sharpness": "Keskinlik",
        "lbl_zoom_step": "Yakınlaştırma Hızı",
        "btn_reset_all": "↺  Tümünü Sıfırla",
        "lbl_ai_upscale": "YAPAY ZEKA ÇÖZÜNÜRLÜK",
        "switch_enable": "Etkinleştir",
        "msg_esrgan_ready": "✓  Real-ESRGAN hazır",
        "msg_torch_fallback": "△  Torch bicubic (ESRGAN yok)",
        "msg_cpu_fallback": "○  CPU / Pillow yedeği",
        "lbl_export": "DIŞA AKTAR",
        "btn_original_size": "Orijinal Boyut",
        "btn_save_image": "Resmi Kaydet",
        "btn_batch_process": "Toplu İşlem (Klasör)",
        "lbl_model_provider": "Model Sağlayıcı:",
        "lbl_model": "Model:",
        "btn_edit_env": "⚙ .env Düzenle",
        "lbl_tone": "Ton:",
        "lbl_length": "Uzunluk:",
        "lbl_custom_prompt": "Özel Talimat (İsteğe Bağlı):",
        "lbl_rough_input": "Ham Metin Girdisi",
        "lbl_polished_output": "Düzenlenmiş Çıktı",
        "btn_polish_text": "Metni Düzenle",
        "btn_copy_output": "Çıktıyı Kopyala",
        "msg_select_template": "Başlamak için bir şablon seçin",
        "msg_error": "Hata",
        "msg_success": "Başarılı",
        "msg_warning": "Uyarı",
        "msg_enter_text": "Lütfen düzenlenecek bir metin girin.",
        "msg_api_key_required": "Ücretli API'ler için API Anahtarı gereklidir. Eklemek için '.env Düzenle' butonuna tıklayın.",
        "msg_generating": "Oluşturuluyor...",
        "msg_done": "Tamamlandı!",
        "msg_copied": "Panoya kopyalandı!",
        "msg_batch_starting": "Toplu işlem başlatılıyor…",
        "msg_batch_processing": "İşleniyor {current} / {total}…",
        "msg_batch_complete": "{count} resim başarıyla işlendi!",
        "tone_prompt_formal": (
            "Türkiye'deki kurumsal bir marka için uzman bir sosyal medya yöneticisisin. "
            "Görevin, gayriresmi ve ham metni alıp, son derece profesyonel ve resmi bir "
            "kurumsal Türkçe paragrafa dönüştürmektir. Metin kusursuz, dilbilgisi kurallarına uygun "
            "ve Instagram gönderileri veya Reels açıklamaları için optimize edilmiş olmalıdır. "
            "Tüm orijinal detayları koru, ancak dili kurumsal ve saygın bir seviyeye yükselt."
        ),
        "tone_prompt_casual": (
            "Sen samimi bir sosyal medya yöneticisisin. "
            "Ham metni al ve Instagram gönderileri veya Reels için mükemmel, rahat, etkileşimli "
            "ve samimi bir Türkçe paragrafa dönüştür. Emojileri zevkli bir şekilde kullan ve okunmasını kolaylaştır."
        ),
        "tone_prompt_energetic": (
            "Sen Türkiye'de yüksek enerjili, heyecan verici bir sosyal medya fenomenisin. "
            "Ham metni al ve Instagram veya Reels için coşkulu, enerjik ve büyüleyici bir Türkçe paragrafa dönüştür. "
            "Heyecan verici bir dil, bol emojiler ve güçlü kancalar (hooks) kullan!"
        ),
    },
    "fr": {
        "tab_photo": "Studio Photo",
        "tab_text": "Studio Texte",
        "tab_vector": "Document / Vecteur",
        "app_subtitle": "Moteur de Modèles Photo v2.0",
        "lbl_template": "MODÈLE",
        "btn_add_template": "＋  Ajouter un Modèle",
        "lbl_framing_mode": "MODE DE CADRAGE",
        "mode_pan_zoom": "Déplacer et Zoomer",
        "mode_auto_fit": "Ajustement Auto",
        "lbl_photo": "PHOTO",
        "btn_load_photo": "📷   Charger une Photo",
        "lbl_no_photo": "Aucune photo chargée",
        "lbl_tools": "OUTILS",
        "btn_move": "✥  Déplacer",
        "btn_draw": "✏  Dessiner",
        "btn_text": "T  Texte",
        "lbl_brush": "Pinceau",
        "txt_placeholder": "Saisissez le texte d'annotation…",
        "lbl_font_size": "Taille de police",
        "btn_clear_annotations": "Effacer les Annotations",
        "lbl_developed_by": f"Développé par {AUTHOR_NAME}",
        "btn_github": "Voir sur GitHub",
        "switch_dark_mode": "Mode Sombre",
        "lbl_adjustments": "RÉGLAGES",
        "lbl_brightness": "Luminosité",
        "lbl_contrast": "Contraste",
        "lbl_sharpness": "Netteté",
        "lbl_zoom_step": "Vitesse de Zoom",
        "btn_reset_all": "↺  Tout Réinitialiser",
        "lbl_ai_upscale": "IA MISE À L'ÉCHELLE",
        "switch_enable": "Activer",
        "msg_esrgan_ready": "✓  Real-ESRGAN prêt",
        "msg_torch_fallback": "△  Torch bicubique (pas d'ESRGAN)",
        "msg_cpu_fallback": "○  CPU / Pillow secours",
        "lbl_export": "EXPORTER",
        "btn_original_size": "Taille Originale",
        "btn_save_image": "Enregistrer l'Image",
        "btn_batch_process": "Traitement par Lot",
        "lbl_model_provider": "Fournisseur :",
        "lbl_model": "Modèle :",
        "btn_edit_env": "⚙ Éditer .env",
        "lbl_tone": "Ton :",
        "lbl_length": "Longueur :",
        "lbl_custom_prompt": "Instruction Personnalisée (Optionnel) :",
        "lbl_rough_input": "Texte Brut",
        "lbl_polished_output": "Texte Poli",
        "btn_polish_text": "Polir le Texte",
        "btn_copy_output": "Copier la Sortie",
        "msg_select_template": "Sélectionnez un modèle pour commencer",
        "msg_error": "Erreur",
        "msg_success": "Succès",
        "msg_warning": "Avertissement",
        "msg_enter_text": "Veuillez entrer du texte à polir.",
        "msg_api_key_required": "Une clé API est requise. Cliquez sur 'Éditer .env' pour l'ajouter.",
        "msg_generating": "Génération en cours...",
        "msg_done": "Terminé !",
        "msg_copied": "Copié dans le presse-papiers !",
        "msg_batch_starting": "Début du traitement par lot…",
        "msg_batch_processing": "Traitement {current} / {total}…",
        "msg_batch_complete": "{count} image(s) traitée(s) avec succès !",
        "tone_prompt_formal": (
            "Vous êtes un gestionnaire expert de réseaux sociaux pour une marque d'entreprise. "
            "Votre tâche est de prendre un texte brut et informel et de le réécrire en un paragraphe "
            "professionnel et formel en français. Il doit être impeccable, grammaticalement parfait "
            "et optimisé pour les publications Instagram ou les descriptions de Reels."
        ),
        "tone_prompt_casual": (
            "Vous êtes un gestionnaire de réseaux sociaux sympathique. "
            "Prenez le texte brut et réécrivez-le en un paragraphe décontracté, engageant "
            "et amical en français, parfait pour Instagram ou les Reels. "
            "Utilisez des emojis avec goût et gardez le texte facile à lire."
        ),
        "tone_prompt_energetic": (
            "Vous êtes un influenceur de réseaux sociaux plein d'énergie. "
            "Prenez le texte brut et réécrivez-le en un paragraphe enthousiaste, "
            "énergique et captivant en français pour Instagram ou les Reels. "
            "Utilisez un langage excitant, des emojis et des accroches puissantes !"
        ),
    }
}

def get_system_prompt(lang, tone, length="Medium", custom_inject=""):
    base_prompt = ""
    if tone == "Formal Business":
        base_prompt = I18N[lang]["tone_prompt_formal"]
    elif tone == "Casual":
        base_prompt = I18N[lang]["tone_prompt_casual"]
    elif tone == "Energetic":
        base_prompt = I18N[lang]["tone_prompt_energetic"]
    else:
        base_prompt = I18N[lang]["tone_prompt_formal"]
        
    length_instruction = f" The target length of the output should be: {length}."
    prompt = base_prompt + length_instruction
    
    if custom_inject:
        prompt += f"\n\nAdditionally, adhere to the following custom instruction: {custom_inject}"
        
    return prompt


def get_models_dir():
    home = os.path.expanduser("~")
    models_dir = os.path.join(home, ".photostudiopro", "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def get_app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_env_file_path():
    return os.path.join(get_app_base_dir(), ".env")


def resolve_template_path(path):
    if os.path.isabs(path) and os.path.exists(path):
        return path
    base = get_app_base_dir()
    resolved = os.path.join(base, path)
    if os.path.exists(resolved):
        return resolved
    return path


def get_platform():
    return platform.system().lower()
