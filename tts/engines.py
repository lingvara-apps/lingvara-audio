"""TTS engines for Lingvara multi-language audio. Each engine: Engine(cfg).synth(text, voice) -> (float32 mono np.array, sr)."""
import json, os, re, subprocess, urllib.request
import numpy as np

CACHE = os.environ.get("TTS_MODELS", "models")
END = re.compile(r"[.!?…。！？؟]$")


def fetch(url, dst):
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        urllib.request.urlretrieve(url, dst + ".part")
        os.rename(dst + ".part", dst)
    return dst


def terminate(text, lang):
    if END.search(text):
        return text
    return text + ("。" if lang in ("ja", "cmn", "zh") else ".")


class Kokoro:
    def __init__(self, cfg):
        from kokoro_onnx import Kokoro as K
        if cfg.get("model") == "v1.1-zh":
            base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/"
            self.k = K(fetch(base + "kokoro-v1.1-zh.onnx", f"{CACHE}/kokoro-v1.1-zh.onnx"),
                       fetch(base + "voices-v1.1-zh.bin", f"{CACHE}/voices-v1.1-zh.bin"))
        else:
            base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
            self.k = K(fetch(base + "kokoro-v1.0.onnx", f"{CACHE}/kokoro.onnx"),
                       fetch(base + "voices-v1.0.bin", f"{CACHE}/voices.bin"))
        self.lang = cfg.get("lang", "en-us")
        self.g2p = None
        g = cfg.get("g2p")
        if g == "misaki-ja":
            from misaki import ja
            self.g2p = ja.JAG2P()
        elif g == "misaki-zh":
            from misaki import zh
            self.g2p = zh.ZHG2P(version="1.1") if cfg.get("model") == "v1.1-zh" else zh.ZHG2P()

    def synth(self, text, voice, speed=1.0):
        text = terminate(text, self.lang)
        if self.g2p:
            ph = self.g2p(text)
            ph = ph[0] if isinstance(ph, tuple) else ph
            s, sr = self.k.create(ph, voice=voice, speed=speed, is_phonemes=True)
        else:
            s, sr = self.k.create(text, voice=voice, speed=speed, lang=self.lang)
        return np.asarray(s, dtype=np.float32), sr


class Piper:
    HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

    def __init__(self, cfg):
        from piper import PiperVoice
        self.PV = PiperVoice
        self.voices = {}
        self.cfg = cfg

    def _voice(self, name):
        if name not in self.voices:
            lang, spk, q = name.split("-")
            path = f"{lang.split('_')[0]}/{lang}/{spk}/{q}/{name}"
            onnx = fetch(self.HF + path + ".onnx", f"{CACHE}/piper/{name}.onnx")
            fetch(self.HF + path + ".onnx.json", f"{CACHE}/piper/{name}.onnx.json")
            self.voices[name] = self.PV.load(onnx)
        return self.voices[name]

    def synth(self, text, voice, speed=1.0):
        v = self._voice(voice)
        text = terminate(text, "")
        try:  # piper-tts >= 1.3
            chunks = list(v.synthesize(text))
            a = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
            return a, chunks[0].sample_rate
        except (AttributeError, TypeError):
            import io, wave
            buf = io.BytesIO()
            with wave.open(buf, "wb") as w:
                v.synthesize(text, w)
            buf.seek(0)
            with wave.open(buf) as w:
                sr = w.getframerate()
                a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
            return a, sr


class Supertonic:
    def __init__(self, cfg):
        from supertonic import TTS
        self.tts = TTS(auto_download=True)
        self.lang = cfg.get("st_lang") or cfg.get("lang", "en").split("-")[0]
        self.styles = {}
        self.sr = getattr(self.tts, "sample_rate", None) or 44100

    def synth(self, text, voice, speed=1.0):
        if voice not in self.styles:
            self.styles[voice] = self.tts.get_voice_style(voice_name=voice)
        text = terminate(text, self.lang)
        kw = {}
        steps = os.environ.get("SUPERTONIC_STEPS")
        if steps:
            kw["total_steps"] = int(steps)
        wav, _ = self.tts.synthesize(text, voice_style=self.styles[voice], lang=self.lang, **kw)
        return np.asarray(wav, dtype=np.float32).reshape(-1), self.sr


class Melo:
    def __init__(self, cfg):
        from melo.api import TTS
        self.m = TTS(language=cfg.get("melo_lang", "KR"), device="cpu")
        self.spk = self.m.hps.data.spk2id

    def synth(self, text, voice, speed=1.0):
        import soundfile as sf, tempfile
        sid = self.spk[voice] if voice in self.spk else list(self.spk.values())[0]
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            self.m.tts_to_file(terminate(text, ""), sid, f.name, speed=speed, quiet=True)
            a, sr = sf.read(f.name, dtype="float32")
        return a, sr


ENGINES = {"kokoro": Kokoro, "piper": Piper, "supertonic": Supertonic, "melo": Melo}


def load(cfg):
    return ENGINES[cfg["engine"]](cfg)


class Router:
    """Voice ids may name another engine: "supertonic:M1" (e.g. a French male voice while the course uses Kokoro).
    Optional ids: "name@0.84" = pitch factor (applied in encode)."""

    def __init__(self, cfg):
        self.cfg, self.e = cfg, {}

    def get(self, voice):
        eng, _, v = voice.rpartition(":")
        eng = eng or self.cfg["engine"]
        if eng not in self.e:
            self.e[eng] = ENGINES[eng](dict(self.cfg, engine=eng))
        return self.e[eng], v

    def synth(self, text, voice):
        v, _, pitch = voice.partition("@")
        e, name = self.get(v)
        a, sr = e.synth(text, name)
        return a, sr, float(pitch or 1)


# Post-processing identical to the English pipeline (tts/gen_full.py)
AF = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
      "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
      "adelay=120:all=1,apad=pad_dur=0.25,loudnorm=I=-18:TP=-2:LRA=11")


def encode(audio, sr, mp3, tempo, pitch=1.0):
    """float32 mono → 24 kHz 40 kbps mp3, trimmed/padded/normalised like English."""
    pre = ""
    if pitch != 1.0:  # optional pitch shift (keeps duration)
        pre = f"asetrate={int(sr * pitch)},aresample={sr},atempo={1 / pitch:.4f},"
    af = pre + (f"atempo={tempo}," if tempo != 1.0 else "") + AF
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                        "-af", af, "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "40k", mp3],
                       input=np.ascontiguousarray(audio, dtype=np.float32).tobytes(), capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode()[-300:])
