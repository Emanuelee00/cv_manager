"""The three CV styles. Each has a renderer, its reading order for ATS checks, and the layout facts used for its ATS score."""
from cvagents.cv_layout import parse_profile
from cvagents.layouts import classic, sidebar

STYLES = {
    "classic": {"render": lambda p, cv, lang, scale=1: classic.render(p, cv, lang, "classic.css"), "order": classic.reading_order,
                "columns": 1, "bars": False, "icons": False},
    "minimal": {"render": lambda p, cv, lang, scale=1: classic.render(p, cv, lang, "minimal.css"), "order": classic.reading_order,
                "columns": 1, "bars": False, "icons": False},
    "modern": {"render": sidebar.render, "order": sidebar.reading_order, "columns": 2, "bars": True, "icons": True},
}


def render_html(style, profile_text, cv, lang, scale=1.0):
    return STYLES[style]["render"](parse_profile(profile_text), cv, lang, scale)


def reading_order(style, cv):
    return STYLES[style]["order"](cv)


__all__ = ["STYLES", "reading_order", "render_html"]
