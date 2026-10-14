"""Language detection (fr, it, en, es) from the most frequent function words."""
import re

WORDS = {"fr": set("le la les des une est pour avec dans nous vous sur du au aux".split()),
         "it": set("il lo gli una per con che nel nella sono del della delle e di".split()),
         "en": set("the and for with you our are will your of to in is".split()),
         "es": set("el los las una para con que del por en es somos tu nuestro buscamos y".split())}


def detect_lang(text):
    tokens = re.findall(r"\w+", text.lower())
    return max(WORDS, key=lambda lang: sum(t in WORDS[lang] for t in tokens))
