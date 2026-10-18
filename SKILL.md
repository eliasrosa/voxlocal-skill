---
name: voxlocal
description: Use when TTS or voice message is needed in a Telegram conversation. Local TTS (F5-TTS pt-br GPU, Edge-TTS online, Piper offline) sends voice messages inline via Telegram sendVoice. On-demand only — never send audio automatically.
inclusion: auto
---

# voxlocal — TTS local pt-BR para Telegram

Skill de síntese de voz com 3 engines: F5-TTS local na GPU, Edge-TTS Microsoft online, e Piper offline. Envia voice message diretamente no Telegram via `sendVoice`.

## Quando usar

- **Só sob demanda no Telegram**: quando o usuário pedir áudio/voz explicitamente.
- **NUNCA** enviar áudio automaticamente.
- No **dashboard** NÃO usar esta skill — o dashboard usa o Piper nativo do Kiro Crew.

## Como usar

Chamar o wrapper com o texto do resumo:

```bash
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh "resumo curto aqui"
```

- Teto de **600 chars** por chamada. Resposta longa → quebrar em 2-3 partes e
  chamar em sequência (mesma regra do LunaSpeak).
- Resumo sem markdown/URL/código, ~350-450 chars ideal.

### Engines (VOX_ENGINE)

Selecionável e persistente no env, estilo `--mode` do LunaSpeak:

- `edge` → **Microsoft Edge-TTS online** (voz Francisca, melhor dicção, sem GPU,
  ~3-4s; precisa de internet)
- `f5` → **F5-TTS local na GPU** (offline, voice clone, ~5-15s, ~1.35GB)
- `piper` → **Piper offline na CPU** (leve/portável ~60MB, sem GPU nem rede, robótica)
- `auto` (default) → Edge → fallback F5 → fallback Piper

Trocar o engine padrão (grava no env):

```bash
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --engine edge   # ou f5 | piper | auto
```

Forçar numa chamada só, sem persistir: `VOX_ENGINE=f5 vox_say.sh "texto"`.
Voz do Edge: `VOX_EDGE_VOICE` (pt-BR-FranciscaNeural fem, pt-BR-AntonioNeural masc,
pt-BR-ThalitaMultilingualNeural fem).

**Docs completos:** `docs/instalacao.md` (setup dos 3 engines, compartilhável),
`docs/configuracao.md` (todas as variáveis), `docs/runbook.md` (troubleshooting).

Checar saúde antes do primeiro uso na sessão:

```bash
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --health
```

## Arquitetura

`texto → F5-TTS pt-br (GPU, load sob demanda) → wav → ffmpeg OGG/Opus → Telegram sendVoice`

- **Modelo carregado sob demanda** e liberado ao fim (`torch.cuda.empty_cache()`):
  convive com o whisper STT que já ocupa ~1.9GB na GPU. Cold start ~10-15s no
  primeiro áudio; síntese em si ~2-5s.
- **100% local**: não há chamada de rede exceto o `sendVoice` ao Telegram.

## Credenciais e config

Token e chat_id são lidos **automaticamente do Kiro Crew** (`telegram.bot_token` e `telegram.allowed_user_ids` do `config.json`). Nenhum arquivo extra é necessário.

Variáveis opcionais (engine, voz, velocidade) podem ser configuradas em `~/.kiro/crew/.secrets/voxlocal.env`:

```
VOX_ENGINE=auto           # edge | f5 | piper | auto
VOX_EDGE_VOICE=pt-BR-AntonioNeural
VOX_DEVICE=cuda
VOX_SPEED=0.9
VOX_REF_AUDIO=<path para o áudio de referência .wav>
VOX_REF_TEXT=<transcrição literal do áudio de referência>
```

Ver `docs/configuracao.md` para a lista completa.

## Setup do venv (uma vez — pip pesado, rodar no terminal)

O torch + f5-tts NÃO vêm no venv (sumiram no rebuild do 0.7.x). Instalar no
venv real do Kiro Crew:

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
# torch com CUDA 12.1
$VP install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
# F5-TTS (traz vocos, transformers etc.)
$VP install f5-tts
# piper-tts leve, só para gerar o áudio de referência do clone (faber pt-BR, MIT)
$VP install piper-tts
```

Depois validar: `vox_say.sh --health` deve mostrar torch cuda_available=True,
f5-tts ok, ffmpeg ok, ref_audio ok, bot_token/chat_id ok.

## Áudio de referência (voice clone)

F5-TTS NÃO sintetiza sem um áudio de referência (~6-10s) que define o timbre.
Gerar com a voz Piper faber pt-BR como ponto de partida:

```bash
FRASE="Esta é uma amostra de voz de referência para síntese de fala em português."
VPY=~/.kiro/crew-venv-current/bin/python3
REF_WAV=~/.kiro/crew/models/f5-tts/ref/voz_ref.wav
mkdir -p "$(dirname $REF_WAV)"
echo "$FRASE" | $VPY -m piper \
  --model ~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx \
  --output_file "$REF_WAV"
# setar VOX_REF_TEXT="$FRASE" e VOX_REF_AUDIO="$REF_WAV" no voxlocal.env
```

Trocar por voz personalizada depois: gravar ~10s limpos, salvar no path configurado
em `VOX_REF_AUDIO`, atualizar `VOX_REF_TEXT` com a transcrição literal.

## Notas

- ffmpeg já instalado no Mint (6.1.1).
- VRAM: F5-TTS usa ~2-3GB + whisper STT ~1.9GB → pode ser apertado em GPUs de 6GB; por isso F5-TTS é carregado sob demanda.
- Se der OOM: parar/aliviar o STT, ou usar `VOX_DEVICE=cpu` (lento, ~30s+).
