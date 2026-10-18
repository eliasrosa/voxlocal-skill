#!/usr/bin/env python3
"""
Inicializa ~/.kiro/crew/.secrets/voxlocal.env lendo token e chat_id
diretamente do config do Kiro Crew — o usuário não precisa copiar nada.

Uso: python3 tools/setup_env.py
     python3 tools/setup_env.py --dry-run   # mostra o que seria gravado sem gravar

O script:
  1. Lê o bot_token e o primeiro allowed_user_id do config.json do Kiro Crew
  2. Verifica se voice_reply.enabled está false (recomendado para não conflitar)
  3. Cria ~/.kiro/crew/.secrets/voxlocal.env com os valores e defaults sensatos
  4. Nunca sobrescreve valores já preenchidos (modo idempotente)
"""

import json
import os
import sys
from pathlib import Path

DRY_RUN = "--dry-run" in sys.argv

CREW_CONFIG   = Path.home() / ".kiro/crew/config.json"
SECRETS_DIR   = Path.home() / ".kiro/crew/.secrets"
ENV_FILE      = SECRETS_DIR / "voxlocal.env"

# Defaults que o usuário raramente precisa mudar
DEFAULTS = {
    "VOX_ENGINE":              "auto",
    "VOX_EDGE_VOICE":          "pt-BR-AntonioNeural",
    "VOX_DEVICE":              "cuda",
    "VOX_SPEED":               "0.9",
    "VOX_NFE_STEP":            "32",
    "VOX_OPUS_BITRATE":        "32k",
    "VOX_PIPER_MODEL":         str(Path.home() / ".kiro/crew/models/piper/pt_BR-faber-medium.onnx"),
    "VOX_REF_AUDIO":           str(Path.home() / ".kiro/crew/models/f5-tts/ref/voz_ref.wav"),
    "VOX_REF_TEXT":            "Esta é uma amostra de voz de referência para síntese de fala em português.",
    "VOX_CKPT":                str(Path.home() / ".kiro/crew/models/f5-tts/pt-br/model_last.safetensors"),
    "VOX_VOCAB":               str(Path.home() / ".kiro/crew/models/f5-tts/F5TTS_Base/vocab.txt"),
}


def load_crew_config() -> dict:
    if not CREW_CONFIG.exists():
        print(f"✗ Config do Kiro Crew não encontrado: {CREW_CONFIG}")
        sys.exit(1)
    return json.loads(CREW_CONFIG.read_text())


def load_existing_env() -> dict:
    """Lê o .env atual para não sobrescrever valores já preenchidos."""
    existing = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    return existing


def main():
    cfg = load_crew_config()
    existing = load_existing_env()

    # 1. Extrair token e chat_id do Kiro Crew
    tg = cfg.get("telegram", {})
    bot_token = tg.get("bot_token", "")
    allowed   = tg.get("allowed_user_ids", [])
    chat_id   = str(allowed[0]) if allowed else ""

    if not bot_token:
        print("✗ telegram.bot_token não encontrado no config do Kiro Crew.")
        print("  Configure o Telegram em Settings > Channels > Telegram.")
        sys.exit(1)
    if not chat_id:
        print("✗ telegram.allowed_user_ids vazio no config do Kiro Crew.")
        print("  Configure o Telegram em Settings > Channels > Telegram.")
        sys.exit(1)

    # 2. Avisar se voice_reply.enabled = true (conflito potencial)
    vr = cfg.get("voice_reply", {})
    if vr.get("enabled", False):
        print("⚠️  voice_reply.enabled = true no config do Kiro Crew.")
        print("   Isso pode fazer o gateway mandar .wav automático além do voxlocal.")
        print("   Recomendado: definir voice_reply.enabled = false no config.json.")

    # 3. Montar o env final (não sobrescreve o que já existe)
    final = {}
    final["VOX_BOT_TOKEN"] = existing.get("VOX_BOT_TOKEN") or bot_token
    final["VOX_CHAT_ID"]   = existing.get("VOX_CHAT_ID")   or chat_id
    for k, default in DEFAULTS.items():
        final[k] = existing.get(k) or default

    # 4. Gerar conteúdo do .env
    lines = [
        "# voxlocal.env — gerado por setup_env.py",
        "# NÃO versionar este arquivo (chmod 600)",
        "",
        "# --- Credenciais (do Kiro Crew) ---",
        f"VOX_BOT_TOKEN={final['VOX_BOT_TOKEN']}",
        f"VOX_CHAT_ID={final['VOX_CHAT_ID']}",
        "",
        "# --- Engine ---",
        f"VOX_ENGINE={final['VOX_ENGINE']}",
        f"VOX_EDGE_VOICE={final['VOX_EDGE_VOICE']}",
        "",
        "# --- F5-TTS (GPU) ---",
        f"VOX_DEVICE={final['VOX_DEVICE']}",
        f"VOX_SPEED={final['VOX_SPEED']}",
        f"VOX_NFE_STEP={final['VOX_NFE_STEP']}",
        f"VOX_REF_AUDIO={final['VOX_REF_AUDIO']}",
        f"VOX_REF_TEXT={final['VOX_REF_TEXT']}",
        f"VOX_CKPT={final['VOX_CKPT']}",
        f"VOX_VOCAB={final['VOX_VOCAB']}",
        "",
        "# --- Piper (offline) ---",
        f"VOX_PIPER_MODEL={final['VOX_PIPER_MODEL']}",
        "",
        "# --- Envio ---",
        f"VOX_OPUS_BITRATE={final['VOX_OPUS_BITRATE']}",
    ]
    content = "\n".join(lines) + "\n"

    if DRY_RUN:
        print("--- DRY RUN (nada será gravado) ---")
        print(content)
        return

    # 5. Gravar
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(content)
    os.chmod(ENV_FILE, 0o600)
    print(f"✓ {ENV_FILE} criado/atualizado (chmod 600)")
    print(f"  BOT_TOKEN: {'*' * 10}{bot_token[-6:]}")
    print(f"  CHAT_ID:   {chat_id}")
    print()
    print("Próximo passo: python3 tools/check.py")


if __name__ == "__main__":
    main()
