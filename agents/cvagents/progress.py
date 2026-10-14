"""Barra di avanzamento a una riga per download e operazioni lunghe."""


def progress(status, fraction):
    shown = f"{fraction:4.0%}" if fraction is not None else "  ..."
    print(f"\r{shown} {status[:50]:<50}", end="", flush=True)
