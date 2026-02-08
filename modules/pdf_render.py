"""Rendering helpers for PDF output."""

from urllib.parse import quote

from .pdf_fpdf import XPos, YPos
from .pdf_fonts import _set_pdf_font
from .pdf_icons import ICON_SIZE, _pdf_draw_icon
from .pdf_sanitize import _sanitize_pdf_text
from .pdf_wrap import _wrap_pdf_lines, _wrap_pdf_lines_with_first_width


def _pdf_write_wrapped_text(pdf, text, max_width, line_height=5, spacing=0):
    """Write wrapped text to PDF with optional spacing."""
    sanitized = _sanitize_pdf_text(text, pdf)
    for line in _wrap_pdf_lines(pdf, sanitized, max_width):
        if line.strip() == "":
            pdf.ln(line_height)
            continue
        pdf.cell(
            0,
            line_height,
            text=line,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
    if spacing > 0:
        pdf.ln(spacing)


def _pdf_write_label_with_link(
    pdf,
    label,
    link_text,
    link_url,
    max_width,
    line_height=5
):
    """Write a label and clickable link, wrapping as needed."""
    label_text = _sanitize_pdf_text(label, pdf)
    link_text_sanitized = _sanitize_pdf_text(link_text, pdf)

    pdf.set_text_color(0, 0, 0)
    label_width = pdf.get_string_width(label_text)
    link_width = pdf.get_string_width(link_text_sanitized)

    if label_text == "":
        pdf.set_text_color(0, 0, 255)
        for line in _wrap_pdf_lines(pdf, link_text_sanitized, max_width):
            if line.strip() == "":
                pdf.ln(line_height)
                continue
            pdf.cell(
                0,
                line_height,
                text=line,
                link=link_url,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT
            )
        pdf.set_text_color(0, 0, 0)
        return

    if label_width + link_width <= max_width:
        pdf.cell(label_width, line_height, text=label_text)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(
            0,
            line_height,
            text=link_text_sanitized,
            link=link_url,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        pdf.set_text_color(0, 0, 0)
        return

    if label_text != "":
        pdf.cell(
            0,
            line_height,
            text=label_text,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
    pdf.set_text_color(0, 0, 255)
    for line in _wrap_pdf_lines(pdf, link_text_sanitized, max_width):
        if line.strip() == "":
            pdf.ln(line_height)
            continue
        pdf.cell(
            0,
            line_height,
            text=line,
            link=link_url,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
    pdf.set_text_color(0, 0, 0)


def _pdf_write_bold_label_with_link(
    pdf,
    label,
    link_text,
    link_url,
    max_width,
    line_height=5
):
    """Write a bold label and clickable link, wrapping as needed."""
    pdf.set_text_color(0, 0, 0)
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)

    _set_pdf_font(pdf, bold=False, size=11)
    link_text_sanitized = _sanitize_pdf_text(link_text, pdf)
    link_width = pdf.get_string_width(link_text_sanitized)

    if label_text == "":
        pdf.set_text_color(0, 0, 255)
        for line in _wrap_pdf_lines(pdf, link_text_sanitized, max_width):
            if line.strip() == "":
                pdf.ln(line_height)
                continue
            pdf.cell(
                0,
                line_height,
                text=line,
                link=link_url,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT
            )
        pdf.set_text_color(0, 0, 0)
        return

    if label_width + link_width <= max_width:
        _set_pdf_font(pdf, bold=True, size=11)
        pdf.cell(label_width, line_height, text=label_text)
        _set_pdf_font(pdf, bold=False, size=11)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(
            0,
            line_height,
            text=link_text_sanitized,
            link=link_url,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        pdf.set_text_color(0, 0, 0)
        return

    _set_pdf_font(pdf, bold=True, size=11)
    pdf.cell(
        0,
        line_height,
        text=label_text,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT
    )
    _set_pdf_font(pdf, bold=False, size=11)
    pdf.set_text_color(0, 0, 255)
    for line in _wrap_pdf_lines(pdf, link_text_sanitized, max_width):
        if line.strip() == "":
            pdf.ln(line_height)
            continue
        pdf.cell(
            0,
            line_height,
            text=line,
            link=link_url,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
    pdf.set_text_color(0, 0, 0)


def _pdf_write_bold_label_value(
    pdf,
    label,
    value,
    max_width,
    line_height=5,
    spacing=0
):
    """Write a bold label followed by a normal value, wrapping as needed."""
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    value_text = _sanitize_pdf_text(value, pdf)
    if label_width >= max_width:
        _set_pdf_font(pdf, bold=True, size=11)
        _pdf_write_wrapped_text(pdf, label_text, max_width, line_height=line_height)
        _set_pdf_font(pdf, bold=False, size=11)
        _pdf_write_wrapped_text(
            pdf,
            value_text,
            max_width,
            line_height=line_height,
            spacing=spacing
        )
        return

    _set_pdf_font(pdf, bold=True, size=11)
    pdf.cell(label_width, line_height, text=label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    first_width = max_width - label_width
    lines = _wrap_pdf_lines_with_first_width(pdf, value_text, first_width, max_width)
    if lines:
        pdf.cell(
            0,
            line_height,
            text=lines[0],
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        for line in lines[1:]:
            pdf.cell(
                0,
                line_height,
                text=line,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT
            )
    else:
        pdf.ln(line_height)
    if spacing > 0:
        pdf.ln(spacing)


def _pdf_write_icon_bold_label_value(
    pdf,
    icon_kind,
    label,
    value,
    max_width,
    line_height=5,
    spacing=0
):
    """Write a bold label with an icon and a normal value."""
    icon_advance = _pdf_draw_icon(pdf, icon_kind, ICON_SIZE, line_height)
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    value_text = _sanitize_pdf_text(value, pdf)
    if icon_advance + label_width >= max_width:
        pdf.ln(line_height)
        _pdf_write_bold_label_value(
            pdf,
            label,
            value,
            max_width,
            line_height=line_height,
            spacing=spacing
        )
        return

    _set_pdf_font(pdf, bold=True, size=11)
    pdf.cell(label_width, line_height, text=label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    first_width = max_width - icon_advance - label_width
    lines = _wrap_pdf_lines_with_first_width(pdf, value_text, first_width, max_width)
    if lines:
        pdf.cell(
            0,
            line_height,
            text=lines[0],
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        for line in lines[1:]:
            pdf.cell(
                0,
                line_height,
                text=line,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT
            )
    else:
        pdf.ln(line_height)
    if spacing > 0:
        pdf.ln(spacing)


def _pdf_write_icon_bold_label_with_link(
    pdf,
    icon_kind,
    label,
    link_text,
    link_url,
    max_width,
    line_height=5
):
    """Write a bold label with an icon and a clickable link."""
    icon_advance = _pdf_draw_icon(pdf, icon_kind, ICON_SIZE, line_height)
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    link_text_sanitized = _sanitize_pdf_text(link_text, pdf)
    link_width = pdf.get_string_width(link_text_sanitized)

    if icon_advance + label_width + link_width <= max_width:
        _set_pdf_font(pdf, bold=True, size=11)
        pdf.cell(label_width, line_height, text=label_text)
        _set_pdf_font(pdf, bold=False, size=11)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(
            0,
            line_height,
            text=link_text_sanitized,
            link=link_url,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        pdf.set_text_color(0, 0, 0)
        return

    _set_pdf_font(pdf, bold=True, size=11)
    pdf.cell(
        0,
        line_height,
        text=label_text,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT
    )
    _set_pdf_font(pdf, bold=False, size=11)
    pdf.set_text_color(0, 0, 255)
    first_width = max_width - icon_advance - label_width
    lines = _wrap_pdf_lines_with_first_width(
        pdf,
        link_text_sanitized,
        first_width,
        max_width
    )
    if lines:
        pdf.cell(
            0,
            line_height,
            text=lines[0],
            link=link_url,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT
        )
        for line in lines[1:]:
            pdf.cell(
                0,
                line_height,
                text=line,
                link=link_url,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT
            )
    else:
        pdf.ln(line_height)
    pdf.set_text_color(0, 0, 0)


def _pdf_write_icon_bold_label_links(
    pdf,
    icon_kind,
    label,
    tags,
    url_prefix,
    max_width,
    line_height=5,
    spacing=0
):
    """Write a bold label with an icon and clickable tag links."""
    icon_advance = _pdf_draw_icon(pdf, icon_kind, ICON_SIZE, line_height)
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    if icon_advance + label_width > max_width:
        pdf.ln(line_height)
        pdf.set_x(pdf.l_margin)
        icon_advance = 0

    pdf.cell(label_width, line_height, text=label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    pdf.set_text_color(0, 0, 255)

    space_width = pdf.get_string_width(" ")
    current_x = pdf.get_x()

    for tag in tags:
        tag_text = f"#{tag}"
        tag_text = _sanitize_pdf_text(tag_text, pdf)
        tag_url = f"{url_prefix}{quote(tag)}"
        tag_width = pdf.get_string_width(tag_text)

        if tag_width > max_width:
            chunks = _wrap_pdf_lines_with_first_width(
                pdf,
                tag_text,
                max_width,
                max_width
            )
            for chunk in chunks:
                if current_x != pdf.l_margin:
                    pdf.ln(line_height)
                    pdf.set_x(pdf.l_margin)
                pdf.cell(0, line_height, text=chunk, link=tag_url)
                pdf.ln(line_height)
                pdf.set_x(pdf.l_margin)
                current_x = pdf.get_x()
            continue

        if current_x - pdf.l_margin + tag_width > max_width:
            pdf.ln(line_height)
            pdf.set_x(pdf.l_margin)
            current_x = pdf.get_x()

        pdf.cell(tag_width, line_height, text=tag_text, link=tag_url)
        current_x += tag_width

        if current_x - pdf.l_margin + space_width > max_width:
            pdf.ln(line_height)
            pdf.set_x(pdf.l_margin)
            current_x = pdf.get_x()
        else:
            pdf.cell(space_width, line_height, text=" ")
            current_x += space_width

    pdf.set_text_color(0, 0, 0)
    if current_x != pdf.l_margin:
        pdf.ln(line_height)
    if spacing > 0:
        pdf.ln(spacing)


def _pdf_write_starred_bold_label_value(
    pdf,
    label,
    value,
    max_width,
    line_height=5,
    spacing=0
):
    """Write a yellow star, bold label, and normal value, wrapping as needed."""
    _pdf_write_icon_bold_label_value(
        pdf,
        "star",
        label,
        value,
        max_width,
        line_height=line_height,
        spacing=spacing
    )


def _pdf_draw_separator(pdf):
    """Draw a thin horizontal separator line."""
    x_start = pdf.l_margin
    x_end = pdf.w - pdf.r_margin
    y = pdf.get_y()
    pdf.set_draw_color(170, 170, 170)
    pdf.line(x_start, y, x_end, y)
    pdf.ln(4)
