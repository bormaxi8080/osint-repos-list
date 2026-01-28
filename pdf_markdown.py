"""Minimal markdown helpers for PDF output."""

from pdf_fonts import _set_pdf_font
from pdf_wrap import _wrap_pdf_lines_with_first_width


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
