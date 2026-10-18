# voxlocal — F5-TTS e Voice Clone

O engine `f5` usa **F5-TTS** — um modelo de síntese por _voice cloning_: em vez de uma voz fixa, ele copia o timbre de um áudio de referência que você fornece. Isso significa que a voz da síntese é a voz do arquivo de referência.

---

## Como o voice clone funciona

```
[áudio de referência ~6-10s]  +  [transcrição literal]  →  F5-TTS aprende o timbre
                                                          ↓
                               [texto a sintetizar]  →  F5-TTS gera na voz clonada
```

Dois parâmetros definem a voz:

| Chave | O que é |
|-------|---------|
| `ref_audio` | Arquivo `.wav` com ~6-10s de voz limpa. Define o **timbre** (quem fala). |
| `ref_text`  | Transcrição **literal** do que é falado no `ref_audio`. O modelo usa isso para alinhar o áudio. |

> Se `ref_text` não bater com o que está no áudio, a síntese fica distorcida. Precisa ser literal — palavra por palavra.

---

## Qualidade da referência

| Tipo de referência | Qualidade | Notas |
|-------------------|-----------|-------|
| Voz humana real (~10s limpos) | ★★★★★ | Melhor resultado. Gravar num ambiente silencioso. |
| Gerada pelo Piper (TTS) | ★★★☆☆ | Funcional. Voz sintética, dicção robótica no resultado. |
| Áudio com ruído de fundo | ★★☆☆☆ | F5-TTS tenta clonar o ruído também. |
| Menos de 3s | ★☆☆☆☆ | Muito curto — síntese fica instável. |

**Dica:** gravar a frase de referência num ambiente silencioso, com microfone próximo, sem eco. 6-10s é o ideal.

---

## Procedimento: trocar a voz de referência

### Opção A — voz humana (melhor resultado)

1. Gravar ~10s de voz limpa em `.wav` (44100Hz, mono, sem ruído)
2. Salvar em qualquer path (ex: `~/.kiro/crew/models/f5-tts/ref/minha_voz.wav`)
3. Anotar a transcrição literal do que foi falado
4. Configurar:

```bash
python3 tools/config.py set ref_audio "~/.kiro/crew/models/f5-tts/ref/minha_voz.wav"
python3 tools/config.py set ref_text  "Transcrição exata do que eu disse no áudio."
```

5. Testar:

```bash
python3 tools/vox_say.py --self-test
```

### Opção B — usar o script `set_voice.py` (interativo)

O script guia o processo: escolhe o arquivo, transcreve (ou aceita digitação manual), configura e testa.

```bash
python3 tools/set_voice.py
```

### Opção C — gerar referência com Piper (sem microfone)

Cria uma referência sintética usando a voz faber do Piper. Resultado funcional mas menos natural.

```bash
CREW_HOME="${KIROCREW_HOME:-$HOME/.kiro/crew}"
VPY=~/.kiro/crew-venv-current/bin/python3
FRASE="Esta é uma amostra de voz de referência para síntese de fala em português."
REF="$CREW_HOME/models/f5-tts/ref/voz_ref.wav"

mkdir -p "$(dirname $REF)"
echo "$FRASE" | $VPY -m piper \
  --model "$CREW_HOME/models/piper/pt_BR-faber-medium.onnx" \
  --output_file "$REF"

python3 tools/config.py set ref_audio "$REF"
python3 tools/config.py set ref_text  "$FRASE"
```

---

## Ajuste fino da síntese

Após trocar a referência, ajustar para a nova voz:

```bash
# Velocidade — menor = mais devagar (padrão: 0.9)
python3 tools/config.py set speed 0.85

# Qualidade — mais passos = melhor dicção, mais lento (padrão: 32)
python3 tools/config.py set nfe_step 48

# Testar e ajustar até ficar natural
python3 tools/vox_say.py "Testando a nova voz de referência."
```

---

## Modelos disponíveis

O checkpoint usado é o `firstpixel/F5-TTS-pt-br` — fine-tuned em português brasileiro. É um modelo separado do F5-TTS base (inglês).

| Arquivo | Tamanho | O que é |
|---------|---------|---------|
| `pt-br/model_last.safetensors` | ~1.35GB | Checkpoint pt-br (pesos do modelo) |
| `F5TTS_Base/vocab.txt` | ~KB | Vocabulário (fonemas pt-br) |

Os modelos ficam em `$CREW_HOME/models/f5-tts/` — fora do venv, não somem no auto-update.

---

## Comportamento de memória GPU

O F5-TTS **carrega sob demanda** e libera a VRAM ao fim de cada síntese:

```
[chamada]  →  carrega modelo (~10-15s cold start, ~1.35GB VRAM)
           →  sintetiza (~2-5s)
           →  libera VRAM (torch.cuda.empty_cache())
[próxima chamada]  →  carrega de novo (mas mais rápido, já está em cache de disco)
```

Isso permite conviver com o whisper STT, que fica residente. Se a VRAM for insuficiente (< ~2.5GB livre), usar `--engine edge` ou `--engine piper`.
