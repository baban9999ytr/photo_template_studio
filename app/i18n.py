"""
Internationalization module for Photo Template Studio Pro.
Provides dynamic language switching using locale dictionaries from constants.py.
All UI text should go through tr() for automatic translation support.
"""

from app.constants import I18N

_current_lang = "en"
_callbacks = []

# Display names for the language selector UI
LANGUAGE_NAMES = {
    "en": "English",
    "tr": "Türkçe",
    "fr": "Français",
}


def set_language(lang):
    """Set the active language and notify all registered listeners."""
    global _current_lang
    if lang in I18N:
        _current_lang = lang
        for cb in _callbacks:
            try:
                cb()
            except Exception:
                pass


def get_language():
    """Return the current language code."""
    return _current_lang


def tr(key, **kwargs):
    """Translate a key to the current language with automatic English fallback.

    Usage:
        tr("btn_save_image")           -> "Save Image"
        tr("msg_batch_processing", current=3, total=10) -> "Processing 3 / 10…"
    """
    text = I18N.get(_current_lang, {}).get(key)
    if text is None:
        text = I18N.get("en", {}).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def on_language_changed(callback):
    """Register a callback to be invoked when the language changes."""
    if callback not in _callbacks:
        _callbacks.append(callback)


def remove_callback(callback):
    """Remove a previously registered language change callback."""
    if callback in _callbacks:
        _callbacks.remove(callback)


def available_languages():
    """Return a list of available language codes that have translations."""
    return [lang for lang in LANGUAGE_NAMES if lang in I18N]


def get_display_name(code):
    """Return the human-readable display name for a language code."""
    return LANGUAGE_NAMES.get(code, code)
