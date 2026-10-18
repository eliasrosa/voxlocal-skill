#!/usr/bin/env python3
"""
Gerenciador de configuração da voxlocal.

Lê e grava .data/config.json. Credenciais (token, chat_id) são sempre
lidas do Kiro Crew — não ficam aqui. Apenas variáveis opcionais de comportamento.

Uso:
  python3 tools/config.py                      # ver configuração atual
  python3 tools/config.py set <chave> <valor>  # alterar um valor
  python3 tools/config.py reset                # restaurar defaults
"""

import json
import sys
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / ".data"
CONFIG_FILE = DATA_DIR / "config.json"

# Defaults — valores usados quando a chave não está no config.json
DEFAULTS: dict = {
    "engine":           "auto",          # edge | f5 | piper | auto
    "edge_voice":       "pt-BR-AntonioNeural",
    "edge_timeout":     10,
    "device":           "cuda",          # cuda | cpu
    "speed":            0.9,             # ritmo F5-TTS (<1 = mais devagar)
    "nfe_step":         32,              # passos F5 (mais = melhor dicção)
    "opus_bitrate":     "32k",
    "send_timeout":     60,
    "max_chars":        600,             # 0 = sem limite
    "piper_model":      str(Path.home() / ".kiro/crew/models/piper/pt_BR-faber-medium.onnx"),
    "piper_length_scale": 1.1,
    "ref_audio":        str(Path.home() / ".kiro/crew/models/f5-tts/ref/voz_ref.wav"),
    "ref_text":         "Esta é uma amostra de voz de referência para síntese de fala em português.",
    "f5_ckpt":          str(Path.home() / ".kiro/crew/models/f5-tts/pt-br/model_last.safetensors"),
    "f5_vocab":         str(Path.home() / ".kiro/crew/models/f5-tts/F5TTS_Base/vocab.txt"),
}

HELP: dict = {
    "engine":           "Engine de síntese: edge (Microsoft online), f5 (GPU local), piper (offline CPU), auto",
    "edge_voice":       "Voz do Edge-TTS. Opções: pt-BR-AntonioNeural, pt-BR-FranciscaNeural, pt-BR-ThalitaMultilingualNeural",
    "edge_timeout":     "Timeout (s) do Edge-TTS antes de cair no fallback",
    "device":           "Dispositivo para F5-TTS: cuda ou cpu",
    "speed":            "Ritmo da fala no F5-TTS (0.85-1.0; menor = mais devagar)",
    "nfe_step":         "Passos de inferência do F5-TTS (32-48; mais = melhor dicção, mais lento)",
    "opus_bitrate":     "Bitrate do OGG/Opus enviado ao Telegram",
    "send_timeout":     "Timeout (s) do upload ao Telegram",
    "max_chars":        "Teto de caracteres por chamada (0 = sem limite)",
    "piper_model":      "Path do modelo Piper .onnx",
    "piper_length_scale": "Ritmo do Piper (>1 = mais devagar)",
    "ref_audio":        "Path do áudio de referência para voice clone do F5-TTS (~6-10s)",
    "ref_text":         "Transcrição literal do áudio de referência (obrigatório para F5-TTS)",
    "f5_ckpt":          "Path do checkpoint F5-TTS pt-br (.safetensors)",
    "f5_vocab":         "Path do vocab.txt do F5-TTS",
}


def load() -> dict:
    """Carrega config do disco, preenchendo defaults para chaves ausentes."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULTS, ensure_ascii=False, indent=2))
        return dict(DEFAULTS)
    stored = json.loads(CONFIG_FILE.read_text())
    for k, v in DEFAULTS.items():
        stored.setdefault(k, v)
    return stored


def save(cfg: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


def get_config() -> dict:
    """Retorna a configuração atual. Uso nos outros scripts da skill."""
    return load()


def show(cfg: dict) -> None:
    print(f"Configuração em {CONFIG_FILE}\n")
    for k, v in cfg.items():
        desc = HELP.get(k, "")
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)}")
        if desc:
            print(f"    {desc}")


def main() -> None:
    args = sys.argv[1:]
    cfg  = load()

    if not args:
        show(cfg)
        return

    if args[0] == "reset":
        save(dict(DEFAULTS))
        print("✓ Configuração restaurada para os defaults.")
        return

    if args[0] == "set" and len(args) >= 3:
        key, value = args[1], " ".join(args[2:])
        for cast in (int, float):
            try:
                value = cast(value)
                break
            except ValueError:
                pass
        if isinstance(value, str) and value.lower() in ("true", "false"):
            value = value.lower() == "true"
        cfg[key] = value
        save(cfg)
        print(f"✓ {key} = {json.dumps(value, ensure_ascii=False)}")
        return

    print("Uso:")
    print("  python3 config.py                      # ver configuração")
    print("  python3 config.py set <chave> <valor>  # alterar valor")
    print("  python3 config.py reset                # restaurar defaults")
    sys.exit(1)


if __name__ == "__main__":
    main()
