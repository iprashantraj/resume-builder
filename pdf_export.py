"""Render a Markdown resume to a clean, professional PDF (bytes).

Designed to look like a standard one-column resume:
  - Name as a large serif header (Georgia)
  - Centered contact line in muted gray
  - Uppercase section headings (Arial) with a thin rule beneath
  - Real bold for roles/degrees via inline **markdown**
  - Hanging-indent bullet points

Embeds TrueType fonts (Arial + Georgia) so typography is crisp and Unicode
(em dashes, bullets, curly quotes) renders correctly. Falls back to the core
Helvetica font with character sanitization if those fonts aren't installed.
"""

from __future__ import annotations

import os
import re

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Standard macOS locations for the fonts most resumes use.
_FONT_DIRS = [
    "/System/Library/Fonts/Supplemental",
    "/System/Library/Fonts",
    "/Library/Fonts",
]

# Family -> {style: filename}. style "" = regular, B = bold, I = italic, BI both.
_FONT_FILES = {
    "ResumeSerif": {  # Georgia — used for the name header
        "": "Georgia.ttf",
        "B": "Georgia Bold.ttf",
        "I": "Georgia Italic.ttf",
        "BI": "Georgia Bold Italic.ttf",
    },
    "ResumeSans": {  # Arial — used for everything else
        "": "Arial.ttf",
        "B": "Arial Bold.ttf",
        "I": "Arial Italic.ttf",
        "BI": "Arial Bold Italic.ttf",
    },
}

# Page geometry (mm)
_MARGIN = 16.0
_BULLET_INDENT = 5.0

# Colors
_INK = (33, 37, 41)        # near-black body text
_MUTED = (90, 96, 102)     # contact line
_RULE = (170, 176, 182)    # section underline


def _find_font(filename: str):
    for d in _FONT_DIRS:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None


def _register_fonts(pdf: FPDF) -> bool:
    """Register the embedded font families. Returns True if both are available."""
    for family, styles in _FONT_FILES.items():
        for style, filename in styles.items():
            path = _find_font(filename)
            if path is None:
                return False
            pdf.add_font(family, style=style, fname=path)
    return True


# ---------------------------------------------------------------------------
# Latin-1 fallback (only used when the TrueType fonts aren't installed)
# ---------------------------------------------------------------------------
_UNICODE_MAP = {
    "—": "-", "–": "-", "−": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "•": "-", "…": "...", " ": " ",
}


def _latin1_safe(text: str) -> str:
    for bad, good in _UNICODE_MAP.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "ignore").decode("latin-1")


def _strip_md(text: str) -> str:
    """Remove inline markdown emphasis markers (used when markdown rendering off)."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


class _ResumePDF(FPDF):
    """Small wrapper holding the active font families + render helpers."""

    def __init__(self) -> None:
        super().__init__(format="A4")
        self.set_auto_page_break(auto=True, margin=14)
        self.set_margins(left=_MARGIN, top=14, right=_MARGIN)
        self.add_page()
        self.unicode_ok = _register_fonts(self)
        # When using the core font we must sanitize text and can't use real bold
        # markdown reliably; track which families to use.
        self.serif = "ResumeSerif" if self.unicode_ok else "Helvetica"
        self.sans = "ResumeSans" if self.unicode_ok else "Helvetica"

    def _txt(self, text: str) -> str:
        return text if self.unicode_ok else _latin1_safe(text)

    @property
    def content_width(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def name(self, text: str) -> None:
        self.set_font(self.serif, "B", 22)
        self.set_text_color(*_INK)
        self.multi_cell(0, 9, self._txt(text), align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.5)

    def contact(self, text: str) -> None:
        self.set_font(self.sans, "", 9.5)
        self.set_text_color(*_MUTED)
        self.multi_cell(0, 4.8, self._txt(text), align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section(self, text: str) -> None:
        self.ln(2.5)
        self.set_font(self.sans, "B", 11)
        self.set_text_color(*_INK)
        self.multi_cell(0, 5.5, self._txt(text.upper()),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = self.get_y() + 0.5
        self.set_draw_color(*_RULE)
        self.set_line_width(0.3)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(2.5)

    def subheading(self, text: str) -> None:
        self.ln(0.8)
        self.set_font(self.sans, "B", 10.5)
        self.set_text_color(*_INK)
        self._body_cell(text, bold_default=True)

    def paragraph(self, text: str) -> None:
        self.set_font(self.sans, "", 10)
        self.set_text_color(*_INK)
        self._body_cell(text)

    def bullet(self, text: str) -> None:
        self.set_font(self.sans, "", 10)
        self.set_text_color(*_INK)
        bullet_char = "•" if self.unicode_ok else "-"
        x = self.l_margin
        self.set_x(x)
        # Draw the bullet glyph, then the wrapped text with a hanging indent.
        self.cell(_BULLET_INDENT, 5.2, self._txt(bullet_char))
        self.set_x(x + _BULLET_INDENT)
        self.multi_cell(
            self.content_width - _BULLET_INDENT, 5.2, self._txt(text),
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            markdown=self.unicode_ok,
        )

    def hrule(self) -> None:
        self.ln(1.5)
        y = self.get_y()
        self.set_draw_color(*_RULE)
        self.set_line_width(0.2)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(2)

    def _body_cell(self, text: str, bold_default: bool = False) -> None:
        rendered = self._txt(text if self.unicode_ok else _strip_md(text))
        self.multi_cell(0, 5.2, rendered, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                        markdown=self.unicode_ok and not bold_default)


def markdown_to_pdf(markdown: str) -> bytes:
    pdf = _ResumePDF()

    lines = markdown.splitlines()
    name_set = False
    in_header = False  # collecting the contact block right under the name

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        # ---- Name (first H1) -------------------------------------------------
        if not name_set and stripped.startswith("# "):
            pdf.name(stripped[2:].strip())
            name_set = True
            in_header = True
            continue

        # ---- Contact block directly beneath the name -------------------------
        if in_header:
            if not stripped:
                in_header = False
                pdf.ln(1)
                continue
            if stripped.startswith("#") or stripped.startswith(("- ", "* ")):
                in_header = False  # fall through to normal handling below
            else:
                # Flatten any markdown in the contact line for a clean look.
                pdf.contact(_strip_md(stripped).replace("•", "|"))
                continue

        # ---- Blank line ------------------------------------------------------
        if not stripped:
            pdf.ln(1.6)
            continue

        # ---- Horizontal rule -------------------------------------------------
        if stripped in ("---", "***", "___"):
            pdf.hrule()
            continue

        # ---- Headings --------------------------------------------------------
        if stripped.startswith("## "):
            pdf.section(stripped[3:].strip())
            continue
        if stripped.startswith("### "):
            pdf.subheading(stripped[4:].strip())
            continue
        if stripped.startswith("# "):  # stray H1 after the name
            pdf.section(stripped[2:].strip())
            continue

        # ---- Bullets ---------------------------------------------------------
        if stripped.startswith(("- ", "* ")):
            pdf.bullet(stripped[2:].strip())
            continue

        # ---- Plain paragraph -------------------------------------------------
        pdf.paragraph(stripped)

    out = pdf.output()
    return bytes(out)
