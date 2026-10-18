---
name: voxlocal
description: Use when the user asks to send an audio message or TTS to Telegram, or when a voice summary should be sent proactively. Generates speech in pt-BR and sends as Telegram voice message (sendVoice). Three engines: Edge-TTS (Microsoft online, no GPU, default), F5-TTS (local GPU, voice clone), Piper (local CPU, offline). Triggers include 'manda um áudio', 'fala isso no Telegram', 'TTS', 'resumo em áudio', 'vox', 'voice message'.
inclusion: auto
---

# voxlocal — TTS pt-BR para Telegram

Skill de síntese de voz com 3 engines. Envia voice message diretamente no Telegram via `sendVoice`.

## Regras de uso

- **Só no Telegram, só sob demanda** — quando o usuário pedir áudio explicitamente.
- **NUNCA** enviar automaticamente sem pedido.
- No **dashboard** NÃO usar — o dashboard usa o Piper nativo do Kiro Crew.
- Teto de **600 chars** por chamada. Resposta longa → quebrar em 2-3 partes em sequência.
- Texto sem markdown, URL ou código. Ideal ~350-450 chars por áudio.

## Comando

```bash
python3 ~/.kiro/skills/voxlocal/tools/vox_say.py "texto aqui"
```

Outros modos:

```bash
python3 ~/.kiro/skills/voxlocal/tools/vox_say.py --health      # diagnóstico completo
python3 ~/.kiro/skills/voxlocal/tools/vox_say.py --self-test   # envia frase de teste
python3 ~/.kiro/skills/voxlocal/tools/vox_say.py --engine edge # troca engine padrão
```

## Engines

| Engine | GPU? | Rede? | Qualidade | Velocidade | Peso |
|--------|------|-------|-----------|------------|------|
| `edge` | não | **sim** | ★★★★☆ melhor dicção | ~3-4s | ~0 (online) |
| `f5` | **sim** | não | ★★★☆☆ voice clone | ~5-15s cold, ~2-5s warm | ~1.35GB + torch |
| `piper` | não | não | ★★☆☆☆ robótica | ~2-5s | ~60MB |

`auto` (default): tenta `edge` → fallback `f5` → fallback `piper`.

**Edge-TTS** usa o mesmo endpoint público que o Microsoft Edge browser — gratuito, sem conta Azure.

Trocar engine padrão (persiste em `.data/config.json`):

```bash
python3 ~/.kiro/skills/voxlocal/tools/vox_say.py --engine edge   # ou f5 | piper | auto
```

Override pontual (só na chamada, não persiste):

```bash
VOX_ENGINE=f5 python3 ~/.kiro/skills/voxlocal/tools/vox_say.py "texto"
```

## Configuração

Token e chat_id são lidos **automaticamente do Kiro Crew** — nenhum arquivo extra necessário.

Variáveis de comportamento ficam em `.data/config.json` (gitignored, persiste entre atualizações):

```bash
python3 ~/.kiro/skills/voxlocal/tools/config.py                     # ver config atual
python3 ~/.kiro/skills/voxlocal/tools/config.py set engine edge      # trocar engine
python3 ~/.kiro/skills/voxlocal/tools/config.py set edge_voice pt-BR-AntonioNeural
python3 ~/.kiro/skills/voxlocal/tools/config.py set speed 0.85
```

### Chaves de configuração

**Engine:**

| Chave | Default | Valores |
|-------|---------|---------|
| `engine` | `auto` | `edge` \| `f5` \| `piper` \| `auto` |

**Edge-TTS (Microsoft online):**

| Chave | Default | Descrição |
|-------|---------|-----------|
| `edge_voice` | `pt-BR-AntonioNeural` | `pt-BR-AntonioNeural` (masc) \| `pt-BR-FranciscaNeural` (fem) \| `pt-BR-ThalitaMultilingualNeural` (fem) |
| `edge_timeout` | `10` | Timeout (s) antes de cair no fallback |

**F5-TTS (GPU local, voice clone):**

| Chave | Default | Descrição |
|-------|---------|-----------|
| `device` | `cuda` | `cuda` \| `cpu` (cpu ~30s+, lento) |
| `speed` | `0.9` | Ritmo da fala — menor = mais devagar (0.85-1.0) |
| `nfe_step` | `32` | Passos de inferência — mais = melhor dicção, mais lento (32-48) |
| `ref_audio` | *(ver instalação)* | Path do áudio de referência ~6-10s (define o timbre) |
| `ref_text` | *(ver instalação)* | Transcrição literal do áudio de referência |
| `f5_ckpt` | *(ver instalação)* | Path do checkpoint pt-br (.safetensors) |
| `f5_vocab` | *(ver instalação)* | Path do vocab.txt |

**Piper (offline, CPU):**

| Chave | Default | Descrição |
|-------|---------|-----------|
| `piper_model` | `~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx` | Model .onnx |
| `piper_length_scale` | `1.1` | Ritmo — maior = mais devagar |

**Envio / geral:**

| Chave | Default | Descrição |
|-------|---------|-----------|
| `opus_bitrate` | `32k` | Bitrate do OGG/Opus enviado |
| `send_timeout` | `60` | Timeout (s) do upload ao Telegram |
| `max_chars` | `600` | Teto de chars por chamada (0 = sem limite) |

## Pré-check

```bash
python3 ~/.kiro/skills/voxlocal/tools/check.py
```

Valida: ffmpeg, Python 3.10+, pacotes no venv, Telegram configurado no Kiro Crew, modelos presentes.

## Instalação de engines

**Mínimo (edge + piper, sem GPU):**

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

**Completo (+ F5-TTS na GPU, ~3GB VRAM):**

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
$VP install f5-tts
```

Baixar checkpoint pt-br e gerar áudio de referência:

```bash
VPY=~/.kiro/crew-venv-current/bin/python3
$VPY -c "
from huggingface_hub import hf_hub_download
import os; d = os.path.expanduser('~/.kiro/crew/models/f5-tts')
hf_hub_download('firstpixel/F5-TTS-pt-br','pt-br/model_last.safetensors',local_dir=d)
hf_hub_download('SWivid/F5-TTS','F5TTS_Base/vocab.txt',local_dir=d)
"
# Gerar áudio de referência com Piper faber
FRASE="Esta é uma amostra de voz de referência para síntese de fala em português."
REF=~/.kiro/crew/models/f5-tts/ref/voz_ref.wav
mkdir -p "$(dirname $REF)"
echo "$FRASE" | $VPY -m piper \
  --model ~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx \
  --output_file "$REF"
# Configurar os paths
python3 ~/.kiro/skills/voxlocal/tools/config.py set ref_audio "$REF"
python3 ~/.kiro/skills/voxlocal/tools/config.py set ref_text "$FRASE"
```

> Trocar por voz humana depois: gravar ~10s limpos, salvar no path de `ref_audio`, atualizar `ref_text` com a transcrição literal.

## Erros Comuns

| Sintoma | Causa | Correção |
|---------|-------|----------|
| `telegram.bot_token não encontrado` | Telegram não configurado no Kiro Crew | Settings > Channels > Telegram |
| `torch: AUSENTE` / `f5-tts: AUSENTE` | venv recriado no auto-update | reinstalar (ver Instalação acima) |
| STT roda mas na CPU | `device=cpu` ou VRAM insuficiente | `config.py set device cuda` |
| `edge falhou ... fallback` | sem internet | esperado no `auto`; usa F5/Piper |
| áudio muito rápido (F5) | speed alto | `config.py set speed 0.85` |
| dicção robótica (F5) | ref gerada por Piper | gravar ref de voz humana + `nfe_step 48` |
| OOM na GPU | F5 + whisper STT juntos | F5 é sob demanda; se persistir usar `--engine piper` |
| `.wav` automático chegando | `voice_reply.enabled=true` no Kiro Crew | `config.json` do Kiro Crew: `voice_reply.enabled=false` |

## Notas

- F5-TTS carrega sob demanda e libera a VRAM ao fim — convive com o whisper STT.
- Cold start do F5 ~10-15s (primeira vez na sessão); síntese em si ~2-5s.
- Em GPUs com ~6GB VRAM, F5 + whisper pode ser apertado. Usar `engine=edge` nesses casos.
