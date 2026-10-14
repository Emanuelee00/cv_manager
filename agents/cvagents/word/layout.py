"""Word header photo: a round picture floating on the right, so name and contacts stay plain text (ATS friendly)."""
import struct

from cvagents.word.parts import PHOTO_EMU

DRAWING = ('xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
           'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


def graphic(rid, size):
    return (f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="0" name="photo.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{size}" cy="{size}"/></a:xfrm><a:prstGeom prst="ellipse"/></pic:spPr>'
            f'</pic:pic></a:graphicData></a:graphic>')


def floating_picture(rid, size=PHOTO_EMU):
    """A run with the photo anchored to the top right margin; the text wraps on its left. No table, no text box."""
    return (f'<w:r><w:drawing><wp:anchor {DRAWING} distT="0" distB="0" distL="114300" distR="0" simplePos="0" relativeHeight="1" '
            f'behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0"/>'
            f'<wp:positionH relativeFrom="margin"><wp:align>right</wp:align></wp:positionH>'
            f'<wp:positionV relativeFrom="margin"><wp:posOffset>0</wp:posOffset></wp:positionV>'
            f'<wp:extent cx="{size}" cy="{size}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapSquare wrapText="left"/>'
            f'<wp:docPr id="1" name="Photo"/><wp:cNvGraphicFramePr/>{graphic(rid, size)}</wp:anchor></w:drawing></w:r>')
