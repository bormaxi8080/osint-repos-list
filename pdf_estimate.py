"""Height estimation helpers for PDF output."""

from pdf_fonts import _set_pdf_font
from pdf_icons import ICON_SIZE
from pdf_sanitize import _sanitize_pdf_text
from pdf_utils import _format_github_date
from pdf_wrap import (
    _count_wrapped_lines,
    _count_wrapped_lines_first_width,
    _wrap_pdf_lines_with_first_width
)


def _estimate_label_with_link_height(
    pdf,
    label,
    link_text,
    max_width,
    line_height=5,
    bold=False,
    size=11
):
    _set_pdf_font(pdf, bold=bold, size=size)
    label_text = _sanitize_pdf_text(label, pdf)
    link_text_sanitized = _sanitize_pdf_text(link_text, pdf)
    label_width = pdf.get_string_width(label_text)
    link_width = pdf.get_string_width(link_text_sanitized)

    if label_text == "":
        lines = _count_wrapped_lines(pdf, link_text_sanitized, max_width)
        return lines * line_height

    if label_width + link_width <= max_width:
        return line_height

    link_lines = _count_wrapped_lines(pdf, link_text_sanitized, max_width)
    return (1 + link_lines) * line_height


def _estimate_bold_label_value_height(
    pdf,
    label,
    value,
    max_width,
    line_height=5,
    spacing=0
):
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    value_text = _sanitize_pdf_text(value, pdf)

    if label_width >= max_width:
        _set_pdf_font(pdf, bold=True, size=11)
        label_lines = _count_wrapped_lines(pdf, label_text, max_width)
        _set_pdf_font(pdf, bold=False, size=11)
        value_lines = _count_wrapped_lines(pdf, value_text, max_width)
        if value_lines == 0:
            value_lines = 1
        return (label_lines + value_lines) * line_height + spacing

    first_width = max_width - label_width
    value_lines = _count_wrapped_lines_first_width(
        pdf,
        value_text,
        first_width,
        max_width
    )
    if value_lines == 0:
        value_lines = 1
    return value_lines * line_height + spacing


def _estimate_icon_bold_label_value_height(
    pdf,
    label,
    value,
    max_width,
    line_height=5,
    spacing=0
):
    icon_advance = ICON_SIZE + 2
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    value_text = _sanitize_pdf_text(value, pdf)

    if icon_advance + label_width >= max_width:
        return line_height + _estimate_bold_label_value_height(
            pdf,
            label,
            value,
            max_width,
            line_height=line_height,
            spacing=spacing
        )

    first_width = max_width - icon_advance - label_width
    value_lines = _count_wrapped_lines_first_width(
        pdf,
        value_text,
        first_width,
        max_width
    )
    if value_lines == 0:
        value_lines = 1
    return value_lines * line_height + spacing


def _estimate_icon_bold_label_with_link_height(
    pdf,
    label,
    link_text,
    max_width,
    line_height=5
):
    icon_advance = ICON_SIZE + 2
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)
    link_text_sanitized = _sanitize_pdf_text(link_text, pdf)
    link_width = pdf.get_string_width(link_text_sanitized)

    if icon_advance + label_width + link_width <= max_width:
        return line_height

    first_width = max_width - icon_advance - label_width
    link_lines = _count_wrapped_lines_first_width(
        pdf,
        link_text_sanitized,
        first_width,
        max_width
    )
    if link_lines == 0:
        link_lines = 1
    return (1 + link_lines) * line_height


def _estimate_icon_bold_label_links_height(
    pdf,
    label,
    tags,
    max_width,
    line_height=5,
    spacing=0
):
    icon_advance = ICON_SIZE + 2
    _set_pdf_font(pdf, bold=True, size=11)
    label_text = _sanitize_pdf_text(label, pdf)
    label_width = pdf.get_string_width(label_text)
    _set_pdf_font(pdf, bold=False, size=11)

    line_count = 1
    if icon_advance + label_width > max_width:
        line_count += 1
        current_width = label_width
    else:
        current_width = icon_advance + label_width
    space_width = pdf.get_string_width(" ")

    for tag in tags:
        tag_text = _sanitize_pdf_text(f"#{tag}", pdf)
        tag_width = pdf.get_string_width(tag_text)

        if tag_width > max_width:
            chunks = _wrap_pdf_lines_with_first_width(
                pdf,
                tag_text,
                max_width,
                max_width
            )
            chunk_lines = max(1, len(chunks))
            line_count += chunk_lines
            current_width = 0
            continue

        if current_width + tag_width > max_width:
            line_count += 1
            current_width = 0

        current_width += tag_width

        if current_width + space_width > max_width:
            line_count += 1
            current_width = 0
        else:
            current_width += space_width

    return line_count * line_height + spacing


def _estimate_repo_block_height(pdf, repo, max_width):
    repo_name = str(repo.get("name", ""))
    repo_url = str(repo.get("html_url", ""))
    owner = repo.get("owner") or {}
    owner_login = str(owner.get("login", ""))

    description = repo.get("description")
    if description is None:
        description = "No project description"

    stars = repo.get("stargazers_count")
    created_on = _format_github_date(repo.get("created_at"))
    updated_on = _format_github_date(repo.get("updated_at"))
    topics = repo.get("topics") or []

    height = 0
    height += _estimate_label_with_link_height(
        pdf,
        "Repository: ",
        repo_name,
        max_width,
        line_height=6,
        bold=True,
        size=12
    )
    height += 5

    if repo_url:
        height += _estimate_icon_bold_label_with_link_height(
            pdf,
            "Repository Url: ",
            repo_url,
            max_width
        )

    height += _estimate_icon_bold_label_with_link_height(
        pdf,
        "Repository Owner: ",
        owner_login,
        max_width
    )

    height += _estimate_icon_bold_label_value_height(
        pdf,
        "Description: ",
        str(description),
        max_width,
        spacing=1
    )

    height += _estimate_icon_bold_label_value_height(
        pdf,
        "Stars: ",
        str(stars),
        max_width,
        spacing=1
    )

    height += _estimate_icon_bold_label_value_height(
        pdf,
        "Created at: ",
        created_on,
        max_width,
        spacing=1
    )

    height += _estimate_icon_bold_label_value_height(
        pdf,
        "Last commit: ",
        updated_on,
        max_width,
        spacing=1
    )

    if topics:
        height += _estimate_icon_bold_label_links_height(
            pdf,
            "Topics: ",
            [str(item) for item in topics],
            max_width,
            spacing=1
        )

    height += 4
    return height
