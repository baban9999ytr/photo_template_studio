import sys

def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
    except ImportError:
        print(
            "ERROR: PySide6 is required.\n"
            "Install it with:  pip install PySide6"
        )
        sys.exit(1)
        
    app = QApplication(sys.argv)
    
    from app import theme
    app.setStyleSheet(theme.get_theme(dark=True))
    
    from app.application import PhotoTemplateStudioPro

    window = PhotoTemplateStudioPro()
    window.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()