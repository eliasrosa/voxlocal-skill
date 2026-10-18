# voxlocal — Configuração

Configuração via `.data/config.json` (gitignored, persiste entre `git pull`).
Credenciais (token, chat_id) são lidas do Kiro Crew — não ficam aqui.

## Gerenciar configuração

```bash
python3 tools/config.py                      # ver configuração atual
python3 tools/config.py set <chave> <valor>  # alterar um valor
python3 tools/config.py reset                # restaurar todos os defaults
```

Override pontual (só na chamada, não persiste no config.json):

```bash
VOX_ENGINE=f5 python3 tools/vox_say.py "texto"
```

## Referência completa de chaves

### Engine

| Chave | Default | Valores |
|-------|---------|---------|
| `engine` | `auto` | `edge` \| `f5` \| `piper` \| `auto` (tenta edge→f5→piper) |

### Edge-TTS — Microsoft online, sem GPU, precisa de internet

| Chave | Default | Descrição |
|-------|---------|-----------|
| `edge_voice` | `pt-BR-AntonioNeural` | Voz pt-BR a usar (ver tabela abaixo) |
| `edge_timeout` | `10` | Timeout (s) da síntese antes de cair no fallback |

**Vozes pt-BR disponíveis:**

| Voz | Gênero | Personalidade |
|-----|--------|---------------|
| `pt-BR-AntonioNeural` | Masculina | Friendly, Positive |
| `pt-BR-FranciscaNeural` | Feminina | Friendly, Positive |
| `pt-BR-ThalitaMultilingualNeural` | Feminina | Friendly, Positive |

> Edge-TTS usa o endpoint público do Microsoft Edge browser — gratuito, sem conta Azure.

### F5-TTS — GPU local, voice clone, offline

| Chave | Default | Descrição |
|-------|---------|-----------|
| `device` | `cuda` | `cuda` \| `cpu` (cpu muito lento, ~30s+) |
| `speed` | `0.9` | Ritmo da fala — menor = mais devagar (recomendado: 0.85–0.95) |
| `nfe_step` | `32` | Passos de inferência — mais = melhor dicção, mais lento (recomendado: 32–48) |
| `ref_audio` | `~/.kiro/crew/models/f5-tts/ref/voz_ref.wav` | Path do áudio de referência ~6-10s (define o timbre) |
| `ref_text` | *(frase padrão)* | Transcrição literal do áudio de referência |
| `f5_ckpt` | `~/.kiro/crew/models/f5-tts/pt-br/model_last.safetensors` | Checkpoint pt-br |
| `f5_vocab` | `~/.kiro/crew/models/f5-tts/F5TTS_Base/vocab.txt` | Vocabulário |

### Piper — offline, CPU, sem GPU

| Chave | Default | Descrição |
|-------|---------|-----------|
| `piper_model` | `~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx` | Model .onnx |
| `piper_length_scale` | `1.1` | Ritmo — maior = mais devagar |

### Envio / geral

| Chave | Default | Descrição |
|-------|---------|-----------|
| `opus_bitrate` | `32k` | Bitrate do OGG/Opus enviado ao Telegram |
| `send_timeout` | `60` | Timeout (s) do upload ao Telegram (para redes lentas) |
| `max_chars` | `600` | Teto de chars por chamada (0 = sem limite) |

## Exemplo de config.json mínimo

O arquivo só precisa conter o que foi alterado — o resto usa os defaults:

```json
{
  "engine": "edge",
  "edge_voice": "pt-BR-AntonioNeural",
  "speed": 0.85
}
```
