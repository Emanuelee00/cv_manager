"""Intestazione Word: foto rotonda e tabella senza bordi."""
import struct

from cvagents.word.parts import PHOTO_EMU, TEXT_WIDTH, para

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


DRAWING = ('xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
           'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def picture(rid, size=PHOTO_EMU):
    return (f'<w:r><w:drawing><wp:inline {DRAWING}><wp:extent cx="{size}" cy="{size}"/><wp:docPr id="1" name="Foto"/>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="0" name="foto.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{size}" cy="{size}"/></a:xfrm><a:prstGeom prst="ellipse"/></pic:spPr>'
            f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def cell(content, width):
    return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>{content}</w:tc>'


def header_table(left, right):
    none = "".join(f'<w:{s} w:val="nil"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/><w:tblBorders>{none}</w:tblBorders></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{TEXT_WIDTH - 1300}"/><w:gridCol w:w="1300"/></w:tblGrid><w:tr>'
            f'{cell(left, TEXT_WIDTH - 1300)}{cell(right or para([]), 1300)}</w:tr></w:tbl>')
