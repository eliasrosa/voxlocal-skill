#!/usr/bin/env bash
# vox_say.sh — wrapper da skill voxlocal (TTS local F5-TTS pt-br na GPU + Telegram).
#
# O agente chama apenas:  vox_say.sh "texto do resumo"
# Credenciais e config do modelo são lidas de ~/.kiro/crew/.secrets/voxlocal.env
# (nunca passam pela linha de comando, então não vazam no chat).
#
# Uso:
#   vox_say.sh "texto"        -> sintetiza na GPU e envia a voice message ao Telegram
#   vox_say.sh --health       -> checa GPU/torch/f5-tts/ffmpeg/credenciais
#   vox_say.sh --self-test    -> sintetiza uma frase curta e envia
#
# Roda o vox_say.py com o Python do venv do Kiro Crew (onde torch+f5-tts ficam).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python do venv real do Kiro Crew (tem torch/f5-tts). Fallback pro python3 do PATH.
VOX_PYTHON="${VOX_PYTHON:-/home/elias/.kiro/crew-venv-current/bin/python3}"
if [[ ! -x "$VOX_PYTHON" ]]; then
  VOX_PYTHON="$(command -v python3)"
fi

exec "$VOX_PYTHON" "$HERE/vox_say.py" "$@"
