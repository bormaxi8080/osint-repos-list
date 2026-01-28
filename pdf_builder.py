"""PDF generation helpers for OSINT repositories list."""

from datetime import datetime
import os
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

PDF_FONT_FAMILY = "Helvetica"
PDF_FONT_SUPPORTS_UNICODE = False
PDF_FONT_HAS_BOLD = True

_EMOJI_RANGES = (
    (0x1F1E6, 0x1F1FF),
    (0x1F300, 0x1F5FF),
    (0x1F600, 0x1F64F),
    (0x1F680, 0x1F6FF),
    (0x1F700, 0x1F77F),
    (0x1F780, 0x1F7FF),
    (0x1F800, 0x1F8FF),
    (0x1F900, 0x1F9FF),
    (0x1FA00, 0x1FA6F),
    (0x1FA70, 0x1FAFF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF)
)
_EMOJI_SINGLETONS = {0x200D, 0xFE0F, 0xFE0E, 0x20E3}
_CONTROL_SINGLETONS = {0xFEFF}


def _configure_pdf_fonts(pdf):
    """Try to load a Unicode-capable font; fall back to core fonts."""
    global PDF_FONT_FAMILY, PDF_FONT_SUPPORTS_UNICODE, PDF_FONT_HAS_BOLD

    base_dir = os.path.dirname(__file__)
    candidates = [
        (
            "NotoSans",
            os.path.join(base_dir, "fonts", "NotoSans-Regular.ttf"),
            os.path.join(base_dir, "fonts", "NotoSans-Bold.ttf")
        ),
        (
            "DejaVuSans",
            os.path.join(base_dir, "fonts", "DejaVuSans.ttf"),
            os.path.join(base_dir, "fonts", "DejaVuSans-Bold.ttf")
        ),
        (
            "ArialUnicodeLocal",
            os.path.join(base_dir, "fonts", "ArialUnicode.ttf"),
            None
        ),
        (
            "DejaVuSansSys",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ),
        (
            "LiberationSans",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ),
        (
            "ArialUnicodeMS",
            "/Library/Fonts/Arial Unicode.ttf",
            None
        ),
        (
            "ArialUnicodeMS2",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            None
        ),
        (
            "ArialUnicodeMS3",
            "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
            None
        )
    ]

    for family, regular_path, bold_path in candidates:
        if not regular_path or not os.path.isfile(regular_path):
            continue
        try:
            pdf.add_font(family, "", regular_path)
        except Exception:
            continue

        PDF_FONT_FAMILY = family
        PDF_FONT_SUPPORTS_UNICODE = True
        PDF_FONT_HAS_BOLD = False

        bold_path = bold_path if bold_path and os.path.isfile(bold_path) else None
        if bold_path:
            try:
                pdf.add_font(family, "B", bold_path)
                PDF_FONT_HAS_BOLD = True
            except Exception:
                PDF_FONT_HAS_BOLD = False
        return


def _set_pdf_font(pdf, bold=False, size=11):
    """Set the current PDF font based on loaded font capabilities."""
    if bold:
        if PDF_FONT_HAS_BOLD:
            pdf.set_font(PDF_FONT_FAMILY, style="B", size=size)
        elif PDF_FONT_FAMILY != "Helvetica":
            pdf.set_font("Helvetica", style="B", size=size)
        else:
            pdf.set_font(PDF_FONT_FAMILY, style="B", size=size)
        return
    pdf.set_font(PDF_FONT_FAMILY, style="", size=size)


if FPDF is not None:
    class OSINTPDF(FPDF):
        """FPDF subclass with a standard footer."""

        def footer(self):
            footer_text = getattr(self, "footer_text", "")
            show_page_number = getattr(self, "footer_show_page_number", True)
            if not footer_text and not show_page_number:
                return

            self.set_y(-12)
            if footer_text:
                _set_pdf_font(self, bold=False, size=9)
                self.set_text_color(0, 0, 0)
                self.cell(0, 10, text=footer_text, align="L")

            if show_page_number:
                page_no = str(self.page_no())
                self.set_y(-12)
                _set_pdf_font(self, bold=True, size=9)
                self.set_text_color(0, 0, 0)
                self.cell(0, 10, text=page_no, align="R")
else:
    OSINTPDF = None


def _is_emoji_codepoint(codepoint):
    if codepoint in _EMOJI_SINGLETONS:
        return True
    for start, end in _EMOJI_RANGES:
        if start <= codepoint <= end:
            return True
    return False


def _strip_control_chars(text):
    cleaned = []
    for ch in text:
        if ch == "\n":
            cleaned.append("\n")
            continue
        if ch == "\r":
            cleaned.append("\n")
            continue
        if ch == "\t":
            cleaned.append(" ")
            continue
        codepoint = ord(ch)
        if codepoint in _CONTROL_SINGLETONS:
            continue
        if codepoint < 32 or 0x7F <= codepoint <= 0x9F:
            continue
        cleaned.append(ch)
    return "".join(cleaned)


def _strip_emoji(text):
    return "".join(
        ch for ch in text if not _is_emoji_codepoint(ord(ch))
    )


def _font_supports_codepoint(widths, codepoint):
    if isinstance(widths, dict):
        return codepoint in widths
    if isinstance(widths, (list, tuple)):
        return 0 <= codepoint < len(widths) and widths[codepoint] != 0
    return True


def _filter_text_for_current_font(pdf, text):
    font = getattr(pdf, "current_font", None)
    if not isinstance(font, dict):
        return text
    widths = font.get("cw")
    if widths is None:
        return text

    cleaned = []
    for ch in text:
        if ch == "\n":
            cleaned.append(ch)
            continue
        if _font_supports_codepoint(widths, ord(ch)):
            cleaned.append(ch)
    return "".join(cleaned)


def _sanitize_pdf_text(text, pdf=None):
    """Normalize text for PDF output with safe fallbacks."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _strip_control_chars(text)
    if PDF_FONT_SUPPORTS_UNICODE:
        text = _strip_emoji(text)
        if pdf is not None:
            text = _filter_text_for_current_font(pdf, text)
        return text
    return text.encode("latin-1", errors="ignore").decode("latin-1")


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


def _parse_markdown_bold_segments(text):
    """Parse minimal markdown (**bold**) into (text, bold) segments."""
    segments = []
    bold = False
    buffer = []
    idx = 0
    while idx < len(text):
        if text[idx:idx + 2] == "**":
            if buffer:
                segments.append(("".join(buffer), bold))
                buffer = []
            bold = not bold
            idx += 2
            continue
        buffer.append(text[idx])
        idx += 1
    if buffer:
        segments.append(("".join(buffer), bold))

    merged = []
    for segment_text, segment_bold in segments:
        if not segment_text:
            continue
        if merged and merged[-1][1] == segment_bold:
            merged[-1] = (merged[-1][0] + segment_text, segment_bold)
        else:
            merged.append((segment_text, segment_bold))
    return merged


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


def _skip_leading_spaces(segments, seg_idx, seg_offset):
    """Advance segment cursor past leading spaces."""
    while seg_idx < len(segments):
        segment_text = segments[seg_idx][0]
        while seg_offset < len(segment_text) and segment_text[seg_offset] == " ":
            seg_offset += 1
        if seg_offset < len(segment_text):
            break
        seg_idx += 1
        seg_offset = 0
    return seg_idx, seg_offset


def _consume_segments_for_line(segments, seg_idx, seg_offset, length):
    """Consume characters from segments to assemble a line of given length."""
    parts = []
    remaining = length
    while remaining > 0 and seg_idx < len(segments):
        segment_text, segment_bold = segments[seg_idx]
        available = len(segment_text) - seg_offset
        take = min(available, remaining)
        chunk = segment_text[seg_offset:seg_offset + take]
        if chunk:
            if parts and parts[-1][1] == segment_bold:
                parts[-1] = (parts[-1][0] + chunk, segment_bold)
            else:
                parts.append((chunk, segment_bold))
        seg_offset += take
        remaining -= take
        if seg_offset >= len(segment_text):
            seg_idx += 1
            seg_offset = 0
    return parts, seg_idx, seg_offset


def _pdf_write_markdown_bold_text_with_first_width(
    pdf,
    text,
    first_width,
    max_width,
    line_height=5,
    size=11
):
    """Write text with **bold** markers using a custom first-line width."""
    segments = _parse_markdown_bold_segments(text)
    plain_text = "".join(segment for segment, _ in segments)
    if not plain_text:
        pdf.ln(line_height)
        return

    _set_pdf_font(pdf, bold=False, size=size)
    lines = _wrap_pdf_lines_with_first_width(pdf, plain_text, first_width, max_width)
    seg_idx = 0
    seg_offset = 0

    for line in lines:
        seg_idx, seg_offset = _skip_leading_spaces(segments, seg_idx, seg_offset)
        parts, seg_idx, seg_offset = _consume_segments_for_line(
            segments,
            seg_idx,
            seg_offset,
            len(line)
        )
        for part_text, part_bold in parts:
            _set_pdf_font(pdf, bold=part_bold, size=size)
            pdf.cell(pdf.get_string_width(part_text), line_height, text=part_text)
        pdf.ln(line_height)


def _count_wrapped_lines(pdf, text, max_width):
    return len(_wrap_pdf_lines(pdf, text, max_width))


def _count_wrapped_lines_first_width(pdf, text, first_width, max_width):
    return len(_wrap_pdf_lines_with_first_width(pdf, text, first_width, max_width))


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
        spacing=2
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


def save_pdf_from_data(path, repos, users, document_date, config, new_since=None):
    """Generate and save the PDF from repository and user data."""
    if FPDF is None:
        print(
            Fore.RED
            + "Missing dependency: fpdf2. Install it with 'pip install -r requirements.txt'."
        )
        return False

    pdf = OSINTPDF()
    _configure_pdf_fonts(pdf)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.footer_text = config.get("footer_text", "")
    pdf.footer_show_page_number = config.get("footer_show_page_number", True)
    pdf.add_page()
    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    _write_header_section(
        pdf,
        config["repos_header"],
        document_date,
        max_width,
        include_warning=True,
        include_count=len(repos),
        include_new_since=new_since
    )

    _set_pdf_font(pdf, bold=True, size=16)
    _pdf_write_wrapped_text(
        pdf,
        config["section_repos_title"],
        max_width,
        line_height=7,
        spacing=3
    )

    sorted_repos = sorted(repos, key=lambda x: str(x.get("name", "")).lower())
    for repo in sorted_repos:
        repo_block_height = _estimate_repo_block_height(pdf, repo, max_width)
        if pdf.get_y() + repo_block_height > pdf.page_break_trigger:
            pdf.add_page()
        repo_name = str(repo.get("name", ""))
        repo_url = str(repo.get("html_url", ""))
        owner = repo.get("owner") or {}
        owner_login = str(owner.get("login", ""))
        owner_url = str(owner.get("html_url", ""))

        _set_pdf_font(pdf, bold=True, size=12)
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
        _set_pdf_font(pdf, bold=False, size=11)
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

    _set_pdf_font(pdf, bold=True, size=13)
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

        _set_pdf_font(pdf, bold=True, size=12)
        _pdf_write_label_with_link(
            pdf,
            "User: ",
            login,
            html_url,
            max_width,
            line_height=6
        )

        _set_pdf_font(pdf, bold=False, size=11)
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
