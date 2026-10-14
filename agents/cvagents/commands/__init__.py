from cvagents.commands import ai, archive, data, files, flow, sources

SPEC = data.SPEC + archive.SPEC + sources.SPEC + ai.SPEC + flow.SPEC + files.SPEC
HANDLERS = {name: handler for name, _, _, handler in SPEC}
