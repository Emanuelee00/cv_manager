import tempfile
import unittest
from argparse import Namespace
from email import message_from_bytes, policy
from pathlib import Path

from cvagents.commands.mail import mail_eml_cmd

PDF = b"%PDF-1.4 fake cv bytes"
MAIL = "À : a@b.fr\nObjet : Candidature\nPièce jointe : CV_Test.pdf (copie)\n\nBonjour,\n\nMon CV est en pièce jointe.\n"


def write_files(mail=MAIL):
    folder = Path(tempfile.mkdtemp())
    (folder / "mail_x.txt").write_text(mail, encoding="utf8")
    (folder / "mail_x.html").write_text("<p>Bonjour</p>", encoding="utf8")
    (folder / "cv.pdf").write_bytes(PDF)
    return Namespace(mail_txt=folder / "mail_x.txt", mail_html=folder / "mail_x.html", cv_pdf=folder / "cv.pdf")


class MailEml(unittest.TestCase):
    def test_eml_carries_the_cv_under_the_name_in_the_header(self):
        args = write_files()
        mail_eml_cmd(args, None)
        msg = message_from_bytes(args.mail_txt.with_suffix(".eml").read_bytes(), policy=policy.default)
        attachments = list(msg.iter_attachments())
        self.assertEqual([a.get_filename() for a in attachments], ["CV_Test.pdf"])
        self.assertEqual(attachments[0].get_content(), PDF)
        self.assertEqual((msg["To"], msg["Subject"]), ("a@b.fr", "Candidature"))

    def test_body_has_no_header_lines(self):
        args = write_files()
        mail_eml_cmd(args, None)
        msg = message_from_bytes(args.mail_txt.with_suffix(".eml").read_bytes(), policy=policy.default)
        self.assertNotIn("Pièce jointe :", msg.get_body(("plain",)).get_content())

    def test_mail_without_attachment_line_is_refused(self):
        with self.assertRaises(ValueError):
            mail_eml_cmd(write_files("À : a@b.fr\nObjet : x\n\nBonjour"), None)


if __name__ == "__main__":
    unittest.main()
