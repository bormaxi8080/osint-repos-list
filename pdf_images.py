"""Image helpers for PDF output."""

import os


def _get_image_dimensions(path):
    """Return (width, height) in pixels for PNG/JPEG images."""
    try:
        with open(path, "rb") as handle:
            signature = handle.read(8)
            if signature == b"\x89PNG\r\n\x1a\n":
                handle.read(4)
                chunk_type = handle.read(4)
                if chunk_type != b"IHDR":
                    return None
                width = int.from_bytes(handle.read(4), "big")
                height = int.from_bytes(handle.read(4), "big")
                return width, height
            if signature[:2] != b"\xFF\xD8":
                return None
            handle.seek(2)
            while True:
                marker = handle.read(2)
                if len(marker) < 2:
                    return None
                while marker[0] != 0xFF:
                    marker = marker[1:] + handle.read(1)
                while marker[1] == 0xFF:
                    marker = b"\xFF" + handle.read(1)
                marker_type = marker[1]
                if marker_type in (
                    0xC0, 0xC1, 0xC2, 0xC3,
                    0xC5, 0xC6, 0xC7,
                    0xC9, 0xCA, 0xCB,
                    0xCD, 0xCE, 0xCF
                ):
                    length = int.from_bytes(handle.read(2), "big")
                    if length < 7:
                        return None
                    handle.read(1)
                    height = int.from_bytes(handle.read(2), "big")
                    width = int.from_bytes(handle.read(2), "big")
                    return width, height
                length = int.from_bytes(handle.read(2), "big")
                if length < 2:
                    return None
                handle.seek(length - 2, 1)
    except OSError:
        return None
    return None


def _draw_header_image(pdf, image_path, y_top, text_width, max_width, line_height):
    """Draw a header image to the right of two lines of text."""
    if not image_path or not os.path.isfile(image_path):
        return
    dimensions = _get_image_dimensions(image_path)
    if not dimensions:
        return
    img_width_px, img_height_px = dimensions
    if img_width_px <= 0 or img_height_px <= 0:
        return
    padding = 3
    max_image_width = max_width - text_width - padding
    if max_image_width <= 0:
        return
    target_height = line_height * 2
    aspect_ratio = img_width_px / img_height_px
    image_width = target_height * aspect_ratio
    image_height = target_height
    if image_width > max_image_width:
        image_width = max_image_width
        image_height = image_width / aspect_ratio
    if image_width <= 0 or image_height <= 0:
        return
    x_pos = pdf.l_margin + text_width + padding
    current_x = pdf.get_x()
    current_y = pdf.get_y()
    pdf.image(image_path, x=x_pos, y=y_top, w=image_width, h=image_height)
    pdf.set_xy(current_x, current_y)
