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

**Vozes pt-BR disponíveis (engine `edge`):**

| Voz | Gênero |
|-----|--------|
| `pt-BR-AntonioNeural` *(default)* | Masculina |
| `pt-BR-FranciscaNeural` | Feminina |
| `pt-BR-ThalitaMultilingualNeural` | Feminina (multilíngue) |

```bash
python3 tools/config.py set edge_voice pt-BR-FranciscaNeural
```

## Requisitos

| Item | Tipo | Como instalar |
|------|------|---------------|
| Python 3.10+ | Runtime | pré-instalado na maioria dos sistemas |
| `ffmpeg` | Ferramenta | `sudo apt install ffmpeg` |
| Venv do Kiro Crew | Runtime | `~/.kiro/crew-venv-current/` |
| Telegram configurado no Kiro Crew | Credencial | Settings > Channels > Telegram |
| `edge-tts`, `httpx`, `piper-tts` + voz Piper pt-BR | Pacotes + modelo | `python3 tools/install.py` |
| `torch` + `f5-tts` (opcional) | Pacotes | `python3 tools/install.py --f5` |

Verificar tudo:

```bash
python3 tools/check.py
```

## Instalação

```bash
git clone https://github.com/eliasrosa/voxlocal-skill ~/.kiro/skills/voxlocal
python3 ~/.kiro/skills/voxlocal/tools/install.py
```

O `install.py` instala no venv do Kiro Crew os pacotes que faltam, baixa a voz pt-BR do
Piper (~60 MB) e desliga o áudio nativo do gateway no Telegram, que duplicaria o da
voxlocal. É idempotente: rode de novo depois de cada update do Kiro Crew, que recria o
venv. A skill [crew-setup](https://github.com/eliasrosa/kirocrew-setup-skill) faz isso
sozinha quando a voxlocal está vinculada.

O F5-TTS (voice clone na GPU) é opt-in: `python3 tools/install.py --f5`. Ele traz ~128
pacotes (~2,5 GB, torch incluso) para o venv do Kiro Crew. Checkpoint pt-br e voz de
referência: `docs/instalacao.md`.

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

> ⚠️ `voice_reply.enabled` e `telegram.voice_replies` precisam ficar `false` no Kiro Crew, senão o gateway também manda áudio. O `install.py` desliga os dois e o `check.py` avisa se voltarem.

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
| `tools/install.py` | Instala/restaura pacotes e a voz Piper no venv do Kiro Crew (idempotente; `--f5`, `--dry-run`) |
| `tools/config.py` | Lê/grava `.data/config.json` |
| `tools/set_voice.py` | Configura a voz de referência do F5-TTS (interativo ou `--piper`) |
| `tools/vox_say.py` | Script principal: sintetiza e envia voice message (auto-seleciona venv) |

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
│   ├── f5-voice-clone.md # como funciona o voice clone, trocar voz, ajuste fino
│   └── runbook.md      # troubleshooting e operações do dia a dia
└── tools/
    ├── check.py        # pré-check de requisitos (exit 0/1)
    ├── install.py      # instala/restaura dependências no venv do Kiro Crew
    ├── config.py       # lê/grava .data/config.json
    ├── set_voice.py    # configura voz de referência do F5-TTS
    └── vox_say.py      # script principal (auto-seleciona venv do Kiro Crew via re-exec)
```

## Licença

MIT
