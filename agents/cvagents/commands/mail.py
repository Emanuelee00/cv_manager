"""Mail command: mail-eml builds a .eml file that really carries the CV as an attachment, then reads it back to prove it."""
from email import message_from_bytes, policy
from email.message import EmailMessage
from pathlib import Path

from cvagents.i18n import t

HEADERS = {"À": "to", "Objet": "subject", "Pièce jointe": "attachment"}


def parse_mail(text):
    """Split a mail file (header lines 'À :', 'Objet :', 'Pièce jointe :', a blank line, then the body)."""
    head, _, body = text.partition("\n\n")
    found = {}
    for line in head.splitlines():
        label, _, value = line.partition(" :")
        if label in HEADERS:
            found[HEADERS[label]] = value.strip()
    if not found.get("attachment"):
        raise ValueError(t("cmd.eml_no_attachment"))
    return found["to"], found["subject"], found["attachment"].split()[0], body.strip() + "\n"


def mail_eml_cmd(args, conn):
    """Build mail_<offer>.eml from the mail text, its HTML version and the CV PDF; read the attachment back from the file."""
    to, subject, name, body = parse_mail(Path(args.mail_txt).read_text(encoding="utf8"))
    msg = EmailMessage()
    msg["To"], msg["Subject"], msg["X-Unsent"] = to, subject, "1"
    msg.set_content(body)
    msg.add_alternative(Path(args.mail_html).read_text(encoding="utf8"), subtype="html")
    msg.add_attachment(Path(args.cv_pdf).read_bytes(), maintype="application", subtype="pdf", filename=name)
    out = Path(args.mail_txt).with_suffix(".eml")
    out.write_bytes(bytes(msg))
    kept = [part for part in message_from_bytes(out.read_bytes(), policy=policy.default).iter_attachments()]
    return t("cmd.eml", file=out, attachment=", ".join(p.get_filename() for p in kept), size=sum(len(p.get_content()) for p in kept) // 1024)


SPEC = [
    ("mail-eml", "Build a .eml with the CV really attached (and prove it)", [("mail_txt", {}), ("mail_html", {}), ("cv_pdf", {})], mail_eml_cmd),
]
