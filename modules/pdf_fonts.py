"""Font configuration helpers for PDF output."""

import os

from .pdf_fpdf import FPDF

PDF_FONT_STATE = {
    "family": "Helvetica",
    "supports_unicode": False,
    "has_bold": True
}


def _configure_pdf_fonts(pdf):
    """Try to load a Unicode-capable font; fall back to core fonts."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
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
        except (OSError, RuntimeError, ValueError):
            continue

        PDF_FONT_STATE["family"] = family
        PDF_FONT_STATE["supports_unicode"] = True
        PDF_FONT_STATE["has_bold"] = False

        bold_path = bold_path if bold_path and os.path.isfile(bold_path) else None
        if bold_path:
            try:
                pdf.add_font(family, "B", bold_path)
                PDF_FONT_STATE["has_bold"] = True
            except (OSError, RuntimeError, ValueError):
                PDF_FONT_STATE["has_bold"] = False
        return


def _set_pdf_font(pdf, bold=False, size=11):
    """Set the current PDF font based on loaded font capabilities."""
    if bold:
        if PDF_FONT_STATE["has_bold"]:
            pdf.set_font(PDF_FONT_STATE["family"], style="B", size=size)
        elif PDF_FONT_STATE["family"] != "Helvetica":
            pdf.set_font("Helvetica", style="B", size=size)
        else:
            pdf.set_font(PDF_FONT_STATE["family"], style="B", size=size)
        return
    pdf.set_font(PDF_FONT_STATE["family"], style="", size=size)


if FPDF is not None:
    class OSINTPDF(FPDF):
        """FPDF subclass with a standard footer."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.footer_text = ""
            self.footer_show_page_number = True

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
