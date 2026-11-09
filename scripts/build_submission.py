"""Render the design source and verified UI captures into the two-file ZIP.

Run with a Python environment containing reportlab and Pillow. Do not add PDF
authoring dependencies to the application's production requirements.
"""
from pathlib import Path
from html import escape
import re
import shutil
import zipfile

from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
OUT.mkdir(exist_ok=True)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ReportBody', fontName='Helvetica', fontSize=10, leading=15, spaceAfter=8, allowWidows=0, allowOrphans=0))
styles.add(ParagraphStyle(name='ReportTitle', fontName='Helvetica-Bold', fontSize=23, leading=28, spaceAfter=18, textColor=colors.HexColor('#1c1917')))
styles.add(ParagraphStyle(name='ReportHeading', fontName='Helvetica-Bold', fontSize=13, leading=18, spaceBefore=15, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name='ReportBullet', parent=styles['ReportBody'], leftIndent=12, firstLineIndent=-8, spaceAfter=6))
styles.add(ParagraphStyle(name='CaptionSmall', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=10, textColor=colors.HexColor('#57534e')))


def clean(text):
    for old, new in [('→', ' -> '), ('–', '-'), ('—', '-'), ('’', "'"), ('“', '"'), ('”', '"')]:
        text = text.replace(old, new)
    text = escape(text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)
    text = re.sub(r'(https://[^\s<]+)', r'<a href="\1" color="#805a20">\1</a>', text)
    return text


story = []
source = (ROOT / 'docs/technical-design.md').read_text(encoding='utf-8')
for block in re.split(r'\n\s*\n', source):
    block = block.strip()
    if not block:
        continue
    if block.startswith('# '):
        story.append(Paragraph(clean(block[2:]), styles['ReportTitle']))
    elif block.startswith('## '):
        story.append(Paragraph(clean(block[3:]), styles['ReportHeading']))
        if block == '## Architecture and choices':
            boxes = Table([[Paragraph('Browser<br/><b>React + TypeScript</b>', styles['ReportBody']),
                Paragraph('API<br/><b>FastAPI + Decimal</b>', styles['ReportBody']),
                Paragraph('Ledger<br/><b>PostgreSQL + Alembic</b>', styles['ReportBody'])]], colWidths=[165]*3)
            boxes.setStyle(TableStyle([('BACKGROUND', (0,0),(-1,-1),colors.HexColor('#f8f5ee')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#e3d9c5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),10),('LEFTPADDING',(0,0),(-1,-1),10)]))
            story.extend([boxes, Spacer(1, 10)])
    elif block.startswith('- '):
        for item in re.split(r'\n(?=- )', block):
            story.append(KeepTogether([Paragraph(clean(item.replace('\n', ' ')), styles['ReportBullet'])]))
    elif re.match(r'^\d+\.', block):
        for item in re.split(r'\n(?=\d+\.)', block):
            story.append(Paragraph(clean(item.replace('\n', ' ')), styles['ReportBody']))
    else:
        story.append(Paragraph(clean(block.replace('\n', ' ')), styles['ReportBody']))


def capture(name):
    files = list((ROOT / 'frontend/test-results').rglob(name))
    if not files:
        raise RuntimeError(f'Missing browser verification image: {name}')
    return files[0]


def picture(path, width, max_height=10000):
    with PILImage.open(path) as image:
        width = min(width, max_height * image.width / image.height)
        height = width * image.height / image.width
    return Image(str(path), width=width, height=height)


story.extend([PageBreak(), Paragraph('Verified interface views', styles['ReportTitle']),
    Paragraph('Production build in Chromium against the isolated synthetic E2E database. Images document implemented behaviour; they are not client records.', styles['CaptionSmall']),
    picture(capture('scale-proposal.png'), 480),
    Paragraph('The scale image is beside the OCR proposal. A typed mismatch blocks saving and human confirmation is required.', styles['CaptionSmall']),
    picture(capture('finance-review.png'), 460),
    Paragraph('Finance sees review items and linked adjustment evidence. Owner stock is absent from this role.', styles['CaptionSmall'])])
story.extend([PageBreak(), Paragraph('Phone and recovery views', styles['ReportTitle'])])
pair = Table([[picture(capture('phone-tamil-slips.png'), 205, 490), picture(capture('phone-offline-draft.png'), 205, 490)]], colWidths=[247,247])
pair.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
story.extend([pair, Spacer(1,12), Paragraph('Left: own Tamil balance and slips at 390px width. Right: a draft restored after an offline reload. Measurement fields stack on a phone so three-decimal weights remain readable. The modal scrolls independently; reconnecting and a new human confirmation are required before saving.', styles['ReportBody']),
    Paragraph('Browser acceptance covered real OCR and mismatch blocking, per-user offline recovery, Finance agreements/write-off, and owner export/print. Workshop photo trials, native Tamil acceptance remain external acceptance steps. The hosted app and database health were checked separately.', styles['ReportBody'])])


def footer(c, doc):
    c.saveState()
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#78716c'))
    c.drawRightString(A4[0]-48, 28, str(doc.page))
    c.restoreState()


pdf = OUT / 'Technical_Design_Document.pdf'
doc = SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=48, rightMargin=48,
    topMargin=42, bottomMargin=45, title='KarigarFlow Technical Design', author='KarigarFlow project')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
shutil.copyfile(ROOT / 'deployment.md', OUT / 'deployment.md')
archive = OUT / 'KarigarFlow_Submission.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
    bundle.write(pdf, pdf.name)
    bundle.write(OUT / 'deployment.md', 'deployment.md')
assert archive.stat().st_size < 25 * 1024 * 1024
with zipfile.ZipFile(archive) as bundle:
    assert sorted(bundle.namelist()) == ['Technical_Design_Document.pdf', 'deployment.md']
print(f'Created {archive.name}: {archive.stat().st_size:,} bytes; exactly two files')
