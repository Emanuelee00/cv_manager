"""Word text pieces: runs, links, paragraphs."""
from xml.sax.saxutils import escape

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
TEAL, NAVY, GREY, TEXT_WIDTH, PHOTO_EMU = "0B6E75", "1E3A5F", "555555", 10430, 740000


def run(text, bold=False, size=19, color=None, italic=False, tab=False):
    props = f'<w:sz w:val="{size}"/>' + ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + (f'<w:color w:val="{color}"/>' if color else "")
    body = ("<w:tab/>" if tab else "") + f'<w:t xml:space="preserve">{escape(text)}</w:t>'
    return f"<w:r><w:rPr>{props}</w:rPr>{body}</w:r>"


def link(text, rid):
    return f'<w:hyperlink r:id="{rid}"><w:r><w:rPr><w:color w:val="{TEAL}"/><w:u w:val="single"/><w:sz w:val="17"/></w:rPr><w:t>{escape(text)}</w:t></w:r></w:hyperlink>'


def para(runs, after=40, before=0, border=False, tabs=False, left=0, hanging=0):
    ppr = f'<w:spacing w:before="{before}" w:after="{after}"/>'
    if border:
        ppr = f'<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="1" w:color="{TEAL}"/></w:pBdr>' + ppr
    if tabs:
        ppr = f'<w:tabs><w:tab w:val="right" w:pos="{TEXT_WIDTH}"/></w:tabs>' + ppr
    if left:
        ppr += f'<w:ind w:left="{left}" w:hanging="{hanging}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{''.join(runs)}</w:p>"
