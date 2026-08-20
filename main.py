import sys


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    try:
        import customtkinter as ctk
    except ImportError:
        print(
            "ERROR: customtkinter is required.\n"
            "Install it with:  pip install customtkinter"
        )
        sys.exit(1)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    from app.application import PhotoTemplateStudioPro

    app = PhotoTemplateStudioPro()
    app.mainloop()


if __name__ == "__main__":
    main()