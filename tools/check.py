#!/usr/bin/env python3
"""
Pré-check da voxlocal.
Uso: python3 tools/check.py
Exit 0 = tudo OK. Exit 1 = algum requisito falhou.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ok = True


def check(label: str, result: bool, fix: str = "") -> None:
    global ok
    print(f"  {'✓' if result else '✗'} {label}")
    if not result:
        if fix:
            print(f"    → {fix}")
        ok = False


print("Verificando requisitos da voxlocal...\n")

# --- Ferramentas ---
print("Ferramentas:")
check("ffmpeg instalado", shutil.which("ffmpeg") is not None,
      "sudo apt install ffmpeg")
check("Python 3.10+", sys.version_info >= (3, 10))

VP = Path.home() / ".kiro/crew-venv-current/bin/pip3"
venv_ok = VP.exists()
check("venv do Kiro Crew existe", venv_ok,
      "Kiro Crew precisa estar instalado (~/.kiro/crew-venv-current/)")

# --- Pacotes no venv ---
if venv_ok:
    print("\nPacotes no venv:")
    for pkg in ["edge-tts", "httpx", "f5-tts", "piper-tts"]:
        r = subprocess.run([str(VP), "show", pkg], capture_output=True)
        check(f"{pkg} instalado", r.returncode == 0,
              f"~/.kiro/crew-venv-current/bin/pip3 install {pkg}")

# --- Credenciais via Kiro Crew ---
print("\nKiro Crew (credenciais):")
try:
    import json as _json
    crew_cfg = _json.loads(open(Path.home() / ".kiro/crew/config.json").read())
    tg = crew_cfg.get("telegram", {})
    has_token   = bool(tg.get("bot_token", ""))
    has_chat_id = bool(tg.get("allowed_user_ids", []))
    check("telegram.bot_token configurado", has_token,
          "Configure o Telegram em Settings > Channels no Kiro Crew")
    check("telegram.allowed_user_ids configurado", has_chat_id,
          "Configure o Telegram em Settings > Channels no Kiro Crew")
    voice_reply_on = crew_cfg.get("voice_reply", {}).get("enabled", False)
    if voice_reply_on:
        print("  ⚠️  voice_reply.enabled = true — pode gerar áudio automático duplicado")
        print("     Recomendado: voice_reply.enabled = false no config.json do Kiro Crew")
except Exception as e:
    check("config.json do Kiro Crew acessível", False, str(e))

# --- Modelos ---
print("\nModelos:")
models_dir = Path.home() / ".kiro/crew/models"

piper_model = Path(env_vars.get("VOX_PIPER_MODEL",
    str(models_dir / "piper/pt_BR-faber-medium.onnx"))).expanduser()
check("Piper model (pt_BR-faber-medium.onnx)", piper_model.exists(),
      "Ver docs/instalacao.md — seção 'Mínimo (só edge + piper)'")

ref_audio = Path(env_vars.get("VOX_REF_AUDIO",
    str(models_dir / "f5-tts/ref/voz_ref.wav"))).expanduser()
check("F5-TTS ref audio", ref_audio.exists(),
      "Ver docs/instalacao.md — seção 'Completo (adiciona f5 na GPU)'")

# --- GPU (opcional) ---
engine = env_vars.get("VOX_ENGINE", "auto")
if engine in ("f5", "auto"):
    print("\nGPU (necessário para engine f5):")
    try:
        VPY = Path.home() / ".kiro/crew-venv-current/bin/python3"
        r = subprocess.run(
            [str(VPY), "-c", "import torch; print(torch.cuda.is_available())"],
            capture_output=True, text=True, timeout=10
        )
        cuda_ok = r.stdout.strip() == "True"
        check("torch CUDA disponível", cuda_ok,
              "Instalar torch com CUDA: ver docs/instalacao.md")
    except Exception:
        check("torch importável", False,
              "~/.kiro/crew-venv-current/bin/pip3 install torch torchaudio "
              "--index-url https://download.pytorch.org/whl/cu121")

print()
if ok:
    print("✓ Todos os requisitos satisfeitos. Execute vox_say.sh --health para teste completo.")
else:
    print("✗ Corrija os itens acima antes de usar a skill.")
    sys.exit(1)
