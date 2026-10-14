from cvagents.commands import ai, data, sources

SPEC = data.SPEC + sources.SPEC + ai.SPEC
HANDLERS = {name: handler for name, _, _, handler in SPEC}
