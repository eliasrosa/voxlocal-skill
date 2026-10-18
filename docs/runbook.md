# voxlocal — Runbook

Procedimentos operacionais e troubleshooting.

## Trocar o engine padrão

```bash
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --engine edge    # Microsoft online
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --engine f5      # GPU local
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --engine piper   # offline CPU
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --engine auto    # híbrido (default)
```

Override só numa chamada (não persiste):

```bash
VOX_ENGINE=piper bash ~/.kiro/skills/voxlocal/tools/vox_say.sh "texto"
```

## Trocar a voz do Edge

Editar `VOX_EDGE_VOICE` no env. Vozes pt-BR: `pt-BR-FranciscaNeural` (fem),
`pt-BR-AntonioNeural` (masc), `pt-BR-ThalitaMultilingualNeural` (fem).

## Ajustar ritmo / dicção

- **F5**: `VOX_SPEED` (0.85-0.95) e `VOX_NFE_STEP` (32-48; mais = melhor, mais lento).
- **Piper**: `VOX_PIPER_LENGTH_SCALE` (>1 = mais devagar).

## Trocar a voz de referência do F5 (voice clone)

1. Gravar ~10s de voz limpa → `~/.kiro/crew/models/f5-tts/ref/voz_ref.wav`
2. Atualizar `VOX_REF_TEXT` com a transcrição literal do que foi falado.
   Voz humana real melhora muito a dicção vs. a referência gerada por Piper.

## Troubleshooting

| Sintoma | Causa provável | Fix |
|---------|----------------|-----|
| `torch: AUSENTE` / `f5-tts: AUSENTE` no health | venv recriado no auto-update | reinstalar (ver `docs/instalacao.md`) |
| `httpx.ReadTimeout` no envio | rede lenta no upload | subir `VOX_SEND_TIMEOUT` no env |
| `edge falhou ... fallback` | sem internet | esperado no `auto`; usa F5/Piper |
| áudio muito rápido (F5) | speed alto | baixar `VOX_SPEED` (ex 0.85) |
| dicção robótica (F5) | ref gerada por Piper | usar ref de voz humana + subir `VOX_NFE_STEP` |
| `sendVoice falhou 401/404` | token errado | conferir `VOX_BOT_TOKEN` (bot desta conta) |
| chega `.wav` automático (não é o voxlocal) | Piper nativo do gateway | `config.json`: `voice_reply.enabled=false` E `telegram.voice_replies=false` |
| OOM na GPU | F5 + whisper STT juntos | F5 é sob demanda; se persistir, usar `--engine piper` ou `edge` |

## Verificar uso de GPU (F5)

```bash
watch -n 1 nvidia-smi   # a VRAM sobe ~1.2GB durante a síntese e volta depois
```

## Health check

```bash
bash ~/.kiro/skills/voxlocal/tools/vox_say.sh --health
```
Deve listar: ffmpeg ok, torch cuda_available=True (se GPU), f5-tts ok, edge-tts ok,
piper ok + model ok, engine, ref_audio ok, bot_token/chat_id ok.
