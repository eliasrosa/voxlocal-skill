# voxlocal — Configuração

Arquivo: `~/.kiro/crew/.secrets/voxlocal.env` (chmod 600, NÃO versionar).
Formato `KEY=value`, um por linha. Uma env var do PROCESSO com o mesmo nome
tem precedência (permite override pontual: `VOX_ENGINE=f5 vox_say.sh "texto"`).

## Credenciais (obrigatórias)

| Chave | Descrição |
|-------|-----------|
| `VOX_BOT_TOKEN` | Token do bot Telegram (@BotFather). Fallback: `LUNA_BOT_TOKEN`. |
| `VOX_CHAT_ID`   | Seu chat_id no Telegram. Fallback: `LUNA_CHAT_ID`. |

## Seleção de engine

| Chave | Default | Descrição |
|-------|---------|-----------|
| `VOX_ENGINE` | `auto` | `edge` \| `f5` \| `piper` \| `auto` (edge→f5→piper) |

## Edge-TTS (Microsoft online)

| Chave | Default | Descrição |
|-------|---------|-----------|
| `VOX_EDGE_VOICE` | `pt-BR-FranciscaNeural` | Voz: Francisca (fem), `pt-BR-AntonioNeural` (masc), `pt-BR-ThalitaMultilingualNeural` (fem) |
| `VOX_EDGE_TIMEOUT` | `10` | Timeout (s) da síntese online antes de cair no fallback |

## F5-TTS (GPU local)

| Chave | Default | Descrição |
|-------|---------|-----------|
| `VOX_DEVICE` | `cuda` | `cuda` \| `cpu` (cpu é muito lento) |
| `VOX_SPEED` | `0.9` | Ritmo da fala (<1 = mais devagar) |
| `VOX_NFE_STEP` | `32` | Passos de inferência (mais = melhor dicção, mais lento) |
| `VOX_REF_AUDIO` | — | Áudio de referência ~6-10s (voz do clone) |
| `VOX_REF_TEXT` | — | Transcrição literal do áudio de referência |
| `VOX_MODEL` | `F5TTS_Base` | Arquitetura base |
| `VOX_CKPT` | — | Path do checkpoint pt-br (.safetensors) |
| `VOX_VOCAB` | — | Path do vocab.txt |

## Piper (offline, sem GPU)

| Chave | Default | Descrição |
|-------|---------|-----------|
| `VOX_PIPER_MODEL` | `~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx` | Modelo .onnx |
| `VOX_PIPER_LENGTH_SCALE` | `1.1` | Ritmo (>1 = mais devagar) |

## Envio / geral

| Chave | Default | Descrição |
|-------|---------|-----------|
| `VOX_OPUS_BITRATE` | `32k` | Bitrate do OGG/Opus |
| `VOX_SEND_TIMEOUT` | `60` | Timeout (s) do upload ao Telegram (rede lenta) |
| `VOX_MAX_CHARS` | `600` | Teto de chars por chamada (0 desliga) |

## Exemplo de env

```
VOX_BOT_TOKEN=<token>
VOX_CHAT_ID=<seu_chat_id>
VOX_ENGINE=auto
VOX_EDGE_VOICE=pt-BR-FranciscaNeural
VOX_DEVICE=cuda
VOX_SPEED=0.87
VOX_NFE_STEP=48
VOX_REF_AUDIO=~/.kiro/crew/models/f5-tts/ref/voz_ref.wav
VOX_REF_TEXT=Esta é uma amostra de voz de referência...
VOX_CKPT=~/.kiro/crew/models/f5-tts/pt-br/model_last.safetensors
VOX_VOCAB=~/.kiro/crew/models/f5-tts/F5TTS_Base/vocab.txt
VOX_PIPER_MODEL=~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx
```
