#!/usr/bin/env bash
# Installs the TTS engine(s) needed for a course: install.sh <engine> [<engine>...] [--g2p misaki-ja|misaki-zh]
set -x
sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg espeak-ng >/dev/null
pip install -q soundfile numpy
for e in "$@"; do
  case "$e" in
    kokoro) pip install -q kokoro-onnx ;;
    misaki-ja) pip install -q "misaki[ja]" && (python -m unidic download >/dev/null 2>&1 || true) ;;
    misaki-zh) pip install -q "misaki[zh]" ;;
    piper) pip install -q piper-tts ;;
    supertonic) pip install -q supertonic ;;
    melo) pip install -q git+https://github.com/myshell-ai/MeloTTS.git && python -m unidic download >/dev/null 2>&1 ;;
    whisper) pip install -q faster-whisper ;;
  esac
done
exit 0
