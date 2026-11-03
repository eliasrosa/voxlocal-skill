#!/usr/bin/env python3
"""
Pré-check da voxlocal.

Verifica os requisitos e, quando o F5-TTS está em uso, se a GPU é compatível
(CUDA disponível no torch e compute capability ≥ 7.0). Os pacotes e a regra de
"F5 em uso" vêm do tools/install.py, a fonte única das dependências.

Uso: python3 tools/check.py
Exit 0 = tudo OK. Exit 1 = algum requisito falhou.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install  # noqa: E402

# Mínimo de compute capability para F5-TTS (Volta+)
GPU_MIN_CC = (7, 0)
# Mínimo de VRAM recomendado para F5-TTS (MB)
GPU_MIN_VRAM_MB = 2500
FIX_INSTALL = "python3 tools/install.py"

ok = True


def check(label: str, result: bool, fix: str = "") -> None:
    global ok
    print(f"  {'✓' if result else '✗'} {label}")
    if not result:
        if fix:
            print(f"    → {fix}")
        ok = False


def warn(msg: str) -> None:
    """Aviso não-fatal."""
    print(f"  ⚠️  {msg}")


def get_gpu_info() -> dict | None:
    """Retorna info da GPU via torch do venv, ou None se o torch não carrega."""
    script = (
        "import torch, json; "
        "d = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None; "
        "print(json.dumps({"
        "'available': torch.cuda.is_available(),"
        "'name': d.name if d else '',"
        "'cc': [d.major, d.minor] if d else [0,0],"
        "'total_mb': d.total_memory // (1024*1024) if d else 0"
        "}))"
    )
    try:
        r = subprocess.run([str(install.VENV_PY), "-c", script],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return json.loads(r.stdout.strip())
    except Exception:
        pass
    return None


print("Verificando requisitos da voxlocal...\n")
cfg = install.voxcfg.peek()  # só lê: o check não grava nada
engine = str(cfg.get("engine", "auto")).lower()
use_f5 = install.f5_wanted(cfg)

# ─── Ferramentas ───────────────────────────
print("Ferramentas:")
check("ffmpeg instalado", shutil.which("ffmpeg") is not None, "sudo apt install ffmpeg")
check("Python 3.10+", sys.version_info >= (3, 10))
venv_ok = install.VENV_PY.exists()
check("venv do Kiro Crew existe", venv_ok,
      f"o Kiro Crew precisa estar instalado ({install.CREW_HOME}-venv-current)")

# ─── Pacotes no venv ───────────────────────
if venv_ok:
    print("\nPacotes no venv:")
    packages = list(install.BASE_PACKAGES)
    if use_f5:
        packages += install.TORCH_PACKAGES + install.F5_PACKAGES
    for name, _spec in packages:
        check(f"{name} instalado", install.pip_installed(name), FIX_INSTALL)
    if not use_f5:
        f5_ready = all(install.pip_installed(n) for n, _ in install.TORCH_PACKAGES + install.F5_PACKAGES)
        state = "instalado" if f5_ready else "não instalado (opcional: python3 tools/install.py --f5)"
        print(f"  • F5-TTS: {state}; engine {engine} não depende dele")
        if f5_ready:
            print("    (sem install_f5 = true, o próximo update do Kiro Crew remove o F5-TTS)")

# ─── Kiro Crew / Telegram ──────────────────
print("\nKiro Crew:")
try:
    crew_cfg = json.loads(Path(install.CREW_HOME, "config.json").read_text())
    tg = crew_cfg.get("telegram", {})
    check("telegram.bot_token configurado", bool(tg.get("bot_token", "")),
          "Configure o Telegram em Settings > Channels no Kiro Crew")
    check("telegram.allowed_user_ids configurado", bool(tg.get("allowed_user_ids", [])),
          "Configure o Telegram em Settings > Channels no Kiro Crew")
    if crew_cfg.get("voice_reply", {}).get("enabled", False):
        warn("voice_reply.enabled = true — o gateway também manda áudio (duplicado)")
        print(f"     Correção: {FIX_INSTALL}  (ou kirocrew config set voice_reply.enabled false)")
    if tg.get("voice_replies", False):
        warn("telegram.voice_replies = true — o gateway também manda áudio (duplicado)")
        print(f"     Correção: {FIX_INSTALL}  (ou kirocrew config set telegram.voice_replies false)")
except Exception as e:
    check("config.json do Kiro Crew acessível", False, str(e))

# ─── Modelos ───────────────────────────────
print("\nModelos:")
piper_path = Path(str(cfg.get("piper_model", ""))).expanduser()
check("Piper model (.onnx)", piper_path.is_file(), f"{FIX_INSTALL}  (baixa a voz pt-BR padrão)")
if use_f5:
    for key in ("f5_ckpt", "f5_vocab", "ref_audio"):
        p = Path(str(cfg.get(key, ""))).expanduser()
        check(f"F5-TTS {key}", p.is_file(), "ver docs/instalacao.md — seção F5-TTS")

# ─── GPU — compatibilidade com F5-TTS ──────
if use_f5 and venv_ok:
    print("\nGPU (F5-TTS):")
    gpu = get_gpu_info()
    if gpu is None:
        check("torch importável", False, FIX_INSTALL)
    elif not gpu["available"]:
        check("CUDA disponível no torch", False,
              "GPU NVIDIA com driver é necessária para o F5-TTS. "
              "Alternativa: python3 tools/config.py set engine edge")
    else:
        cc = tuple(gpu["cc"])
        vram = gpu["total_mb"]
        name = gpu["name"]
        print(f"  GPU detectada: {name}")
        print(f"  Compute capability: {cc[0]}.{cc[1]}  |  VRAM total: {vram} MB")
        cc_ok = cc >= GPU_MIN_CC
        check(
            f"Compute capability ≥ {GPU_MIN_CC[0]}.{GPU_MIN_CC[1]} (Volta+)",
            cc_ok,
            f"GPU {name} (cc {cc[0]}.{cc[1]}) não suporta F5-TTS. "
            "Use engine edge (sem GPU) ou piper (CPU).",
        )
        if cc_ok:
            if vram < GPU_MIN_VRAM_MB:
                warn(f"VRAM total {vram} MB < {GPU_MIN_VRAM_MB} MB recomendado para F5-TTS.")
                print("     F5-TTS pode dar OOM se o STT (whisper) também estiver na GPU.")
                print("     Alternativa: VOX_ENGINE=edge ou VOX_DEVICE=cpu (lento).")
            else:
                check(f"VRAM total ≥ {GPU_MIN_VRAM_MB} MB", True)

# ─── Resultado ─────────────────────────────
print()
if ok:
    print("✓ Todos os requisitos satisfeitos.")
    print("  Execute: python3 tools/vox_say.py --health  (teste de síntese completo)")
else:
    print("✗ Corrija os itens acima antes de usar a skill.")
    sys.exit(1)
