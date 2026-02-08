"""FPDF import helpers."""

try:
    from fpdf import FPDF, XPos, YPos
except ImportError:  # pragma: no cover - handled gracefully
    FPDF = None
    XPos = None
    YPos = None
