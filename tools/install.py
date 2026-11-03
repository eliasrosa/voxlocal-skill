#!/usr/bin/env python3
"""Instala ou restaura as dependências da voxlocal no venv do Kiro Crew.

O update do Kiro Crew cria um venv novo e os pacotes da voxlocal somem. Este
script reinstala o que falta (é idempotente) e baixa o modelo Piper pt-BR se ele
não existir. A skill crew-setup roda este script sozinha quando a voxlocal está
vinculada; também dá para rodar direto.

Uso:
  python3 tools/install.py            # base (edge + piper); F5-TTS se já optou por ele
  python3 tools/install.py --f5       # inclui o F5-TTS e grava o opt-in (install_f5)
  python3 tools/install.py --no-f5    # não instala o F5-TTS nesta execução
  python3 tools/install.py --dry-run  # só mostra o que faria

O F5-TTS é opt-in: entra com --f5 (que grava install_f5 = true em .data/config.json,
para os próximos updates) ou com engine f5. Ele traz ~128 pacotes (~2,5 GB, torch
incluso) para o venv do próprio Kiro Crew e pode trocar versões que o Crew usa
(ex.: pillow). O engine auto funciona sem ele: Edge e, sem rede, Piper.
Desfazer o opt-in: python3 tools/config.py set install_f5 false

Exit 0 = ok. Exit 1 = alguma etapa falhou.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as voxcfg  # noqa: E402

CREW_HOME = (os.environ.get("KIROCREW_HOME") or str(Path.home() / ".kiro/crew")).rstrip("/")
# O Crew deriva o venv do data home: <KIROCREW_HOME>-venv-current (link estável).
VENV_PY = Path(f"{CREW_HOME}-venv-current/bin/python3")
if not VENV_PY.exists():
    VENV_PY = Path(f"{CREW_HOME}-venv/bin/python3")  # instalação legada (pré-0.10)

# Fonte única das dependências: o check.py importa estas listas.
# (nome no pip, especificação para instalar)
BASE_PACKAGES = [
    ("edge-tts", "edge-tts>=7.0"),
    ("httpx", "httpx>=0.27"),
    ("piper-tts", "piper-tts>=1.2"),
]
TORCH_PACKAGES = [("torch", "torch"), ("torchaudio", "torchaudio")]
TORCH_INDEX = "https://download.pytorch.org/whl/cu121"
F5_PACKAGES = [("f5-tts", "f5-tts")]

PIPER_DEFAULT_VOICE = "pt_BR-faber-medium.onnx"
PIPER_VOICE_URL = ("https://huggingface.co/rhasspy/piper-voices/resolve/main/"
                   "pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx")


def has_nvidia_gpu() -> bool:
    if not shutil.which("nvidia-smi"):
        return False
    return subprocess.run(["nvidia-smi", "-L"], capture_output=True).returncode == 0


def f5_wanted(cfg: dict) -> bool:
    """F5-TTS deve ser instalado? Com engine f5 ou com o opt-in install_f5."""
    return str(cfg.get("engine", "auto")).lower() == "f5" or cfg.get("install_f5") is True


def pip_installed(name: str) -> bool:
    r = subprocess.run([str(VENV_PY), "-m", "pip", "show", name], capture_output=True)
    return r.returncode == 0


def missing(packages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [p for p in packages if not pip_installed(p[0])]


def pip_install(packages: list[tuple[str, str]], extra: list[str], dry: bool) -> bool:
    todo = missing(packages)
    if not todo:
        print(f"  ✓ já instalado: {', '.join(n for n, _ in packages)}")
        return True
    specs = [s for _, s in todo]
    cmd = [str(VENV_PY), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *extra, *specs]
    if dry:
        print(f"  • faria: pip install {' '.join(extra + specs)}")
        return True
    print(f"  • instalando: {' '.join(specs)}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"  ✗ falhou: pip install {' '.join(specs)}")
        return False
    print(f"  ✓ instalado: {', '.join(n for n, _ in todo)}")
    return True


def ensure_piper_model(cfg: dict, dry: bool) -> bool:
    model = Path(str(cfg.get("piper_model", ""))).expanduser()
    if model.is_file():
        print(f"  ✓ modelo Piper presente: {model.name}")
        return True
    if model.name != PIPER_DEFAULT_VOICE:
        print(f"  ✗ modelo Piper ausente: {model}")
        print("    → baixe a voz em https://huggingface.co/rhasspy/piper-voices (.onnx + .onnx.json)")
        return False
    if dry:
        print(f"  • faria: baixar {PIPER_DEFAULT_VOICE} (~60 MB) para {model.parent}")
        return True
    model.parent.mkdir(parents=True, exist_ok=True)
    for url, dest in ((PIPER_VOICE_URL, model), (PIPER_VOICE_URL + ".json", Path(f"{model}.json"))):
        print(f"  • baixando {dest.name}...")
        fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".download-")
        os.close(fd)
        try:
            urllib.request.urlretrieve(url, tmp)
            os.replace(tmp, dest)
        except OSError as exc:
            Path(tmp).unlink(missing_ok=True)
            print(f"  ✗ download falhou ({exc}): {url}")
            return False
    print(f"  ✓ modelo Piper baixado: {model}")
    return True


def ensure_crew_voice_off(dry: bool) -> None:
    """O áudio do Telegram sai pela voxlocal: o envio nativo do Crew duplicaria."""
    try:
        crew = json.loads(Path(CREW_HOME, "config.json").read_text())
    except (OSError, json.JSONDecodeError):
        print("  ⚠️  não consegui ler o config.json do Kiro Crew; confira voice_reply.enabled = false")
        return
    keys = {
        "voice_reply.enabled": crew.get("voice_reply", {}).get("enabled", False),
        "telegram.voice_replies": crew.get("telegram", {}).get("voice_replies", False),
    }
    for key, value in keys.items():
        if value is not True:
            continue
        cmd = ["kirocrew", "config", "set", key, "false"]
        if dry:
            print(f"  • faria: {' '.join(cmd)}")
            continue
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            print(f"  ✓ {key} = false (evita áudio duplicado no Telegram)")
        else:
            print(f"  ⚠️  {key} está true; rode no terminal: {' '.join(cmd)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Instala/restaura as dependências da voxlocal")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--f5", action="store_true", help="instala o F5-TTS mesmo sem uso detectado")
    g.add_argument("--no-f5", action="store_true", help="nunca instala o F5-TTS")
    ap.add_argument("--dry-run", action="store_true", help="só mostra o que faria")
    args = ap.parse_args()

    if not VENV_PY.exists():
        print(f"✗ venv do Kiro Crew não encontrado ({CREW_HOME}-venv-current). O Kiro Crew está instalado?")
        return 1
    if not shutil.which("ffmpeg"):
        print("  ⚠️  ffmpeg ausente: a conversão para OGG/Opus falha (sudo apt install ffmpeg)")

    cfg = voxcfg.load()
    ok = pip_install(BASE_PACKAGES, [], args.dry_run)
    ok = ensure_piper_model(cfg, args.dry_run) and ok

    use_f5 = args.f5 or (not args.no_f5 and f5_wanted(cfg))
    if args.f5 and not args.dry_run and cfg.get("install_f5") is not True:
        cfg["install_f5"] = True
        voxcfg.save(cfg)
        print("  • opt-in gravado: install_f5 = true (os próximos updates reinstalam o F5-TTS)")
    if use_f5:
        if not has_nvidia_gpu():
            print("  ⚠️  sem GPU NVIDIA: o F5-TTS vai rodar na CPU (lento)")
        ok = pip_install(TORCH_PACKAGES, ["--index-url", TORCH_INDEX], args.dry_run) and ok
        ok = pip_install(F5_PACKAGES, [], args.dry_run) and ok
    else:
        print("  • F5-TTS fora de uso: pulado (use --f5 para instalar)")

    ensure_crew_voice_off(args.dry_run)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
