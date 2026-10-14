"""Anagrafica e preferenze del candidato, nel formato che gli agenti leggono dal database."""
import json

from cvagents.db import get_item, upsert_item

FIELDS = (("name", "Nome e cognome"), ("headline", "Titolo (es. Étudiant en informatique, Développeur web)"),
          ("city", "Città e Paese"), ("email", "Email"), ("phones", "Telefono/i (separati da virgola)"),
          ("links", "Link: GitHub, LinkedIn, portfolio (separati da spazio)"), ("github_login", "Nome utente GitHub (può essere vuoto)"))
OPTIONAL = (("age", "Età (es. 26 ans), vuoto se non vuoi indicarla"),
            ("citizenship", "Cittadinanza (es. italiana, cittadino UE), vuoto per non indicarla"),
            ("license", "Patente (es. B), vuoto per non indicarla"), ("photo", "Percorso di una foto per il CV (vuoto = nessuna foto)"))


def profile_body(data):
    lines = [f"NOME: {data['name']}", f"TITOLO BASE: {data['headline']}", f"CITTÀ: {data['city']}"]
    for key, label in (("age", "ETÀ"), ("citizenship", "CITTADINANZA"), ("license", "PATENTE"),
                       ("github_login", "LOGIN GITHUB"), ("photo", "FOTO")):
        if data.get(key):
            lines.append(f"{label}: {data[key]}")
    lines += [f"LINK: {data.get('links', '')} · email {data['email']}", "TELEFONI: vedi manual:profilo-telefoni"]
    return "\n".join(lines)


def preferences_body(data):
    shown = [label for key, label in (("age", "età"), ("citizenship", "cittadinanza"), ("license", "patente"),
                                      ("photo", "foto")) if data.get(key)]
    return ("Preferenze del candidato (decisioni definitive, gli agenti le applicano senza riproporle):\n"
            "FORMA: una sola pagina; ordine Profil → Formation → Expérience → Projets → Compétences → Langues → "
            "Certifications → Centres d'intérêt; nessuna parola ripetuta.\n"
            f"DATI PERSONALI DA MOSTRARE: {', '.join(shown) or 'solo nome e contatti'}; stato civile mai.\n"
            "PROGETTI ESCLUSI: nessuno finora.")


def save_profile(conn, data):
    upsert_item(conn, "manual:profilo-candidato", "manual", "profile", "Anagrafica del candidato", profile_body(data))
    old = get_item(conn, "manual:preferenze-candidato")
    upsert_item(conn, "manual:preferenze-candidato", "manual", "preferences", "Preferenze e decisioni del candidato",
                old["body"] if old else preferences_body(data), json.loads(old["meta"]) if old else {"excluded_ids": []})
    phones = data.get("phones", "")
    if phones:
        upsert_item(conn, "manual:profilo-telefoni", "manual", "profile", "Telefoni e regola di scelta",
                    f"Telefoni: {phones}. Se l'offerta è in un Paese con un solo numero locale, usa solo quello; altrimenti il primo.")
    return data["name"]


def set_excluded(conn, item_id, excluded=True):
    """Esclude (o riammette) una voce dal CV, nelle preferenze del candidato. Ritorna l'elenco aggiornato."""
    old = get_item(conn, "manual:preferenze-candidato")
    body, meta = (old["body"], json.loads(old["meta"])) if old else ("Preferenze del candidato.", {})
    ids = set(meta.get("excluded_ids", []))
    ids = ids | {item_id} if excluded else ids - {item_id}
    upsert_item(conn, "manual:preferenze-candidato", "manual", "preferences", "Preferenze e decisioni del candidato",
                body, {**meta, "excluded_ids": sorted(ids)})
    return sorted(ids)
