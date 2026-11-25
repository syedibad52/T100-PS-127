"""Reproducibly create the PS-127 design-document PDF from the maintained Markdown outline."""
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "design_document.pdf"
styles = getSampleStyleSheet()
title = ParagraphStyle("Title", parent=styles["Title"], textColor=HexColor("#075E54"), spaceAfter=18)
heading = ParagraphStyle("Heading", parent=styles["Heading2"], textColor=HexColor("#0F766E"), spaceBefore=12, spaceAfter=6)
body = ParagraphStyle("Body", parent=styles["BodyText"], leading=15, spaceAfter=8)

sections = [
    ("PS-127 Design Document", "Organ Transplant Waitlist Allocation Engine<br/>Academic, offline, deterministic simulation<br/><br/>Team T100 | ISE D<br/>Sharathkumar - 1AT24IS175<br/>Shashidhar Tiwari - 1AT24IS176"),
    ("Abstract", "PS-127 simulates regional deceased-donor kidney, liver and heart allocation. It generates explainable rankings, validates compatibility, models event-based offer outcomes and preserves a canonical audit. It is not clinically validated and must not be used for real-world transplant decisions."),
    ("Objectives", "Maintain waitlists and historical status; calculate urgency and waiting time; evaluate blood, HLA, size, age, geography and cold ischemia; rank deterministically; process backups and multi-organ allocation; reproduce stored audits."),
    ("Architecture", "CSV and JSON inputs flow through isolated storage adapters into typed domain models. Pure rule policies feed the deterministic match and offer engine. The CLI renders predictable output, while JSON audit snapshots preserve every decision.<br/><br/><b>Flow:</b> input -> validation -> compatibility -> score/tier -> ranking -> offer events -> audit."),
    ("Business-rule implementation", "BR-01 blood matrix and identical priority. BR-02 kidney/liver/heart scoring. BR-03 active-time accumulation. BR-04 tiers and ischemia. BR-05 size and age. BR-06 tie keys. BR-07 refusal policy. BR-08 three candidates and backup event flow. BR-09 atomic liver-kidney policy. BR-10 status/staleness. BR-11 canonical audit. BR-12 explicit pipeline precedence."),
    ("Data and validation", "Candidates, donors and routes use provisional CSV schemas; structured status and audit histories use JSON. Invalid blood groups, malformed HLA, duplicate IDs, invalid scores, negative durations and malformed status spans are rejected before allocation."),
    ("Testing and limitations", "Automated pytest coverage includes the supplied edge boundaries: MELD 35, exact ischemia, inactive time, 70%/130% heart ratio, third refusal on day 365, backup at four hours and liver-kidney override. Official samples are pending; parser compatibility and ambiguity confirmations remain provisional."),
]

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.setFillColor(HexColor("#475569")); canvas.drawString(2*cm, 1.2*cm, "PS-127 | Academic simulation only"); canvas.drawRightString(A4[0]-2*cm, 1.2*cm, f"Page {doc.page}"); canvas.restoreState()

story = []
for idx, (name, text) in enumerate(sections):
    story.append(Paragraph(name, title if idx == 0 else heading)); story.append(Paragraph(text, body)); story.append(Spacer(1, 8))
    if idx == 0: story.append(PageBreak())
OUT.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm, title="PS-127 Design Document").build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
