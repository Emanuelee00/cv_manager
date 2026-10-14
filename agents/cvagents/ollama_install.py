"""Install and start Ollama in a user folder, without sudo (Linux only)."""
import json
import os
import platform
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path

from cvagents.i18n import t
from cvagents.llm.ollama import DEFAULT_HOST, is_up

RELEASE_API = "https://api.github.com/repos/ollama/ollama/releases/latest"
ARCH = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}


def pick_asset(assets, machine=None):
    """Pick the right Linux archive for the architecture (.tgz or .tar.zst)."""
    arch = ARCH.get((machine or platform.machine()).lower())
    wanted = f"ollama-linux-{arch}"
    for asset in assets:
        name = asset["name"]
        if arch and name.startswith(wanted) and name.endswith((".tgz", ".tar.zst")):
            return asset
    raise RuntimeError(t("ollama.no_archive", machine=machine or platform.machine()))


def download(url, target, on_progress=None):
    with urllib.request.urlopen(url, timeout=60) as response, open(target, "wb") as out:
        total, done = int(response.headers.get("Content-Length", 0)), 0
        while block := response.read(1 << 20):
            out.write(block)
            done += len(block)
            if on_progress and total:
                on_progress("download Ollama", done / total)


def install_linux(dest, on_progress=None):
    """Download the latest release into `dest` and return the path of the `ollama` program."""
    dest = Path(dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(RELEASE_API, timeout=30) as response:
        asset = pick_asset(json.load(response)["assets"])
    archive = dest / asset["name"]
    download(asset["browser_download_url"], archive, on_progress)
    with tarfile.open(archive, "r:*") as tar:
        tar.extractall(dest, filter="data")
    archive.unlink()
    return str(dest / "bin" / "ollama")


def start_server(binary, models_dir=None, host=DEFAULT_HOST, wait=40):
    """Start `ollama serve` in the background (with its libraries next to it) and wait until it answers."""
    env = dict(os.environ)
    lib = Path(binary).resolve().parent.parent / "lib" / "ollama"
    env["LD_LIBRARY_PATH"] = f"{lib}:{env.get('LD_LIBRARY_PATH', '')}"
    if models_dir:
        env["OLLAMA_MODELS"] = str(models_dir)
    process = subprocess.Popen([binary, "serve"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(wait):
        if is_up(host):
            return process
        time.sleep(1)
    process.terminate()
    raise RuntimeError(t("ollama.start_timeout"))
