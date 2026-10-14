"""Shared CV structure (HTML and Word): section titles, order, header data."""
import re
from pathlib import Path

ROOTS = (Path.cwd(), Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[1])

LABELS = {
    "fr": {"profile": "PROFIL", "education": "FORMATION", "experience": "EXPÉRIENCE", "project": "PROJETS", "skill": "COMPÉTENCES",
           "language": "LANGUES", "certification": "CERTIFICATIONS", "interest": "CENTRES D'INTÉRÊT", "contact": "CONTACT"},
    "it": {"profile": "PROFILO", "education": "FORMAZIONE", "experience": "ESPERIENZA", "project": "PROGETTI", "skill": "COMPETENZE",
           "language": "LINGUE", "certification": "CERTIFICAZIONI", "interest": "INTERESSI", "contact": "CONTATTI"},
    "en": {"profile": "PROFILE", "education": "EDUCATION", "experience": "EXPERIENCE", "project": "PROJECTS", "skill": "SKILLS",
           "language": "LANGUAGES", "certification": "CERTIFICATIONS", "interest": "INTERESTS", "contact": "CONTACT"},
    "es": {"profile": "PERFIL", "education": "FORMACIÓN", "experience": "EXPERIENCIA", "project": "PROYECTOS", "skill": "COMPETENCIAS",
           "language": "IDIOMAS", "certification": "CERTIFICACIONES", "interest": "INTERESES", "contact": "CONTACTO"}}
ORDER = ("education", "experience", "project", "skill", "language", "certification", "interest")
INLINE = ("skill", "language", "certification", "interest")
LICENSE = {"fr": "Permis", "it": "Patente", "en": "Driving licence", "es": "Carné de conducir"}


def resolve_photo(raw):
    """Absolute path of the photo: as written, or relative to the current folder, the project root or agents/."""
    if not raw:
        return ""
    path = Path(raw).expanduser()
    candidates = [path] if path.is_absolute() else [root / path for root in ROOTS]
    return next((str(c.resolve()) for c in candidates if c.is_file()), raw)


def parse_profile(text):
    """Read from the candidate profile the fields the CV header needs."""
    def field(label):
        match = re.search(rf"^{label}:\s*(.+)$", text, re.M)
        return match.group(1).strip() if match else ""
    license_text = re.sub(r"\s*[—(].*$", "", field("LICENSE")).strip()
    phone = re.search(r"\+?\d[\d ]{7,}\d", text.split("PHONES")[-1]) if "PHONES" in text or "Phones" in text else None
    return {"name": field("NAME"), "city": field("CITY"), "age": field("AGE"), "citizenship": field("CITIZENSHIP"),
            "license": license_text, "photo": resolve_photo(field("PHOTO").split(" (")[0]), "email": (re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text) or [""])[0],
            "links": re.findall(r"https?://[^\s·)]+", field("LINKS")), "phone": phone.group(0) if phone else ""}
