# voxlocal — Runbook

Procedimentos operacionais e troubleshooting.

## Trocar o engine padrão

```bash
bash tools/vox_say.sh --engine edge    # Microsoft online (sem GPU, precisa de rede)
bash tools/vox_say.sh --engine f5      # F5-TTS local na GPU
bash tools/vox_say.sh --engine piper   # Piper offline na CPU
bash tools/vox_say.sh --engine auto    # híbrido edge→f5→piper (default)
```

Override pontual sem persistir:

```bash
VOX_ENGINE=piper bash tools/vox_say.sh "texto"
```

## Trocar a voz do Edge

```bash
python3 tools/config.py set edge_voice pt-BR-AntonioNeural       # masculina
python3 tools/config.py set edge_voice pt-BR-FranciscaNeural     # feminina
python3 tools/config.py set edge_voice pt-BR-ThalitaMultilingualNeural  # feminina multilíngue
```

## Ajustar ritmo / dicção

**F5-TTS:**
```bash
python3 tools/config.py set speed 0.85     # mais devagar (0.85–0.95)
python3 tools/config.py set nfe_step 48    # melhor dicção, mais lento (32–48)
```

**Piper:**
```bash
python3 tools/config.py set piper_length_scale 1.2  # mais devagar (>1)
```

**Edge-TTS:** velocidade não é configurável — a voz online tem ritmo fixo por voz.

## Trocar a voz de referência do F5 (voice clone)

```bash
# Configurar nova referência
python3 tools/config.py set ref_audio "/caminho/para/nova_ref.wav"   # ~6-10s
python3 tools/config.py set ref_text  "transcrição literal do áudio"
```

Voz humana real melhora muito a dicção vs. a referência gerada por Piper.

## Verificar configuração atual

```bash
python3 tools/config.py         # todas as chaves e valores
python3 tools/config.py reset   # restaurar defaults
```

## Troubleshooting

| Sintoma | Causa provável | Fix |
|---------|----------------|-----|
| `telegram.bot_token não encontrado` | Telegram não configurado no Kiro Crew | Settings > Channels > Telegram |
| `torch: AUSENTE` / `f5-tts: AUSENTE` | venv recriado no auto-update | reinstalar — ver `docs/instalacao.md` |
| `httpx.ReadTimeout` no envio | rede lenta no upload | `config.py set send_timeout 120` |
| `edge falhou ... fallback` | sem internet | esperado no `auto`; usa F5/Piper |
| áudio muito rápido (F5) | speed alto | `config.py set speed 0.85` |
| dicção robótica (F5) | ref gerada por Piper | usar ref de voz humana real + `config.py set nfe_step 48` |
| OOM na GPU | F5 + whisper STT juntos ao mesmo tempo | F5 carrega sob demanda; se persistir usar `--engine piper` ou `edge` |
| `.wav` chegando automaticamente no Telegram | `voice_reply.enabled=true` no Kiro Crew | `config.json` do Kiro Crew: `voice_reply.enabled=false` e `telegram.voice_replies=false` |
| GPU incompatível com F5-TTS | compute capability < 7.0 | `python3 tools/check.py` para diagnóstico; usar `--engine edge` |

## Verificar uso de GPU durante síntese

```bash
watch -n 1 nvidia-smi   # VRAM sobe ~1.2-3GB durante a síntese e libera ao fim
```

## Health check completo

```bash
bash tools/vox_say.sh --health
```

Deve listar: ffmpeg ok, torch cuda_available=True (se GPU), f5-tts ok, edge-tts ok,
piper ok + model ok, engine configurado, ref_audio ok, bot_token/chat_id ok.
