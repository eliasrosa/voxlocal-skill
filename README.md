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

Criar `~/.kiro/crew/.secrets/voxlocal.env` (chmod 600):

```
VOX_BOT_TOKEN=<token do @BotFather>
VOX_CHAT_ID=<seu chat_id no Telegram>
VOX_ENGINE=auto
```

Ver `docs/configuracao.md` para todas as variáveis.

## Uso

```bash
bash tools/vox_say.sh "texto a sintetizar"
bash tools/vox_say.sh --health           # diagnóstico completo
bash tools/vox_say.sh --engine edge      # trocar engine padrão
```

## Ferramentas

| Script | Uso |
|--------|-----|
| `tools/check.py` | Pré-check: valida requisitos (exit 0/1) |
| `tools/vox_say.sh` | Wrapper principal: sintetiza e envia voice message |
| `tools/vox_say.py` | Implementação Python (chamado pelo wrapper) |

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
│   ├── configuracao.md # todas as variáveis de env
│   └── runbook.md     # troubleshooting e operações
└── tools/
    ├── check.py       # pré-check de requisitos
    ├── vox_say.sh     # wrapper bash
    └── vox_say.py     # implementação Python
```

## Licença

MIT
