"""AI commands: doctor (checks, installing Ollama and downloading the local model)."""
from cvagents import doctor, local_setup, ollama_install, sysinfo
from cvagents.i18n import t
from cvagents.llm import ollama
from cvagents.progress import progress


def install_step(args):
    binary = ollama_install.install_linux(args.install_here, progress)
    return "\n" + t("cmd.ollama_installed", path=binary)


def pull_step(args):
    binary = local_setup.find_ollama(args.install_here or ())
    if not ollama.is_up() and binary:
        ollama_install.start_server(binary, args.models_dir)
    model = args.model or local_setup.pick_model(sysinfo.total_ram_gb())
    local_setup.pull_model(model, on_progress=progress)
    return "\n" + t("cmd.model_ready", model=model)


def doctor_cmd(args, conn):
    steps = ([install_step] if args.install_here else []) + ([pull_step] if args.pull else [])
    done = [step(args) for step in steps]
    return "\n".join(done + doctor.report())


SPEC = [
    ("doctor", "Check what the AI needs; --install-here and --pull for the local model", [
        ("--install-here", {"default": None, "help": "install Ollama in this folder, without sudo (Linux)"}),
        ("--pull", {"action": "store_true", "help": "download the suggested model"}),
        ("--model", {"default": None}), ("--models-dir", {"default": None})], doctor_cmd),
]
