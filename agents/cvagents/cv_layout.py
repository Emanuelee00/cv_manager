"""Struttura comune del CV (HTML e Word): titoli delle sezioni, ordine, dati dell'intestazione."""
import re

LABELS = {
    "fr": {"profile": "PROFIL", "education": "FORMATION", "experience": "EXPÉRIENCE", "project": "PROJETS", "skill": "COMPÉTENCES",
           "language": "LANGUES", "certification": "CERTIFICATIONS", "interest": "CENTRES D'INTÉRÊT"},
    "it": {"profile": "PROFILO", "education": "FORMAZIONE", "experience": "ESPERIENZA", "project": "PROGETTI", "skill": "COMPETENZE",
           "language": "LINGUE", "certification": "CERTIFICAZIONI", "interest": "INTERESSI"},
    "en": {"profile": "PROFILE", "education": "EDUCATION", "experience": "EXPERIENCE", "project": "PROJECTS", "skill": "SKILLS",
           "language": "LANGUAGES", "certification": "CERTIFICATIONS", "interest": "INTERESTS"}}
ORDER = ("education", "experience", "project", "skill", "language", "certification", "interest")
INLINE = ("skill", "language", "certification", "interest")
LICENSE = {"fr": "Permis", "it": "Patente", "en": "Driving licence"}



def parse_profile(text):
    """Estrae dal testo del profilo i campi che servono all'intestazione."""
    def field(label):
        match = re.search(rf"^{label}:\s*(.+)$", text, re.M)
        return match.group(1).strip() if match else ""
    license_text = re.sub(r"\s*[—(].*$", "", field("PATENTE")).strip()
    phone = re.search(r"\+?\d[\d ]{7,}\d", text.split("TELEFONI")[-1]) if "Telefoni" in text or "TELEFONI" in text else None
    return {"name": field("NOME"), "city": field("CITTÀ"), "age": field("ETÀ"), "citizenship": field("CITTADINANZA"),
            "license": license_text, "photo": field("FOTO").split(" (")[0], "email": (re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text) or [""])[0],
            "links": re.findall(r"https?://[^\s·)]+", field("LINK")), "phone": phone.group(0) if phone else ""}
