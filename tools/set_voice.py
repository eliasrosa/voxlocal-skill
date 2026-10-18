#!/usr/bin/env python3
# Re-exec para o venv do Kiro Crew se necessário
import os as _os, sys as _sys
_VENV_PY = _os.path.expanduser("~/.kiro/crew-venv-current/bin/python3")
if _os.path.isfile(_VENV_PY) and not _sys.executable.startswith(
    _os.path.expanduser("~/.kiro/crew")
):
    _os.execv(_VENV_PY, [_VENV_PY] + _sys.argv)

"""
set_voice.py — configura a voz de referência do F5-TTS.

Modos de uso:
  python3 tools/set_voice.py                        # interativo: escolha o arquivo
  python3 tools/set_voice.py /path/para/voz.wav     # arquivo já pronto
  python3 tools/set_voice.py --piper                # gera ref com Piper faber (sem microfone)
  python3 tools/set_voice.py --show                 # mostra config atual da voz

Após configurar, rode:
  python3 tools/vox_say.py --self-test              # testa a nova voz
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config as _cfg

CREW_HOME = os.environ.get("KIROCREW_HOME") or str(Path.home() / ".kiro/crew")
VPY = Path.home() / ".kiro/crew-venv-current/bin/python3"
DEFAULT_REF_DIR = os.path.join(CREW_HOME, "models/f5-tts/ref")


def show_current():
    """Mostra a configuração atual da voz de referência."""
    cfg = _cfg.load()
    ref_audio = cfg.get("ref_audio", "")
    ref_text  = cfg.get("ref_text",  "")
    print("Configuração atual:")
    print(f"  ref_audio : {ref_audio}")
    print(f"             {'✓ arquivo existe' if os.path.isfile(ref_audio) else '✗ arquivo não encontrado'}")
    print(f"  ref_text  : {ref_text[:80]}{'...' if len(ref_text) > 80 else ''}")
    print(f"  speed     : {cfg.get('speed', 0.9)}")
    print(f"  nfe_step  : {cfg.get('nfe_step', 32)}")


def generate_piper_ref() -> tuple[str, str]:
    """Gera referência sintética com Piper faber. Retorna (path, text)."""
    piper_model = os.path.join(CREW_HOME, "models/piper/pt_BR-faber-medium.onnx")
    if not os.path.isfile(piper_model):
        print(f"✗ Modelo Piper não encontrado: {piper_model}")
        print("  Instale com: ver docs/instalacao.md — seção Mínimo")
        sys.exit(1)

    ref_dir = DEFAULT_REF_DIR
    os.makedirs(ref_dir, exist_ok=True)
    ref_path = os.path.join(ref_dir, "voz_ref_piper.wav")
    ref_text = "Esta é uma amostra de voz de referência para síntese de fala em português brasileiro."

    print(f"Gerando referência com Piper faber...")
    r = subprocess.run(
        [str(VPY), "-m", "piper",
         "--model", piper_model,
         "--output_file", ref_path],
        input=ref_text.encode(),
        capture_output=True,
    )
    if r.returncode != 0:
        print(f"✗ Piper falhou: {r.stderr.decode()[:200]}")
        sys.exit(1)
    print(f"✓ Referência gerada em {ref_path}")
    return ref_path, ref_text


def validate_wav(path: str) -> bool:
    """Verifica que o arquivo é um WAV válido e tem duração adequada."""
    if not os.path.isfile(path):
        print(f"✗ Arquivo não encontrado: {path}")
        return False

    # Verificar duração com ffprobe
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", path],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print("⚠️  Não foi possível verificar a duração (ffprobe falhou)")
        return True  # aceita mesmo assim

    try:
        info = json.loads(r.stdout)
        duration = float(info.get("format", {}).get("duration", 0))
        if duration < 3:
            print(f"⚠️  Áudio muito curto ({duration:.1f}s) — recomendado ≥ 6s para melhor resultado")
        elif duration > 30:
            print(f"⚠️  Áudio longo ({duration:.1f}s) — recomendado ≤ 15s")
        else:
            print(f"✓ Duração: {duration:.1f}s (OK)")
    except Exception:
        pass

    return True


def set_voice(ref_audio: str, ref_text: str):
    """Aplica a nova configuração de voz."""
    cfg = _cfg.load()
    cfg["ref_audio"] = ref_audio
    cfg["ref_text"]  = ref_text
    _cfg.save(cfg)
    print(f"\n✓ Voz configurada:")
    print(f"  ref_audio = {ref_audio}")
    print(f"  ref_text  = {ref_text[:60]}{'...' if len(ref_text) > 60 else ''}")
    print(f"\nTeste a nova voz:")
    print(f"  python3 tools/vox_say.py --self-test")
    print(f"\nAjuste fino se necessário:")
    print(f"  python3 tools/config.py set speed 0.85    # mais devagar")
    print(f"  python3 tools/config.py set nfe_step 48   # melhor dicção")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--show":
        show_current()
        return

    if args[0] == "--piper":
        ref_audio, ref_text = generate_piper_ref()
        set_voice(ref_audio, ref_text)
        return

    # Arquivo fornecido diretamente
    ref_audio = os.path.expanduser(args[0])
    if not validate_wav(ref_audio):
        sys.exit(1)

    # Pedir transcrição
    print(f"\nArquivo: {ref_audio}")
    print("Digite a transcrição LITERAL do que é falado no áudio (palavra por palavra):")
    print("(Pressione Enter duas vezes para confirmar)")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        if line:
            lines.append(line)
    ref_text = " ".join(lines).strip()

    if not ref_text:
        print("✗ Transcrição não pode ser vazia.")
        sys.exit(1)

    set_voice(ref_audio, ref_text)


if __name__ == "__main__":
    main()
