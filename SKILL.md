---
name: voxlocal
description: Use when the user asks to send an audio message or TTS to Telegram, or when a voice summary should be sent proactively. Generates speech in pt-BR and sends as Telegram voice message (sendVoice). Three engines: Edge-TTS (Microsoft online, no GPU, default), F5-TTS (local GPU, voice clone), Piper (local CPU, offline). Triggers include 'manda um áudio', 'fala isso no Telegram', 'TTS', 'resumo em áudio', 'vox', 'voice message'.
inclusion: auto
---

# voxlocal — TTS pt-BR para Telegram

Skill de síntese de voz com 3 engines. Envia voice message diretamente no Telegram via `sendVoice`.

## Regras de uso

- **Só no Telegram.** No dashboard não usar: ele tem o TTS nativo do Kiro Crew (`voice_reply.provider`).
- **Quando enviar** (sob demanda ou proativo) é regra do usuário, definida no steering dele. Sem essa regra, enviar só quando o usuário pedir áudio.
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
| `install_f5` | `false` | `true` = o `install.py` reinstala o F5-TTS a cada update (`install.py --f5` grava) |

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

## Instalação

```bash
python3 ~/.kiro/skills/voxlocal/tools/install.py          # edge + piper (baixa a voz pt-BR do Piper)
python3 ~/.kiro/skills/voxlocal/tools/install.py --f5     # inclui o F5-TTS (opt-in, ~2,5 GB)
python3 ~/.kiro/skills/voxlocal/tools/install.py --dry-run
```

O update do Kiro Crew recria o venv e apaga esses pacotes. A skill `crew-setup` roda o
`install.py` sozinha depois do update quando a voxlocal está vinculada; sem ela, rode o
comando acima. O `install.py` também desliga o áudio nativo do gateway no Telegram
(`voice_reply.enabled` e `telegram.voice_replies`), que duplicaria o da voxlocal.

O F5-TTS é opt-in porque traz ~128 pacotes (torch incluso) para o venv do próprio Kiro
Crew e pode trocar versões que o Crew usa. Checkpoint pt-br e voz de referência:
`docs/instalacao.md`.

## Erros Comuns

| Sintoma | Causa | Correção |
|---------|-------|----------|
| `telegram.bot_token não encontrado` | Telegram não configurado no Kiro Crew | Settings > Channels > Telegram |
| `piper: AUSENTE` / `edge-tts: AUSENTE` | venv recriado no update do Kiro Crew | `python3 tools/install.py` (ou o `crew-setup`) |
| `torch: AUSENTE` / `f5-tts: AUSENTE` | F5-TTS não instalado (é opt-in) | `python3 tools/install.py --f5`; o `auto` funciona sem ele |
| F5 roda na CPU (lento) | `device=cpu` ou VRAM insuficiente | `config.py set device cuda` |
| `edge falhou ... fallback` | sem internet | esperado no `auto`; usa F5/Piper |
| áudio muito rápido (F5) | speed alto | `config.py set speed 0.85` |
| dicção robótica (F5) | ref gerada por Piper | gravar ref de voz humana + `nfe_step 48` |
| OOM na GPU | F5 + whisper STT juntos | F5 é sob demanda; se persistir usar `--engine piper` |
| `.wav` automático chegando | `voice_reply.enabled` ou `telegram.voice_replies` = true no Kiro Crew | `python3 tools/install.py` desliga os dois |

## Notas

- F5-TTS carrega sob demanda e libera a VRAM ao fim — convive com o whisper STT.
- Cold start do F5 ~10-15s (primeira vez na sessão); síntese em si ~2-5s.
- Em GPUs com ~6GB VRAM, F5 + whisper pode ser apertado. Usar `engine=edge` nesses casos.
