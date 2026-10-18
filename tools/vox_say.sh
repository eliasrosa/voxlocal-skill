#!/usr/bin/env bash
# vox_say.sh — wrapper da skill voxlocal (TTS pt-BR para Telegram).
#
# Uso:
#   vox_say.sh "texto"        # sintetiza e envia voice message ao Telegram
#   vox_say.sh --health       # diagnóstico: ffmpeg, pacotes, Kiro Crew, modelos
#   vox_say.sh --self-test    # sintetiza uma frase curta e envia
#   vox_say.sh --engine edge  # troca engine padrão (edge|f5|piper|auto)
#
# Credenciais (token, chat_id) lidas do Kiro Crew automaticamente.
# Configuração de comportamento em .data/config.json — ver tools/config.py.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python do venv do Kiro Crew (onde torch/f5-tts/edge-tts/piper-tts ficam).
# Sobrescreva VOX_PYTHON para usar outro interpretador.
VOX_PYTHON="${VOX_PYTHON:-~/.kiro/crew-venv-current/bin/python3}"
VOX_PYTHON="${VOX_PYTHON/#\~/$HOME}"   # expande ~ manualmente (não expandida em aspas)

if [[ ! -x "$VOX_PYTHON" ]]; then
  VOX_PYTHON="$(command -v python3)"
fi

exec "$VOX_PYTHON" "$HERE/vox_say.py" "$@"
