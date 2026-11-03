# voxlocal — Instalação

Skill de TTS pt-BR com **3 engines** e envio de voice message inline no Telegram.
Funciona com ou sem GPU.

## Engines

| Engine | GPU? | Rede? | Qualidade | Velocidade | Peso |
|--------|------|-------|-----------|------------|------|
| `edge` | não | **sim** | ★★★★☆ melhor dicção | ~3-4s | ~0 (online) |
| `f5` | **sim** | não | ★★★☆☆ voice clone | ~5-15s | ~1.35GB + torch |
| `piper` | não | não | ★★☆☆☆ robótica | ~2-5s | ~60MB |

`auto` (default): tenta `edge` → cai pro `f5` → cai pro `piper`. O F5-TTS é opcional:
sem ele, o `auto` usa o Edge e, sem rede, o Piper.

## Requisitos comuns

- Python 3.10+ no venv do Kiro Crew (`~/.kiro/crew-venv-current/`)
- `ffmpeg`: `sudo apt install ffmpeg`
- Telegram configurado no Kiro Crew (Settings > Channels) — token e chat_id são lidos automaticamente

## Instalar (edge + piper)

```bash
python3 tools/install.py
```

Instala `edge-tts`, `httpx` e `piper-tts` no venv do Kiro Crew, baixa a voz pt-BR do Piper
(`pt_BR-faber-medium`, ~60 MB) em `~/.kiro/crew/models/piper/` e desliga o áudio nativo do
gateway no Telegram (`voice_reply.enabled` e `telegram.voice_replies`), que duplicaria o da
voxlocal. É idempotente; `--dry-run` mostra o que faria sem alterar nada.

## Adicionar o F5-TTS (GPU, voice clone)

Requer GPU NVIDIA com compute capability ≥ 7.0 e ~3GB VRAM (`python3 tools/check.py`
confere). O F5 traz ~128 pacotes (~2,5 GB, torch incluso) para o venv do próprio Kiro
Crew e pode trocar versões que o Crew usa (ex.: pillow), por isso é opt-in.

1. Pacotes. O `--f5` também grava `install_f5 = true`, para os próximos updates
   reinstalarem o F5:

   ```bash
   python3 tools/install.py --f5
   ```

2. Checkpoint pt-br (~1,35 GB):

   ```bash
   VPY=~/.kiro/crew-venv-current/bin/python3
   $VPY - <<'PY'
   import os
   from huggingface_hub import hf_hub_download
   home = os.environ.get("KIROCREW_HOME") or os.path.expanduser("~/.kiro/crew")
   d = os.path.join(home, "models/f5-tts")
   hf_hub_download("firstpixel/F5-TTS-pt-br", "pt-br/model_last.safetensors", local_dir=d)
   hf_hub_download("SWivid/F5-TTS", "F5TTS_Base/vocab.txt", local_dir=d)
   PY
   ```

3. Voz de referência: `python3 tools/set_voice.py --piper` gera uma sintética, sem
   microfone; `python3 tools/set_voice.py` usa uma gravação sua. Detalhes e ajuste fino em
   `docs/f5-voice-clone.md`.

4. Usar: `python3 tools/vox_say.py --engine f5`, ou manter o `auto`, que usa o F5 como
   fallback do Edge.

Desfazer o opt-in: `python3 tools/config.py set install_f5 false` (os pacotes saem no
próximo update do Kiro Crew).

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
python3 tools/vox_say.py --health                       # health check
python3 tools/vox_say.py "teste de voz funcionando"     # teste real
```

## Depois de um update do Kiro Crew

O update recria o venv e os pacotes somem; os modelos em `~/.kiro/crew/models/` ficam.
Rode `python3 tools/install.py` de novo (ele reinstala o F5-TTS se `install_f5 = true`).
A skill [crew-setup](https://github.com/eliasrosa/kirocrew-setup-skill) faz isso sozinha
quando a voxlocal está vinculada a ela.
