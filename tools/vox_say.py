#!/usr/bin/env python3
# Re-exec automático para o venv do Kiro Crew — deve ficar ANTES de qualquer import
# de pacote pesado (torch, f5-tts, edge-tts), pois eles só existem no venv.
import os as _os, sys as _sys
_VENV_PY = _os.path.expanduser("~/.kiro/crew-venv-current/bin/python3")
if _os.path.isfile(_VENV_PY) and not _sys.executable.startswith(
    _os.path.expanduser("~/.kiro/crew")
):
    _os.execv(_VENV_PY, [_VENV_PY] + _sys.argv)

"""voxlocal — TTS local pt-BR com envio via Telegram sendVoice.

Suporta 3 engines: F5-TTS local na GPU, Edge-TTS Microsoft online, Piper offline.

Fluxo: texto -> engine escolhido -> wav -> ffmpeg OGG/Opus -> Telegram sendVoice.

Uso:
    python3 vox_say.py "texto do resumo"   # sintetiza e envia a voice message
    python3 vox_say.py --health            # checa GPU, modelo, ffmpeg, credenciais
    python3 vox_say.py --self-test         # sintetiza uma frase curta e envia
    python3 vox_say.py --engine edge       # define engine padrão (persiste em config.json)

Credenciais (token, chat_id) lidas do config do Kiro Crew — nunca via arquivo.
Config de comportamento lida de .data/config.json via tools/config.py.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

# Adiciona o diretório tools/ ao path para importar config.py
sys.path.insert(0, str(Path(__file__).parent))
import config as _config_module

CREW_CONFIG  = os.path.expanduser("~/.kiro/crew/config.json")


def _load_crew_credentials() -> dict:
    """Lê bot_token e chat_id diretamente do config do Kiro Crew (fonte da verdade)."""
    try:
        cfg = json.loads(open(CREW_CONFIG, encoding="utf-8").read())
        tg = cfg.get("telegram", {})
        token   = tg.get("bot_token", "")
        allowed = tg.get("allowed_user_ids", [])
        chat_id = str(allowed[0]) if allowed else ""
        if not token:
            _die("telegram.bot_token não encontrado no config do Kiro Crew.\n"
                 "Configure o Telegram em Settings > Channels.")
        if not chat_id:
            _die("telegram.allowed_user_ids vazio no config do Kiro Crew.\n"
                 "Configure o Telegram em Settings > Channels.")
        return {"VOX_BOT_TOKEN": token, "VOX_CHAT_ID": chat_id}
    except SystemExit:
        raise
    except Exception as e:
        _die(f"Erro ao ler config do Kiro Crew: {e}")


def _load_config() -> dict:
    """Monta o dict de configuração completo.

    Prioridade (maior para menor):
      1. Variável de ambiente do processo (override pontual: VOX_ENGINE=f5 ...)
      2. Kiro Crew config.json (credenciais: token e chat_id)
      3. .data/config.json (variáveis de comportamento com defaults)
    """
    # Base: config.json com defaults
    cfg_data = _config_module.load()

    # Mapeia chaves do config.json para o formato VOX_* esperado internamente
    env = {
        "VOX_ENGINE":             str(cfg_data.get("engine",       "auto")),
        "VOX_EDGE_VOICE":         str(cfg_data.get("edge_voice",   "pt-BR-AntonioNeural")),
        "VOX_EDGE_TIMEOUT":       str(cfg_data.get("edge_timeout", 10)),
        "VOX_DEVICE":             str(cfg_data.get("device",       "cuda")),
        "VOX_SPEED":              str(cfg_data.get("speed",        0.9)),
        "VOX_NFE_STEP":           str(cfg_data.get("nfe_step",     32)),
        "VOX_OPUS_BITRATE":       str(cfg_data.get("opus_bitrate", "32k")),
        "VOX_SEND_TIMEOUT":       str(cfg_data.get("send_timeout", 60)),
        "VOX_MAX_CHARS":          str(cfg_data.get("max_chars",    600)),
        "VOX_PIPER_MODEL":        str(cfg_data.get("piper_model",  "")),
        "VOX_PIPER_LENGTH_SCALE": str(cfg_data.get("piper_length_scale", 1.1)),
        "VOX_REF_AUDIO":          str(cfg_data.get("ref_audio",   "")),
        "VOX_REF_TEXT":           str(cfg_data.get("ref_text",    "")),
        "VOX_CKPT":               str(cfg_data.get("f5_ckpt",     "")),
        "VOX_VOCAB":              str(cfg_data.get("f5_vocab",    "")),
    }

    # Credenciais do Kiro Crew (sobrescrevem qualquer coisa)
    env.update(_load_crew_credentials())

    # Env vars do processo têm precedência final (override pontual)
    for k in list(env.keys()):
        if k in os.environ:
            env[k] = os.environ[k]

    return env


def _die(msg: str, code: int = 1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)



def _to_ogg(src_wav: str, dst_ogg: str, bitrate: str = "32k") -> None:
    """Converte wav -> OGG/Opus (formato voice message do Telegram)."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_wav, "-c:a", "libopus", "-b:a", bitrate, dst_ogg],
        check=True, capture_output=True,
    )


def _synth_edge(text: str, wav_out: str, cfg: dict) -> None:
    """Sintetiza com Microsoft Edge-TTS (online). Gera mp3 e converte pra wav.
    Voz configurável (VOX_EDGE_VOICE, default Francisca). Levanta em falha/timeout
    para o chamador cair no fallback F5 quando engine=auto.
    """
    import asyncio
    import edge_tts  # import tardio

    voice = cfg.get("VOX_EDGE_VOICE", "pt-BR-FranciscaNeural")
    timeout = float(cfg.get("VOX_EDGE_TIMEOUT", "10"))
    mp3 = wav_out.replace(".wav", ".mp3")

    async def _run():
        comm = edge_tts.Communicate(text, voice)
        await asyncio.wait_for(comm.save(mp3), timeout=timeout)

    asyncio.run(_run())
    # normaliza pra wav (o _send_voice converte pra ogg depois)
    subprocess.run(["ffmpeg", "-y", "-i", mp3, wav_out], check=True, capture_output=True)


def _synth_piper(text: str, wav_out: str, cfg: dict) -> None:
    """Sintetiza com Piper (offline, CPU, sem GPU). Engine leve e portável (~60MB
    de modelo), ideal para máquinas sem placa. Voz faber pt-BR por padrão.

    Config: VOX_PIPER_MODEL (path do .onnx), VOX_PIPER_LENGTH_SCALE (ritmo, >1 = mais
    lento). Roda o piper-tts como módulo do venv (python -m piper).
    """
    model = cfg.get("VOX_PIPER_MODEL",
                    os.path.expanduser("~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx"))
    if not os.path.isfile(model):
        _die(f"VOX_PIPER_MODEL ausente: {model}")
    length = cfg.get("VOX_PIPER_LENGTH_SCALE", "1.1")  # >1 = fala mais devagar
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", model,
         "--length-scale", str(length), "-f", wav_out],
        input=text.encode(), check=True, capture_output=True,
    )


def _synth(text: str, wav_out: str, cfg: dict) -> str:
    """Roteia a síntese pelo engine escolhido. Retorna o engine efetivamente usado.

    VOX_ENGINE:
      'edge'  = Microsoft Edge-TTS online (melhor dicção, sem GPU, precisa de rede)
      'f5'    = F5-TTS local na GPU (offline, voz clone)
      'piper' = Piper offline na CPU (leve/portável ~60MB, sem GPU nem rede)
      'auto'  = Edge -> fallback F5 (se F5 indisponível, cai no Piper)
    Precedência: env var do processo > VOX_ENGINE do arquivo.
    """
    engine = cfg.get("VOX_ENGINE", "auto").lower()
    if engine == "f5":
        _synth_f5(text, wav_out, cfg); return "f5"
    if engine == "edge":
        _synth_edge(text, wav_out, cfg); return "edge"
    if engine == "piper":
        _synth_piper(text, wav_out, cfg); return "piper"
    # auto: Edge primeiro; fallback F5; se F5 falhar, Piper
    try:
        _synth_edge(text, wav_out, cfg); return "edge"
    except Exception as e:
        print(f"edge falhou ({type(e).__name__}), fallback local", file=sys.stderr)
        try:
            _synth_f5(text, wav_out, cfg); return "f5"
        except Exception as e2:
            print(f"f5 falhou ({type(e2).__name__}), fallback piper", file=sys.stderr)
            _synth_piper(text, wav_out, cfg); return "piper"


def _synth_f5(text: str, wav_out: str, cfg: dict) -> None:
    """Sintetiza `text` com F5-TTS pt-br na GPU. Carrega o modelo sob demanda e
    libera a VRAM ao fim (para conviver com o whisper STT residente na GPU).

    Requer: f5-tts + torch instalados no venv. Config via env:
      VOX_REF_AUDIO  áudio de referência (.wav ~6-10s) que define a voz
      VOX_REF_TEXT   transcrição literal do áudio de referência
      VOX_DEVICE     cuda (default) | cpu
      VOX_MODEL_DIR  dir do checkpoint pt-br (default ~/.kiro/crew/models/f5-tts)
    """
    import torch  # noqa: F401  (import tardio: só quando sintetiza)
    from importlib import import_module

    device = cfg.get("VOX_DEVICE", "cuda")
    ref_audio = cfg.get("VOX_REF_AUDIO", "")
    ref_text = cfg.get("VOX_REF_TEXT", "")
    if not ref_audio or not os.path.isfile(ref_audio):
        _die(f"VOX_REF_AUDIO ausente ou inexistente: {ref_audio!r} "
             "(grave ~6-10s de voz de referência e aponte no env)")

    try:
        f5_api = import_module("f5_tts.api")
    except ModuleNotFoundError:
        _die("f5-tts não instalado no venv. Rode o pip install (ver SKILL.md).")

    # F5TTS() baixa/carrega o checkpoint pt-br. Carregado aqui, some ao retornar (GC).
    f5 = f5_api.F5TTS(
        model=cfg.get("VOX_MODEL", "F5TTS_Base"),
        ckpt_file=cfg.get("VOX_CKPT", ""),
        vocab_file=cfg.get("VOX_VOCAB", ""),
        device=device,
    )
    f5.infer(
        ref_file=ref_audio,
        ref_text=ref_text,
        gen_text=text,
        file_wave=wav_out,
        speed=float(cfg.get("VOX_SPEED", "0.9")),
        nfe_step=int(cfg.get("VOX_NFE_STEP", "32")),
        remove_silence=True,
    )
    # libera a VRAM explicitamente (não deixa o modelo residente brigando com o STT)
    del f5
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def _send_voice(text: str, wav: str, cfg: dict) -> dict:
    """Converte o wav e envia como voice message via Telegram sendVoice."""
    import httpx  # import tardio

    token = cfg.get("VOX_BOT_TOKEN", "")
    chat_id = cfg.get("VOX_CHAT_ID", "")
    if not token:
        _die("VOX_BOT_TOKEN ausente — configure o Telegram no Kiro Crew (Settings > Channels)")
    if not chat_id:
        _die("VOX_CHAT_ID ausente — configure o Telegram no Kiro Crew (Settings > Channels)")

    ogg = wav.replace(".wav", ".ogg")
    _to_ogg(wav, ogg, cfg.get("VOX_OPUS_BITRATE", "32k"))

    url = f"https://api.telegram.org/bot{token}/sendVoice"
    send_timeout = float(cfg.get("VOX_SEND_TIMEOUT", "60"))
    with open(ogg, "rb") as f:
        r = httpx.post(
            url,
            data={"chat_id": chat_id},
            files={"voice": ("voice.ogg", f, "audio/ogg")},
            timeout=send_timeout,
        )
    if r.status_code != 200 or not r.json().get("ok"):
        _die(f"Telegram sendVoice falhou: HTTP {r.status_code} {r.text[:200]}", 2)
    return {"ok": True, "message_id": r.json().get("result", {}).get("message_id")}


def cmd_say(text: str, cfg: dict) -> None:
    text = text.strip()
    if not text:
        _die("texto vazio")
    max_chars = int(cfg.get("VOX_MAX_CHARS", "600"))
    if max_chars > 0 and len(text) > max_chars:
        _die(f"texto too_long: {len(text)} > {max_chars} chars "
             "(quebrar em partes antes de chamar)", 3)

    workdir = tempfile.mkdtemp(prefix="voxlocal_", dir=os.environ.get("KIROCREW_SCRATCH"))
    wav = os.path.join(workdir, f"{uuid.uuid4().hex}.wav")
    started = time.perf_counter()
    try:
        engine_used = _synth(text, wav, cfg)
        res = _send_voice(text, wav, cfg)
        dur = round((time.perf_counter() - started) * 1000)
        print(f"OK engine={engine_used} mode={cfg.get('VOX_ENGINE','auto')} "
              f"duration_ms={dur} chars={len(text)} msg_id={res.get('message_id')}")
    finally:
        for fn in os.listdir(workdir):
            try:
                os.remove(os.path.join(workdir, fn))
            except OSError:
                pass
        try:
            os.rmdir(workdir)
        except OSError:
            pass


def cmd_health(cfg: dict) -> None:
    print("=== voxlocal health ===")
    # ffmpeg
    try:
        v = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        print(f"ffmpeg: {'ok' if v.returncode == 0 else 'FALHOU'}")
    except FileNotFoundError:
        print("ffmpeg: AUSENTE")
    # torch + cuda
    try:
        import torch
        print(f"torch: {torch.__version__}  cuda_available={torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"gpu: {torch.cuda.get_device_name(0)}")
    except ModuleNotFoundError:
        print("torch: AUSENTE (rode o pip install — ver SKILL.md)")
    # f5-tts
    try:
        import f5_tts  # noqa: F401
        print("f5-tts: ok")
    except ModuleNotFoundError:
        print("f5-tts: AUSENTE (rode o pip install — ver SKILL.md)")
    # edge-tts (Microsoft online)
    try:
        import edge_tts  # noqa: F401
        print(f"edge-tts: ok  voice={cfg.get('VOX_EDGE_VOICE','pt-BR-FranciscaNeural')}")
    except ModuleNotFoundError:
        print("edge-tts: AUSENTE (pip install edge-tts)")
    # piper (offline, sem GPU)
    try:
        import piper  # noqa: F401
        pm = cfg.get("VOX_PIPER_MODEL", os.path.expanduser("~/.kiro/crew/models/piper/pt_BR-faber-medium.onnx"))
        print(f"piper: ok  model={'ok' if os.path.isfile(pm) else 'AUSENTE ' + pm}")
    except ModuleNotFoundError:
        print("piper: AUSENTE (pip install piper-tts)")
    print(f"engine (VOX_ENGINE): {cfg.get('VOX_ENGINE','auto')}")
    # referência de voz
    ref = cfg.get("VOX_REF_AUDIO", "")
    print(f"ref_audio: {'ok ' + ref if os.path.isfile(ref) else 'AUSENTE ' + repr(ref)}")
    # credenciais (só presença, nunca valor)
    print(f"bot_token: {'ok' if cfg.get('VOX_BOT_TOKEN') else 'AUSENTE'}")
    print(f"chat_id:   {'ok' if cfg.get('VOX_CHAT_ID') else 'AUSENTE'}")


def main() -> None:
    args = sys.argv[1:]
    cfg = _load_config()

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--health":
        cmd_health(cfg)
        return
    if args[0] == "--engine":
        # persiste engine no config.json via config.py
        if len(args) < 2 or args[1] not in ("edge", "f5", "piper", "auto"):
            _die("uso: --engine edge|f5|piper|auto", 4)
        import config as _cfg
        c = _cfg.load()
        c["engine"] = args[1]
        _cfg.save(c)
        print(f"engine = {args[1]} (persistido em .data/config.json)")
        return
    if args[0] == "--self-test":
        cmd_say("Teste do voxlocal, síntese de voz funcionando.", cfg)
        return
    cmd_say(args[0], cfg)


if __name__ == "__main__":
    main()
