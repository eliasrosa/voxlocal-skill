# voxlocal — Instalação

Skill de TTS pt-BR com **3 engines** e envio de voice message inline no Telegram.
Funciona com ou sem GPU.

## Engines

| Engine | GPU? | Rede? | Qualidade | Velocidade | Peso |
|--------|------|-------|-----------|------------|------|
| `edge` | não | **sim** | ★★★★☆ melhor dicção | ~3-4s | ~0 (online) |
| `f5` | **sim** | não | ★★★☆☆ voice clone | ~5-15s | ~1.35GB + torch |
| `piper` | não | não | ★★☆☆☆ robótica | ~2-5s | ~60MB |

`auto` (default): tenta `edge` → cai pro `f5` → cai pro `piper`.

## Requisitos comuns

- Python 3.10+ no venv do Kiro Crew (`~/.kiro/crew-venv-current/`)
- `ffmpeg`: `sudo apt install ffmpeg`
- Telegram configurado no Kiro Crew (Settings > Channels) — token e chat_id são lidos automaticamente

## Instalação por engine

### Mínimo — edge + piper, sem GPU

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install edge-tts piper-tts httpx
```

Baixar modelo Piper pt-BR (~60MB):

```bash
mkdir -p ~/.kiro/crew/models/piper && cd ~/.kiro/crew/models/piper
curl -fsSL -O https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx
curl -fsSL -O https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json
```

### Completo — adiciona F5-TTS na GPU

Requer GPU NVIDIA com compute capability ≥ 7.0 e ~3GB VRAM.
Verificar compatibilidade antes: `python3 tools/check.py`

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
$VP install f5-tts
```

Baixar checkpoint pt-br e gerar áudio de referência:

```bash
VPY=~/.kiro/crew-venv-current/bin/python3
$VPY - <<'PY'
from huggingface_hub import hf_hub_download
import os
d = os.path.expanduser("~/.kiro/crew/models/f5-tts")
hf_hub_download("firstpixel/F5-TTS-pt-br","pt-br/model_last.safetensors",local_dir=d)
hf_hub_download("SWivid/F5-TTS","F5TTS_Base/vocab.txt",local_dir=d)
PY

# Gerar áudio de referência com Piper faber
FRASE="Esta é uma amostra de voz de referência para síntese de fala em português."
REF=~/.kiro/crew/models/f5-tts/ref/voz_ref.wav
mkdir -p "$(dirname $REF)"
echo "$FRASE" | $VPY -m piper \
  --model ~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx \
  --output_file "$REF"

# Configurar os paths no config.json
python3 ~/.kiro/skills/voxlocal/tools/config.py set ref_audio "$REF"
python3 ~/.kiro/skills/voxlocal/tools/config.py set ref_text "$FRASE"
```

> Para usar voz humana real (melhor dicção): gravar ~10s limpos no lugar do `$REF`,
> atualizar `ref_text` com a transcrição literal via `config.py set ref_text "..."`.

## Configuração

As configurações de comportamento ficam em `.data/config.json`:

```bash
python3 tools/config.py                      # ver configuração atual
python3 tools/config.py set engine edge      # trocar engine padrão
```

Ver `docs/configuracao.md` para a lista completa de chaves.

## Validar

```bash
python3 tools/check.py                                  # pré-check completo
bash tools/vox_say.sh --health                          # health check
bash tools/vox_say.sh --engine piper                    # definir engine padrão
bash tools/vox_say.sh "teste de voz funcionando"        # teste real
```

## Rebuild do venv do Kiro Crew

O auto-update do Kiro Crew recria o venv → torch/f5/edge/piper somem.
Reinstale rodando os `pip install` acima.
Os modelos em `~/.kiro/crew/models/` **não somem** (ficam fora do venv).
