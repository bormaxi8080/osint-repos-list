"""Header helpers for PDF output."""

import os

from pdf_fonts import _set_pdf_font
from pdf_images import _draw_header_image
from pdf_markdown import _pdf_write_markdown_bold_text_with_first_width
from pdf_render import (
    _pdf_draw_separator,
    _pdf_write_icon_bold_label_value,
    _pdf_write_label_with_link,
    _pdf_write_wrapped_text
)
from pdf_sanitize import _sanitize_pdf_text


def _pdf_write_warning(pdf, warning_text, max_width, line_height=5):
    """Write WARNING! in bold with the rest in normal text."""
    label = "WARNING!"
    _set_pdf_font(pdf, bold=False, size=11)
    text = _sanitize_pdf_text(warning_text.strip(), pdf)
    body = text[len(label):].lstrip() if text.startswith(label) else text
    label_text = f"{label} "

    _set_pdf_font(pdf, bold=True, size=11)
    label_width = pdf.get_string_width(label_text)
    pdf.cell(label_width, line_height, text=label_text)
    if body:
        first_width = max_width - label_width
        _pdf_write_markdown_bold_text_with_first_width(
            pdf,
            body,
            first_width,
            max_width,
            line_height=line_height,
            size=11
        )
        return
    pdf.ln(line_height)


def _write_created_at(pdf, document_date, max_width):
    """Write a bold 'Generated at' label with a normal date value."""
    date_label = "Generated at: "
    date_value = document_date
    if ":" in document_date:
        parts = document_date.split(":", 1)
        date_label = parts[0].strip() + ": "
        date_value = parts[1].strip()
    pdf.set_x(pdf.l_margin)
    _pdf_write_icon_bold_label_value(
        pdf,
        "clock",
        date_label,
        date_value,
        max_width,
        spacing=0
    )


def _write_header_section(
    pdf,
    config,
    document_date,
    max_width,
    include_warning=False,
    include_count=None,
    include_new_since=None
):
    """Write a common header section for the PDF pages."""
    _set_pdf_font(pdf, bold=True, size=16)
    _pdf_write_wrapped_text(
        pdf,
        config["header"],
        max_width,
        line_height=7,
        spacing=4
    )

    _set_pdf_font(pdf, bold=False, size=11)
    if config.get("description_text"):
        _pdf_write_wrapped_text(
            pdf,
            config["description_text"],
            max_width,
            spacing=2
        )
    _pdf_write_wrapped_text(
        pdf,
        config["generation_text"],
        max_width,
        spacing=1
    )
    _pdf_write_label_with_link(
        pdf,
        "",
        config["repo_url"],
        config["repo_url"],
        max_width
    )
    pdf.ln(5)
    _pdf_draw_separator(pdf)
    pdf.ln(2)
    if config.get("copyright_link_url"):
        line_height = 5
        y_top = pdf.get_y()
        _set_pdf_font(pdf, bold=True, size=11)
        copyright_text = _sanitize_pdf_text(config["copyright_text"], pdf)
        line1_width = pdf.get_string_width(copyright_text)
        _set_pdf_font(pdf, bold=False, size=11)
        link_prefix = config.get("copyright_link_prefix", "")
        link_text = config.get("copyright_link_text", config["copyright_link_url"])
        link_line = _sanitize_pdf_text(f"{link_prefix}{link_text}", pdf)
        line2_width = pdf.get_string_width(link_line)
        text_width = max(line1_width, line2_width)

        _set_pdf_font(pdf, bold=True, size=11)
        _pdf_write_wrapped_text(pdf, config["copyright_text"], max_width, spacing=1)
        _set_pdf_font(pdf, bold=False, size=11)
        _pdf_write_label_with_link(
            pdf,
            config.get("copyright_link_prefix", ""),
            config.get("copyright_link_text", config["copyright_link_url"]),
            config["copyright_link_url"],
            max_width
        )
        image_path = os.path.join(os.path.dirname(__file__), "img", "osintech.jpeg")
        _draw_header_image(pdf, image_path, y_top, text_width, max_width, line_height)
        pdf.ln(5)
    else:
        if config.get("copyright_bold"):
            _set_pdf_font(pdf, bold=True, size=11)
            _pdf_write_wrapped_text(
                pdf,
                config["copyright_text"],
                max_width,
                spacing=0
            )
            _set_pdf_font(pdf, bold=False, size=11)
        else:
            _pdf_write_wrapped_text(
                pdf,
                config["copyright_text"],
                max_width,
                spacing=0
            )
        pdf.ln(5)

    if include_warning:
        _pdf_write_warning(pdf, config["warning_text"], max_width)
        pdf.ln(5)

    _write_created_at(pdf, document_date, max_width)
    if include_count is not None:
        _pdf_write_icon_bold_label_value(
            pdf,
            "star",
            "Starred repositories count: ",
            str(include_count),
            max_width,
            spacing=0
        )
        if include_new_since is not None:
            _pdf_write_icon_bold_label_value(
                pdf,
                "info",
                "Newly added repositories since last update: ",
                str(include_new_since),
                max_width,
                spacing=0
            )
        pdf.ln(5)
        _pdf_draw_separator(pdf)
