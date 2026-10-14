"""The .docx file: a zip with document, relationships, styles and photo."""
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from cvagents.word.parts import W

RELS_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def content_types(has_png):
    png = '<Default Extension="png" ContentType="image/png"/>' if has_png else ""
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>' + png +
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')


STYLES = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr>'
          '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="19"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>')
ROOT_RELS = (f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             f'<Relationship Id="rId1" Type="{RELS_BASE}/officeDocument" Target="word/document.xml"/></Relationships>')


def write_package(path, body, rels, photo):
    """Write the document zip: content, relationships (links and photo), styles."""
    page = (f'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="620" w:right="737" w:bottom="620" w:left="737" '
            f'w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>')
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>{body}{page}</w:body></w:document>'
    rel_items = "".join(f'<Relationship Id="{rid}" Type="{RELS_BASE}/{kind}" Target="{escape(target)}"' +
                        (' TargetMode="External"' if kind == "hyperlink" else "") + "/>" for rid, kind, target in rels)
    rel_items += f'<Relationship Id="rIdSt" Type="{RELS_BASE}/styles" Target="styles.xml"/>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(bool(photo)))
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/_rels/document.xml.rels", f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rel_items}</Relationships>')
        if photo:
            z.write(photo, "word/media/foto.png")
    return Path(path)
