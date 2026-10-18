#!/usr/bin/env python3
"""
Pré-check da voxlocal.

Verifica todos os requisitos e, para o engine F5-TTS, detecta se a GPU
é compatível (CUDA 12.1+ e compute capability ≥ 7.0). Se não for, pula
as verificações de F5 e informa que só edge/piper estão disponíveis.

Uso: python3 tools/check.py
Exit 0 = tudo OK. Exit 1 = algum requisito falhou.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Mínimo de compute capability para F5-TTS (Volta+)
GPU_MIN_CC = (7, 0)
# Mínimo de VRAM livre recomendado para F5-TTS (MB)
GPU_MIN_VRAM_MB = 2500

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


def get_gpu_info(vpy: Path) -> dict | None:
    """Retorna info da GPU via torch, ou None se torch não disponível."""
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
        r = subprocess.run([str(vpy), "-c", script],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return json.loads(r.stdout.strip())
    except Exception:
        pass
    return None


def load_voxlocal_config() -> dict:
    """Lê .data/config.json se existir, senão retorna defaults mínimos."""
    cfg_file = Path(__file__).parent.parent / ".data/config.json"
    defaults = {
        "engine": "auto",
        "piper_model": str(Path.home() / ".kiro/crew/models/piper/pt_BR-faber-medium.onnx"),
        "ref_audio":   str(Path.home() / ".kiro/crew/models/f5-tts/ref/voz_ref.wav"),
    }
    if cfg_file.exists():
        stored = json.loads(cfg_file.read_text())
        defaults.update(stored)
    return defaults


# ─────────────────────────────────────────────
print("Verificando requisitos da voxlocal...\n")
cfg = load_voxlocal_config()
engine = cfg.get("engine", "auto")

# ─── Ferramentas ───────────────────────────
print("Ferramentas:")
check("ffmpeg instalado", shutil.which("ffmpeg") is not None,
      "sudo apt install ffmpeg")
check("Python 3.10+", sys.version_info >= (3, 10))

VP  = Path.home() / ".kiro/crew-venv-current/bin/pip3"
VPY = Path.home() / ".kiro/crew-venv-current/bin/python3"
venv_ok = VP.exists()
check("venv do Kiro Crew existe", venv_ok,
      "Kiro Crew precisa estar instalado (~/.kiro/crew-venv-current/)")

# ─── Pacotes no venv ───────────────────────
if venv_ok:
    print("\nPacotes no venv:")
    for pkg in ["edge-tts", "httpx", "piper-tts"]:
        r = subprocess.run([str(VP), "show", pkg], capture_output=True)
        check(f"{pkg} instalado", r.returncode == 0,
              f"~/.kiro/crew-venv-current/bin/pip3 install {pkg}")
    # f5-tts só necessário se engine é f5 ou auto
    if engine in ("f5", "auto"):
        r = subprocess.run([str(VP), "show", "f5-tts"], capture_output=True)
        check("f5-tts instalado (engine f5)", r.returncode == 0,
              "~/.kiro/crew-venv-current/bin/pip3 install f5-tts  "
              "(requer torch com CUDA — ver docs/instalacao.md)")

# ─── Kiro Crew / Telegram ──────────────────
print("\nKiro Crew:")
try:
    crew_cfg = json.loads((Path.home() / ".kiro/crew/config.json").read_text())
    tg = crew_cfg.get("telegram", {})
    check("telegram.bot_token configurado", bool(tg.get("bot_token", "")),
          "Configure o Telegram em Settings > Channels no Kiro Crew")
    check("telegram.allowed_user_ids configurado", bool(tg.get("allowed_user_ids", [])),
          "Configure o Telegram em Settings > Channels no Kiro Crew")
    if crew_cfg.get("voice_reply", {}).get("enabled", False):
        warn("voice_reply.enabled = true — pode gerar áudio duplicado")
        print("     Recomendado: voice_reply.enabled = false no config.json do Kiro Crew")
except Exception as e:
    check("config.json do Kiro Crew acessível", False, str(e))

# ─── Modelos ───────────────────────────────
print("\nModelos:")
piper_path = Path(cfg.get("piper_model", "")).expanduser()
check("Piper model (.onnx)", piper_path.exists(),
      "Ver docs/instalacao.md — seção Mínimo")

if engine in ("f5", "auto"):
    ref_path = Path(cfg.get("ref_audio", "")).expanduser()
    check("F5-TTS ref_audio", ref_path.exists(),
          "Ver docs/instalacao.md — seção Completo (voice clone)")

# ─── GPU — compatibilidade com F5-TTS ──────
if engine in ("f5", "auto") and venv_ok:
    print("\nGPU (engine f5):")
    gpu = get_gpu_info(VPY)

    if gpu is None:
        check("torch importável", False,
              "pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121")
    elif not gpu["available"]:
        check("CUDA disponível", False,
              "GPU NVIDIA com driver instalado é necessária para engine f5. "
              "Use --engine edge ou --engine piper como alternativa.")
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
            "Use --engine edge (sem GPU) ou --engine piper (CPU) como alternativa."
        )

        if cc_ok:
            vram_ok = vram >= GPU_MIN_VRAM_MB
            if not vram_ok:
                warn(f"VRAM total {vram} MB < {GPU_MIN_VRAM_MB} MB recomendado para F5-TTS.")
                print(f"     F5-TTS pode dar OOM se o STT (whisper) também estiver ativo.")
                print(f"     Alternativa: VOX_ENGINE=edge ou VOX_DEVICE=cpu (lento).")
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
