from cvagents.commands import ai, archive, data, flow, sources

SPEC = data.SPEC + archive.SPEC + sources.SPEC + ai.SPEC + flow.SPEC
HANDLERS = {name: handler for name, _, _, handler in SPEC}
