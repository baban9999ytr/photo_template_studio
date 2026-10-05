import os

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

from app.constants import DEFAULT_EXPORT_QUALITY, SUPPORTED_IMAGE_EXTENSIONS


class ExportPipeline:

    def __init__(self, gpu_engine, image_processor, annotation_engine):
        self._gpu = gpu_engine
        self._processor = image_processor
        self._annotations = annotation_engine

    def export_single(
        self,
        photo_master,
        template_image,
        mode,
        photo_scale,
        photo_offset_x,
        photo_offset_y,
        template_scale,
        template_offset_x,
        template_offset_y,
        brightness,
        contrast,
        sharpness,
        target_w,
        target_h,
        save_path,
        use_ai_upscale=False,
        ai_scale=4,
    ):
        tw, th = template_image.size
        original_w, original_h = photo_master.size
        final = Image.new("RGBA", (tw, th), (255, 255, 255, 0))

        adjusted = self._apply_adjustments(
            photo_master, brightness, contrast, sharpness
        )

        if use_ai_upscale:
            try:
                adjusted = self._gpu.upscale(adjusted, scale=ai_scale, use_esrgan=True)
            except Exception:
                pass

        if mode == "auto_fit":
            fit_photo = ImageOps.fit(
                adjusted, (tw, th), method=Image.Resampling.LANCZOS
            )
            final.paste(fit_photo.convert("RGBA"), (0, 0))
        else:
            render_w = max(1, int(original_w * photo_scale))
            render_h = max(1, int(original_h * photo_scale))
            resized = adjusted.resize((render_w, render_h), Image.Resampling.LANCZOS)

            paste_x = (tw // 2) - (render_w // 2) + int(photo_offset_x)
            paste_y = (th // 2) - (render_h // 2) + int(photo_offset_y)

            layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            layer.paste(resized.convert("RGBA"), (paste_x, paste_y))
            final = Image.alpha_composite(final, layer)

        template_w = max(1, int(tw * template_scale))
        template_h = max(1, int(th * template_scale))
        resized_template = template_image.resize(
            (template_w, template_h), Image.Resampling.LANCZOS
        )
        template_paste_x = (tw // 2) - (template_w // 2) + int(template_offset_x)
        template_paste_y = (th // 2) - (template_h // 2) + int(template_offset_y)

        template_layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        template_layer.paste(
            resized_template.convert("RGBA"), (template_paste_x, template_paste_y)
        )
        final = Image.alpha_composite(final, template_layer)

        if self._annotations.has_annotations():
            draw = ImageDraw.Draw(final)
            self._annotations.render_to_export(draw, tw, th)

        if (target_w, target_h) != (tw, th):
            final = ImageOps.fit(
                final, (target_w, target_h), method=Image.Resampling.LANCZOS
            )

        self._save_image(final, save_path)
        return True

    def batch_process(
        self,
        input_dir,
        output_dir,
        template_image,
        template_scale,
        template_offset_x,
        template_offset_y,
        brightness,
        contrast,
        sharpness,
        use_ai_upscale=False,
        ai_scale=4,
        progress_callback=None,
    ):
        os.makedirs(output_dir, exist_ok=True)

        files = sorted(
            [
                f
                for f in os.listdir(input_dir)
                if os.path.splitext(f)[1].lower() in SUPPORTED_IMAGE_EXTENSIONS
            ]
        )
        total = len(files)
        if total == 0:
            return 0

        tw, th = template_image.size

        template_w = max(1, int(tw * template_scale))
        template_h = max(1, int(th * template_scale))
        resized_template = template_image.resize(
            (template_w, template_h), Image.Resampling.LANCZOS
        )
        template_paste_x = (tw // 2) - (template_w // 2) + int(template_offset_x)
        template_paste_y = (th // 2) - (template_h // 2) + int(template_offset_y)
        template_layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        template_layer.paste(
            resized_template.convert("RGBA"), (template_paste_x, template_paste_y)
        )

        processed = 0

        for i, fname in enumerate(files):
            try:
                input_path = os.path.join(input_dir, fname)
                photo = Image.open(input_path).convert("RGBA")

                adjusted = self._apply_adjustments(
                    photo, brightness, contrast, sharpness
                )

                if use_ai_upscale:
                    try:
                        adjusted = self._gpu.upscale(
                            adjusted, scale=ai_scale, use_esrgan=True
                        )
                    except Exception:
                        pass

                fit_photo = ImageOps.fit(
                    adjusted, (tw, th), method=Image.Resampling.LANCZOS
                )

                final = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
                final.paste(fit_photo.convert("RGBA"), (0, 0))
                final = Image.alpha_composite(final, template_layer)

                base_name = os.path.splitext(fname)[0]
                output_path = os.path.join(output_dir, f"{base_name}_templated.jpg")
                self._save_image(final, output_path)
                processed += 1
            except Exception:
                pass

            if progress_callback:
                progress_callback(i + 1, total)

        return processed

    @staticmethod
    def _apply_adjustments(image, brightness, contrast, sharpness):
        img = image.copy()
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
        return img

    @staticmethod
    def _save_image(image, path):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if path.lower().endswith(".png"):
            image.save(path, "PNG")
        elif path.lower().endswith(".heic"):
            try:
                import pillow_heif

                pillow_heif.register_heif_opener()
                image.save(path, "HEIC")
            except ImportError:
                raise RuntimeError(
                    "HEIC export failed. Please install 'pillow-heif' library."
                )
            except Exception as e:
                raise RuntimeError(f"HEIC export failed: {e}")
        else:
            rgb = image.convert("RGB")
            rgb.save(
                path,
                "JPEG",
                quality=DEFAULT_EXPORT_QUALITY,
                subsampling=0,
            )
