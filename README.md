# voxlocal

Skill do [Kiro Crew](https://kiro.dev) para síntese de voz pt-BR com envio de voice message inline no Telegram.

Suporta 3 engines: **F5-TTS** local na GPU (voice clone), **Edge-TTS** Microsoft online, e **Piper** offline sem GPU.

## Requisitos

| Item | Tipo | Como instalar |
|------|------|---------------|
| Python 3.10+ | Runtime | pré-instalado na maioria dos sistemas |
| `ffmpeg` | Ferramenta | `sudo apt install ffmpeg` |
| Venv do Kiro Crew | Runtime | `~/.kiro/crew-venv-current/` |
| Bot do Telegram | Credencial | criar em @BotFather |
| `edge-tts` + `httpx` | Pacote | `pip install edge-tts httpx` (engine edge) |
| `piper-tts` | Pacote | `pip install piper-tts` (engine piper) |
| `torch` + `f5-tts` | Pacote | ver Instalação abaixo (engine f5, GPU) |

Verificar tudo:

```bash
python3 tools/check.py
```

## Instalação

```bash
git clone https://github.com/eliasrosa/voxlocal-skill ~/.kiro/skills/voxlocal
```

### Mínimo (edge + piper, sem GPU)

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

### Completo (+ F5-TTS na GPU, ~3GB VRAM)

```bash
VP=~/.kiro/crew-venv-current/bin/pip3
$VP install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
$VP install f5-tts
```

Ver `docs/instalacao.md` para baixar o checkpoint pt-br e gerar o áudio de referência.

## Configuração

**Credenciais (token, chat_id) são lidas automaticamente do Kiro Crew** — nenhum arquivo extra necessário.

Variáveis de comportamento ficam em `.data/config.json` (gitignored):

```bash
python3 tools/config.py                          # ver configuração atual
python3 tools/config.py set engine edge          # trocar engine padrão
python3 tools/config.py set edge_voice pt-BR-AntonioNeural
python3 tools/config.py set speed 0.85
```

Ver `docs/configuracao.md` para a lista completa de chaves.

> ⚠️ Verificar que `voice_reply.enabled = false` no `config.json` do Kiro Crew — evita conflito de áudio automático pelo gateway.

## Uso

```bash
bash tools/vox_say.sh "texto a sintetizar"
bash tools/vox_say.sh --health           # diagnóstico completo
bash tools/vox_say.sh --engine edge      # trocar engine padrão
```

## Ferramentas

| Script | Uso |
|--------|-----|
| `tools/check.py` | Pré-check: valida requisitos + Telegram no Kiro Crew (exit 0/1) |
| `tools/config.py` | Lê/grava `.data/config.json` (engine, voz, velocidade, paths) |
| `tools/vox_say.sh` | Wrapper principal: sintetiza e envia voice message |
| `tools/vox_say.py` | Implementação Python (lê Kiro Crew + config.json) |

## Engines

| Engine | GPU? | Rede? | Qualidade | Velocidade |
|--------|------|-------|-----------|------------|
| `edge` | não | sim | ★★★★☆ | ~3-4s |
| `f5` | sim | não | ★★★☆☆ | ~5-15s |
| `piper` | não | não | ★★☆☆☆ | ~2-5s |

`auto` (default): tenta `edge` → fallback `f5` → fallback `piper`.

## Compatibilidade

| Ambiente | Suporte |
|----------|---------|
| Linux + GPU NVIDIA | ✅ Completo (todos os engines) |
| Linux sem GPU | ✅ edge + piper |
| macOS | ⚠️ edge + piper (ffmpeg e ffmpeg necessários) |
| Windows | ⚠️ WSL2 recomendado |

## Estrutura

```
voxlocal/
├── SKILL.md           # instruções para o agente
├── README.md          # este arquivo
├── .gitignore
├── docs/
│   ├── instalacao.md  # setup detalhado dos 3 engines
│   ├── configuracao.md # chaves do config.json
│   └── runbook.md     # troubleshooting e operações
└── tools/
    ├── check.py       # pré-check de requisitos + Kiro Crew
    ├── config.py      # lê/grava .data/config.json
    ├── vox_say.sh     # wrapper bash
    └── vox_say.py     # implementação Python
```

## Licença

MIT
