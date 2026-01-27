"""PDF generation helpers for OSINT repositories list."""

from datetime import datetime
from urllib.parse import quote

from colorama import Fore

try:
    from fpdf import FPDF, XPos, YPos
except ImportError:
    FPDF = None
    XPos = None
    YPos = None

ICON_SIZE = 4
ICON_COLORS = {
    "person": (52, 152, 219),
    "book": (39, 174, 96),
    "clock": (243, 156, 18),
    "info": (26, 188, 156),
    "link": (155, 89, 182),
    "star": (255, 204, 0)
}


def _sanitize_pdf_text(text):
    """Convert text to Latin-1-safe content for PDF output."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _wrap_pdf_lines(pdf, text, max_width):
    """Wrap text into lines that fit within the PDF width."""
    wrapped_lines = []
    for raw_line in text.splitlines():
        if raw_line.strip() == "":
            wrapped_lines.append("")
            continue

        words = raw_line.split()
        current = ""

        for word in words:
            candidate = word if current == "" else f"{current} {word}"
            if pdf.get_string_width(candidate) <= max_width:
                current = candidate
                continue

            if current:
                wrapped_lines.append(current)
                current = ""

            while pdf.get_string_width(word) > max_width:
                part = ""
                for ch in word:
                    if pdf.get_string_width(part + ch) <= max_width:
                        part += ch
                    else:
                        break
                if part == "":
                    part = word[:1]
                wrapped_lines.append(part)
                word = word[len(part):]

            current = word

        if current:
            wrapped_lines.append(current)

    return wrapped_lines


def _wrap_pdf_lines_with_first_width(pdf, text, first_width, max_width):
    """Wrap text with a custom first-line width and full width afterwards."""
    wrapped_lines = []
    words = text.split()
    current = ""
    current_width = first_width

    for word in words:
        candidate = word if current == "" else f"{current} {word}"
        if pdf.get_string_width(candidate) <= current_width:
            current = candidate
            continue

        if current:
            wrapped_lines.append(current)
            current = ""
            current_width = max_width

        while pdf.get_string_width(word) > current_width:
            part = ""
            for ch in word:
                if pdf.get_string_width(part + ch) <= current_width:
                    part += ch
                else:
                    break
            if part == "":
                part = word[:1]
            wrapped_lines.append(part)
            word = word[len(part):]
            current_width = max_width

        current = word

    if current:
        wrapped_lines.append(current)

    return wrapped_lines


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
        pdf.line(x_start + size * 0.45, y_offset, x_start + size * 0.45, y_offset + size)
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


def _pdf_write_wrapped_text(pdf, text, max_width, line_height=5, spacing=0):
    """Write wrapped text to PDF with optional spacing."""
    sanitized = _sanitize_pdf_text(text)
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
    label_text = _sanitize_pdf_text(label)
    link_text_sanitized = _sanitize_pdf_text(link_text)

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
    label_text = _sanitize_pdf_text(label)
    link_text_sanitized = _sanitize_pdf_text(link_text)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", style="B", size=11)
    label_width = pdf.get_string_width(label_text)

    pdf.set_font("Helvetica", size=11)
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
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.cell(label_width, line_height, text=label_text)
        pdf.set_font("Helvetica", size=11)
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

    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(
        0,
        line_height,
        text=label_text,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT
    )
    pdf.set_font("Helvetica", size=11)
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
    label_text = _sanitize_pdf_text(label)
    value_text = _sanitize_pdf_text(value)

    pdf.set_font("Helvetica", style="B", size=11)
    label_width = pdf.get_string_width(label_text)
    if label_width >= max_width:
        _pdf_write_wrapped_text(pdf, label_text, max_width, line_height=line_height)
        pdf.set_font("Helvetica", size=11)
        _pdf_write_wrapped_text(
            pdf,
            value_text,
            max_width,
            line_height=line_height,
            spacing=spacing
        )
        return

    pdf.cell(label_width, line_height, text=label_text)
    pdf.set_font("Helvetica", size=11)
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
    label_text = _sanitize_pdf_text(label)
    value_text = _sanitize_pdf_text(value)

    pdf.set_font("Helvetica", style="B", size=11)
    label_width = pdf.get_string_width(label_text)
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

    pdf.cell(label_width, line_height, text=label_text)
    pdf.set_font("Helvetica", size=11)
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
    label_text = _sanitize_pdf_text(label)
    link_text_sanitized = _sanitize_pdf_text(link_text)

    pdf.set_font("Helvetica", style="B", size=11)
    label_width = pdf.get_string_width(label_text)
    pdf.set_font("Helvetica", size=11)
    link_width = pdf.get_string_width(link_text_sanitized)

    if icon_advance + label_width + link_width <= max_width:
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.cell(label_width, line_height, text=label_text)
        pdf.set_font("Helvetica", size=11)
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

    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(
        0,
        line_height,
        text=label_text,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT
    )
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(0, 0, 255)
    first_width = max_width - icon_advance - label_width
    lines = _wrap_pdf_lines_with_first_width(pdf, link_text_sanitized, first_width, max_width)
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
    label_text = _sanitize_pdf_text(label)

    pdf.set_font("Helvetica", style="B", size=11)
    label_width = pdf.get_string_width(label_text)
    if icon_advance + label_width > max_width:
        pdf.ln(line_height)
        pdf.set_x(pdf.l_margin)
        icon_advance = 0

    pdf.cell(label_width, line_height, text=label_text)
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(0, 0, 255)

    space_width = pdf.get_string_width(" ")
    current_x = pdf.get_x()

    for tag in tags:
        tag_text = f"#{tag}"
        tag_text = _sanitize_pdf_text(tag_text)
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


def _pdf_write_warning(pdf, warning_text, max_width, line_height=5):
    """Write WARNING! in bold with the rest in normal text."""
    label = "WARNING!"
    text = warning_text.strip()
    body = text[len(label):].lstrip() if text.startswith(label) else text
    label_text = f"{label} "

    pdf.set_font("Helvetica", style="B", size=11)
    label_width = pdf.get_string_width(label_text)
    pdf.cell(label_width, line_height, text=label_text)
    pdf.set_font("Helvetica", size=11)

    if body:
        first_width = max_width - label_width
        lines = _wrap_pdf_lines_with_first_width(pdf, body, first_width, max_width)
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
            return
    pdf.ln(line_height)


def _format_github_date(value):
    """Format GitHub ISO dates to YYYY-MM-DD."""
    if not value:
        return "unknown"
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    except ValueError:
        return str(value)


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
        spacing=2
    )


def _write_header_section(
    pdf,
    config,
    document_date,
    max_width,
    include_warning=False,
    include_count=None
):
    """Write a common header section for the PDF pages."""
    pdf.set_font("Helvetica", style="B", size=16)
    _pdf_write_wrapped_text(
        pdf,
        config["header"],
        max_width,
        line_height=7,
        spacing=2
    )

    pdf.set_font("Helvetica", size=11)
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
    _write_created_at(pdf, document_date, max_width)
    if config.get("copyright_link_url"):
        pdf.set_font("Helvetica", style="B", size=11)
        _pdf_write_wrapped_text(pdf, config["copyright_text"], max_width, spacing=1)
        pdf.set_font("Helvetica", size=11)
        _pdf_write_label_with_link(
            pdf,
            config.get("copyright_link_prefix", ""),
            config.get("copyright_link_text", config["copyright_link_url"]),
            config["copyright_link_url"],
            max_width
        )
        pdf.ln(5)
    else:
        if config.get("copyright_bold"):
            pdf.set_font("Helvetica", style="B", size=11)
            _pdf_write_wrapped_text(
                pdf,
                config["copyright_text"],
                max_width,
                spacing=0
            )
            pdf.set_font("Helvetica", size=11)
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

    if include_count is not None:
        _pdf_write_bold_label_value(
            pdf,
            "Starred repositories count: ",
            str(include_count),
            max_width,
            spacing=0
        )
        pdf.ln(5)
        _pdf_draw_separator(pdf)


def save_pdf_from_data(path, repos, users, document_date, config):
    """Generate and save the PDF from repository and user data."""
    if FPDF is None:
        print(
            Fore.RED
            + "Missing dependency: fpdf2. Install it with 'pip install -r requirements.txt'."
        )
        return False

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    _write_header_section(
        pdf,
        config["repos_header"],
        document_date,
        max_width,
        include_warning=True,
        include_count=len(repos)
    )

    pdf.set_font("Helvetica", style="B", size=13)
    _pdf_write_wrapped_text(
        pdf,
        config["section_repos_title"],
        max_width,
        line_height=6,
        spacing=3
    )

    sorted_repos = sorted(repos, key=lambda x: str(x.get("name", "")).lower())
    for repo in sorted_repos:
        repo_name = str(repo.get("name", ""))
        repo_url = str(repo.get("html_url", ""))
        owner = repo.get("owner") or {}
        owner_login = str(owner.get("login", ""))
        owner_url = str(owner.get("html_url", ""))

        pdf.set_font("Helvetica", style="B", size=12)
        _pdf_write_label_with_link(
            pdf,
            "Repository: ",
            repo_name,
            repo_url,
            max_width,
            line_height=6
        )
        pdf.ln(5)
        if repo_url:
            _pdf_write_icon_bold_label_with_link(
                pdf,
                "link",
                "Repository Url: ",
                repo_url,
                repo_url,
                max_width
            )
        pdf.set_font("Helvetica", size=11)
        _pdf_write_icon_bold_label_with_link(
            pdf,
            "person",
            "Repository Owner: ",
            owner_login,
            owner_url,
            max_width
        )

        description = repo.get("description")
        if description is None:
            description = "No project description"
        _pdf_write_icon_bold_label_value(
            pdf,
            "book",
            "Description: ",
            str(description),
            max_width,
            spacing=1
        )

        stars = repo.get("stargazers_count")
        created_on = _format_github_date(repo.get("created_at"))
        updated_on = _format_github_date(repo.get("updated_at"))
        _pdf_write_starred_bold_label_value(
            pdf,
            "Stars: ",
            str(stars),
            max_width,
            spacing=1
        )
        _pdf_write_icon_bold_label_value(
            pdf,
            "clock",
            "Created at: ",
            created_on,
            max_width,
            spacing=1
        )
        _pdf_write_icon_bold_label_value(
            pdf,
            "clock",
            "Last commit: ",
            updated_on,
            max_width,
            spacing=1
        )

        topics = repo.get("topics") or []
        if len(topics) > 0:
            _pdf_write_icon_bold_label_links(
                pdf,
                "info",
                "Topics: ",
                [str(item) for item in topics],
                "https://github.com/topics/",
                max_width,
                spacing=1
            )

        _pdf_draw_separator(pdf)

    pdf.add_page()

    _write_header_section(
        pdf,
        config["users_header"],
        document_date,
        max_width
    )

    pdf.set_font("Helvetica", style="B", size=13)
    _pdf_write_wrapped_text(
        pdf,
        config["section_users_title"],
        max_width,
        line_height=6,
        spacing=3
    )

    sorted_users = sorted(users, key=lambda x: str(x.get("login", "")).lower())
    for owner_data in sorted_users:
        login = str(owner_data.get("login", ""))
        html_url = str(owner_data.get("html_url", ""))
        name = owner_data.get("name")
        location = owner_data.get("location")

        pdf.set_font("Helvetica", style="B", size=12)
        _pdf_write_label_with_link(
            pdf,
            "User: ",
            login,
            html_url,
            max_width,
            line_height=6
        )

        pdf.set_font("Helvetica", size=11)
        if name is not None:
            _pdf_write_wrapped_text(pdf, f"Name: {name}", max_width, spacing=1)
        if location is not None:
            _pdf_write_wrapped_text(pdf, f"Location: {location}", max_width, spacing=1)

        bio = owner_data.get("bio")
        if bio is not None:
            _pdf_write_wrapped_text(pdf, str(bio), max_width, spacing=1)

        blog = owner_data.get("blog")
        if blog is not None and str(blog) != "":
            _pdf_write_label_with_link(
                pdf,
                "Site/Blog: ",
                str(blog),
                str(blog),
                max_width
            )

        public_repos = owner_data.get("public_repos")
        if public_repos is not None and html_url:
            repos_url = f"{html_url}?tab=repositories"
            _pdf_write_label_with_link(
                pdf,
                "Public repos: ",
                str(public_repos),
                repos_url,
                max_width
            )

        followers = owner_data.get("followers")
        followers_url = owner_data.get("followers_url")
        if followers is not None and followers_url:
            _pdf_write_label_with_link(
                pdf,
                "Followers: ",
                str(followers),
                str(followers_url),
                max_width
            )

        twitter_username = owner_data.get("twitter_username")
        if twitter_username is not None:
            twitter_handle = f"@{twitter_username}"
            twitter_url = f"https://twitter.com/{twitter_username}"
            _pdf_write_label_with_link(
                pdf,
                "Twitter: ",
                twitter_handle,
                twitter_url,
                max_width
            )

        owner_email = owner_data.get("email")
        if owner_email is not None:
            mailto = f"mailto:{owner_email}"
            _pdf_write_label_with_link(
                pdf,
                "Email: ",
                str(owner_email),
                mailto,
                max_width
            )

        _pdf_draw_separator(pdf)

    pdf.output(path)
    print(Fore.GREEN + f"Document saved: {path}")
    return True
