"""Text sanitization helpers for PDF output."""

from .pdf_fonts import PDF_FONT_STATE

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
    if PDF_FONT_STATE["supports_unicode"]:
        text = _strip_emoji(text)
        if pdf is not None:
            text = _filter_text_for_current_font(pdf, text)
        return text
    return text.encode("latin-1", errors="ignore").decode("latin-1")
