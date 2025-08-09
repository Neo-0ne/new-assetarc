
import io, os
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

WATERMARK_TEXT_DEFAULT="ASSETARC – PREVIEW ONLY"
FONT_SIZE=22

def watermark_image(raw_bytes: bytes, overlay_text: str) -> bytes:
    im=Image.open(io.BytesIO(raw_bytes)).convert('RGBA')
    W,H=im.size
    overlay=Image.new('RGBA', im.size, (255,255,255,0))
    draw=ImageDraw.Draw(overlay)
    try:
        font=ImageFont.truetype("arial.ttf", FONT_SIZE)
    except Exception:
        font=ImageFont.load_default()
    text=overlay_text or WATERMARK_TEXT_DEFAULT
    # Diagonal repeated
    step=max(200, min(W,H)//3)
    for y in range(0, H, step):
        for x in range(0, W, step):
            draw.text((x,y), text, font=font, fill=(255,0,0,70), anchor=None)
    out=Image.alpha_composite(im, overlay).convert('RGB')
    b=io.BytesIO(); out.save(b, format='JPEG', quality=85); return b.getvalue()

def watermark_pdf(raw_bytes: bytes, overlay_text: str) -> bytes:
    reader=PdfReader(io.BytesIO(raw_bytes))
    writer=PdfWriter()
    text=overlay_text or WATERMARK_TEXT_DEFAULT
    for page in reader.pages:
        packet=io.BytesIO()
        c=canvas.Canvas(packet, pagesize=letter)
        c.setFont("Helvetica-Bold", 28)
        c.setFillColorRGB(1,0,0,0.35)
        c.saveState()
        c.translate(300,400)
        c.rotate(45)
        c.drawCentredString(0,0,text)
        c.restoreState()
        c.save()
        packet.seek(0)
        wm=PdfReader(packet).pages[0]
        page.merge_page(wm)
        writer.add_page(page)
    out=io.BytesIO(); writer.write(out); return out.getvalue()
