"""Icon drawing helpers for PDF output."""

ICON_SIZE = 4
ICON_COLORS = {
    "person": (52, 152, 219),
    "book": (39, 174, 96),
    "clock": (243, 156, 18),
    "info": (26, 188, 156),
    "link": (155, 89, 182),
    "star": (255, 204, 0)
}


def _pdf_draw_icon(pdf, kind, size, line_height):
    """Draw a simple icon and advance the cursor by its width."""
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    y_offset = y_start + (line_height - size) / 2
    x_mid = x_start + size / 2
    y_mid = y_offset + size / 2

    color = ICON_COLORS.get(kind, (0, 0, 0))
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.2)

    if kind == "person":
        head_size = size * 0.35
        head_x = x_start + (size - head_size) / 2
        head_y = y_offset
        pdf.ellipse(head_x, head_y, head_size, head_size)
        body_y = head_y + head_size + size * 0.1
        pdf.line(x_mid, body_y, x_mid, y_offset + size)
        arms_y = body_y + size * 0.2
        pdf.line(x_start + size * 0.2, arms_y, x_start + size * 0.8, arms_y)
    elif kind == "book":
        pdf.rect(x_start, y_offset, size, size)
        pdf.line(
            x_start + size * 0.45,
            y_offset,
            x_start + size * 0.45,
            y_offset + size
        )
    elif kind == "clock":
        pdf.ellipse(x_start, y_offset, size, size)
        pdf.line(x_mid, y_mid, x_mid, y_offset + size * 0.25)
        pdf.line(x_mid, y_mid, x_start + size * 0.75, y_mid)
    elif kind == "info":
        pdf.ellipse(x_start, y_offset, size, size)
        dot_size = size * 0.15
        pdf.set_fill_color(*color)
        pdf.ellipse(
            x_mid - dot_size / 2,
            y_offset + size * 0.25,
            dot_size,
            dot_size,
            style="F"
        )
        pdf.line(x_mid, y_offset + size * 0.45, x_mid, y_offset + size * 0.8)
    elif kind == "link":
        ring = size * 0.45
        left_x = x_start
        right_x = x_start + size - ring
        pdf.ellipse(left_x, y_offset, ring, ring)
        pdf.ellipse(right_x, y_offset, ring, ring)
        pdf.line(
            left_x + ring * 0.7,
            y_offset + ring * 0.7,
            right_x + ring * 0.3,
            y_offset + ring * 0.3
        )
    elif kind == "star":
        points = [
            (x_mid, y_offset),
            (x_mid + size * 0.2, y_offset + size * 0.35),
            (x_start + size, y_offset + size * 0.4),
            (x_mid + size * 0.3, y_offset + size * 0.6),
            (x_mid + size * 0.45, y_offset + size),
            (x_mid, y_offset + size * 0.75),
            (x_mid - size * 0.45, y_offset + size),
            (x_mid - size * 0.3, y_offset + size * 0.6),
            (x_start, y_offset + size * 0.4),
            (x_mid - size * 0.2, y_offset + size * 0.35)
        ]
        pdf.set_fill_color(*color)
        pdf.polygon(points, style="F")

    advance = size + 2
    pdf.set_xy(x_start + advance, y_start)
    pdf.set_draw_color(0, 0, 0)
    return advance
