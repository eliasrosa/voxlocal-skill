# voxlocal — Instalação

Skill de TTS pt-BR com **3 engines** e envio de voice message inline no Telegram.
Feita para ser **compartilhável**: funciona com ou sem GPU.

## Engines

| Engine | Runtime | GPU? | Rede? | Qualidade | Velocidade | Peso |
|--------|---------|------|-------|-----------|------------|------|
| `edge`  | Microsoft Edge-TTS | não | **sim** | melhor dicção | ~3-4s | ~0 (online) |
| `f5`    | F5-TTS local | **sim** | não | boa (voice clone) | ~5-15s | ~1.35GB + torch |
| `piper` | Piper local | não | não | robótica | ~2-5s | ~60MB |

`auto` (default): tenta `edge` → cai pro `f5` → cai pro `piper`.

## Requisitos comuns

- Python 3.12 (usa o venv do Kiro Crew: `~/.kiro/crew-venv-current/bin/python3`)
- `ffmpeg` (conversão OGG/Opus). No Debian/Ubuntu: `sudo apt install ffmpeg`.
- Um bot do Telegram (token do @BotFather) e o seu `chat_id`.

## Instalação por engine (instale só o que for usar)

### Mínimo (só `edge` + `piper`, SEM GPU — recomendado para compartilhar)

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install edge-tts piper-tts httpx
```

Baixe um modelo Piper pt-BR (~60MB), ex. faber:

```bash
mkdir -p ~/.kiro/crew/models/piper && cd ~/.kiro/crew/models/piper
curl -fsSL -o pt_BR-faber-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx
curl -fsSL -o pt_BR-faber-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json
```

### Completo (adiciona `f5` na GPU)

Requer GPU NVIDIA (~3GB VRAM livre) + driver compatível com CUDA 12.1.

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
$VP install f5-tts
```

Baixe o checkpoint pt-br + vocab e uma voz de referência (~6-10s):

```bash
VPY=~/.kiro/crew-venv-current/bin/python3
$VPY - <<'PY'
from huggingface_hub import hf_hub_download
import os
d = os.path.expanduser("~/.kiro/crew/models/f5-tts")
hf_hub_download("firstpixel/F5-TTS-pt-br","pt-br/model_last.safetensors",local_dir=d)
hf_hub_download("SWivid/F5-TTS","F5TTS_Base/vocab.txt",local_dir=d)
PY
# referência: gerar com o piper faber (ou usar uma gravação humana ~10s)
echo "Amostra de voz de referência." | $VPY -m piper \
  -m ~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx \
  -f ~/.kiro/crew/models/f5-tts/ref/voz_ref.wav
```

## Config (`~/.kiro/crew/.secrets/voxlocal.env`, chmod 600)

Ver `docs/configuracao.md` para a lista completa de variáveis.

## Validar

```bash
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --health
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --engine piper   # define o padrão
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh "teste"
```

## Rebuild do venv do Kiro Crew

O auto-update do Kiro Crew recria o venv em updates minor/major → torch/f5/edge/piper
somem. Reinstale rodando os `pip install` acima. Os modelos em
`~/.kiro/crew/models/` NÃO somem (ficam fora do venv).
