# voxlocal

Skill do [Kiro Crew](https://kiro.dev) para síntese de voz pt-BR com envio de voice message inline no Telegram.

Suporta 3 engines: **Edge-TTS** (Microsoft online, sem GPU), **F5-TTS** (GPU local, voice clone) e **Piper** (offline, CPU).

## Engines

| Engine | GPU? | Rede? | Qualidade | Velocidade | Peso |
|--------|------|-------|-----------|------------|------|
| `edge` | não | **sim** | ★★★★☆ melhor dicção | ~3-4s | ~0 (online) |
| `f5` | **sim** | não | ★★★☆☆ voice clone | ~5-15s cold, ~2-5s warm | ~1.35GB + torch |
| `piper` | não | não | ★★☆☆☆ robótica | ~2-5s | ~60MB |

`auto` (default): tenta `edge` → fallback `f5` → fallback `piper`.

> **Edge-TTS** usa o endpoint público do Microsoft Edge browser — gratuito, sem conta Azure.

## Requisitos

| Item | Tipo | Como instalar |
|------|------|---------------|
| Python 3.10+ | Runtime | pré-instalado na maioria dos sistemas |
| `ffmpeg` | Ferramenta | `sudo apt install ffmpeg` |
| Venv do Kiro Crew | Runtime | `~/.kiro/crew-venv-current/` |
| Telegram configurado no Kiro Crew | Credencial | Settings > Channels > Telegram |
| `edge-tts` + `httpx` | Pacote Python | ver Instalação — engine `edge` |
| `piper-tts` | Pacote Python | ver Instalação — engine `piper` |
| `torch` + `f5-tts` | Pacote Python | ver Instalação — engine `f5` (GPU) |

Verificar tudo:

```bash
python3 tools/check.py
```

## Instalação

```bash
git clone https://github.com/eliasrosa/voxlocal-skill ~/.kiro/skills/voxlocal
```

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

### Completo — adiciona F5-TTS na GPU (~3GB VRAM)

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
$VP install f5-tts
```

Ver `docs/instalacao.md` para baixar o checkpoint pt-br e gerar o áudio de referência do voice clone.

## Configuração

**Token e chat_id são lidos automaticamente do Kiro Crew** — nenhum arquivo extra necessário.

Variáveis de comportamento ficam em `.data/config.json` (gitignored, persiste entre `git pull`):

```bash
python3 tools/config.py                              # ver configuração atual
python3 tools/config.py set engine edge              # trocar engine padrão
python3 tools/config.py set edge_voice pt-BR-AntonioNeural  # trocar voz
python3 tools/config.py set speed 0.85               # ritmo do F5-TTS
python3 tools/config.py reset                        # restaurar defaults
```

O arquivo `.data/config.json` só precisa conter o que foi alterado — o resto usa defaults:

```json
{ "engine": "edge", "edge_voice": "pt-BR-AntonioNeural" }
```

Ver `docs/configuracao.md` para a referência completa de chaves.

> ⚠️ Verificar que `voice_reply.enabled = false` no `config.json` do Kiro Crew para evitar conflito de áudio automático pelo gateway.

## Uso

```bash
# Sintetizar e enviar voice message
python3 tools/vox_say.py "texto aqui"

# Diagnóstico completo (ffmpeg, pacotes, Kiro Crew, modelos)
python3 tools/vox_say.py --health

# Enviar frase de teste
python3 tools/vox_say.py --self-test

# Trocar engine padrão (persiste em .data/config.json)
python3 tools/vox_say.py --engine edge     # ou f5 | piper | auto

# Override pontual sem persistir
VOX_ENGINE=f5 python3 tools/vox_say.py "texto"
```

## Ferramentas

| Script | Uso |
|--------|-----|
| `tools/check.py` | Pré-check: valida requisitos + Telegram no Kiro Crew (exit 0/1) |
| `tools/config.py` | Lê/grava `.data/config.json` |
| `tools/vox_say.py` | Script principal: sintetiza e envia voice message (auto-seleciona venv) |
| `tools/vox_say.py` | Implementação Python |

## Compatibilidade

| Ambiente | Suporte |
|----------|---------|
| Linux + GPU NVIDIA | ✅ Completo (todos os engines) |
| Linux sem GPU | ✅ edge + piper |
| macOS | ⚠️ edge + piper (requer `ffmpeg` via Homebrew) |
| Windows | ⚠️ WSL2 recomendado |

## Estrutura

```
voxlocal/
├── SKILL.md            # instruções para o agente Kiro Crew
├── README.md           # este arquivo
├── .gitignore          # exclui .data/ (dados locais)
├── docs/
│   ├── instalacao.md   # setup detalhado dos 3 engines + voice clone
│   ├── configuracao.md # referência completa das chaves do config.json
│   └── runbook.md      # troubleshooting e operações do dia a dia
└── tools/
    ├── check.py        # pré-check de requisitos (exit 0/1)
    ├── config.py       # lê/grava .data/config.json
    └── vox_say.py      # script principal (auto-seleciona venv do Kiro Crew via re-exec)
```

## Licença

MIT
