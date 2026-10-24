"""Render thesis/thesis.md to a two-page A4 PDF (ReportLab, same house style as the shipping lab paper)."""

import argparse
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "thesis" / "thesis.md"
OUT = ROOT / "thesis" / "Ambekar_Star-Bulk_thesis.pdf"
FOOTER = "Hrush Ambekar | Equity research, October 2026"

INK, MUTED, RULE, ACCENT = (colors.HexColor(c) for c in ("#1B1F24", "#5B6470", "#D9DDE3", "#1F4E79"))
body = ParagraphStyle("b", fontName="Helvetica", fontSize=8.6, leading=11.5, textColor=INK, spaceAfter=4)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=9.6, leading=12, spaceBefore=5, spaceAfter=2.5,
                    textColor=ACCENT, keepWithNext=1)
title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=INK, spaceAfter=2)
sub = ParagraphStyle("s", fontName="Helvetica", fontSize=8.8, leading=11.5, textColor=MUTED, spaceAfter=1)
cap = ParagraphStyle("cap", parent=body, fontSize=7, leading=9, textColor=MUTED, spaceAfter=4)
cell = ParagraphStyle("c", parent=body, fontSize=8.1, leading=10.2, spaceAfter=0)
cellb = ParagraphStyle("cb", parent=cell, fontName="Helvetica-Bold")


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)


def table(block, width):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in block.splitlines()
            if not re.match(r"^\|[-\s|]+\|$", ln.strip())]
    n = len(rows[0])
    first = 0.40 if n > 3 else 0.46
    widths = [width * first] + [width * (1 - first) / (n - 1)] * (n - 1)
    data = [[Paragraph(inline(c), cellb if i == 0 else cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.7, INK), ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6), ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
    return t


def build(out=OUT, footer_text=FOOTER):
    src = SRC.read_text()
    fm = dict(re.findall(r'^(\w+): "(.*)"$', src.split("---")[1], re.M))
    width = A4[0] - 30 * mm
    story = [Paragraph(inline(fm["title"]), title), Paragraph(inline(fm["subtitle"]), sub),
             Paragraph(f"{fm['author']} &middot; {fm['date']}", sub), Spacer(1, 3 * mm)]
    for b in re.split(r"\n\s*\n", src.split("---", 2)[2].strip()):
        b = b.strip()
        if b.startswith("## "):
            story.append(Paragraph(inline(b[3:]), h2))
        elif b.startswith("[Figure 1]"):
            img = Image(str(ROOT / "thesis" / "fig_stewardship.png"))
            img.drawWidth, img.drawHeight = width, img.imageHeight * width / img.imageWidth
            story += [img]
        elif b.startswith("|"):
            story += [table(b, width), Spacer(1, 1.5)]
        elif b.startswith("* "):
            items = [ListItem(Paragraph(inline(re.sub(r"\s+", " ", it[2:])), body), leftIndent=9)
                     for it in re.split(r"\n(?=\* )", b)]
            story.append(ListFlowable(items, bulletType="bullet", bulletFontSize=6, leftIndent=10))
        elif b.startswith("*") and not b.startswith("**"):
            # A caption stays on the same page as the table or figure it describes
            held = [story.pop()] if isinstance(story[-1], Spacer) else []
            story.append(KeepTogether([story.pop(), *held, Paragraph(inline(re.sub(r"\s+", " ", b)), cap)]))
        else:
            story.append(Paragraph(inline(re.sub(r"\s+", " ", b)), body))

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawString(15 * mm, 9 * mm, footer_text)
        c.drawRightString(A4[0] - 15 * mm, 9 * mm, f"{d.page} / 2")
        c.restoreState()

    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=13 * mm,
                            bottomMargin=15 * mm, title=fm["title"], author=fm["author"])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", out.read_bytes()))
    print(f"wrote {out} ({pages} pages)")
    return pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT, help="Output PDF path")
    parser.add_argument("--footer", default=FOOTER, help="Footer text on each page")
    args = parser.parse_args()
    sys.exit(0 if build(args.out, args.footer) <= 2 else 1)
